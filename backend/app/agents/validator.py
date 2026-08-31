"""Decision validation and execution pipeline.

Implements the core safety architecture:

    LLM decision
        Schema validation   (Pydantic, at decision parse time)
        Permission validation
        State validation
        Domain action
        Database persistence

The LLM never touches the database. The validator translates a validated
Decision into concrete ORM mutations and persisted events/decisions.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.agents.decisions import (
    ACTION_AUTHORITY,
    ActionType,
    AgentDecision,
)
from app.enums import (
    GoalStatus,
    IncidentStatus,
    ObjectiveStatus,
    PlanStatus,
    ProjectStatus,
    ResourceType,
    RiskSeverity,
    RiskStatus,
    TaskStatus,
)
from app.models.agent import Agent
from app.models.company import Company
from app.models.decision import Decision
from app.models.event import Event
from app.models.goal import Goal
from app.models.milestone import Milestone
from app.models.message import Message
from app.models.plan import Plan, PlanStep
from app.models.product_feature import ProductFeature
from app.models.project import Project
from app.models.task import Task

logger = logging.getLogger("agent_company_simulator")


@dataclass
class ActionResult:
    """Outcome of validating and executing a decision."""

    success: bool
    message: str
    events: list[Event] = field(default_factory=list)
    decision: Decision | None = None


class DecisionValidator:
    """Validates and executes agent decisions against live simulation state."""

    def __init__(self, db: Session, agent: Agent, company: Company) -> None:
        self.db = db
        self.agent = agent
        self.company = company

    def _ctx(self, day: int | None = None):
        """Build a lightweight SimulationContext for system calls."""
        from app.simulation.domain import SimulationContext, make_rng
        d = day if day is not None else self.company.current_day
        return SimulationContext(
            db=self.db,
            company=self.company,
            day=d,
            rng=make_rng(self.company.seed, d),
        )

    # --- public entry point ---

    def execute(self, decision: AgentDecision) -> ActionResult:
        """Validate and execute a decision.

        Any failure is captured in the returned ActionResult; the simulation
        never crashes because of an invalid decision.
        """
        try:
            with self.db.begin_nested():
                return self._run(decision)
        except Exception as exc:
            logger.exception(
                "Unhandled error executing decision for agent %s: %s",
                self.agent.id,
                exc,
            )
            return ActionResult(
                success=False,
                message=f"Internal error: {type(exc).__name__}",
            )

    # --- pipeline ---

    def _run(self, decision: AgentDecision) -> ActionResult:
        if decision.action == ActionType.NO_ACTION:
            return self._handle_no_action(decision)

        perm_error = self._check_permissions(decision)
        if perm_error is not None:
            return self._rejected(decision, perm_error)

        handler = self._HANDLERS.get(decision.action)
        if handler is None:
            return self._rejected(decision, f"Unsupported action: {decision.action.value}")

        result = handler(self, decision)
        if not result.success:
            return result  # already a rejection with message

        record = Decision(
            company_id=self.company.id,
            agent_id=self.agent.id,
            action=decision.action.value,
            reasoning=decision.reasoning,
            context=decision.model_dump(mode="json"),
            outcome=result.message,
            simulation_day=self.company.current_day,
        )
        result.decision = record
        return result

    # --- permission / authority checks ---

    def _check_permissions(self, decision: AgentDecision) -> str | None:
        required = ACTION_AUTHORITY.get(decision.action, 99)
        if self.agent.authority < required:
            return (
                f"Authority {self.agent.authority} insufficient for "
                f"{decision.action.value} (requires {required})"
            )
        return None

    # --- helpers ---

    def _company_agent(self, agent_id: int) -> Agent | None:
        agent = self.db.get(Agent, agent_id)
        if agent is not None and agent.company_id == self.company.id:
            return agent
        return None

    def _company_task(self, task_id: int) -> Task | None:
        task = self.db.get(Task, task_id)
        if task is not None and task.company_id == self.company.id:
            return task
        return None

    def _company_goal(self, goal_id: int) -> Goal | None:
        goal = self.db.get(Goal, goal_id)
        if goal is not None and goal.company_id == self.company.id:
            return goal
        return None

    def _company_project(self, project_id: int) -> Project | None:
        project = self.db.get(Project, project_id)
        if project is not None and project.company_id == self.company.id:
            return project
        return None

    @staticmethod
    def _priority_value(priority: str | None) -> int:
        if priority == "HIGH":
            return 3
        if priority == "LOW":
            return 1
        return 2  # MEDIUM / default

    def _rejected(self, decision: AgentDecision, reason: str) -> ActionResult:
        logger.info(
            "Decision rejected for agent %s (%s): %s",
            self.agent.id,
            self.agent.role.value,
            reason,
        )
        record = Decision(
            company_id=self.company.id,
            agent_id=self.agent.id,
            action=decision.action.value,
            reasoning=decision.reasoning,
            context=decision.model_dump(mode="json"),
            outcome=f"REJECTED: {reason}",
            simulation_day=self.company.current_day,
        )
        event = Event(
            company_id=self.company.id,
            actor_id=self.agent.id,
            event_type="DECISION",
            description=f"Decision rejected: {reason}",
            target_type="agent",
            target_id=self.agent.id,
            meta={
                "action": decision.action.value,
                "rejected": True,
                "reason": reason,
            },
            simulation_day=self.company.current_day,
        )
        return ActionResult(success=False, message=reason, events=[event], decision=record)

    # --- handlers ---

    def _handle_no_action(self, decision: AgentDecision) -> ActionResult:
        record = Decision(
            company_id=self.company.id,
            agent_id=self.agent.id,
            action=ActionType.NO_ACTION.value,
            reasoning=decision.reasoning,
            context=decision.model_dump(mode="json"),
            outcome="No action taken.",
            simulation_day=self.company.current_day,
        )
        return ActionResult(
            success=True,
            message="No action taken.",
            events=[
                Event(
                    company_id=self.company.id,
                    actor_id=self.agent.id,
                    event_type="DECISION",
                    description=f"{self.agent.role.value} decided to take no action.",
                    target_type="agent",
                    target_id=self.agent.id,
                    meta={"action": ActionType.NO_ACTION.value},
                    simulation_day=self.company.current_day,
                )
            ],
            decision=record,
        )

    def _handle_create_task(self, decision: AgentDecision) -> ActionResult:
        if not decision.title:
            return self._rejected(decision, "CREATE_TASK requires a title.")
        if not decision.description:
            return self._rejected(decision, "CREATE_TASK requires a description.")

        assignee: Agent | None = None
        if decision.target_agent_id is not None:
            assignee = self._company_agent(decision.target_agent_id)
            if assignee is None:
                return self._rejected(decision, "Assignee does not belong to the company.")

        priority = self._priority_value(decision.priority)
        task = Task(
            company_id=self.company.id,
            project_id=decision.project_id,
            title=decision.title,
            description=decision.description or "",
            created_by=self.agent.id,
            assigned_to=assignee.id if assignee else None,
            priority=priority,
            status=TaskStatus.TODO,
            progress=0.0,
        )
        self.db.add(task)
        self.db.flush()

        event = Event(
            company_id=self.company.id,
            actor_id=self.agent.id,
            event_type="TASK_CREATED",
            description=(
                f"Task '{task.title}' created by {self.agent.role.value}"
                + (f" and assigned to {assignee.name}" if assignee else "")
                + "."
            ),
            target_type="task",
            target_id=task.id,
            meta={
                "action": ActionType.CREATE_TASK.value,
                "task_id": task.id,
                "assignee_id": assignee.id if assignee else None,
            },
            simulation_day=self.company.current_day,
        )

        return ActionResult(
            success=True,
            message=f"Task '{task.title}' created.",
            events=[event],
        )

    def _handle_assign_task(self, decision: AgentDecision) -> ActionResult:
        if decision.task_id is None:
            return self._rejected(decision, "ASSIGN_TASK requires a task_id.")
        task = self._company_task(decision.task_id)
        if task is None:
            return self._rejected(decision, "Task does not exist or belongs to another company.")
        if decision.target_agent_id is None:
            return self._rejected(decision, "ASSIGN_TASK requires a target_agent_id.")
        target = self._company_agent(decision.target_agent_id)
        if target is None:
            return self._rejected(decision, "Target agent does not belong to the company.")

        previous_assignee = task.assigned_to
        task.assigned_to = target.id
        self.db.flush()

        event = Event(
            company_id=self.company.id,
            actor_id=self.agent.id,
            event_type="TASK_CREATED",
            description=(
                f"Task '{task.title}' assigned to {target.name} by {self.agent.role.value}."
            ),
            target_type="task",
            target_id=task.id,
            meta={
                "action": ActionType.ASSIGN_TASK.value,
                "task_id": task.id,
                "assignee_id": target.id,
                "previous_assignee_id": previous_assignee,
            },
            simulation_day=self.company.current_day,
        )

        return ActionResult(
            success=True,
            message=f"Task '{task.title}' assigned to {target.name}.",
            events=[event],
        )

    def _handle_update_task(self, decision: AgentDecision) -> ActionResult:
        if decision.task_id is None:
            return self._rejected(decision, "UPDATE_TASK requires a task_id.")
        task = self._company_task(decision.task_id)
        if task is None:
            return self._rejected(decision, "Task does not exist or belongs to another company.")

        if task.status == TaskStatus.COMPLETED:
            return self._rejected(decision, "Cannot update a completed task.")

        changed: list[str] = []
        if decision.status is not None:
            try:
                task.status = TaskStatus(decision.status)
            except ValueError:
                return self._rejected(decision, f"Invalid task status: {decision.status}")
            changed.append(f"status={task.status.value}")
        if decision.progress is not None:
            task.progress = max(0.0, min(100.0, decision.progress))
            changed.append(f"progress={task.progress}")
        if decision.title is not None:
            task.title = decision.title
            changed.append("title")
        self.db.flush()

        if not changed:
            return self._rejected(decision, "UPDATE_TASK provided no updatable fields.")

        event = Event(
            company_id=self.company.id,
            actor_id=self.agent.id,
            event_type="TASK_CREATED",
            description=(
                f"Task '{task.title}' updated by {self.agent.role.value}: "
                + ", ".join(changed)
                + "."
            ),
            target_type="task",
            target_id=task.id,
            meta={
                "action": ActionType.UPDATE_TASK.value,
                "task_id": task.id,
                "changes": changed,
            },
            simulation_day=self.company.current_day,
        )

        return ActionResult(
            success=True,
            message=f"Task '{task.title}' updated ({', '.join(changed)}).",
            events=[event],
        )

    def _handle_complete_task(self, decision: AgentDecision) -> ActionResult:
        if decision.task_id is None:
            return self._rejected(decision, "COMPLETE_TASK requires a task_id.")
        task = self._company_task(decision.task_id)
        if task is None:
            return self._rejected(decision, "Task does not exist or belongs to another company.")
        if task.status == TaskStatus.COMPLETED:
            return self._rejected(decision, "Task is already completed.")

        task.status = TaskStatus.COMPLETED
        task.progress = 100.0
        self.db.flush()

        event = Event(
            company_id=self.company.id,
            actor_id=self.agent.id,
            event_type="TASK_CREATED",
            description=f"Task '{task.title}' completed by {self.agent.role.value}.",
            target_type="task",
            target_id=task.id,
            meta={
                "action": ActionType.COMPLETE_TASK.value,
                "task_id": task.id,
            },
            simulation_day=self.company.current_day,
        )

        return ActionResult(
            success=True,
            message=f"Task '{task.title}' completed.",
            events=[event],
        )

    def _handle_create_goal(self, decision: AgentDecision) -> ActionResult:
        if not decision.title:
            return self._rejected(decision, "CREATE_GOAL requires a title.")
        if not decision.description:
            return self._rejected(decision, "CREATE_GOAL requires a description.")

        priority = self._priority_value(decision.priority)
        goal = Goal(
            company_id=self.company.id,
            title=decision.title,
            description=decision.description or "",
            status=GoalStatus.TODO,
            priority=priority,
            progress=0.0,
        )
        self.db.add(goal)
        self.db.flush()

        event = Event(
            company_id=self.company.id,
            actor_id=self.agent.id,
            event_type="GOAL_CREATED",
            description=f"Goal '{goal.title}' created by {self.agent.role.value}.",
            target_type="goal",
            target_id=goal.id,
            meta={
                "action": ActionType.CREATE_GOAL.value,
                "goal_id": goal.id,
            },
            simulation_day=self.company.current_day,
        )

        return ActionResult(
            success=True,
            message=f"Goal '{goal.title}' created.",
            events=[event],
        )

    def _handle_update_goal(self, decision: AgentDecision) -> ActionResult:
        if decision.goal_id is None:
            return self._rejected(decision, "UPDATE_GOAL requires a goal_id.")
        goal = self._company_goal(decision.goal_id)
        if goal is None:
            return self._rejected(decision, "Goal does not exist or belongs to another company.")

        changed: list[str] = []
        if decision.status is not None:
            try:
                goal.status = GoalStatus(decision.status)
            except ValueError:
                return self._rejected(decision, f"Invalid goal status: {decision.status}")
            changed.append(f"status={goal.status.value}")
        if decision.progress is not None:
            goal.progress = max(0.0, min(100.0, decision.progress))
            changed.append(f"progress={goal.progress}")
        self.db.flush()

        if not changed:
            return self._rejected(decision, "UPDATE_GOAL provided no updatable fields.")

        event = Event(
            company_id=self.company.id,
            actor_id=self.agent.id,
            event_type="GOAL_CREATED",
            description=(
                f"Goal '{goal.title}' updated by {self.agent.role.value}: "
                + ", ".join(changed)
                + "."
            ),
            target_type="goal",
            target_id=goal.id,
            meta={
                "action": ActionType.UPDATE_GOAL.value,
                "goal_id": goal.id,
                "changes": changed,
            },
            simulation_day=self.company.current_day,
        )

        return ActionResult(
            success=True,
            message=f"Goal '{goal.title}' updated ({', '.join(changed)}).",
            events=[event],
        )

    def _handle_create_project(self, decision: AgentDecision) -> ActionResult:
        if not decision.title:
            return self._rejected(decision, "CREATE_PROJECT requires a title.")

        project = Project(
            company_id=self.company.id,
            name=decision.title,
            description=decision.description or "",
            status=ProjectStatus.PLANNED,
            progress=0.0,
        )
        self.db.add(project)
        self.db.flush()

        event = Event(
            company_id=self.company.id,
            actor_id=self.agent.id,
            event_type="DECISION",
            description=f"Project '{project.name}' created by {self.agent.role.value}.",
            target_type="project",
            target_id=project.id,
            meta={
                "action": ActionType.CREATE_PROJECT.value,
                "project_id": project.id,
            },
            simulation_day=self.company.current_day,
        )

        return ActionResult(
            success=True,
            message=f"Project '{project.name}' created.",
            events=[event],
        )

    def _handle_create_milestone(self, decision: AgentDecision) -> ActionResult:
        if not decision.title:
            return self._rejected(decision, "CREATE_MILESTONE requires a title.")
        if not decision.project_id:
            return self._rejected(decision, "CREATE_MILESTONE requires a project_id.")
        project = self._company_project(decision.project_id)
        if project is None:
            return self._rejected(decision, "Project does not exist or belongs to another company.")

        milestone = Milestone(
            company_id=self.company.id,
            project_id=project.id,
            name=decision.title,
            description=decision.description or "",
            sequence=0,
            status="PLANNED",
            progress=0.0,
        )
        self.db.add(milestone)
        self.db.flush()

        event = Event(
            company_id=self.company.id,
            actor_id=self.agent.id,
            event_type="DECISION",
            description=f"Milestone '{milestone.name}' created by {self.agent.role.value}.",
            target_type="milestone",
            target_id=milestone.id,
            meta={"action": ActionType.CREATE_MILESTONE.value, "milestone_id": milestone.id},
            simulation_day=self.company.current_day,
        )

        return ActionResult(success=True, message=f"Milestone '{milestone.name}' created.", events=[event])

    def _handle_create_feature(self, decision: AgentDecision) -> ActionResult:
        if not decision.title:
            return self._rejected(decision, "CREATE_FEATURE requires a title.")

        project = None
        if decision.project_id is not None:
            project = self._company_project(decision.project_id)
            if project is None:
                return self._rejected(decision, "Project does not exist or belongs to another company.")

        feature = ProductFeature(
            company_id=self.company.id,
            project_id=project.id if project else None,
            name=decision.title,
            description=decision.description or "",
            status="PLANNED",
            progress=0.0,
            quality=0.0,
            importance=self._priority_value(decision.priority),
        )
        self.db.add(feature)
        self.db.flush()

        event = Event(
            company_id=self.company.id,
            actor_id=self.agent.id,
            event_type="DECISION",
            description=f"Feature '{feature.name}' created by {self.agent.role.value}.",
            target_type="feature",
            target_id=feature.id,
            meta={"action": ActionType.CREATE_FEATURE.value, "feature_id": feature.id},
            simulation_day=self.company.current_day,
        )

        return ActionResult(success=True, message=f"Feature '{feature.name}' created.", events=[event])

    def _handle_create_plan(self, decision: AgentDecision) -> ActionResult:
        if not decision.objective:
            return self._rejected(decision, "CREATE_PLAN requires an objective.")
        steps = decision.plan_steps or []
        if not steps:
            return self._rejected(decision, "CREATE_PLAN requires at least one plan step.")

        from app.simulation import plan as plan_system

        plan, events = plan_system.create_plan(
            self._ctx(),
            agent_id=self.agent.id,
            objective=decision.objective,
            priority=self._priority_value(decision.priority),
            steps=steps,
            goal_id=decision.goal_id,
        )
        return ActionResult(
            success=True,
            message=f"Plan '{plan.objective}' created with {len(steps)} steps.",
            events=events,
        )

    def _handle_update_plan(self, decision: AgentDecision) -> ActionResult:
        if decision.plan_id is None:
            return self._rejected(decision, "UPDATE_PLAN requires a plan_id.")
        plan = self.db.get(Plan, decision.plan_id)
        if plan is None or plan.company_id != self.company.id:
            return self._rejected(decision, "Plan does not exist or belongs to another company.")
        if plan.agent_id != self.agent.id:
            return self._rejected(decision, "Can only update your own plans.")

        from app.simulation import plan as plan_system

        new_status = (decision.status or "").upper()
        if new_status == "COMPLETED":
            events = plan_system.complete_plan(self._ctx(), plan)
            return ActionResult(success=True, message=f"Plan '{plan.objective}' completed.", events=events)
        if new_status in ("ABANDONED", "FAILED", "CANCELLED"):
            events = plan_system.abandon_plan(self._ctx(), plan)
            return ActionResult(success=True, message=f"Plan '{plan.objective}' abandoned.", events=events)
        if new_status == "REVISED":
            if not decision.objective or not decision.plan_steps:
                return self._rejected(decision, "REVISED requires objective and plan_steps.")
            _, events = plan_system.revise_plan(
                self._ctx(),
                plan,
                new_objective=decision.objective,
                new_steps=decision.plan_steps,
            )
            return ActionResult(success=True, message=f"Plan revised to '{decision.objective}'.", events=events)
        return self._rejected(decision, f"Unsupported UPDATE_PLAN status: {decision.status}")

    def _handle_send_message(self, decision: AgentDecision) -> ActionResult:
        if decision.target_agent_id is None:
            return self._rejected(decision, "SEND_MESSAGE requires a target_agent_id.")
        target = self._company_agent(decision.target_agent_id)
        if target is None:
            return self._rejected(decision, "Message target does not belong to the company.")
        if not decision.message:
            return self._rejected(decision, "SEND_MESSAGE requires a message body.")

        from app.simulation import communication as comm_system

        msg, events = comm_system.send_message(
            self._ctx(),
            sender_agent_id=self.agent.id,
            recipient_agent_id=target.id,
            subject=(decision.subject or decision.title or "")[:255],
            content=decision.message,
            priority=decision.priority.value if decision.priority else "NORMAL",
        )
        if msg is None:
            return self._rejected(decision, "Message could not be created (empty content).")
        return ActionResult(
            success=True,
            message=f"Message sent to {target.name}.",
            events=events,
        )

    # --- Phase 6 strategic handlers ---

    def _handle_set_price(self, decision: AgentDecision) -> ActionResult:
        if decision.price is None or decision.price < 0:
            return self._rejected(decision, "SET_PRICE requires a non-negative price.")
        old_price = self.company.price
        self.company.price = round(decision.price, 2)
        self.db.flush()
        event = Event(
            company_id=self.company.id,
            actor_id=self.agent.id,
            event_type="PRICE_CHANGED",
            description=f"Price changed from {old_price:.2f} to {self.company.price:.2f} by {self.agent.role.value}.",
            target_type="company",
            target_id=self.company.id,
            meta={"old_price": old_price, "new_price": self.company.price, "day": self.company.current_day},
            simulation_day=self.company.current_day,
        )

        return ActionResult(
            success=True,
            message=f"Price set to {self.company.price:.2f}.",
            events=[event],
        )

    def _handle_set_target_segment(self, decision: AgentDecision) -> ActionResult:
        if not decision.target_segment:
            return self._rejected(decision, "SET_TARGET_SEGMENT requires a target_segment.")
        valid_segments = {"SMB", "MID_MARKET", "ENTERPRISE", "STARTUP"}
        if decision.target_segment.upper() not in valid_segments:
            return self._rejected(decision, f"Invalid target segment: {decision.target_segment}")
        old_segment = self.company.target_segment
        self.company.target_segment = decision.target_segment.upper()
        self.db.flush()
        event = Event(
            company_id=self.company.id,
            actor_id=self.agent.id,
            event_type="TARGET_SEGMENT_CHANGED",
            description=f"Target segment changed from {old_segment} to {self.company.target_segment} by {self.agent.role.value}.",
            target_type="company",
            target_id=self.company.id,
            meta={"old_segment": old_segment, "new_segment": self.company.target_segment, "day": self.company.current_day},
            simulation_day=self.company.current_day,
        )

        return ActionResult(
            success=True,
            message=f"Target segment set to {self.company.target_segment}.",
            events=[event],
        )

    def _handle_update_positioning(self, decision: AgentDecision) -> ActionResult:
        if not decision.positioning:
            return self._rejected(decision, "UPDATE_POSITIONING requires positioning text.")
        old_positioning = self.company.positioning
        self.company.positioning = decision.positioning[:500]
        self.db.flush()
        event = Event(
            company_id=self.company.id,
            actor_id=self.agent.id,
            event_type="POSITIONING_CHANGED",
            description=f"Positioning updated by {self.agent.role.value}.",
            target_type="company",
            target_id=self.company.id,
            meta={"old_positioning": old_positioning, "new_positioning": self.company.positioning, "day": self.company.current_day},
            simulation_day=self.company.current_day,
        )

        return ActionResult(
            success=True,
            message="Positioning updated.",
            events=[event],
        )

    def _handle_create_campaign(self, decision: AgentDecision) -> ActionResult:
        if not decision.campaign_name:
            return self._rejected(decision, "CREATE_CAMPAIGN requires a campaign_name.")
        if decision.campaign_budget is None or decision.campaign_budget <= 0:
            return self._rejected(decision, "CREATE_CAMPAIGN requires a positive budget.")
        if decision.campaign_duration is None or decision.campaign_duration <= 0:
            return self._rejected(decision, "CREATE_CAMPAIGN requires a positive duration.")

        from app.simulation import marketing as marketing_system
        from app.enums import SegmentType

        try:
            segment = SegmentType(decision.target_segment.upper()) if decision.target_segment else SegmentType.SMB
        except ValueError:
            segment = SegmentType.SMB

        campaign, events = marketing_system.create_campaign(
            self._ctx(),
            company=self.company,
            name=decision.campaign_name,
            segment=segment,
            budget=decision.campaign_budget,
            duration_days=min(decision.campaign_duration, 60),
        )
        if campaign is None:
            return self._rejected(decision, "Campaign could not be created.")
        return ActionResult(
            success=True,
            message=f"Campaign '{campaign.name}' created.",
            events=events,
        )

    def _handle_create_sales_opportunity(self, decision: AgentDecision) -> ActionResult:
        if not decision.opportunity_name:
            return self._rejected(decision, "CREATE_SALES_OPPORTUNITY requires an opportunity_name.")
        if decision.opportunity_value is None or decision.opportunity_value <= 0:
            return self._rejected(decision, "CREATE_SALES_OPPORTUNITY requires a positive value.")

        from app.simulation import sales as sales_system
        from app.enums import SegmentType

        try:
            segment = SegmentType(decision.target_segment.upper()) if decision.target_segment else SegmentType.SMB
        except ValueError:
            segment = SegmentType.SMB

        opportunity, events = sales_system.create_opportunity(
            self._ctx(),
            company=self.company,
            segment=segment,
            name=decision.opportunity_name,
            value=decision.opportunity_value,
        )
        if opportunity is None:
            return self._rejected(decision, "Opportunity could not be created.")
        return ActionResult(
            success=True,
            message=f"Opportunity '{opportunity.name}' created.",
            events=events,
        )

    # --- Phase 9 workforce handlers ---

    def _handle_create_job_opening(self, decision: AgentDecision) -> ActionResult:
        if not decision.job_title:
            return self._rejected(decision, "CREATE_JOB_OPENING requires a job_title.")
        if not decision.job_role:
            return self._rejected(decision, "CREATE_JOB_OPENING requires a job_role.")

        from app.models.job_opening import JobOpening
        from app.enums import JobStatus

        salary_min = decision.salary_min or 2000.0
        salary_max = decision.salary_max or 5000.0
        if salary_max < salary_min:
            return self._rejected(decision, "salary_max must be >= salary_min.")

        opening = JobOpening(
            company_id=self.company.id,
            role=decision.job_role,
            title=decision.job_title,
            description=decision.job_description or "",
            required_skills=decision.required_skills or [],
            salary_min=salary_min,
            salary_max=salary_max,
            capacity_required=decision.capacity_required or 3.0,
            created_day=self.company.current_day,
            status=JobStatus.OPEN,
            created_by=self.agent.id,
        )
        self.db.add(opening)
        self.db.flush()

        event = Event(
            company_id=self.company.id,
            actor_id=self.agent.id,
            event_type="JOB_OPENED",
            description=f"Job opening for '{opening.title}' ({opening.role}) created by {self.agent.role.value}.",
            target_type="job_opening",
            target_id=opening.id,
            meta={
                "action": ActionType.CREATE_JOB_OPENING.value,
                "job_opening_id": opening.id,
                "role": opening.role,
                "day": self.company.current_day,
            },
            simulation_day=self.company.current_day,
        )

        return ActionResult(
            success=True,
            message=f"Job opening '{opening.title}' created.",
            events=[event],
        )

    def _handle_review_candidate(self, decision: AgentDecision) -> ActionResult:
        if decision.candidate_id is None:
            return self._rejected(decision, "REVIEW_CANDIDATE requires a candidate_id.")

        from app.models.candidate import Candidate
        from app.simulation import candidates as candidate_system

        candidate = self.db.get(Candidate, decision.candidate_id)
        if candidate is None or candidate.company_id != self.company.id:
            return self._rejected(decision, "Candidate does not exist or belongs to another company.")

        evaluated = candidate_system.evaluate_candidate(
            self._ctx(), candidate, evaluator_agent_id=self.agent.id
        )
        event = Event(
            company_id=self.company.id,
            actor_id=self.agent.id,
            event_type="CANDIDATE_EVALUATED",
            description=f"Candidate '{evaluated.name}' ({evaluated.role}) evaluated: {evaluated.hiring_score:.0%} fit.",
            target_type="candidate",
            target_id=evaluated.id,
            meta={
                "action": ActionType.REVIEW_CANDIDATE.value,
                "candidate_id": evaluated.id,
                "hiring_score": evaluated.hiring_score,
                "day": self.company.current_day,
            },
            simulation_day=self.company.current_day,
        )

        return ActionResult(
            success=True,
            message=f"Candidate '{evaluated.name}' evaluated: {evaluated.hiring_score:.0%}.",
            events=[event],
        )

    def _handle_make_hiring_decision(self, decision: AgentDecision) -> ActionResult:
        if decision.candidate_id is None:
            return self._rejected(decision, "MAKE_HIRING_DECISION requires a candidate_id.")

        from app.models.candidate import Candidate
        from app.models.job_opening import JobOpening
        from app.simulation import workforce as workforce_system
        from app.enums import JobStatus

        candidate = self.db.get(Candidate, decision.candidate_id)
        if candidate is None or candidate.company_id != self.company.id:
            return self._rejected(decision, "Candidate does not exist or belongs to another company.")

        job = self.db.get(JobOpening, candidate.job_opening_id)
        if job is None or job.company_id != self.company.id:
            return self._rejected(decision, "Job opening does not exist or belongs to another company.")
        if job.status != JobStatus.OPEN:
            return self._rejected(decision, "Job opening is not open.")

        salary = candidate.salary_expectation
        if salary < job.salary_min:
            salary = job.salary_min
        if salary > job.salary_max:
            salary = job.salary_max

        employee, events = workforce_system.hire_employee(
            self._ctx(), job, candidate.name, salary
        )
        if employee is None:
            return self._rejected(decision, "Hiring failed.")

        candidate.status = "INTERVIEWING"
        self.db.flush()

        event = Event(
            company_id=self.company.id,
            actor_id=self.agent.id,
            event_type="EMPLOYEE_HIRED",
            description=f"Employee '{employee.name}' hired as {employee.role} by {self.agent.role.value}.",
            target_type="employee",
            target_id=employee.id,
            meta={
                "action": ActionType.MAKE_HIRING_DECISION.value,
                "employee_id": employee.id,
                "candidate_id": candidate.id,
                "role": employee.role,
                "salary": salary,
                "day": self.company.current_day,
            },
            simulation_day=self.company.current_day,
        )

        events.append(event)
        return ActionResult(
            success=True,
            message=f"Employee '{employee.name}' hired as {employee.role}.",
            events=events,
        )

    def _handle_set_employee_manager(self, decision: AgentDecision) -> ActionResult:
        if decision.employee_id is None:
            return self._rejected(decision, "SET_EMPLOYEE_MANAGER requires an employee_id.")
        if decision.new_manager_id is None:
            return self._rejected(decision, "SET_EMPLOYEE_MANAGER requires a new_manager_id.")

        from app.models.employee import Employee

        employee = self.db.get(Employee, decision.employee_id)
        if employee is None or employee.company_id != self.company.id:
            return self._rejected(decision, "Employee does not exist or belongs to another company.")
        manager = self.db.get(Employee, decision.new_manager_id)
        if manager is None or manager.company_id != self.company.id:
            return self._rejected(decision, "Manager does not exist or belongs to another company.")

        employee.manager_id = manager.id
        self.db.flush()
        return ActionResult(
            success=True,
            message=f"{employee.name} now reports to {manager.name}.",
            events=[],
        )

    def _handle_promote_employee(self, decision: AgentDecision) -> ActionResult:
        if decision.employee_id is None:
            return self._rejected(decision, "PROMOTE_EMPLOYEE requires an employee_id.")
        if not decision.new_role:
            return self._rejected(decision, "PROMOTE_EMPLOYEE requires a new_role.")

        from app.models.employee import Employee
        from app.simulation import workforce as workforce_system

        employee = self.db.get(Employee, decision.employee_id)
        if employee is None or employee.company_id != self.company.id:
            return self._rejected(decision, "Employee does not exist or belongs to another company.")

        old_role = employee.role
        employee.role = decision.new_role
        if decision.new_salary is not None and decision.new_salary > 0:
            employee.salary = decision.new_salary
        employee.capacity = workforce_system.ROLE_CAPACITY.get(decision.new_role, employee.capacity)
        self.db.flush()

        event = Event(
            company_id=self.company.id,
            actor_id=self.agent.id,
            event_type="EMPLOYEE_PROMOTED",
            description=f"Employee '{employee.name}' promoted from {old_role} to {employee.role}.",
            target_type="employee",
            target_id=employee.id,
            meta={
                "action": ActionType.PROMOTE_EMPLOYEE.value,
                "employee_id": employee.id,
                "old_role": old_role,
                "new_role": employee.role,
                "day": self.company.current_day,
            },
            simulation_day=self.company.current_day,
        )

        return ActionResult(
            success=True,
            message=f"Employee '{employee.name}' promoted to {employee.role}.",
            events=[event],
        )

    def _handle_terminate_employee(self, decision: AgentDecision) -> ActionResult:
        if decision.employee_id is None:
            return self._rejected(decision, "TERMINATE_EMPLOYEE requires an employee_id.")

        from app.models.employee import Employee
        from app.simulation import workforce as workforce_system

        employee = self.db.get(Employee, decision.employee_id)
        if employee is None or employee.company_id != self.company.id:
            return self._rejected(decision, "Employee does not exist or belongs to another company.")

        reason = decision.termination_reason or ""
        events = workforce_system.terminate_employee(self._ctx(), employee, reason)
        return ActionResult(
            success=True,
            message=f"Employee '{employee.name}' terminated.",
            events=events,
        )

    # --- Phase 10 financial/capital handlers ---

    def _handle_create_funding_round(self, decision: AgentDecision) -> ActionResult:
        if not decision.funding_stage:
            return self._rejected(decision, "CREATE_FUNDING_ROUND requires a funding_stage.")
        if decision.funding_amount_requested is None or decision.funding_amount_requested <= 0:
            return self._rejected(decision, "CREATE_FUNDING_ROUND requires a positive funding_amount_requested.")
        if decision.funding_valuation is None or decision.funding_valuation <= 0:
            return self._rejected(decision, "CREATE_FUNDING_ROUND requires a positive funding_valuation.")

        from app.enums import InvestorStage
        from app.simulation import fundraising as fundraising_system

        try:
            stage = InvestorStage(decision.funding_stage.upper())
        except ValueError:
            return self._rejected(decision, f"Invalid funding_stage: {decision.funding_stage}")

        round_stage = fundraising_system.create_funding_round(
            self._ctx(),
            stage=stage,
            amount_requested=decision.funding_amount_requested,
            valuation=decision.funding_valuation,
        )
        if round_stage is None:
            return self._rejected(decision, "Could not create funding round.")

        event = Event(
            company_id=self.company.id,
            actor_id=self.agent.id,
            event_type="FUNDING_ROUND_CREATED",
            description=f"Funding round {stage.value} opened by {self.agent.role.value} requesting ${decision.funding_amount_requested:,.2f}.",
            target_type="funding_round",
            target_id=round_stage.id,
            meta={
                "action": ActionType.CREATE_FUNDING_ROUND.value,
                "funding_round_id": round_stage.id,
                "stage": stage.value,
                "amount_requested": decision.funding_amount_requested,
                "valuation": decision.funding_valuation,
                "day": self.company.current_day,
            },
            simulation_day=self.company.current_day,
        )

        return ActionResult(
            success=True,
            message=f"Funding round {stage.value} created.",
            events=[event],
        )

    def _handle_contact_investor(self, decision: AgentDecision) -> ActionResult:
        if decision.investor_id is None:
            return self._rejected(decision, "CONTACT_INVESTOR requires an investor_id.")

        from app.models.investor import Investor
        from app.simulation import fundraising as fundraising_system

        investor = self.db.get(Investor, decision.investor_id)
        if investor is None or investor.company_id != self.company.id:
            return self._rejected(decision, "Investor does not exist or belongs to another company.")

        from app.enums import FundingRoundStatus, InvestorStage
        from app.models.fundraising_pipeline import FundraisingPipeline

        pipeline = FundraisingPipeline(
            company_id=self.company.id,
            investor_id=investor.id,
            funding_round_id=None,
            status=FundingRoundStatus.CONTACTED,
            stage=investor.preferred_stage,
            interest_score=0.0,
            notes="",
            day_updated=self.company.current_day,
        )
        self.db.add(pipeline)
        self.db.flush()

        event = Event(
            company_id=self.company.id,
            actor_id=self.agent.id,
            event_type="INVESTOR_CONTACTED",
            description=f"Investor '{investor.name}' contacted by {self.agent.role.value}.",
            target_type="investor",
            target_id=investor.id,
            meta={
                "action": ActionType.CONTACT_INVESTOR.value,
                "investor_id": investor.id,
                "pipeline_id": pipeline.id,
                "day": self.company.current_day,
            },
            simulation_day=self.company.current_day,
        )

        return ActionResult(
            success=True,
            message=f"Investor '{investor.name}' contacted.",
            events=[event],
        )

    def _handle_advance_pipeline(self, decision: AgentDecision) -> ActionResult:
        if decision.budget_request_id is None:
            return self._rejected(decision, "ADVANCE_PIPELINE requires a budget_request_id (pipeline entry id).")

        from app.simulation import fundraising as fundraising_system

        pipeline = fundraising_system.advance_pipeline(self._ctx(), decision.budget_request_id)
        if pipeline is None:
            return self._rejected(decision, "Pipeline entry not found.")

        event = Event(
            company_id=self.company.id,
            actor_id=self.agent.id,
            event_type="PIPELINE_ADVANCED",
            description=f"Pipeline advanced to {pipeline.status.value} by {self.agent.role.value}.",
            target_type="fundraising_pipeline",
            target_id=pipeline.id,
            meta={
                "action": ActionType.ADVANCE_PIPELINE.value,
                "pipeline_id": pipeline.id,
                "new_status": pipeline.status.value,
                "day": self.company.current_day,
            },
            simulation_day=self.company.current_day,
        )

        return ActionResult(
            success=True,
            message=f"Pipeline advanced to {pipeline.status.value}.",
            events=[event],
        )

    def _handle_make_investment_decision(self, decision: AgentDecision) -> ActionResult:
        if decision.budget_request_id is None:
            return self._rejected(decision, "MAKE_INVESTMENT_DECISION requires a budget_request_id (pipeline entry id).")
        if decision.funding_amount_requested is None or decision.funding_amount_requested <= 0:
            return self._rejected(decision, "MAKE_INVESTMENT_DECISION requires a positive funding_amount_requested.")

        from app.simulation import fundraising as fundraising_system

        invested = decision.funding_amount_requested > 0
        pipeline = fundraising_system.make_investment_decision(
            self._ctx(),
            decision.budget_request_id,
            invested=invested,
            amount=decision.funding_amount_requested,
        )
        if pipeline is None:
            return self._rejected(decision, "Pipeline entry not found or not in OFFERED status.")

        status_str = "INVESTED" if invested else "PASSED"
        event = Event(
            company_id=self.company.id,
            actor_id=self.agent.id,
            event_type="INVESTMENT_DECIDED",
            description=f"Investment decision: {status_str} by {self.agent.role.value}.",
            target_type="fundraising_pipeline",
            target_id=pipeline.id,
            meta={
                "action": ActionType.MAKE_INVESTMENT_DECISION.value,
                "pipeline_id": pipeline.id,
                "status": status_str,
                "amount": decision.funding_amount_requested,
                "day": self.company.current_day,
            },
            simulation_day=self.company.current_day,
        )

        return ActionResult(
            success=True,
            message=f"Investment decision: {status_str}.",
            events=[event],
        )

    def _handle_request_budget(self, decision: AgentDecision) -> ActionResult:
        if decision.budget_amount is None or decision.budget_amount <= 0:
            return self._rejected(decision, "REQUEST_BUDGET requires a positive budget_amount.")
        if not decision.budget_purpose or not decision.budget_purpose.strip():
            return self._rejected(decision, "REQUEST_BUDGET requires a budget_purpose.")

        from app.simulation import capital as capital_system

        request = capital_system.create_budget_request(
            self._ctx(),
            requester_id=self.agent.id,
            amount=decision.budget_amount,
            purpose=decision.budget_purpose,
        )
        if request is None:
            return self._rejected(decision, "Could not create budget request.")

        event = Event(
            company_id=self.company.id,
            actor_id=self.agent.id,
            event_type="BUDGET_REQUESTED",
            description=f"Budget request for ${decision.budget_amount:,.2f} by {self.agent.role.value}: {decision.budget_purpose[:100]}.",
            target_type="budget_request",
            target_id=request.id,
            meta={
                "action": ActionType.REQUEST_BUDGET.value,
                "budget_request_id": request.id,
                "amount": decision.budget_amount,
                "purpose": decision.budget_purpose[:200],
                "day": self.company.current_day,
            },
            simulation_day=self.company.current_day,
        )

        return ActionResult(
            success=True,
            message=f"Budget request created for ${decision.budget_amount:,.2f}.",
            events=[event],
        )

    def _handle_approve_budget(self, decision: AgentDecision) -> ActionResult:
        if decision.budget_request_id is None:
            return self._rejected(decision, "APPROVE_BUDGET requires a budget_request_id.")
        if decision.budget_amount is None or decision.budget_amount <= 0:
            return self._rejected(decision, "APPROVE_BUDGET requires a positive budget_amount.")

        from app.simulation import capital as capital_system

        request = capital_system.approve_budget_request(
            self._ctx(),
            request_id=decision.budget_request_id,
            approver_id=self.agent.id,
            approved_amount=decision.budget_amount,
            decision_notes=decision.reasoning,
        )
        if request is None:
            return self._rejected(decision, "Budget request not found or cannot be approved.")

        event = Event(
            company_id=self.company.id,
            actor_id=self.agent.id,
            event_type="BUDGET_APPROVED",
            description=f"Budget request approved for ${decision.budget_amount:,.2f} by {self.agent.role.value}.",
            target_type="budget_request",
            target_id=request.id,
            meta={
                "action": ActionType.APPROVE_BUDGET.value,
                "budget_request_id": request.id,
                "approved_amount": decision.budget_amount,
                "day": self.company.current_day,
            },
            simulation_day=self.company.current_day,
        )

        return ActionResult(
            success=True,
            message=f"Budget approved for ${decision.budget_amount:,.2f}.",
            events=[event],
        )

    def _handle_reject_budget(self, decision: AgentDecision) -> ActionResult:
        if decision.budget_request_id is None:
            return self._rejected(decision, "REJECT_BUDGET requires a budget_request_id.")

        from app.simulation import capital as capital_system

        request = capital_system.reject_budget_request(
            self._ctx(),
            request_id=decision.budget_request_id,
            approver_id=self.agent.id,
            decision_notes=decision.reasoning,
        )
        if request is None:
            return self._rejected(decision, "Budget request not found or cannot be rejected.")

        event = Event(
            company_id=self.company.id,
            actor_id=self.agent.id,
            event_type="BUDGET_REJECTED",
            description=f"Budget request rejected by {self.agent.role.value}.",
            target_type="budget_request",
            target_id=request.id,
            meta={
                "action": ActionType.REJECT_BUDGET.value,
                "budget_request_id": request.id,
                "day": self.company.current_day,
            },
            simulation_day=self.company.current_day,
        )

        return ActionResult(
            success=True,
            message="Budget request rejected.",
            events=[event],
        )

    # --- Phase 11 advanced autonomous operations handlers ---

    def _handle_create_objective(self, decision: AgentDecision) -> ActionResult:
        if not decision.objective_title:
            return self._rejected(decision, "CREATE_OBJECTIVE requires an objective_title.")

        from app.enums import ObjectiveType
        from app.simulation import objective as objective_system

        obj_type = ObjectiveType.OPERATIONAL
        if decision.objective_type:
            try:
                obj_type = ObjectiveType(decision.objective_type.upper())
            except ValueError:
                pass

        objective = objective_system.create_objective(
            self._ctx(),
            title=decision.objective_title,
            description=decision.objective_description or "",
            objective_type=obj_type,
            priority=5,
            owner_id=self.agent.id,
            expected_outcome=decision.expected_outcome or "",
        )
        if objective is None:
            return self._rejected(decision, "Objective could not be created.")

        event = Event(
            company_id=self.company.id,
            actor_id=self.agent.id,
            event_type="OBJECTIVE_CREATED",
            description=f"Objective '{objective.title}' created by {self.agent.role.value}.",
            target_type="objective",
            target_id=objective.id,
            meta={"objective_id": objective.id, "day": self.company.current_day},
            simulation_day=self.company.current_day,
        )
        return ActionResult(
            success=True,
            message=f"Objective '{objective.title}' created.",
            events=[event],
        )

    def _handle_update_objective(self, decision: AgentDecision) -> ActionResult:
        if decision.objective_id is None:
            return self._rejected(decision, "UPDATE_OBJECTIVE requires an objective_id.")

        from app.simulation import objective as objective_system

        progress = 50.0
        if decision.objective_progress is not None:
            progress = decision.objective_progress

        objective = objective_system.update_objective_progress(
            self._ctx(), decision.objective_id, progress
        )
        if objective is None:
            return self._rejected(decision, "Objective not found or cannot be updated.")

        event = Event(
            company_id=self.company.id,
            actor_id=self.agent.id,
            event_type="OBJECTIVE_UPDATED",
            description=f"Objective '{objective.title}' updated to {objective.progress:.1f}%.",
            target_type="objective",
            target_id=objective.id,
            meta={"objective_id": objective.id, "progress": objective.progress, "day": self.company.current_day},
            simulation_day=self.company.current_day,
        )
        return ActionResult(
            success=True,
            message=f"Objective updated to {objective.progress:.1f}%.",
            events=[event],
        )

    def _handle_allocate_resource(self, decision: AgentDecision) -> ActionResult:
        if decision.resource_type is None or decision.resource_amount is None:
            return self._rejected(decision, "ALLOCATE_RESOURCE requires resource_type and resource_amount.")

        from app.enums import ResourceType
        from app.simulation import resource as resource_system

        try:
            resource_type = ResourceType(decision.resource_type.upper())
        except ValueError:
            return self._rejected(decision, f"Invalid resource_type: {decision.resource_type}")

        allocation = resource_system.allocate_resource(
            self._ctx(),
            resource_type=resource_type,
            allocated_amount=decision.resource_amount,
            purpose=decision.reasoning,
            owner_id=self.agent.id,
        )
        if allocation is None:
            return self._rejected(decision, "Insufficient resources for allocation.")

        event = Event(
            company_id=self.company.id,
            actor_id=self.agent.id,
            event_type="RESOURCE_ALLOCATED",
            description=f"Resource {resource_type.value} allocated: ${decision.resource_amount:,.2f}.",
            target_type="resource_allocation",
            target_id=allocation.id,
            meta={"resource_type": resource_type.value, "amount": decision.resource_amount, "day": self.company.current_day},
            simulation_day=self.company.current_day,
        )
        return ActionResult(
            success=True,
            message=f"Resource {resource_type.value} allocated.",
            events=[event],
        )

    def _handle_escalate_risk(self, decision: AgentDecision) -> ActionResult:
        if decision.risk_id is None:
            return self._rejected(decision, "ESCALATE_RISK requires a risk_id.")

        from app.simulation import risk as risk_system

        risk = risk_system.escalate_risk(self._ctx(), decision.risk_id)
        if risk is None:
            return self._rejected(decision, "Risk not found or cannot be escalated.")

        event = Event(
            company_id=self.company.id,
            actor_id=self.agent.id,
            event_type="RISK_ESCALATED",
            description=f"Risk '{risk.risk_type}' escalated by {self.agent.role.value}.",
            target_type="risk",
            target_id=risk.id,
            meta={"risk_id": risk.id, "day": self.company.current_day},
            simulation_day=self.company.current_day,
        )
        return ActionResult(
            success=True,
            message=f"Risk {risk.id} escalated.",
            events=[event],
        )

    def _handle_create_mitigation(self, decision: AgentDecision) -> ActionResult:
        if decision.risk_id is None or not decision.mitigation_actions:
            return self._rejected(decision, "CREATE_MITIGATION requires risk_id and mitigation_actions.")

        from app.simulation import risk as risk_system

        risk = risk_system.resolve_risk(self._ctx(), decision.risk_id)
        if risk is None:
            return self._rejected(decision, "Risk not found or cannot be resolved.")

        risk.mitigation_actions = decision.mitigation_actions.strip()[:1000]
        risk.status = RiskStatus.MITIGATING
        self._ctx().db.flush()

        event = Event(
            company_id=self.company.id,
            actor_id=self.agent.id,
            event_type="RISK_RESOLVED",
            description=f"Mitigation created for risk '{risk.risk_type}'.",
            target_type="risk",
            target_id=risk.id,
            meta={"risk_id": risk.id, "mitigation": decision.mitigation_actions[:200], "day": self.company.current_day},
            simulation_day=self.company.current_day,
        )
        return ActionResult(
            success=True,
            message="Mitigation created.",
            events=[event],
        )

    def _handle_reassign_work(self, decision: AgentDecision) -> ActionResult:
        if decision.reassign_task_id is None or decision.reassign_to_agent_id is None:
            return self._rejected(decision, "REASSIGN_WORK requires reassign_task_id and reassign_to_agent_id.")

        from app.models.task import Task
        from app.models.agent import Agent

        task = self._ctx().db.get(Task, decision.reassign_task_id)
        if task is None or task.company_id != self.company.id:
            return self._rejected(decision, "Task not found or belongs to another company.")

        agent = self._ctx().db.get(Agent, decision.reassign_to_agent_id)
        if agent is None or agent.company_id != self.company.id:
            return self._rejected(decision, "Target agent not found or belongs to another company.")

        task.assigned_to = agent.id
        self._ctx().db.flush()

        event = Event(
            company_id=self.company.id,
            actor_id=self.agent.id,
            event_type="WORK_REASSIGNED",
            description=f"Task '{task.title}' reassigned to agent {agent.id}.",
            target_type="task",
            target_id=task.id,
            meta={"task_id": task.id, "from_agent": task.assigned_to, "to_agent": agent.id, "day": self.company.current_day},
            simulation_day=self.company.current_day,
        )
        return ActionResult(
            success=True,
            message=f"Task reassigned to agent {agent.id}.",
            events=[event],
        )

    def _handle_pause_work(self, decision: AgentDecision) -> ActionResult:
        if decision.pause_task_id is None:
            return self._rejected(decision, "PAUSE_WORK requires a pause_task_id.")

        from app.models.task import Task

        task = self._ctx().db.get(Task, decision.pause_task_id)
        if task is None or task.company_id != self.company.id:
            return self._rejected(decision, "Task not found or belongs to another company.")

        if task.status.value == "BLOCKED":
            return self._rejected(decision, "Task is already blocked/paused.")

        task.status = TaskStatus.BLOCKED
        self._ctx().db.flush()

        event = Event(
            company_id=self.company.id,
            actor_id=self.agent.id,
            event_type="WORK_PAUSED",
            description=f"Task '{task.title}' paused by {self.agent.role.value}.",
            target_type="task",
            target_id=task.id,
            meta={"task_id": task.id, "day": self.company.current_day},
            simulation_day=self.company.current_day,
        )
        return ActionResult(
            success=True,
            message=f"Task {task.id} paused.",
            events=[event],
        )

    def _handle_resume_work(self, decision: AgentDecision) -> ActionResult:
        if decision.resume_task_id is None:
            return self._rejected(decision, "RESUME_WORK requires a resume_task_id.")

        from app.models.task import Task

        task = self._ctx().db.get(Task, decision.resume_task_id)
        if task is None or task.company_id != self.company.id:
            return self._rejected(decision, "Task not found or belongs to another company.")

        if task.status.value != "BLOCKED":
            return self._rejected(decision, "Task is not paused/blocked.")

        task.status = TaskStatus.TODO
        self._ctx().db.flush()

        event = Event(
            company_id=self.company.id,
            actor_id=self.agent.id,
            event_type="WORK_RESUMED",
            description=f"Task '{task.title}' resumed by {self.agent.role.value}.",
            target_type="task",
            target_id=task.id,
            meta={"task_id": task.id, "day": self.company.current_day},
            simulation_day=self.company.current_day,
        )
        return ActionResult(
            success=True,
            message=f"Task {task.id} resumed.",
            events=[event],
        )

    def _handle_request_resource(self, decision: AgentDecision) -> ActionResult:
        if decision.resource_type is None or decision.resource_amount is None:
            return self._rejected(decision, "REQUEST_RESOURCE requires resource_type and resource_amount.")

        from app.enums import ResourceType
        from app.simulation import resource as resource_system

        try:
            resource_type = ResourceType(decision.resource_type.upper())
        except ValueError:
            return self._rejected(decision, f"Invalid resource_type: {decision.resource_type}")

        available = resource_system._get_available_amount(self._ctx(), resource_type)
        if decision.resource_amount > available:
            return self._rejected(decision, f"Insufficient {resource_type.value}. Available: {available:.2f}")

        event = Event(
            company_id=self.company.id,
            actor_id=self.agent.id,
            event_type="RESOURCE_CONSTRAINED",
            description=f"Resource request for {resource_type.value}: ${decision.resource_amount:,.2f}.",
            target_type="resource",
            meta={"resource_type": resource_type.value, "requested": decision.resource_amount, "available": available, "day": self.company.current_day},
            simulation_day=self.company.current_day,
        )
        return ActionResult(
            success=True,
            message=f"Resource request for {resource_type.value} noted.",
            events=[event],
        )

    _HANDLERS = {
        ActionType.CREATE_TASK: _handle_create_task,
        ActionType.ASSIGN_TASK: _handle_assign_task,
        ActionType.UPDATE_TASK: _handle_update_task,
        ActionType.COMPLETE_TASK: _handle_complete_task,
        ActionType.CREATE_GOAL: _handle_create_goal,
        ActionType.UPDATE_GOAL: _handle_update_goal,
        ActionType.CREATE_PROJECT: _handle_create_project,
        ActionType.CREATE_MILESTONE: _handle_create_milestone,
        ActionType.CREATE_FEATURE: _handle_create_feature,
        ActionType.SEND_MESSAGE: _handle_send_message,
        ActionType.CREATE_PLAN: _handle_create_plan,
        ActionType.UPDATE_PLAN: _handle_update_plan,
        ActionType.SET_PRICE: _handle_set_price,
        ActionType.SET_TARGET_SEGMENT: _handle_set_target_segment,
        ActionType.UPDATE_POSITIONING: _handle_update_positioning,
        ActionType.CREATE_CAMPAIGN: _handle_create_campaign,
        ActionType.CREATE_SALES_OPPORTUNITY: _handle_create_sales_opportunity,
        # Phase 9 workforce actions
        ActionType.CREATE_JOB_OPENING: _handle_create_job_opening,
        ActionType.REVIEW_CANDIDATE: _handle_review_candidate,
        ActionType.MAKE_HIRING_DECISION: _handle_make_hiring_decision,
        ActionType.SET_EMPLOYEE_MANAGER: _handle_set_employee_manager,
        ActionType.PROMOTE_EMPLOYEE: _handle_promote_employee,
        ActionType.TERMINATE_EMPLOYEE: _handle_terminate_employee,
        # Phase 10 financial/capital actions
        ActionType.CREATE_FUNDING_ROUND: _handle_create_funding_round,
        ActionType.CONTACT_INVESTOR: _handle_contact_investor,
        ActionType.ADVANCE_PIPELINE: _handle_advance_pipeline,
        ActionType.MAKE_INVESTMENT_DECISION: _handle_make_investment_decision,
        ActionType.REQUEST_BUDGET: _handle_request_budget,
        ActionType.APPROVE_BUDGET: _handle_approve_budget,
        ActionType.REJECT_BUDGET: _handle_reject_budget,
        # Phase 11 advanced autonomous operations
        ActionType.CREATE_OBJECTIVE: _handle_create_objective,
        ActionType.UPDATE_OBJECTIVE: _handle_update_objective,
        ActionType.SET_PRIORITY: _handle_update_objective,
        ActionType.ALLOCATE_RESOURCE: _handle_allocate_resource,
        ActionType.ESCALATE_RISK: _handle_escalate_risk,
        ActionType.CREATE_MITIGATION: _handle_create_mitigation,
        ActionType.REQUEST_RESOURCE: _handle_request_resource,
        ActionType.REASSIGN_WORK: _handle_reassign_work,
        ActionType.PAUSE_WORK: _handle_pause_work,
        ActionType.RESUME_WORK: _handle_resume_work,
    }
