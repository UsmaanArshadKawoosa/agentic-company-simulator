from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.enums import (
    CompanyStatus,
    CustomerStatus,
    EventType,
    ExpectationStatus,
    FeatureStatus,
    GoalStatus,
    MessagePriority,
    MilestoneStatus,
    PlanStatus,
    ProjectStatus,
    TaskStatus,
    IncidentStatus,
    IncidentType,
    ObjectiveStatus,
    ObjectiveType,
    ResourceType,
    RiskSeverity,
    RiskStatus,
)
from app.schemas.agent import AgentRead


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    actor_id: int | None = None
    event_type: EventType
    description: str
    target_type: str | None = None
    target_id: int | None = None
    meta: dict | None = None
    simulation_day: int
    created_at: datetime


class GoalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    status: GoalStatus
    priority: int
    progress: float


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    status: ProjectStatus
    progress: float


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    status: TaskStatus
    priority: int
    progress: float
    assigned_to: int | None = None
    project_id: int | None = None


class CustomerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    status: CustomerStatus
    monthly_value: float
    acquired_day: int
    churn_day: int | None = None


class MilestoneRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    status: MilestoneStatus
    progress: float
    project_id: int


class FeatureRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    status: FeatureStatus
    progress: float
    quality: float
    importance: int
    project_id: int | None = None


class DecisionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action: str
    reasoning: str | None = None
    outcome: str | None = None
    simulation_day: int


class MemoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    agent_id: int
    memory_type: str
    content: str
    importance: float
    simulation_day: int


class PlanStepRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sequence: int
    description: str
    status: PlanStatus


class PlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    agent_id: int
    goal_id: int | None = None
    objective: str
    status: PlanStatus
    priority: int
    progress: float
    current_step: int
    total_steps: int
    created_day: int
    completed_day: int | None = None
    steps: list[PlanStepRead] = []


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sender_agent_id: int
    recipient_agent_id: int
    subject: str
    content: str
    priority: MessagePriority
    created_day: int
    read_day: int | None = None


class ExpectationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    agent_id: int
    description: str
    target_day: int
    target_metric: str
    expected_value: float
    actual_value: float | None = None
    status: ExpectationStatus


class AgentMetricsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    agent_id: int
    role: str
    tasks_completed: int
    tasks_blocked: int
    plans_completed: int
    plans_failed: int
    decisions: int
    messages_sent: int
    messages_received: int


class FinancialRead(BaseModel):
    cash: float
    revenue: float
    expenses: float
    profit: float
    daily_burn: float
    runway_days: float | None
    financial_health_score: float
    financial_health: str
    financial_risk_level: str


class MarketRead(BaseModel):
    demand: float
    competition: float
    sentiment: float


class ProductRead(BaseModel):
    readiness: float


# --- Phase 11 schemas ---


class ObjectiveRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    parent_id: int | None = None
    title: str
    description: str | None = ""
    objective_type: ObjectiveType
    status: ObjectiveStatus
    priority: int
    progress: float
    expected_outcome: str | None = ""
    owner_id: int | None = None
    created_day: int
    completed_day: int | None = None


class ResourceAllocationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    resource_type: ResourceType
    allocated_amount: float
    available_amount: float
    allocation_day: int
    purpose: str | None = ""
    owner_id: int | None = None


class RiskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    risk_type: str
    severity: RiskSeverity
    source: str | None = ""
    description: str | None = ""
    affected_entity_type: str | None = None
    affected_entity_id: int | None = None
    status: RiskStatus
    mitigation_actions: str | None = ""
    detected_day: int
    resolved_day: int | None = None


class IncidentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    incident_type: IncidentType
    severity: RiskSeverity
    description: str | None = ""
    status: IncidentStatus
    detected_day: int
    resolved_day: int | None = None
    root_cause: str | None = ""
    impact_assessment: str | None = ""
    related_risk_id: int | None = None


class SimulationStateRead(BaseModel):
    company_id: int
    status: CompanyStatus
    current_day: int
    agents: list[AgentRead]
    goals: list[GoalRead]
    projects: list[ProjectRead]
    tasks: list[TaskRead]
    customers: list[CustomerRead]
    milestones: list[MilestoneRead]
    features: list[FeatureRead]
    recent_events: list[EventRead]
    recent_decisions: list[DecisionRead]
    recent_memories: list[MemoryRead]
    # Phase 5 autonomy state
    plans: list[PlanRead] = []
    messages: list[MessageRead] = []
    expectations: list[ExpectationRead] = []
    agent_metrics: list[AgentMetricsRead] = []
    financial: FinancialRead
    market: MarketRead
    product: ProductRead
    agent_count: int
    event_count: int
    goal_count: int
    task_count: int
    customer_count: int
    active_customer_count: int
    milestone_count: int
    feature_count: int
    # Phase 11 operational state
    objectives: list[ObjectiveRead] = []
    resources: list[ResourceAllocationRead] = []
    risks: list[RiskRead] = []
    incidents: list[IncidentRead] = []


class SimulationActionResponse(BaseModel):
    message: str
    state: SimulationStateRead
