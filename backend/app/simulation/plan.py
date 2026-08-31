"""Plan system: create, advance, revise, complete, and abandon plans.

Plan progress is derived deterministically from actual plan-step completion:

    progress = completed_steps / total_steps

A plan step is complete when its linked task (if any) is completed, or when
the step is explicitly marked complete via an UPDATE_PLAN action. Steps without
a linked task must be advanced by agent decisions.
"""

from __future__ import annotations

import logging

from sqlalchemy import select

from app.enums import EventType, PlanStatus, TaskStatus
from app.models.event import Event
from app.models.plan import Plan, PlanStep
from app.models.task import Task
from app.simulation.domain import SimulationContext

logger = logging.getLogger("agent_company_simulator")


def plan_progress(plan: Plan, steps: list[PlanStep]) -> float:
    """Deterministic progress: completed_steps / total_steps."""
    if not steps:
        return 0.0
    completed = sum(1 for s in steps if s.status == PlanStatus.COMPLETED)
    return completed / len(steps)


def step_is_complete(step: PlanStep, task_map: dict[int, Task]) -> bool:
    """A step is complete if linked task is done, or step already marked complete."""
    if step.status == PlanStatus.COMPLETED:
        return True
    if step.linked_task_id is not None:
        task = task_map.get(step.linked_task_id)
        if task is not None and task.status == TaskStatus.COMPLETED:
            return True
    return False


def create_plan(
    ctx: SimulationContext,
    agent_id: int,
    objective: str,
    priority: int,
    steps: list[str],
    goal_id: int | None = None,
) -> tuple[Plan, list[Event]]:
    """Create a plan with ordered steps. Returns the plan and creation event."""
    plan = Plan(
        company_id=ctx.company.id,
        agent_id=agent_id,
        goal_id=goal_id,
        objective=objective,
        status=PlanStatus.ACTIVE,
        priority=priority,
        created_day=ctx.day,
        current_step=0,
    )
    ctx.db.add(plan)
    ctx.db.flush()

    for i, desc in enumerate(steps):
        step = PlanStep(
            plan_id=plan.id,
            sequence=i,
            description=desc,
            status=PlanStatus.ACTIVE,
        )
        ctx.db.add(step)
    ctx.db.flush()

    event = Event(
        company_id=ctx.company.id,
        actor_id=agent_id,
        event_type=EventType.PLAN_CREATED,
        description=f"Plan created: {objective} ({len(steps)} steps).",
        target_type="plan",
        target_id=plan.id,
        meta={"plan_id": plan.id, "steps": len(steps), "day": ctx.day},
        simulation_day=ctx.day,
    )
    ctx.db.add(event)
    return plan, [event]


def advance_plan(ctx: SimulationContext, plan: Plan) -> list[Event]:
    """Deterministically advance a plan based on step completion.

    Steps with linked tasks auto-complete when the task completes. The
    current_step cursor moves to the first incomplete step. When all steps
    are complete, the plan completes automatically.
    """
    if plan.status != PlanStatus.ACTIVE:
        return []

    steps = list(
        ctx.db.execute(
            select(PlanStep)
            .where(PlanStep.plan_id == plan.id)
            .order_by(PlanStep.sequence)
        )
        .scalars()
        .all()
    )
    if not steps:
        return []

    tasks = list(
        ctx.db.execute(select(Task).where(Task.company_id == ctx.company.id)).scalars().all()
    )
    task_map = {t.id: t for t in tasks}

    events: list[Event] = []
    newly_completed = False
    for step in steps:
        if step.status == PlanStatus.COMPLETED:
            continue
        if step_is_complete(step, task_map):
            step.status = PlanStatus.COMPLETED
            newly_completed = True

    # Move current_step cursor to first incomplete step.
    plan.current_step = len(steps)
    for i, step in enumerate(steps):
        if step.status != PlanStatus.COMPLETED:
            plan.current_step = i
            break

    if newly_completed:
        progress = plan_progress(plan, steps)
        logger.debug("Plan %s advanced: progress=%.2f", plan.id, progress)

    # Auto-complete plan when all steps done.
    if all(s.status == PlanStatus.COMPLETED for s in steps):
        plan.status = PlanStatus.COMPLETED
        plan.completed_day = ctx.day
        events.append(
            Event(
                company_id=ctx.company.id,
                actor_id=plan.agent_id,
                event_type=EventType.PLAN_COMPLETED,
                description=f"Plan '{plan.objective}' completed.",
                target_type="plan",
                target_id=plan.id,
                meta={"plan_id": plan.id, "day": ctx.day},
                simulation_day=ctx.day,
            )
        )
    return events


