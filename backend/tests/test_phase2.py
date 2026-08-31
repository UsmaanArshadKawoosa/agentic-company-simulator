"""Tests for Phase 2 agent intelligence: structured decisions, validation,
role behavior, memory, and failure handling."""

import pytest
from sqlalchemy.orm import Session

from app.agents.context import AgentContext, build_context, CompanyView, OrganizationView
from app.agents.decisions import ActionType, AgentDecision, Priority
from app.agents.validator import DecisionValidator
from app.enums import AgentRole, CompanyStatus, GoalStatus, TaskStatus
from app.models.agent import Agent
from app.models.company import Company
from app.models.goal import Goal
from app.models.task import Task
from app.services.llm import MockLLMService, NoOpLLMService, build_decision_from_llm
from app.simulation.engine import SimulationEngine


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def engine():
    llm = MockLLMService(
        decisions={
            "CEO": {
                "action": "CREATE_GOAL",
                "reasoning": "MVP is the top priority.",
                "confidence": 0.9,
                "title": "Launch MVP",
                "description": "Build and launch the MVP within 14 days.",
                "priority": "HIGH",
            },
            "CTO": {
                "action": "CREATE_PROJECT",
                "reasoning": "Need an engineering project for the MVP.",
                "confidence": 0.85,
                "title": "Engineering MVP",
                "description": "Build the engineering MVP.",
            },
            "CMO": {
                "action": "CREATE_TASK",
                "reasoning": "Need customer research before launch.",
                "confidence": 0.8,
                "title": "Customer research",
                "description": "Research target customers.",
                "priority": "HIGH",
            },
            "ENGINEER": {
                "action": "NO_ACTION",
                "reasoning": "No tasks assigned yet.",
                "confidence": 0.5,
            },
        }
    )
    return SimulationEngine(llm=llm)


def _create_company_with_agents(db: Session, name: str = "Phase2Co") -> Company:
    from app.enums import AgentRole

    company = Company(name=name, mission="Build an AI support platform.", status=CompanyStatus.RUNNING)
    db.add(company)
    db.flush()

    ceo = Agent(company_id=company.id, name="CEO", role=AgentRole.CEO, authority=10)
    db.add(ceo)
    db.flush()
    cto = Agent(company_id=company.id, name="CTO", role=AgentRole.CTO, authority=8, manager_id=ceo.id)
    db.add(cto)
    db.flush()
    eng = Agent(company_id=company.id, name="Eng", role=AgentRole.ENGINEER, authority=5, manager_id=cto.id)
    db.add(eng)
    db.flush()
    cmo = Agent(company_id=company.id, name="CMO", role=AgentRole.CMO, authority=7, manager_id=ceo.id)
    db.add(cmo)
    db.commit()
    db.refresh(company)
    return company


# ---------------------------------------------------------------------------
# LLM service tests
# ---------------------------------------------------------------------------


class TestMockLLMService:
    def test_mock_returns_configured_decision(self):
        llm = MockLLMService(
            decisions={"CEO": {"action": "NO_ACTION", "reasoning": "testing", "confidence": 0.5}}
        )
        result = llm.structured_generate("prompt", role="CEO")
        assert result["action"] == "NO_ACTION"
        assert result["reasoning"] == "testing"

    def test_mock_default_for_unknown_role(self):
        llm = MockLLMService()
        result = llm.structured_generate("prompt", role="UNKNOWN")
        assert result["action"] == "NO_ACTION"

    def test_noop_returns_placeholder(self):
        llm = NoOpLLMService()
        result = llm.structured_generate("prompt")
        assert result["placeholder"] is True


