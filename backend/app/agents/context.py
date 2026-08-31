"""Structured observation/context representation for agents.

Produces a compact, deterministic view of company state so that agents
receive only the information relevant to their decision-making.
"""

from pydantic import BaseModel

from app.models.agent import Agent
from app.models.company import Company
from app.models.goal import Goal
from app.models.milestone import Milestone
from app.models.product_feature import ProductFeature
from app.models.project import Project
from app.models.task import Task


class CompanyView(BaseModel):
    name: str
    mission: str
    current_day: int
    cash: float
    revenue: float
    expenses: float
    profit: float
    status: str


class GoalView(BaseModel):
    id: int
    title: str
    status: str
    priority: int
    progress: float


class ProjectView(BaseModel):
    id: int
    name: str
    status: str
    progress: float


class TaskView(BaseModel):
    id: int
    title: str
    status: str
    priority: int
    progress: float
    effort: float
    remaining_effort: float
    task_type: str
    assigned_to: int | None
    created_by: int | None
    project_id: int | None
    milestone_id: int | None
    feature_id: int | None


class MilestoneView(BaseModel):
    id: int
    name: str
    status: str
    progress: float
    project_id: int


class FeatureView(BaseModel):
    id: int
    name: str
    status: str
    progress: float
    quality: float
    importance: int
    project_id: int | None


class OrganizationView(BaseModel):
    agent_id: int
    name: str
    role: str
    authority: int
    capacity: float
    workload: float
    morale: float
    energy: float
    manager_id: int | None
    direct_report_ids: list[int]


class FinancialView(BaseModel):
    cash: float
    revenue: float
    expenses: float
    profit: float
    burn: float
    runway_days: float | None
    financial_health_score: float
    financial_health: str
    financial_risk_level: str


class CustomerView(BaseModel):
    active_count: int
    churned_count: int
    total_monthly_value: float


class ProductView(BaseModel):
    readiness: float
    quality: float
    technical_debt: float


class MarketView(BaseModel):
    demand: float
    competition: float
    sentiment: float


class MarketingView(BaseModel):
    effectiveness: float


class EngineeringView(BaseModel):
    assigned_tasks: list[TaskView]
    available_tasks: list[TaskView]
    blocked_tasks: list[TaskView]


class WorkforceOverview(BaseModel):
    headcount: int = 0
    active_count: int = 0
    onboarding_count: int = 0
    underperforming_count: int = 0
    payroll: float = 0.0
    total_capacity: float = 0.0
    avg_morale: float = 0.0
    avg_productivity: float = 0.0


class EmployeeView(BaseModel):
    id: int
    name: str
    role: str
    status: str
    salary: float
    capacity: float
    productivity: float
    morale: float
    performance_score: float
    manager_id: int | None
    hired_day: int | None


class JobOpeningView(BaseModel):
    id: int
    role: str
    title: str
    status: str
    salary_min: float
    salary_max: float
    created_day: int


class CandidateView(BaseModel):
    id: int
    name: str
    role: str
    skills: list[str]
    experience: float
    salary_expectation: float
    productivity_potential: float
    culture_fit: float
    reliability: float
    hiring_score: float
    status: str


class WorkforceView(BaseModel):
    overview: WorkforceOverview
    employees: list[EmployeeView]
    job_openings: list[JobOpeningView]
    candidates: list[CandidateView]
    capacity_by_role: dict[str, float]


class RecentActivityView(BaseModel):
    recent_events: list[dict]
    recent_decisions: list[dict]
    recent_environmental_events: list[dict]


# --- Phase 5 autonomy views ---


class PlanStepView(BaseModel):
    sequence: int
    description: str
    status: str


class PlanView(BaseModel):
    id: int
    objective: str
    status: str
    priority: int
    progress: float
    current_step: int
    total_steps: int
    steps: list[PlanStepView]


class MessageView(BaseModel):
    id: int
    sender_agent_id: int
    recipient_agent_id: int
    subject: str
    content: str
    priority: str
    created_day: int
    is_unread: bool


class MemoryView(BaseModel):
    id: int
    memory_type: str
    content: str
    importance: float
    simulation_day: int


class ExpectationView(BaseModel):
    id: int
    description: str
    target_day: int
    target_metric: str
    expected_value: float
    actual_value: float | None
    status: str


class AgentStateView(BaseModel):
    current_objective: str | None
    current_plan: PlanView | None
    active_plan_count: int
    workload: float
    capacity: float


