from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.agent import Agent
from app.models.company import Company
from app.models.customer import Customer
from app.models.decision import Decision
from app.models.event import Event
from app.models.expectation import Expectation
from app.models.goal import Goal
from app.models.incident import Incident
from app.models.memory import Memory
from app.models.message import Message
from app.models.milestone import Milestone
from app.models.objective import Objective
from app.models.plan import Plan
from app.models.product_feature import ProductFeature
from app.models.project import Project
from app.models.resource_allocation import ResourceAllocation
from app.models.risk import Risk
from app.models.task import Task
from app.simulation.domain import SimulationContext, make_rng
from app.schemas.simulation import (
    AgentMetricsRead,
    CustomerRead,
    DecisionRead,
    EventRead,
    ExpectationRead,
    FeatureRead,
    FinancialRead,
    GoalRead,
    IncidentRead,
    MarketRead,
    MemoryRead,
    MessageRead,
    MilestoneRead,
    ObjectiveRead,
    PlanRead,
    ProductRead,
    ProjectRead,
    ResourceAllocationRead,
    RiskRead,
    SimulationStateRead,
    TaskRead,
)


def _sim_ctx(db: Session, company: Company, day: int):
    return SimulationContext(db=db, company=company, day=day, rng=make_rng(company.seed, day))


