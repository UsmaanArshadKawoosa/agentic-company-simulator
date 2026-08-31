"""Structured decision representation and action vocabulary."""

from enum import Enum

from pydantic import BaseModel, Field


class ActionType(str, Enum):
    """Controlled action vocabulary available to agents.

    The simulation only permits actions from this set. Agents cannot emit
    arbitrary database operations or SQL.
    """

    CREATE_TASK = "CREATE_TASK"
    ASSIGN_TASK = "ASSIGN_TASK"
    UPDATE_TASK = "UPDATE_TASK"
    COMPLETE_TASK = "COMPLETE_TASK"
    CREATE_GOAL = "CREATE_GOAL"
    UPDATE_GOAL = "UPDATE_GOAL"
    CREATE_PROJECT = "CREATE_PROJECT"
    CREATE_MILESTONE = "CREATE_MILESTONE"
    CREATE_FEATURE = "CREATE_FEATURE"
    SEND_MESSAGE = "SEND_MESSAGE"
    CREATE_PLAN = "CREATE_PLAN"
    UPDATE_PLAN = "UPDATE_PLAN"
    # Phase 6 strategic actions
    SET_PRICE = "SET_PRICE"
    SET_TARGET_SEGMENT = "SET_TARGET_SEGMENT"
    UPDATE_POSITIONING = "UPDATE_POSITIONING"
    CREATE_CAMPAIGN = "CREATE_CAMPAIGN"
    CREATE_SALES_OPPORTUNITY = "CREATE_SALES_OPPORTUNITY"
    # Phase 9 workforce actions
    CREATE_JOB_OPENING = "CREATE_JOB_OPENING"
    REVIEW_CANDIDATE = "REVIEW_CANDIDATE"
    MAKE_HIRING_DECISION = "MAKE_HIRING_DECISION"
    SET_EMPLOYEE_MANAGER = "SET_EMPLOYEE_MANAGER"
    PROMOTE_EMPLOYEE = "PROMOTE_EMPLOYEE"
    TERMINATE_EMPLOYEE = "TERMINATE_EMPLOYEE"
    # Phase 10 financial/capital actions
    CREATE_FUNDING_ROUND = "CREATE_FUNDING_ROUND"
    CONTACT_INVESTOR = "CONTACT_INVESTOR"
    ADVANCE_PIPELINE = "ADVANCE_PIPELINE"
    MAKE_INVESTMENT_DECISION = "MAKE_INVESTMENT_DECISION"
    REQUEST_BUDGET = "REQUEST_BUDGET"
    APPROVE_BUDGET = "APPROVE_BUDGET"
    REJECT_BUDGET = "REJECT_BUDGET"
    # Phase 11 advanced autonomous operations
    CREATE_OBJECTIVE = "CREATE_OBJECTIVE"
    UPDATE_OBJECTIVE = "UPDATE_OBJECTIVE"
    SET_PRIORITY = "SET_PRIORITY"
    ALLOCATE_RESOURCE = "ALLOCATE_RESOURCE"
    ESCALATE_RISK = "ESCALATE_RISK"
    CREATE_MITIGATION = "CREATE_MITIGATION"
    REQUEST_RESOURCE = "REQUEST_RESOURCE"
    REASSIGN_WORK = "REASSIGN_WORK"
    PAUSE_WORK = "PAUSE_WORK"
    RESUME_WORK = "RESUME_WORK"
    NO_ACTION = "NO_ACTION"


class Priority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class AgentDecision(BaseModel):
    """Structured decision produced by an LLM.

    This is the canonical shape of an agent decision. It is validated before
    entering the simulation, and the simulation engine (not the LLM) performs
    any state mutation.
    """

    action: ActionType
    reasoning: str = Field(..., min_length=1)
    confidence: float = Field(0.5, ge=0.0, le=1.0)
    target_agent_id: int | None = None
    title: str | None = None
    description: str | None = None
    priority: Priority | None = None
    task_id: int | None = None
    goal_id: int | None = None
    project_id: int | None = None
    milestone_id: int | None = None
    feature_id: int | None = None
    depends_on_id: int | None = None
    status: str | None = None
    progress: float | None = Field(None, ge=0.0, le=100.0)
    message: str | None = None
    # Phase 5 autonomy fields
    objective: str | None = None
    plan_id: int | None = None
    plan_steps: list[str] | None = None
    expectation_description: str | None = None
    target_day: int | None = None
    target_metric: str | None = None
    expected_value: float | None = None
    decision_evaluation: str | None = None
    subject: str | None = None
    # Phase 6 strategic fields
    price: float | None = None
    target_segment: str | None = None
    positioning: str | None = None
    campaign_name: str | None = None
    campaign_budget: float | None = None
    campaign_duration: int | None = None
    opportunity_name: str | None = None
    opportunity_value: float | None = None
    # Phase 7 cognition fields
    expected_outcome: str | None = None
    expected_by_day: int | None = None
    context_version: str = "phase7-v1"
    # Phase 9 workforce fields
    job_title: str | None = None
    job_role: str | None = None
    job_description: str | None = None
    required_skills: list[str] | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    capacity_required: float | None = None
    employee_id: int | None = None
    candidate_id: int | None = None
    candidate_name: str | None = None
    candidate_role: str | None = None
    candidate_skills: list[str] | None = None
    candidate_experience: float | None = None
    candidate_salary_expectation: float | None = None
    candidate_productivity_potential: float | None = None
    candidate_culture_fit: float | None = None
    candidate_reliability: float | None = None
    hiring_score: float | None = None
    new_manager_id: int | None = None
    new_role: str | None = None
    new_salary: float | None = None
    promotion_reason: str | None = None
    termination_reason: str | None = None
    # Phase 10 financial/capital fields
    funding_stage: str | None = None
    funding_amount_requested: float | None = None
    funding_valuation: float | None = None
    investor_id: int | None = None
    budget_amount: float | None = None
    budget_purpose: str | None = None
    budget_request_id: int | None = None
    # Phase 11 advanced operations fields
    objective_title: str | None = None
    objective_description: str | None = None
    objective_type: str | None = None
    objective_id: int | None = None
    objective_progress: float | None = None
    resource_type: str | None = None
    resource_amount: float | None = None
    risk_id: int | None = None
    incident_id: int | None = None
    mitigation_actions: str | None = None
    reassign_task_id: int | None = None
    reassign_to_agent_id: int | None = None
    pause_task_id: int | None = None
    resume_task_id: int | None = None
    priority_score: float | None = None