class TestBuildDecisionFromLLM:
    def test_valid_dict_parses(self):
        raw = {"action": "CREATE_TASK", "reasoning": "need work", "confidence": 0.8}
        decision = build_decision_from_llm(raw)
        assert decision is not None
        assert decision.action == ActionType.CREATE_TASK

    def test_invalid_action_rejected(self):
        raw = {"action": "DROP_TABLE", "reasoning": "hack", "confidence": 0.9}
        assert build_decision_from_llm(raw) is None

    def test_missing_reasoning_rejected(self):
        raw = {"action": "NO_ACTION", "confidence": 0.5}
        assert build_decision_from_llm(raw) is None

    def test_non_dict_rejected(self):
        assert build_decision_from_llm("not a dict") is None
        assert build_decision_from_llm(None) is None


# ---------------------------------------------------------------------------
# Context tests
# ---------------------------------------------------------------------------


class TestAgentContext:
    def test_build_context_compact_shape(self, db: Session):
        from app.enums import AgentRole

        company = Company(name="CtxCo", mission="m", status=CompanyStatus.RUNNING, current_day=3, cash=50000.0)
        db.add(company)
        db.flush()
        agent = Agent(company_id=company.id, name="CEO", role=AgentRole.CEO, authority=10)
        db.add(agent)
        db.flush()

        ctx = build_context(
            company=company,
            agent=agent,
            goals=[],
            projects=[],
            tasks=[],
            milestones=[],
            features=[],
            recent_events=[],
            recent_decisions=[],
            recent_environmental_events=[],
            customer_active_count=0,
            customer_churned_count=0,
            customer_total_monthly_value=0.0,
            plans=[],
            messages=[],
            memories=[],
            expectations=[],
            adaptation_signals={"at_risk_expectations": [], "recently_missed": [], "plan_risks": []},
            segments=[],
            competitors=[],
            campaigns=[],
            sales_opportunities=[],
            strategy={"target_segment": "SMB", "price": 100.0, "positioning": "", "brand_strength": 0.1, "sales_effectiveness": 0.1, "market_share": 0.0, "product_market_fit": 0.0, "competitive_pressure": 0.0},
        )
        assert ctx.company.name == "CtxCo"
        assert ctx.company.current_day == 3
        assert ctx.organization.agent_id == agent.id
        assert ctx.organization.direct_report_ids == []

    def test_context_serializes_to_json(self, db: Session):
        from app.enums import AgentRole

        company = Company(name="JsonCo", mission="m", status=CompanyStatus.RUNNING)
        db.add(company)
        db.flush()
        agent = Agent(company_id=company.id, name="CEO", role=AgentRole.CEO, authority=10)
        db.add(agent)
        db.flush()
        ctx = build_context(
            company,
            agent,
            goals=[],
            projects=[],
            tasks=[],
            milestones=[],
            features=[],
            recent_events=[],
            recent_decisions=[],
            recent_environmental_events=[],
            customer_active_count=0,
            customer_churned_count=0,
            customer_total_monthly_value=0.0,
            plans=[],
            messages=[],
            memories=[],
            expectations=[],
            adaptation_signals={"at_risk_expectations": [], "recently_missed": [], "plan_risks": []},
            segments=[],
            competitors=[],
            campaigns=[],
            sales_opportunities=[],
            strategy={"target_segment": "SMB", "price": 100.0, "positioning": "", "brand_strength": 0.1, "sales_effectiveness": 0.1, "market_share": 0.0, "product_market_fit": 0.0, "competitive_pressure": 0.0},
        )
        data = ctx.model_dump()
        assert data["company"]["name"] == "JsonCo"


# ---------------------------------------------------------------------------
# Validator tests
# ---------------------------------------------------------------------------