class AdaptationSignalView(BaseModel):
    at_risk_expectations: list[dict]
    recently_missed: list[dict]
    plan_risks: list[dict]


# --- Phase 6 market & strategy views ---


class SegmentView(BaseModel):
    name: str
    segment_type: str
    size: float
    demand: float
    price_sensitivity: float
    avg_customer_value: float
    sales_cycle_days: int


class CompetitorView(BaseModel):
    id: int
    name: str
    market_share: float
    price: float
    product_quality: float
    brand_strength: float
    target_segment: str
    strategy: str


class StrategyView(BaseModel):
    target_segment: str
    price: float
    positioning: str
    brand_strength: float
    sales_effectiveness: float
    market_share: float
    product_market_fit: float
    competitive_pressure: float


class CampaignView(BaseModel):
    id: int
    name: str
    segment: str
    daily_spend: float
    days_remaining: int
    effectiveness: float
    status: str


class SalesOpportunityView(BaseModel):
    id: int
    name: str
    segment: str
    value: float
    stage: str
    created_day: int
    expected_close_day: int


# --- Phase 11 operational context views ---


class ObjectiveView(BaseModel):
    id: int
    title: str
    objective_type: str
    status: str
    priority: int
    progress: float
    expected_outcome: str
    owner_id: int | None
    created_day: int
    completed_day: int | None


class ResourceView(BaseModel):
    resource_type: str
    allocated_amount: float
    available_amount: float
    purpose: str
    owner_id: int | None


class RiskView(BaseModel):
    id: int
    risk_type: str
    severity: str
    source: str
    description: str
    affected_entity_type: str | None
    affected_entity_id: int | None
    status: str
    mitigation_actions: str
    detected_day: int
    resolved_day: int | None


class IncidentView(BaseModel):
    id: int
    incident_type: str
    severity: str
    description: str
    status: str
    detected_day: int
    resolved_day: int | None
    root_cause: str
    impact_assessment: str


class AttentionView(BaseModel):
    active_objectives: int
    active_risks: int
    active_incidents: int
    attention_capacity: float


class AgentContext(BaseModel):
    """Compact, serializable snapshot of company state for an agent."""

    company: CompanyView
    goals: list[GoalView]
    projects: list[ProjectView]
    tasks: list[TaskView]
    milestones: list[MilestoneView]
    features: list[FeatureView]
    organization: OrganizationView
    financial: FinancialView
    customers: CustomerView
    product: ProductView
    market: MarketView
    marketing: MarketingView
    engineering: EngineeringView
    workforce: WorkforceView
    recent_activity: RecentActivityView
    # Phase 5 autonomy context
    agent_state: AgentStateView
    plans: list[PlanView]
    messages: list[MessageView]
    memories: list[MemoryView]
    expectations: list[ExpectationView]
    adaptation_signals: AdaptationSignalView
    # Phase 6 market & strategy context
    strategy: StrategyView
    segments: list[SegmentView]
    competitors: list[CompetitorView]
    campaigns: list[CampaignView]
    sales_opportunities: list[SalesOpportunityView]
    # Phase 11 operational context
    objectives: list[ObjectiveView]
    resources: list[ResourceView]
    risks: list[RiskView]
    incidents: list[IncidentView]
    attention: AttentionView