# Authority levels required for each action. Higher authority can perform
# actions reserved for senior roles. Authority values come from Agent.authority.
ACTION_AUTHORITY: dict[ActionType, int] = {
    ActionType.CREATE_GOAL: 8,
    ActionType.UPDATE_GOAL: 8,
    ActionType.CREATE_PROJECT: 6,
    ActionType.CREATE_MILESTONE: 6,
    ActionType.CREATE_FEATURE: 5,
    ActionType.CREATE_TASK: 1,
    ActionType.ASSIGN_TASK: 6,
    ActionType.UPDATE_TASK: 1,
    ActionType.COMPLETE_TASK: 1,
    ActionType.SEND_MESSAGE: 1,
    ActionType.CREATE_PLAN: 7,
    ActionType.UPDATE_PLAN: 7,
    ActionType.SET_PRICE: 8,
    ActionType.SET_TARGET_SEGMENT: 8,
    ActionType.UPDATE_POSITIONING: 7,
    ActionType.CREATE_CAMPAIGN: 6,
    ActionType.CREATE_SALES_OPPORTUNITY: 6,
    # Phase 9 workforce actions
    ActionType.CREATE_JOB_OPENING: 6,
    ActionType.REVIEW_CANDIDATE: 5,
    ActionType.MAKE_HIRING_DECISION: 8,
    ActionType.SET_EMPLOYEE_MANAGER: 6,
    ActionType.PROMOTE_EMPLOYEE: 8,
    ActionType.TERMINATE_EMPLOYEE: 8,
    # Phase 10 financial/capital actions
    ActionType.CREATE_FUNDING_ROUND: 8,
    ActionType.CONTACT_INVESTOR: 7,
    ActionType.ADVANCE_PIPELINE: 7,
    ActionType.MAKE_INVESTMENT_DECISION: 8,
    ActionType.REQUEST_BUDGET: 5,
    ActionType.APPROVE_BUDGET: 8,
    ActionType.REJECT_BUDGET: 8,
    # Phase 11 advanced autonomous operations
    ActionType.CREATE_OBJECTIVE: 8,
    ActionType.UPDATE_OBJECTIVE: 7,
    ActionType.SET_PRIORITY: 6,
    ActionType.ALLOCATE_RESOURCE: 7,
    ActionType.ESCALATE_RISK: 7,
    ActionType.CREATE_MITIGATION: 6,
    ActionType.REQUEST_RESOURCE: 5,
    ActionType.REASSIGN_WORK: 6,
    ActionType.PAUSE_WORK: 5,
    ActionType.RESUME_WORK: 5,
    ActionType.NO_ACTION: 0,
}


# Actions that a manager-only agent may perform. Engineers may only modify
# tasks they own (owner check happens in the validator).
MANAGER_ONLY_ACTIONS: set[ActionType] = {
    ActionType.CREATE_GOAL,
    ActionType.UPDATE_GOAL,
    ActionType.CREATE_PROJECT,
    ActionType.ASSIGN_TASK,
    ActionType.CREATE_PLAN,
    ActionType.UPDATE_PLAN,
    ActionType.SET_PRICE,
    ActionType.SET_TARGET_SEGMENT,
    ActionType.UPDATE_POSITIONING,
    ActionType.CREATE_CAMPAIGN,
    ActionType.CREATE_SALES_OPPORTUNITY,
    # Phase 9 workforce actions
    ActionType.CREATE_JOB_OPENING,
    ActionType.REVIEW_CANDIDATE,
    ActionType.MAKE_HIRING_DECISION,
    ActionType.SET_EMPLOYEE_MANAGER,
    ActionType.PROMOTE_EMPLOYEE,
    ActionType.TERMINATE_EMPLOYEE,
    # Phase 10 financial/capital actions
    ActionType.CREATE_FUNDING_ROUND,
    ActionType.CONTACT_INVESTOR,
    ActionType.ADVANCE_PIPELINE,
    ActionType.MAKE_INVESTMENT_DECISION,
    ActionType.APPROVE_BUDGET,
    ActionType.REJECT_BUDGET,
    # Phase 11 advanced operations
    ActionType.CREATE_OBJECTIVE,
    ActionType.UPDATE_OBJECTIVE,
    ActionType.SET_PRIORITY,
    ActionType.ALLOCATE_RESOURCE,
    ActionType.ESCALATE_RISK,
    ActionType.CREATE_MITIGATION,
    ActionType.REASSIGN_WORK,
    ActionType.PAUSE_WORK,
    ActionType.RESUME_WORK,
}