class TestDecisionValidator:
    @pytest.fixture
    def setup(self, db: Session):
        from app.enums import AgentRole

        company = Company(name="ValCo", mission="m", status=CompanyStatus.RUNNING, current_day=2)
        db.add(company)
        db.flush()
        ceo = Agent(company_id=company.id, name="CEO", role=AgentRole.CEO, authority=10)
        db.add(ceo)
        db.flush()
        eng = Agent(company_id=company.id, name="Eng", role=AgentRole.ENGINEER, authority=5, manager_id=ceo.id)
        db.add(eng)
        db.flush()
        db.refresh(company)
        db.refresh(ceo)
        db.refresh(eng)
        return company, ceo, eng

    def test_create_goal_succeeds(self, db: Session, setup):
        company, ceo, _ = setup
        validator = DecisionValidator(db, ceo, company)
        decision = AgentDecision(
            action=ActionType.CREATE_GOAL,
            reasoning="Strategic priority.",
            confidence=0.9,
            title="Launch MVP",
            description="Launch within 14 days.",
            priority="HIGH",
        )
        result = validator.execute(decision)
        assert result.success is True
        assert "created" in result.message
        goals = db.query(Goal).filter(Goal.company_id == company.id).all()
        assert len(goals) == 1
        assert goals[0].title == "Launch MVP"

    def test_create_task_without_title_rejected(self, db: Session, setup):
        company, ceo, _ = setup
        validator = DecisionValidator(db, ceo, company)
        decision = AgentDecision(
            action=ActionType.CREATE_TASK,
            reasoning="Need work.",
            description="desc",
        )
        result = validator.execute(decision)
        assert result.success is False
        assert "title" in result.message.lower()

    def test_engineer_cannot_create_goal(self, db: Session, setup):
        company, _, eng = setup
        validator = DecisionValidator(db, eng, company)
        decision = AgentDecision(
            action=ActionType.CREATE_GOAL,
            reasoning="I want to set strategy.",
            title="My goal",
            description="desc",
        )
        result = validator.execute(decision)
        assert result.success is False
        assert "authority" in result.message.lower()

    def test_cross_company_task_assignee_rejected(self, db: Session, setup):
        from app.enums import AgentRole

        company, ceo, _ = setup
        # Foreign agent from another company.
        other_company = Company(name="OtherCo", mission="m", status=CompanyStatus.RUNNING)
        db.add(other_company)
        db.flush()
        foreign_agent = Agent(company_id=other_company.id, name="Foreign", role=AgentRole.ENGINEER, authority=5)
        db.add(foreign_agent)
        db.flush()

        # First create a valid task in the company.
        task = Task(company_id=company.id, title="T", description="d", created_by=ceo.id)
        db.add(task)
        db.flush()

        validator = DecisionValidator(db, ceo, company)
        decision = AgentDecision(
            action=ActionType.ASSIGN_TASK,
            reasoning="Assign to foreign agent.",
            task_id=task.id,
            target_agent_id=foreign_agent.id,
        )
        result = validator.execute(decision)
        assert result.success is False
        assert "belong" in result.message.lower()

    def test_complete_task_succeeds(self, db: Session, setup):
        company, ceo, eng = setup
        task = Task(company_id=company.id, title="Build thing", description="d", created_by=ceo.id, assigned_to=eng.id, status=TaskStatus.IN_PROGRESS)
        db.add(task)
        db.flush()

        validator = DecisionValidator(db, eng, company)
        decision = AgentDecision(action=ActionType.COMPLETE_TASK, reasoning="Done.", task_id=task.id)
        result = validator.execute(decision)
        assert result.success is True
        db.refresh(task)
        assert task.status == TaskStatus.COMPLETED
        assert task.progress == 100.0

    def test_complete_already_completed_task_rejected(self, db: Session, setup):
        company, ceo, eng = setup
        task = Task(company_id=company.id, title="Done thing", description="d", status=TaskStatus.COMPLETED, progress=100.0)
        db.add(task)
        db.flush()
        validator = DecisionValidator(db, eng, company)
        decision = AgentDecision(action=ActionType.COMPLETE_TASK, reasoning="Already done.", task_id=task.id)
        result = validator.execute(decision)
        assert result.success is False

    def test_no_action_succeeds_without_side_effects(self, db: Session, setup):
        company, ceo, _ = setup
        validator = DecisionValidator(db, ceo, company)
        decision = AgentDecision(action=ActionType.NO_ACTION, reasoning="Nothing to do.")
        result = validator.execute(decision)
        assert result.success is True
        assert result.decision is not None

    def test_rejected_decision_persisted(self, db: Session, setup):
        company, _, eng = setup
        validator = DecisionValidator(db, eng, company)
        decision = AgentDecision(action=ActionType.CREATE_GOAL, reasoning="Overstepping.", title="X", description="Y")
        result = validator.execute(decision)
        assert result.success is False
        assert result.decision is not None
        assert "REJECTED" in (result.decision.outcome or "")