@dataclass
class SimulationState:
    """Snapshot of the current company simulation state."""

    company_id: int
    status: Any
    current_day: int
    company: Company | None = None
    agents: list[Agent] = field(default_factory=list)
    goals: list[Goal] = field(default_factory=list)
    projects: list[Project] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)
    customers: list[Customer] = field(default_factory=list)
    milestones: list[Milestone] = field(default_factory=list)
    features: list[ProductFeature] = field(default_factory=list)
    recent_events: list[Event] = field(default_factory=list)
    recent_decisions: list[Decision] = field(default_factory=list)
    recent_memories: list[Memory] = field(default_factory=list)
    # Phase 5 autonomy state
    plans: list[Plan] = field(default_factory=list)
    messages: list[Message] = field(default_factory=list)
    expectations: list[Expectation] = field(default_factory=list)
    agent_metrics: list[dict] = field(default_factory=list)
    agent_count: int = 0
    event_count: int = 0
    goal_count: int = 0
    task_count: int = 0
    customer_count: int = 0
    milestone_count: int = 0
    feature_count: int = 0
    financial_metrics: dict | None = None
    objectives: list[Objective] = field(default_factory=list)
    resources: list[ResourceAllocation] = field(default_factory=list)
    risks: list[Risk] = field(default_factory=list)
    incidents: list[Incident] = field(default_factory=list)

    @classmethod
    def from_company(
        cls, db: Session, company: Company, *, event_limit: int = 50
    ) -> "SimulationState":
        company_id = company.id
        agents = list(
            db.execute(select(Agent).where(Agent.company_id == company_id)).scalars().all()
        )
        goals = list(
            db.execute(select(Goal).where(Goal.company_id == company_id)).scalars().all()
        )
        projects = list(
            db.execute(select(Project).where(Project.company_id == company_id)).scalars().all()
        )
        tasks = list(
            db.execute(select(Task).where(Task.company_id == company_id)).scalars().all()
        )
        customers = list(
            db.execute(select(Customer).where(Customer.company_id == company_id)).scalars().all()
        )
        milestones = list(
            db.execute(select(Milestone).where(Milestone.company_id == company_id)).scalars().all()
        )
        features = list(
            db.execute(select(ProductFeature).where(ProductFeature.company_id == company_id)).scalars().all()
        )
        events = list(
            db.execute(
                select(Event)
                .where(Event.company_id == company_id)
                .order_by(Event.id.desc())
                .limit(event_limit)
            ).scalars().all()
        )
        events.sort(key=lambda e: e.id)
        decisions = list(
            db.execute(
                select(Decision)
                .where(Decision.company_id == company_id)
                .order_by(Decision.id.desc())
                .limit(event_limit)
            ).scalars().all()
        )
        decisions.sort(key=lambda d: d.id)
        company_agent_ids = [a.id for a in agents]
        memories = list(
            db.execute(
                select(Memory)
                .where(Memory.agent_id.in_(company_agent_ids))
                .order_by(Memory.id.desc())
                .limit(event_limit)
            ).scalars().all()
        )
        memories.sort(key=lambda m: m.id)
        # --- Phase 5 autonomy state ---
        plans = list(
            db.execute(
                select(Plan).where(Plan.company_id == company_id).order_by(Plan.id)
            ).scalars().all()
        )
        messages = list(
            db.execute(
                select(Message).where(Message.company_id == company_id).order_by(Message.id)
            ).scalars().all()
        )
        expectations = list(
            db.execute(
                select(Expectation).where(Expectation.company_id == company_id).order_by(Expectation.id)
            ).scalars().all()
        )
        # --- Phase 11 operational state ---
        objectives = list(
            db.execute(
                select(Objective).where(Objective.company_id == company_id).order_by(Objective.id)
            ).scalars().all()
        )
        resources = list(
            db.execute(
                select(ResourceAllocation).where(ResourceAllocation.company_id == company_id).order_by(ResourceAllocation.id)
            ).scalars().all()
        )
        risks = list(
            db.execute(
                select(Risk).where(Risk.company_id == company_id).order_by(Risk.id)
            ).scalars().all()
        )
        incidents = list(
            db.execute(
                select(Incident).where(Incident.company_id == company_id).order_by(Incident.id)
            ).scalars().all()
        )
        from app.simulation import metrics as metrics_system
        from app.simulation.financial_health import get_financial_metrics
        financial_metrics = get_financial_metrics(company)
        agent_metrics = [
            metrics_system.compute_agent_metrics(
                _sim_ctx(db, company, company.current_day), a
            )
            for a in agents
        ]
        return cls(
            company_id=company.id,
            status=company.status,
            current_day=company.current_day,
            company=company,
            agents=agents,
            goals=goals,
            projects=projects,
            tasks=tasks,
            customers=customers,
            milestones=milestones,
            features=features,
            recent_events=events,
            recent_decisions=decisions,
            recent_memories=memories,
            plans=plans,
            messages=messages,
            expectations=expectations,
            objectives=objectives,
            resources=resources,
            risks=risks,
            incidents=incidents,
            agent_metrics=agent_metrics,
            agent_count=len(agents),
            event_count=db.execute(select(Event).where(Event.company_id == company_id)).scalars().all().__len__(),
            goal_count=len(goals),
            task_count=len(tasks),
            customer_count=len(customers),
            milestone_count=len(milestones),
            feature_count=len(features),
        )

    def to_read_model(self) -> SimulationStateRead:
        active_customers = [c for c in self.customers if c.status.value == "ACTIVE"]
        company = self.company
        if company is not None:
            cash = round(company.cash, 2)
            revenue = round(company.revenue, 2)
            expenses = round(company.expenses, 2)
            profit = round(company.revenue - company.expenses, 2)
            demand = round(company.market_demand, 3)
            competition = round(company.market_competition, 3)
            sentiment = round(company.market_sentiment, 3)
            readiness = round(company.product_readiness, 2)
        else:
            cash = revenue = expenses = profit = 0.0
            demand = competition = sentiment = 0.0
            readiness = 0.0
        financial_metrics = getattr(self, "financial_metrics", None)
        return SimulationStateRead(
            company_id=self.company_id,
            status=self.status,
            current_day=self.current_day,
            agents=[a for a in self.agents],
            goals=[
                GoalRead(
                    id=g.id,
                    title=g.title,
                    status=g.status,
                    priority=g.priority,
                    progress=g.progress,
                )
                for g in self.goals
            ],
            projects=[
                ProjectRead(
                    id=p.id,
                    name=p.name,
                    status=p.status,
                    progress=p.progress,
                )
                for p in self.projects
            ],
            tasks=[
                TaskRead(
                    id=t.id,
                    title=t.title,
                    status=t.status,
                    priority=t.priority,
                    progress=t.progress,
                    assigned_to=t.assigned_to,
                    project_id=t.project_id,
                )
                for t in self.tasks
            ],
            customers=[
                CustomerRead(
                    id=c.id,
                    name=c.name,
                    status=c.status,
                    monthly_value=c.monthly_value,
                    acquired_day=c.acquired_day,
                    churn_day=c.churn_day,
                )
                for c in self.customers
            ],
            milestones=[
                MilestoneRead(
                    id=m.id,
                    name=m.name,
                    status=m.status,
                    progress=m.progress,
                    project_id=m.project_id,
                )
                for m in self.milestones
            ],
            features=[
                FeatureRead(
                    id=f.id,
                    name=f.name,
                    status=f.status,
                    progress=f.progress,
                    quality=f.quality,
                    importance=f.importance,
                    project_id=f.project_id,
                )
                for f in self.features
            ],
            recent_events=[
                EventRead(
                    id=e.id,
                    company_id=e.company_id,
                    actor_id=e.actor_id,
                    event_type=e.event_type,
                    description=e.description,
                    target_type=e.target_type,
                    target_id=e.target_id,
                    meta=e.meta,
                    simulation_day=e.simulation_day,
                    created_at=e.created_at,
                )
                for e in self.recent_events
            ],
            recent_decisions=[
                DecisionRead(
                    id=d.id,
                    action=d.action,
                    reasoning=d.reasoning,
                    outcome=d.outcome,
                    simulation_day=d.simulation_day,
                )
                for d in self.recent_decisions
            ],
            recent_memories=[
                MemoryRead(
                    id=m.id,
                    agent_id=m.agent_id,
                    memory_type=m.memory_type,
                    content=m.content,
                    importance=m.importance,
                    simulation_day=m.simulation_day,
                )
                for m in self.recent_memories
            ],
            plans=[
                PlanRead(
                    id=p.id,
                    agent_id=p.agent_id,
                    goal_id=p.goal_id,
                    objective=p.objective,
                    status=p.status,
                    priority=p.priority,
                    progress=round(
                        sum(1 for s in p.steps if s.status == PlanStatus.COMPLETED) / len(p.steps), 2
                    ) if p.steps else 0.0,
                    current_step=p.current_step,
                    total_steps=len(p.steps),
                    created_day=p.created_day,
                    completed_day=p.completed_day,
                    steps=[
                        PlanStepRead(
                            id=s.id,
                            sequence=s.sequence,
                            description=s.description,
                            status=s.status,
                        )
                        for s in sorted(p.steps, key=lambda x: x.sequence)
                    ],
                )
                for p in self.plans
            ],
            messages=[
                MessageRead(
                    id=m.id,
                    sender_agent_id=m.sender_agent_id,
                    recipient_agent_id=m.recipient_agent_id,
                    subject=m.subject,
                    content=m.content,
                    priority=m.priority,
                    created_day=m.created_day,
                    read_day=m.read_day,
                )
                for m in self.messages
            ],
            expectations=[
                ExpectationRead(
                    id=e.id,
                    agent_id=e.agent_id,
                    description=e.description,
                    target_day=e.target_day,
                    target_metric=e.target_metric,
                    expected_value=e.expected_value,
                    actual_value=e.actual_value,
                    status=e.status,
                )
                for e in self.expectations
            ],
            agent_metrics=[
                AgentMetricsRead(
                    agent_id=m["agent_id"],
                    role=m["role"],
                    tasks_completed=m["tasks_completed"],
                    tasks_blocked=m["tasks_blocked"],
                    plans_completed=m["plans_completed"],
                    plans_failed=m["plans_failed"],
                    decisions=m["decisions"],
                    messages_sent=m["messages_sent"],
                    messages_received=m["messages_received"],
                )
                for m in self.agent_metrics
            ],
            financial=FinancialRead(
                cash=cash,
                revenue=revenue,
                expenses=expenses,
                profit=profit,
                daily_burn=round(financial_metrics.get("daily_burn", 0.0), 2) if financial_metrics else 0.0,
                runway_days=round(financial_metrics.get("runway_days", 0.0) or 0.0, 1) if financial_metrics else 0.0,
                financial_health_score=round(financial_metrics.get("financial_health_score", 0.0), 4) if financial_metrics else 0.0,
                financial_health=financial_metrics.get("financial_health", "HEALTHY") if financial_metrics else "HEALTHY",
                financial_risk_level=financial_metrics.get("financial_risk_level", "LOW") if financial_metrics else "LOW",
            ),
            market=MarketRead(
                demand=demand,
                competition=competition,
                sentiment=sentiment,
            ),
            product=ProductRead(
                readiness=readiness,
            ),
            agent_count=self.agent_count,
            event_count=self.event_count,
            goal_count=self.goal_count,
            task_count=self.task_count,
            customer_count=self.customer_count,
            active_customer_count=len(active_customers),
            milestone_count=self.milestone_count,
            feature_count=self.feature_count,
            objectives=[
                ObjectiveRead(
                    id=o.id,
                    company_id=o.company_id,
                    parent_id=o.parent_id,
                    title=o.title,
                    description=o.description,
                    objective_type=o.objective_type,
                    status=o.status,
                    priority=o.priority,
                    progress=o.progress,
                    expected_outcome=o.expected_outcome,
                    owner_id=o.owner_id,
                    created_day=o.created_day,
                    completed_day=o.completed_day,
                )
                for o in self.objectives
            ],
            resources=[
                ResourceAllocationRead(
                    id=r.id,
                    company_id=r.company_id,
                    resource_type=r.resource_type,
                    allocated_amount=r.allocated_amount,
                    available_amount=r.available_amount,
                    allocation_day=r.allocation_day,
                    purpose=r.purpose,
                    owner_id=r.owner_id,
                )
                for r in self.resources
            ],
            risks=[
                RiskRead(
                    id=r.id,
                    company_id=r.company_id,
                    risk_type=r.risk_type,
                    severity=r.severity,
                    source=r.source,
                    description=r.description,
                    affected_entity_type=r.affected_entity_type,
                    affected_entity_id=r.affected_entity_id,
                    status=r.status,
                    mitigation_actions=r.mitigation_actions,
                    detected_day=r.detected_day,
                    resolved_day=r.resolved_day,
                )
                for r in self.risks
            ],
            incidents=[
                IncidentRead(
                    id=i.id,
                    company_id=i.company_id,
                    incident_type=i.incident_type,
                    severity=i.severity,
                    description=i.description,
                    status=i.status,
                    detected_day=i.detected_day,
                    resolved_day=i.resolved_day,
                    root_cause=i.root_cause,
                    impact_assessment=i.impact_assessment,
                    related_risk_id=i.related_risk_id,
                )
                for i in self.incidents
            ],
        )