def revise_plan(
    ctx: SimulationContext,
    plan: Plan,
    new_objective: str,
    new_steps: list[str],
) -> tuple[Plan, list[Event]]:
    """Revise a plan: mark old plan as cancelled, create a replacement.

    Plan history is preserved (old plan is not silently overwritten).
    """
    plan.status = PlanStatus.CANCELLED
    plan.completed_day = ctx.day
    ctx.db.flush()

    replacement, events = create_plan(
        ctx,
        agent_id=plan.agent_id,
        objective=new_objective,
        priority=plan.priority,
        steps=new_steps,
        goal_id=plan.goal_id,
    )
    events.append(
        Event(
            company_id=ctx.company.id,
            actor_id=plan.agent_id,
            event_type=EventType.PLAN_REVISED,
            description=(
                f"Plan revised: '{plan.objective}' -> '{new_objective}'."
            ),
            target_type="plan",
            target_id=replacement.id,
            meta={
                "old_plan_id": plan.id,
                "new_plan_id": replacement.id,
                "day": ctx.day,
            },
            simulation_day=ctx.day,
        )
    )
    return replacement, events


def complete_plan(ctx: SimulationContext, plan: Plan) -> list[Event]:
    """Explicitly mark a plan as completed."""
    if plan.status != PlanStatus.ACTIVE:
        return []
    plan.status = PlanStatus.COMPLETED
    plan.completed_day = ctx.day
    steps = list(
        ctx.db.execute(select(PlanStep).where(PlanStep.plan_id == plan.id)).scalars().all()
    )
    for step in steps:
        if step.status == PlanStatus.ACTIVE:
            step.status = PlanStatus.COMPLETED
    ctx.db.flush()
    return [
        Event(
            company_id=ctx.company.id,
            actor_id=plan.agent_id,
            event_type=EventType.PLAN_COMPLETED,
            description=f"Plan '{plan.objective}' marked completed.",
            target_type="plan",
            target_id=plan.id,
            meta={"plan_id": plan.id, "day": ctx.day},
            simulation_day=ctx.day,
        )
    ]


def abandon_plan(ctx: SimulationContext, plan: Plan) -> list[Event]:
    """Abandon a plan (failure/cancellation)."""
    if plan.status not in (PlanStatus.ACTIVE,):
        return []
    plan.status = PlanStatus.FAILED
    plan.completed_day = ctx.day
    ctx.db.flush()
    return [
        Event(
            company_id=ctx.company.id,
            actor_id=plan.agent_id,
            event_type=EventType.PLAN_FAILED,
            description=f"Plan '{plan.objective}' abandoned.",
            target_type="plan",
            target_id=plan.id,
            meta={"plan_id": plan.id, "day": ctx.day},
            simulation_day=ctx.day,
        )
    ]


def update_plans(ctx: SimulationContext) -> list[Event]:
    """Advance all active plans for the company. Returns generated events."""
    plans = list(
        ctx.db.execute(
            select(Plan)
            .where(Plan.company_id == ctx.company.id)
            .where(Plan.status == PlanStatus.ACTIVE)
        )
        .scalars()
        .all()
    )
    events: list[Event] = []
    for plan in plans:
        events.extend(advance_plan(ctx, plan))
    return events