# ---------------------------------------------------------------------------
# Simulation engine integration tests
# ---------------------------------------------------------------------------


class TestSimulationTick:
    def test_tick_invokes_agents_and_persists_decisions(self, db: Session, engine: SimulationEngine):
        company = _create_company_with_agents(db)
        state = engine.tick(db, company.id)
        assert state.current_day == 2

        # Decisions should have been persisted.
        from app.models.decision import Decision
        decisions = db.query(Decision).filter(Decision.company_id == company.id).all()
        assert len(decisions) >= 4  # one per agent

    def test_tick_creates_goal_from_ceo(self, db: Session, engine: SimulationEngine):
        company = _create_company_with_agents(db)
        engine.tick(db, company.id)
        goals = db.query(Goal).filter(Goal.company_id == company.id).all()
        assert len(goals) >= 1
        assert any(g.title == "Launch MVP" for g in goals)

    def test_tick_creates_project_from_cto(self, db: Session, engine: SimulationEngine):
        company = _create_company_with_agents(db)
        engine.tick(db, company.id)
        from app.models.project import Project
        projects = db.query(Project).filter(Project.company_id == company.id).all()
        assert len(projects) >= 1

    def test_tick_creates_task_from_cmo(self, db: Session, engine: SimulationEngine):
        company = _create_company_with_agents(db)
        engine.tick(db, company.id)
        tasks = db.query(Task).filter(Task.company_id == company.id).all()
        assert len(tasks) >= 1
        assert any(t.title == "Customer research" for t in tasks)

    def test_tick_persists_memories(self, db: Session, engine: SimulationEngine):
        company = _create_company_with_agents(db)
        engine.tick(db, company.id)
        from app.models.memory import Memory
        memories = db.query(Memory).all()
        assert len(memories) >= 1

    def test_one_agent_failure_does_not_kill_tick(self, db: Session):
        company = _create_company_with_agents(db)

        # Engine with a broken LLM that raises.
        class BrokenLLM(MockLLMService):
            def structured_generate(self, prompt, schema=None, **kwargs):
                if kwargs.get("role") == "CEO":
                    raise RuntimeError("provider timeout")
                return super().structured_generate(prompt, schema, **kwargs)

        engine = SimulationEngine(
            llm=BrokenLLM(
                decisions={
                    "CTO": {"action": "NO_ACTION", "reasoning": "x", "confidence": 0.5},
                    "CMO": {"action": "NO_ACTION", "reasoning": "x", "confidence": 0.5},
                    "ENGINEER": {"action": "NO_ACTION", "reasoning": "x", "confidence": 0.5},
                }
            )
        )
        state = engine.tick(db, company.id)
        assert state.current_day == 2
        # CTO/CMO/ENGINEER still produced decisions despite CEO failure.
        from app.models.decision import Decision
        decisions = db.query(Decision).filter(Decision.company_id == company.id).all()
        assert len(decisions) >= 3

    def test_tick_advances_day_deterministically(self, db: Session, engine: SimulationEngine):
        company = _create_company_with_agents(db)
        s1 = engine.tick(db, company.id)
        s2 = engine.tick(db, company.id)
        assert s1.current_day == 2
        assert s2.current_day == 3