def build_context(
    company: Company,
    agent: Agent,
    *,
    goals: list[Goal],
    projects: list[Project],
    tasks: list[Task],
    milestones: list[Milestone],
    features: list[ProductFeature],
    recent_events: list[dict],
    recent_decisions: list[dict],
    recent_environmental_events: list[dict],
    customer_active_count: int,
    customer_churned_count: int,
    customer_total_monthly_value: float,
    # Phase 5 autonomy context
    plans: list,
    messages: list,
    memories: list,
    expectations: list,
    adaptation_signals: dict,
    # Phase 6 market & strategy context
    segments: list,
    competitors: list,
    campaigns: list,
    sales_opportunities: list,
    strategy: dict,
    # Phase 9 workforce context
    workforce_overview: dict | None = None,
    employees: list | None = None,
    job_openings: list | None = None,
    candidates: list | None = None,
    capacity_by_role: dict | None = None,
    # Phase 10 financial health context
    financial_metrics: dict | None = None,
    # Phase 11 operational context
    objectives: list | None = None,
    resources: list | None = None,
    risks: list | None = None,
    incidents: list | None = None,
    active_objectives_count: int = 0,
    active_risks_count: int = 0,
    active_incidents_count: int = 0,
    attention_capacity: float = 5.0,
) -> AgentContext:
    direct_report_ids = [sub.id for sub in agent.subordinates]

    # Engineering view: tasks relevant to this engineer.
    assigned = [t for t in tasks if t.assigned_to == agent.id]
    available = [t for t in assigned if t.status in ("TODO", "IN_PROGRESS")]
    blocked = [t for t in assigned if t.status == "BLOCKED"]

    def _task_view(t: Task) -> TaskView:
        return TaskView(
            id=t.id,
            title=t.title,
            status=t.status.value,
            priority=t.priority,
            progress=round(t.progress, 2),
            effort=t.effort,
            remaining_effort=round(t.remaining_effort, 2),
            task_type=t.task_type.value,
            assigned_to=t.assigned_to,
            created_by=t.created_by,
            project_id=t.project_id,
            milestone_id=t.milestone_id,
            feature_id=t.feature_id,
        )

    # --- Plan views ---
    def _plan_step_view(s) -> PlanStepView:
        return PlanStepView(
            sequence=s.sequence,
            description=s.description,
            status=s.status.value,
        )

    def _plan_view(p) -> PlanView:
        steps = sorted(p.steps, key=lambda s: s.sequence)
        total = len(steps)
        completed = sum(1 for s in steps if s.status.value == "COMPLETED")
        progress = completed / total if total > 0 else 0.0
        return PlanView(
            id=p.id,
            objective=p.objective,
            status=p.status.value,
            priority=p.priority,
            progress=round(progress, 2),
            current_step=p.current_step,
            total_steps=total,
            steps=[_plan_step_view(s) for s in steps],
        )

    active_plans = [p for p in plans if p.status.value == "ACTIVE"]
    current_plan = active_plans[0] if active_plans else None

    # --- Agent state ---
    agent_state = AgentStateView(
        current_objective=current_plan.objective if current_plan else None,
        current_plan=_plan_view(current_plan) if current_plan else None,
        active_plan_count=len(active_plans),
        workload=agent.workload,
        capacity=agent.capacity,
    )

    # --- Message views ---
    def _message_view(m) -> MessageView:
        return MessageView(
            id=m.id,
            sender_agent_id=m.sender_agent_id,
            recipient_agent_id=m.recipient_agent_id,
            subject=m.subject,
            content=m.content,
            priority=m.priority.value if hasattr(m.priority, "value") else str(m.priority),
            created_day=m.created_day,
            is_unread=m.read_day is None,
        )

    # --- Memory views ---
    def _memory_view(m) -> MemoryView:
        return MemoryView(
            id=m.id,
            memory_type=m.memory_type,
            content=m.content,
            importance=m.importance,
            simulation_day=m.simulation_day,
        )

    # --- Expectation views ---
    def _expectation_view(e) -> ExpectationView:
        return ExpectationView(
            id=e.id,
            description=e.description,
            target_day=e.target_day,
            target_metric=e.target_metric,
            expected_value=e.expected_value,
            actual_value=e.actual_value,
            status=e.status.value if hasattr(e.status, "value") else str(e.status),
        )

    # --- Workforce views ---
    def _employee_view(e) -> EmployeeView:
        return EmployeeView(
            id=e.id,
            name=e.name,
            role=e.role,
            status=e.status.value if hasattr(e.status, "value") else str(e.status),
            salary=round(e.salary, 2),
            capacity=round(e.capacity, 2),
            productivity=round(e.productivity, 2),
            morale=round(e.morale, 2),
            performance_score=round(e.performance_score, 2),
            manager_id=e.manager_id,
            hired_day=e.hired_day,
        )

    def _job_view(j) -> JobOpeningView:
        return JobOpeningView(
            id=j.id,
            role=j.role,
            title=j.title,
            status=j.status.value if hasattr(j.status, "value") else str(j.status),
            salary_min=round(j.salary_min, 2),
            salary_max=round(j.salary_max, 2),
            created_day=j.created_day,
        )

    def _candidate_view(c) -> CandidateView:
        return CandidateView(
            id=c.id,
            name=c.name,
            role=c.role,
            skills=c.skills or [],
            experience=round(c.experience, 1),
            salary_expectation=round(c.salary_expectation, 2),
            productivity_potential=round(c.productivity_potential, 2),
            culture_fit=round(c.culture_fit, 2),
            reliability=round(c.reliability, 2),
            hiring_score=round(c.hiring_score, 2),
            status=c.status.value if hasattr(c.status, "value") else str(c.status),
        )

    workforce_view = WorkforceView(
        overview=WorkforceOverview(
            **(workforce_overview or {}),
        ),
        employees=[_employee_view(e) for e in (employees or [])],
        job_openings=[_job_view(j) for j in (job_openings or [])],
        candidates=[_candidate_view(c) for c in (candidates or [])],
        capacity_by_role=capacity_by_role or {},
    )

    # --- Phase 11 operational views ---
    def _objective_view(o) -> ObjectiveView:
        return ObjectiveView(
            id=o.id,
            title=o.title,
            objective_type=o.objective_type.value if hasattr(o.objective_type, "value") else str(o.objective_type),
            status=o.status.value if hasattr(o.status, "value") else str(o.status),
            priority=o.priority,
            progress=round(o.progress, 2),
            expected_outcome=o.expected_outcome or "",
            owner_id=o.owner_id,
            created_day=o.created_day,
            completed_day=o.completed_day,
        )

    def _resource_view(r) -> ResourceView:
        return ResourceView(
            resource_type=r.resource_type.value if hasattr(r.resource_type, "value") else str(r.resource_type),
            allocated_amount=round(r.allocated_amount, 2),
            available_amount=round(r.available_amount, 2),
            purpose=r.purpose or "",
            owner_id=r.owner_id,
        )

    def _risk_view(r) -> RiskView:
        return RiskView(
            id=r.id,
            risk_type=r.risk_type,
            severity=r.severity.value if hasattr(r.severity, "value") else str(r.severity),
            source=r.source or "",
            description=r.description or "",
            affected_entity_type=r.affected_entity_type,
            affected_entity_id=r.affected_entity_id,
            status=r.status.value if hasattr(r.status, "value") else str(r.status),
            mitigation_actions=r.mitigation_actions or "",
            detected_day=r.detected_day,
            resolved_day=r.resolved_day,
        )

    def _incident_view(i) -> IncidentView:
        return IncidentView(
            id=i.id,
            incident_type=i.incident_type.value if hasattr(i.incident_type, "value") else str(i.incident_type),
            severity=i.severity.value if hasattr(i.severity, "value") else str(i.severity),
            description=i.description or "",
            status=i.status.value if hasattr(i.status, "value") else str(i.status),
            detected_day=i.detected_day,
            resolved_day=i.resolved_day,
            root_cause=i.root_cause or "",
            impact_assessment=i.impact_assessment or "",
        )

    attention_view = AttentionView(
        active_objectives=active_objectives_count,
        active_risks=active_risks_count,
        active_incidents=active_incidents_count,
        attention_capacity=round(attention_capacity, 2),
    )

    return AgentContext(
        company=CompanyView(
            name=company.name,
            mission=company.mission or "",
            current_day=company.current_day,
            cash=round(company.cash, 2),
            revenue=round(company.revenue, 2),
            expenses=round(company.expenses, 2),
            profit=round(company.revenue - company.expenses, 2),
            status=company.status.value,
        ),
        goals=[
            GoalView(
                id=g.id,
                title=g.title,
                status=g.status.value,
                priority=g.priority,
                progress=g.progress,
            )
            for g in goals
        ],
        projects=[
            ProjectView(
                id=p.id,
                name=p.name,
                status=p.status.value,
                progress=p.progress,
            )
            for p in projects
        ],
        tasks=[_task_view(t) for t in tasks],
        milestones=[
            MilestoneView(
                id=m.id,
                name=m.name,
                status=m.status.value,
                progress=m.progress,
                project_id=m.project_id,
            )
            for m in milestones
        ],
        features=[
            FeatureView(
                id=f.id,
                name=f.name,
                status=f.status.value,
                progress=f.progress,
                quality=f.quality,
                importance=f.importance,
                project_id=f.project_id,
            )
            for f in features
        ],
        organization=OrganizationView(
            agent_id=agent.id,
            name=agent.name,
            role=agent.role.value,
            authority=agent.authority,
            capacity=agent.capacity,
            workload=agent.workload,
            morale=agent.morale,
            energy=agent.energy,
            manager_id=agent.manager_id,
            direct_report_ids=direct_report_ids,
        ),
        financial=FinancialView(
            cash=round(company.cash, 2),
            revenue=round(company.revenue, 2),
            expenses=round(company.expenses, 2),
            profit=round(company.revenue - company.expenses, 2),
            burn=round(financial_metrics.get("daily_burn", 0.0), 2) if financial_metrics else 0.0,
            runway_days=round(financial_metrics.get("runway_days", 0.0) or 0.0, 1) if financial_metrics else 0.0,
            financial_health_score=round(financial_metrics.get("financial_health_score", 0.0), 4) if financial_metrics else 0.0,
            financial_health=financial_metrics.get("financial_health", "HEALTHY") if financial_metrics else "HEALTHY",
            financial_risk_level=financial_metrics.get("financial_risk_level", "LOW") if financial_metrics else "LOW",
        ),
        customers=CustomerView(
            active_count=customer_active_count,
            churned_count=customer_churned_count,
            total_monthly_value=round(customer_total_monthly_value, 2),
        ),
        product=ProductView(
            readiness=round(company.product_readiness, 4),
            quality=round(company.product_quality, 4),
            technical_debt=round(company.technical_debt, 4),
        ),
        market=MarketView(
            demand=round(company.market_demand, 3),
            competition=round(company.market_competition, 3),
            sentiment=round(company.market_sentiment, 3),
        ),
        marketing=MarketingView(
            effectiveness=round(company.marketing_effectiveness, 4),
        ),
        engineering=EngineeringView(
            assigned_tasks=[_task_view(t) for t in assigned],
            available_tasks=[_task_view(t) for t in available],
            blocked_tasks=[_task_view(t) for t in blocked],
        ),
        workforce=workforce_view,
        recent_activity=RecentActivityView(
            recent_events=recent_events,
            recent_decisions=recent_decisions,
            recent_environmental_events=recent_environmental_events,
        ),
        agent_state=agent_state,
        plans=[_plan_view(p) for p in plans],
        messages=[_message_view(m) for m in messages],
        memories=[_memory_view(m) for m in memories],
        expectations=[_expectation_view(e) for e in expectations],
        adaptation_signals=AdaptationSignalView(
            at_risk_expectations=adaptation_signals.get("at_risk_expectations", []),
            recently_missed=adaptation_signals.get("recently_missed", []),
            plan_risks=adaptation_signals.get("plan_risks", []),
        ),
        strategy=StrategyView(
            target_segment=strategy.get("target_segment", "SMB"),
            price=strategy.get("price", 100.0),
            positioning=strategy.get("positioning", ""),
            brand_strength=strategy.get("brand_strength", 0.1),
            sales_effectiveness=strategy.get("sales_effectiveness", 0.1),
            market_share=strategy.get("market_share", 0.0),
            product_market_fit=strategy.get("product_market_fit", 0.0),
            competitive_pressure=strategy.get("competitive_pressure", 0.0),
        ),
        segments=[
            SegmentView(
                name=s.name,
                segment_type=s.segment_type.value if hasattr(s.segment_type, "value") else str(s.segment_type),
                size=s.size,
                demand=s.demand,
                price_sensitivity=s.price_sensitivity,
                avg_customer_value=s.avg_customer_value,
                sales_cycle_days=s.sales_cycle_days,
            )
            for s in segments
        ],
        competitors=[
            CompetitorView(
                id=c.id,
                name=c.name,
                market_share=c.market_share,
                price=c.price,
                product_quality=c.product_quality,
                brand_strength=c.brand_strength,
                target_segment=c.target_segment.value if hasattr(c.target_segment, "value") else str(c.target_segment),
                strategy=c.strategy.value if hasattr(c.strategy, "value") else str(c.strategy),
            )
            for c in competitors
        ],
        campaigns=[
            CampaignView(
                id=c.id,
                name=c.name,
                segment=c.segment.value if hasattr(c.segment, "value") else str(c.segment),
                daily_spend=c.daily_spend,
                days_remaining=c.days_remaining,
                effectiveness=c.effectiveness,
                status=c.status.value if hasattr(c.status, "value") else str(c.status),
            )
            for c in campaigns
        ],
        sales_opportunities=[
            SalesOpportunityView(
                id=o.id,
                name=o.name,
                segment=o.segment.value if hasattr(o.segment, "value") else str(o.segment),
                value=o.value,
                stage=o.stage.value if hasattr(o.stage, "value") else str(o.stage),
                created_day=o.created_day,
                expected_close_day=o.expected_close_day,
            )
            for o in sales_opportunities
        ],
        objectives=[_objective_view(o) for o in (objectives or [])],
        resources=[_resource_view(r) for r in (resources or [])],
        risks=[_risk_view(r) for r in (risks or [])],
        incidents=[_incident_view(i) for i in (incidents or [])],
        attention=attention_view,
    )
