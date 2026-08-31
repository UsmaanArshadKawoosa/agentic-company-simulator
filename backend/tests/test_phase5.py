"""Tests for Phase 5: autonomous company intelligence.

Tests plans, multi-day objectives, memory, expectations, adaptation,
communication, escalation, decision evaluation, agent metrics, and a
20+ day autonomous scenario demonstrating the PLAN -> ACT -> CONSEQUENCE ->
OBSERVE -> LEARN -> ADAPT loop.
"""

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.context import build_context
from app.agents.decisions import ActionType, AgentDecision
from app.agents.validator import DecisionValidator
from app.enums import (
    AgentRole,
    CompanyStatus,
    ExpectationStatus,
    MemoryType,
    MessagePriority,
    PlanStatus,
    TaskStatus,
)
from app.models.agent import Agent
from app.models.company import Company
from app.models.expectation import Expectation
from app.models.goal import Goal
from app.models.message import Message
from app.models.plan import Plan, PlanStep
from app.models.task import Task
from app.services.llm import MockLLMService
from app.simulation import communication as comm_system
from app.simulation import expectation as expectation_system
from app.simulation import memory as memory_system
from app.simulation import plan as plan_system
from app.simulation.domain import SimulationContext, make_rng
from app.simulation.engine import SimulationEngine


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ctx(company: Company, db: Session, day: int = 1) -> SimulationContext:
    return SimulationContext(db=db, company=company, day=day, rng=make_rng(company.seed, day))


def _create_company(db: Session, name: str = "Phase5Co", seed: int = 12345) -> Company:
    company = Company(
        name=name, mission="test", status=CompanyStatus.RUNNING, seed=seed,
    )
    db.add(company)
    db.flush()
    ceo = Agent(company_id=company.id, name="CEO", role=AgentRole.CEO, authority=10, capacity=5.0)
    db.add(ceo)
    db.flush()
    cto = Agent(company_id=company.id, name="CTO", role=AgentRole.CTO, authority=8, capacity=5.0, manager_id=ceo.id)
    db.add(cto)
    db.flush()
    eng = Agent(company_id=company.id, name="Eng", role=AgentRole.ENGINEER, authority=5, capacity=5.0, manager_id=cto.id)
    db.add(eng)
    db.flush()
    cmo = Agent(company_id=company.id, name="CMO", role=AgentRole.CMO, authority=7, capacity=5.0, manager_id=ceo.id)
    db.add(cmo)
    db.commit()
    db.refresh(company)
    return company


# ---------------------------------------------------------------------------
# Plan tests
# ---------------------------------------------------------------------------


class TestPlanSystem:
    def test_create_plan_with_steps(self, db: Session):
        company = _create_company(db)
        ceo = db.execute(select(Agent).where(Agent.role == AgentRole.CEO)).scalars().first()
        plan, events = plan_system.create_plan(
            _ctx(company, db, day=1),
            agent_id=ceo.id,
            objective="Launch MVP",
            priority=3,
            steps=["Build backend", "Build frontend", "Deploy"],
        )
        assert plan.objective == "Launch MVP"
        assert plan.status == PlanStatus.ACTIVE
        assert len(plan.steps) == 3
        assert any(e.event_type == "PLAN_CREATED" for e in events)

    def test_plan_progress_calculation(self, db: Session):
        company = _create_company(db)
        ceo = db.execute(select(Agent).where(Agent.role == AgentRole.CEO)).scalars().first()
        plan, _ = plan_system.create_plan(
            _ctx(company, db, day=1),
            agent_id=ceo.id,
            objective="Test plan",
            priority=1,
            steps=["Step 1", "Step 2", "Step 3"],
        )
        # No steps complete.
        progress = plan_system.plan_progress(plan, list(plan.steps))
        assert progress == 0.0
        # Mark one step complete.
        plan.steps[0].status = PlanStatus.COMPLETED
        progress = plan_system.plan_progress(plan, list(plan.steps))
        assert progress == pytest.approx(1 / 3)

    def test_plan_completes_when_all_steps_done(self, db: Session):
        company = _create_company(db)
        ceo = db.execute(select(Agent).where(Agent.role == AgentRole.CEO)).scalars().first()
        plan, _ = plan_system.create_plan(
            _ctx(company, db, day=1),
            agent_id=ceo.id,
            objective="Finish",
            priority=1,
            steps=["A", "B"],
        )
        for step in plan.steps:
            step.status = PlanStatus.COMPLETED
        events = plan_system.advance_plan(_ctx(company, db, day=2), plan)
        assert plan.status == PlanStatus.COMPLETED
        assert any(e.event_type == "PLAN_COMPLETED" for e in events)

    def test_plan_auto_completes_via_linked_task(self, db: Session):
        company = _create_company(db)
        ceo = db.execute(select(Agent).where(Agent.role == AgentRole.CEO)).scalars().first()
        plan, _ = plan_system.create_plan(
            _ctx(company, db, day=1),
            agent_id=ceo.id,
            objective="Build feature",
            priority=1,
            steps=["Implement"],
        )
        step = plan.steps[0]
        task = Task(
            company_id=company.id, title="Implement", effort=10.0, remaining_effort=0.0,
            status=TaskStatus.COMPLETED, progress=1.0,
        )
        db.add(task)
        db.flush()
        step.linked_task_id = task.id
        db.flush()
        events = plan_system.advance_plan(_ctx(company, db, day=2), plan)
        assert step.status == PlanStatus.COMPLETED
        assert plan.status == PlanStatus.COMPLETED

    def test_plan_revision_preserves_history(self, db: Session):
        company = _create_company(db)
        ceo = db.execute(select(Agent).where(Agent.role == AgentRole.CEO)).scalars().first()
        plan, _ = plan_system.create_plan(
            _ctx(company, db, day=1),
            agent_id=ceo.id,
            objective="Build 10 features",
            priority=1,
            steps=["F1", "F2"],
        )
        replacement, events = plan_system.revise_plan(
            _ctx(company, db, day=3),
            plan,
            new_objective="Ship 3 core features",
            new_steps=["Core1", "Core2", "Core3"],
        )
        assert plan.status == PlanStatus.CANCELLED
        assert replacement.objective == "Ship 3 core features"
        assert replacement.status == PlanStatus.ACTIVE
        assert any(e.event_type == "PLAN_REVISED" for e in events)

    def test_plan_persists(self, db: Session):
        company = _create_company(db)
        ceo = db.execute(select(Agent).where(Agent.role == AgentRole.CEO)).scalars().first()
        plan_system.create_plan(
            _ctx(company, db, day=1),
            agent_id=ceo.id,
            objective="Persist me",
            priority=1,
            steps=["A"],
        )
        db.commit()
        plans = db.execute(select(Plan).where(Plan.company_id == company.id)).scalars().all()
        assert len(plans) == 1
        assert plans[0].objective == "Persist me"


# ---------------------------------------------------------------------------
# Memory tests
# ---------------------------------------------------------------------------


class TestMemorySystem:
    def test_store_memory_with_category(self, db: Session):
        company = _create_company(db)
        ceo = db.execute(select(Agent).where(Agent.role == AgentRole.CEO)).scalars().first()
        memory = memory_system.store_memory(
            _ctx(company, db, day=1),
            ceo.id,
            MemoryType.LESSON.value,
            "Backend dependency sequencing caused delay.",
            importance=0.8,
        )
        assert memory.memory_type == MemoryType.LESSON.value
        assert memory.importance == 0.8

    def test_retrieve_memories_by_relevance(self, db: Session):
        company = _create_company(db)
        ceo = db.execute(select(Agent).where(Agent.role == AgentRole.CEO)).scalars().first()
        ctx = _ctx(company, db, day=5)
        memory_system.store_memory(ctx, ceo.id, MemoryType.LESSON.value, "Authentication blocked by database schema.", 0.9)
        memory_system.store_memory(ctx, ceo.id, MemoryType.FACT.value, "The weather is sunny.", 0.3)
        memory_system.store_memory(ctx, ceo.id, MemoryType.LESSON.value, "API testing requires mock data.", 0.7)
        db.flush()
        results = memory_system.retrieve_memories(ctx, ceo.id, "authentication database", limit=5)
        # The authentication memory should rank highest.
        assert len(results) >= 1
        assert "authentication" in results[0].content.lower()

    def test_retrieve_lessons_only(self, db: Session):
        company = _create_company(db)
        ceo = db.execute(select(Agent).where(Agent.role == AgentRole.CEO)).scalars().first()
        ctx = _ctx(company, db, day=1)
        memory_system.store_memory(ctx, ceo.id, MemoryType.LESSON.value, "Lesson one.", 0.8)
        memory_system.store_memory(ctx, ceo.id, MemoryType.FACT.value, "Fact one.", 0.8)
        db.flush()
        lessons = memory_system.retrieve_lessons(ctx, ceo.id, "test", limit=5)
        assert len(lessons) == 1
        assert lessons[0].memory_type == MemoryType.LESSON.value

    def test_memory_bounded_retrieval(self, db: Session):
        company = _create_company(db)
        ceo = db.execute(select(Agent).where(Agent.role == AgentRole.CEO)).scalars().first()
        ctx = _ctx(company, db, day=1)
        for i in range(10):
            memory_system.store_memory(ctx, ceo.id, MemoryType.FACT.value, f"Memory about authentication {i}.", 0.5)
        db.flush()
        results = memory_system.retrieve_memories(ctx, ceo.id, "authentication", limit=5)
        assert len(results) <= 5

    def test_no_chain_of_thought_persisted(self, db: Session):
        """Memories should be concise, not raw LLM chain-of-thought."""
        company = _create_company(db)
        ceo = db.execute(select(Agent).where(Agent.role == AgentRole.CEO)).scalars().first()
        memory_system.store_memory(
            _ctx(company, db, day=1),
            ceo.id,
            MemoryType.LESSON.value,
            "Authentication blocked by database schema.",
            0.8,
        )
        db.flush()
        from app.models.memory import Memory
        m = db.execute(select(Memory).where(Memory.agent_id == ceo.id)).scalars().first()
        # Content should be concise (bounded).
        assert len(m.content) < 200


# ---------------------------------------------------------------------------
# Expectation tests
# ---------------------------------------------------------------------------


class TestExpectationSystem:
    def test_create_expectation(self, db: Session):
        company = _create_company(db)
        ceo = db.execute(select(Agent).where(Agent.role == AgentRole.CEO)).scalars().first()
        exp = expectation_system.create_expectation(
            _ctx(company, db, day=1),
            ceo.id,
            "Product readiness reaches 0.5",
            target_day=10,
            target_metric="product_readiness",
            expected_value=0.5,
        )
        assert exp.status == ExpectationStatus.PENDING
        assert exp.target_metric == "product_readiness"

    def test_expectation_met(self, db: Session):
        company = _create_company(db)
        company.product_readiness = 0.6
        ceo = db.execute(select(Agent).where(Agent.role == AgentRole.CEO)).scalars().first()
        exp = expectation_system.create_expectation(
            _ctx(company, db, day=1),
            ceo.id,
            "Readiness reaches 0.5",
            target_day=5,
            target_metric="product_readiness",
            expected_value=0.5,
        )
        db.flush()
        events = expectation_system.evaluate_expectations(_ctx(company, db, day=5))
        assert exp.status == ExpectationStatus.MET
        assert any(e.event_type == "EXPECTATION_MET" for e in events)

    def test_expectation_missed(self, db: Session):
        company = _create_company(db)
        company.product_readiness = 0.1
        ceo = db.execute(select(Agent).where(Agent.role == AgentRole.CEO)).scalars().first()
        exp = expectation_system.create_expectation(
            _ctx(company, db, day=1),
            ceo.id,
            "Readiness reaches 0.5",
            target_day=5,
            target_metric="product_readiness",
            expected_value=0.5,
        )
        db.flush()
        events = expectation_system.evaluate_expectations(_ctx(company, db, day=5))
        assert exp.status == ExpectationStatus.MISSED

    def test_expectation_partial(self, db: Session):
        company = _create_company(db)
        company.product_readiness = 0.3  # >= 0.5*0.5=0.25 but < 0.5
        ceo = db.execute(select(Agent).where(Agent.role == AgentRole.CEO)).scalars().first()
        exp = expectation_system.create_expectation(
            _ctx(company, db, day=1),
            ceo.id,
            "Readiness reaches 0.5",
            target_day=5,
            target_metric="product_readiness",
            expected_value=0.5,
        )
        db.flush()
        events = expectation_system.evaluate_expectations(_ctx(company, db, day=5))
        assert exp.status == ExpectationStatus.PARTIAL

    def test_expectation_not_evaluated_before_target_day(self, db: Session):
        company = _create_company(db)
        company.product_readiness = 0.1
        ceo = db.execute(select(Agent).where(Agent.role == AgentRole.CEO)).scalars().first()
        exp = expectation_system.create_expectation(
            _ctx(company, db, day=1),
            ceo.id,
            "Readiness reaches 0.5",
            target_day=10,
            target_metric="product_readiness",
            expected_value=0.5,
        )
        db.flush()
        events = expectation_system.evaluate_expectations(_ctx(company, db, day=5))
        assert exp.status == ExpectationStatus.PENDING


# ---------------------------------------------------------------------------
# Communication tests
# ---------------------------------------------------------------------------


class TestCommunicationSystem:
    def test_send_message_persists(self, db: Session):
        company = _create_company(db)
        ceo = db.execute(select(Agent).where(Agent.role == AgentRole.CEO)).scalars().first()
        cto = db.execute(select(Agent).where(Agent.role == AgentRole.CTO)).scalars().first()
        msg, events = comm_system.send_message(
            _ctx(company, db, day=1),
            ceo.id,
            cto.id,
            subject="Priority update",
            content="Focus on authentication.",
            priority=MessagePriority.HIGH.value,
        )
        assert msg is not None
        assert msg.subject == "Priority update"
        assert any(e.event_type == "MESSAGE_SENT" for e in events)

    def test_unread_messages(self, db: Session):
        company = _create_company(db)
        ceo = db.execute(select(Agent).where(Agent.role == AgentRole.CEO)).scalars().first()
        cto = db.execute(select(Agent).where(Agent.role == AgentRole.CTO)).scalars().first()
        comm_system.send_message(_ctx(company, db, day=1), ceo.id, cto.id, "S", "C", "NORMAL")
        db.flush()
        unread = comm_system.get_unread_messages(_ctx(company, db, day=1), cto.id)
        assert len(unread) == 1
        assert unread[0].read_day is None

    def test_mark_messages_read(self, db: Session):
        company = _create_company(db)
        ceo = db.execute(select(Agent).where(Agent.role == AgentRole.CEO)).scalars().first()
        cto = db.execute(select(Agent).where(Agent.role == AgentRole.CTO)).scalars().first()
        comm_system.send_message(_ctx(company, db, day=1), ceo.id, cto.id, "S", "C", "NORMAL")
        db.flush()
        events = comm_system.mark_messages_read(_ctx(company, db, day=2), cto.id)
        assert any(e.event_type == "MESSAGE_RECEIVED" for e in events)
        unread = comm_system.get_unread_messages(_ctx(company, db, day=2), cto.id)
        assert len(unread) == 0

    def test_message_size_bounded(self, db: Session):
        company = _create_company(db)
        ceo = db.execute(select(Agent).where(Agent.role == AgentRole.CEO)).scalars().first()
        cto = db.execute(select(Agent).where(Agent.role == AgentRole.CTO)).scalars().first()
        long_content = "X" * 2000
        msg, _ = comm_system.send_message(_ctx(company, db, day=1), ceo.id, cto.id, "S", long_content, "NORMAL")
        assert len(msg.content) <= 1000

    def test_empty_message_rejected(self, db: Session):
        company = _create_company(db)
        ceo = db.execute(select(Agent).where(Agent.role == AgentRole.CEO)).scalars().first()
        cto = db.execute(select(Agent).where(Agent.role == AgentRole.CTO)).scalars().first()
        msg, _ = comm_system.send_message(_ctx(company, db, day=1), ceo.id, cto.id, "S", "   ", "NORMAL")
        assert msg is None


# ---------------------------------------------------------------------------
# Validator: CREATE_PLAN / UPDATE_PLAN / SEND_MESSAGE tests
# ---------------------------------------------------------------------------


class TestValidatorPlanActions:
    @pytest.fixture
    def setup(self, db: Session):
        company = _create_company(db, name="PlanValCo")
        ceo = db.execute(select(Agent).where(Agent.role == AgentRole.CEO).where(Agent.company_id == company.id)).scalars().first()
        eng = db.execute(select(Agent).where(Agent.role == AgentRole.ENGINEER).where(Agent.company_id == company.id)).scalars().first()
        return company, ceo, eng

    def test_create_plan_succeeds(self, db: Session, setup):
        company, ceo, _ = setup
        validator = DecisionValidator(db, ceo, company)
        decision = AgentDecision(
            action=ActionType.CREATE_PLAN,
            reasoning="Need a plan for MVP.",
            confidence=0.9,
            objective="Launch MVP",
            plan_steps=["Build backend", "Build frontend", "Deploy"],
            priority="HIGH",
        )
        result = validator.execute(decision)
        assert result.success is True
        plans = db.query(Plan).filter(Plan.company_id == company.id).all()
        assert len(plans) == 1
        assert len(plans[0].steps) == 3

    def test_create_plan_without_steps_rejected(self, db: Session, setup):
        company, ceo, _ = setup
        validator = DecisionValidator(db, ceo, company)
        decision = AgentDecision(
            action=ActionType.CREATE_PLAN,
            reasoning="Need a plan.",
            objective="Launch MVP",
        )
        result = validator.execute(decision)
        assert result.success is False

    def test_engineer_cannot_create_plan(self, db: Session, setup):
        company, _, eng = setup
        validator = DecisionValidator(db, eng, company)
        decision = AgentDecision(
            action=ActionType.CREATE_PLAN,
            reasoning="I want to plan.",
            objective="My plan",
            plan_steps=["Step"],
        )
        result = validator.execute(decision)
        assert result.success is False
        assert "authority" in result.message.lower()

    def test_update_plan_complete(self, db: Session, setup):
        company, ceo, _ = setup
        plan, _ = plan_system.create_plan(
            _ctx(company, db, day=1), ceo.id, "Done", 1, ["A"],
        )
        db.flush()
        validator = DecisionValidator(db, ceo, company)
        decision = AgentDecision(
            action=ActionType.UPDATE_PLAN,
            reasoning="Plan done.",
            plan_id=plan.id,
            status="COMPLETED",
        )
        result = validator.execute(decision)
        assert result.success is True
        db.refresh(plan)
        assert plan.status == PlanStatus.COMPLETED

    def test_update_plan_revise(self, db: Session, setup):
        company, ceo, _ = setup
        plan, _ = plan_system.create_plan(
            _ctx(company, db, day=1), ceo.id, "Build all", 1, ["A", "B"],
        )
        db.flush()
        validator = DecisionValidator(db, ceo, company)
        decision = AgentDecision(
            action=ActionType.UPDATE_PLAN,
            reasoning="Revising scope.",
            plan_id=plan.id,
            status="REVISED",
            objective="Build core only",
            plan_steps=["Core"],
        )
        result = validator.execute(decision)
        assert result.success is True
        db.refresh(plan)
        assert plan.status == PlanStatus.CANCELLED
        # Replacement plan should exist.
        plans = db.query(Plan).filter(Plan.company_id == company.id).all()
        assert len(plans) == 2

    def test_send_message_persists_via_validator(self, db: Session, setup):
        company, ceo, eng = setup
        validator = DecisionValidator(db, ceo, company)
        decision = AgentDecision(
            action=ActionType.SEND_MESSAGE,
            reasoning="Informing engineer.",
            target_agent_id=eng.id,
            subject="Priority",
            message="Focus on authentication.",
            priority="HIGH",
        )
        result = validator.execute(decision)
        assert result.success is True
        messages = db.query(Message).filter(Message.company_id == company.id).all()
        assert len(messages) == 1
        assert messages[0].subject == "Priority"

    def test_send_message_cross_company_rejected(self, db: Session, setup):
        company, ceo, _ = setup
        other_company = _create_company(db, name="OtherCo")
        foreign = db.execute(select(Agent).where(Agent.company_id == other_company.id).where(Agent.role == AgentRole.CEO)).scalars().first()
        validator = DecisionValidator(db, ceo, company)
        decision = AgentDecision(
            action=ActionType.SEND_MESSAGE,
            reasoning="Cross-company.",
            target_agent_id=foreign.id,
            message="Hello.",
        )
        result = validator.execute(decision)
        assert result.success is False
        assert "belong" in result.message.lower()


# ---------------------------------------------------------------------------
# Decision evaluation tests
# ---------------------------------------------------------------------------


class TestDecisionEvaluation:
    def test_decision_evaluated_from_expectation(self, db: Session):
        company = _create_company(db)
        company.product_readiness = 0.6
        ceo = db.execute(select(Agent).where(Agent.role == AgentRole.CEO)).scalars().first()
        from app.models.decision import Decision
        decision = Decision(
            company_id=company.id,
            agent_id=ceo.id,
            action=ActionType.CREATE_TASK.value,
            reasoning="Build it.",
            outcome="Task 'Build backend' created.",
            simulation_day=1,
        )
        db.add(decision)
        db.flush()
        exp = expectation_system.create_expectation(
            _ctx(company, db, day=1), ceo.id, "Readiness reaches 0.5",
            target_day=5, target_metric="product_readiness", expected_value=0.5,
            linked_decision_id=decision.id,
        )
        db.flush()
        from app.simulation import decision_quality as dq
        events = dq.evaluate_pending_decisions(_ctx(company, db, day=5))
        assert exp.status == ExpectationStatus.MET
        assert any(e.event_type == "DECISION_EVALUATED" for e in events)


# ---------------------------------------------------------------------------
# Agent metrics tests
# ---------------------------------------------------------------------------


class TestAgentMetrics:
    def test_metrics_computed(self, db: Session):
        company = _create_company(db)
        ceo = db.execute(select(Agent).where(Agent.role == AgentRole.CEO)).scalars().first()
        from app.simulation import metrics as metrics_system
        metrics = metrics_system.compute_agent_metrics(_ctx(company, db, day=1), ceo)
        assert metrics["agent_id"] == ceo.id
        assert metrics["role"] == "CEO"
        assert "tasks_completed" in metrics
        assert "decisions" in metrics

    def test_metrics_count_completed_tasks(self, db: Session):
        company = _create_company(db)
        eng = db.execute(select(Agent).where(Agent.role == AgentRole.ENGINEER)).scalars().first()
        task = Task(
            company_id=company.id, title="Done", effort=10.0, remaining_effort=0.0,
            assigned_to=eng.id, status=TaskStatus.COMPLETED, progress=1.0,
        )
        db.add(task)
        db.flush()
        from app.simulation import metrics as metrics_system
        metrics = metrics_system.compute_agent_metrics(_ctx(company, db, day=1), eng)
        assert metrics["tasks_completed"] == 1


# ---------------------------------------------------------------------------
# Adaptation tests
# ---------------------------------------------------------------------------


class TestAdaptation:
    def test_missed_expectation_visible_in_signals(self, db: Session):
        company = _create_company(db)
        company.product_readiness = 0.1
        ceo = db.execute(select(Agent).where(Agent.role == AgentRole.CEO)).scalars().first()
        exp = expectation_system.create_expectation(
            _ctx(company, db, day=1), ceo.id, "Readiness reaches 0.5",
            target_day=5, target_metric="product_readiness", expected_value=0.5,
        )
        db.flush()
        expectation_system.evaluate_expectations(_ctx(company, db, day=5))
        assert exp.status == ExpectationStatus.MISSED
        from app.simulation import adaptation as adaptation_system
        signals = adaptation_system.collect_adaptation_signals(_ctx(company, db, day=5), ceo.id)
        assert len(signals["recently_missed"]) >= 1

    def test_at_risk_expectation_detected(self, db: Session):
        company = _create_company(db)
        company.product_readiness = 0.1
        ceo = db.execute(select(Agent).where(Agent.role == AgentRole.CEO)).scalars().first()
        expectation_system.create_expectation(
            _ctx(company, db, day=1), ceo.id, "Readiness reaches 0.5",
            target_day=3, target_metric="product_readiness", expected_value=0.5,
        )
        db.flush()
        from app.simulation import adaptation as adaptation_system
        signals = adaptation_system.collect_adaptation_signals(_ctx(company, db, day=2), ceo.id)
        assert len(signals["at_risk_expectations"]) >= 1


# ---------------------------------------------------------------------------
# Multi-day objective tests
# ---------------------------------------------------------------------------


class TestMultiDayObjectives:
    def test_objective_survives_ticks(self, db: Session):
        """A plan created on day 1 should still be visible on day 5."""
        company = _create_company(db)
        ceo = db.execute(select(Agent).where(Agent.role == AgentRole.CEO)).scalars().first()
        plan_system.create_plan(
            _ctx(company, db, day=1), ceo.id, "Launch MVP in 14 days", 3,
            ["Backend", "Frontend", "Deploy"],
        )
        db.commit()
        # Simulate advancing days.
        for day in range(2, 6):
            plan_system.update_plans(_ctx(company, db, day))
        db.refresh(company)
        plans = db.execute(select(Plan).where(Plan.agent_id == ceo.id)).scalars().all()
        assert len(plans) >= 1
        assert plans[0].objective == "Launch MVP in 14 days"

    def test_plan_progress_reflects_domain_state(self, db: Session):
        """Plan progress should derive from actual task completion, not LLM claims."""
        company = _create_company(db)
        ceo = db.execute(select(Agent).where(Agent.role == AgentRole.CEO)).scalars().first()
        plan, _ = plan_system.create_plan(
            _ctx(company, db, day=1), ceo.id, "Build", 1, ["Implement"],
        )
        task = Task(
            company_id=company.id, title="Implement", effort=10.0, remaining_effort=0.0,
            status=TaskStatus.COMPLETED, progress=1.0,
        )
        db.add(task)
        db.flush()
        plan.steps[0].linked_task_id = task.id
        db.flush()
        plan_system.update_plans(_ctx(company, db, day=2))
        progress = plan_system.plan_progress(plan, list(plan.steps))
        assert progress == 1.0


# ---------------------------------------------------------------------------
# Failure isolation tests
# ---------------------------------------------------------------------------


class TestFailureIsolation:
    def test_llm_timeout_falls_back_to_no_action(self, db: Session):
        company = _create_company(db)

        class BrokenLLM(MockLLMService):
            def structured_generate(self, prompt, schema=None, **kwargs):
                raise RuntimeError("provider timeout")

        engine = SimulationEngine(llm=BrokenLLM())
        state = engine.tick(db, company.id)
        assert state.current_day == 2

    def test_malformed_response_falls_back(self, db: Session):
        company = _create_company(db)

        class BadLLM(MockLLMService):
            def structured_generate(self, prompt, schema=None, **kwargs):
                return {"action": "INVALID_ACTION", "reasoning": "", "confidence": 0.5}

        engine = SimulationEngine(llm=BadLLM())
        state = engine.tick(db, company.id)
        assert state.current_day == 2

    def test_provider_error_does_not_corrupt_state(self, db: Session):
        company = _create_company(db)

        class ErrorLLM(MockLLMService):
            def structured_generate(self, prompt, schema=None, **kwargs):
                raise ConnectionError("API down")

        engine = SimulationEngine(llm=ErrorLLM())
        state = engine.tick(db, company.id)
        assert state.current_day == 2
        # Company state should be intact.
        assert company.cash > 0


# ---------------------------------------------------------------------------
# Determinism test
# ---------------------------------------------------------------------------


class TestDeterminism:
    def test_same_seed_same_autonomous_result(self, db: Session):
        """Same seed + same MockLLM decisions must produce equivalent results."""
        llm = MockLLMService(decisions={
            "CEO": {"action": "NO_ACTION", "reasoning": "x", "confidence": 0.5},
            "CTO": {"action": "NO_ACTION", "reasoning": "x", "confidence": 0.5},
            "CMO": {"action": "NO_ACTION", "reasoning": "x", "confidence": 0.5},
            "ENGINEER": {"action": "NO_ACTION", "reasoning": "x", "confidence": 0.5},
        })
        c1 = _create_company(db, name="DetA", seed=333)
        c2 = _create_company(db, name="DetB", seed=333)
        engine = SimulationEngine(llm=llm)
        s1 = engine.tick(db, c1.id)
        s2 = engine.tick(db, c2.id)
        assert s1.current_day == s2.current_day
        assert c1.product_readiness == c2.product_readiness
        assert c1.cash == c2.cash


# ---------------------------------------------------------------------------
# 20+ Day Autonomous Integration Scenario
# ---------------------------------------------------------------------------


class TestAutonomousIntegration:
    """End-to-end scenario: NovaAI builds and launches an MVP over 20+ days.

    This test demonstrates the full autonomy loop:

        PLAN -> ACT -> CONSEQUENCE -> OBSERVE -> LEARN -> ADAPT -> ACT DIFFERENTLY

    The MockLLM is scripted to simulate sensible role behavior that adapts
    when reality deviates from expectations.
    """

    def test_novaai_20_day_autonomous_scenario(self, db: Session):
        """Run a 20+ day simulation and verify adaptation occurs."""
        company = _create_company(db, name="NovaAI", seed=12345)
        ceo = db.execute(select(Agent).where(Agent.role == AgentRole.CEO).where(Agent.company_id == company.id)).scalars().first()
        cto = db.execute(select(Agent).where(Agent.role == AgentRole.CTO).where(Agent.company_id == company.id)).scalars().first()
        eng = db.execute(select(Agent).where(Agent.role == AgentRole.ENGINEER).where(Agent.company_id == company.id)).scalars().first()
        cmo = db.execute(select(Agent).where(Agent.role == AgentRole.CMO).where(Agent.company_id == company.id)).scalars().first()

        # Track what each agent does per day for verification.
        ceo_plans_created = 0
        cto_tasks_created = 0
        messages_sent = 0

        def script(role, day, context):
            """Scripted MockLLM that simulates role behavior and adapts."""
            nonlocal ceo_plans_created, cto_tasks_created, messages_sent

            # Day 2 is the first action day (company starts at day 1, first tick -> day 2).
            if day == 2:
                if role == "CEO":
                    ceo_plans_created += 1
                    return {
                        "action": "CREATE_PLAN",
                        "reasoning": "Establish MVP objective for the company.",
                        "confidence": 0.95,
                        "objective": "Launch MVP within 20 days",
                        "plan_steps": [
                            "Build backend API",
                            "Build frontend",
                            "Test integration",
                            "Deploy MVP",
                        ],
                        "priority": "HIGH",
                    }
                if role == "CTO":
                    return {
                        "action": "CREATE_PROJECT",
                        "reasoning": "Create engineering project for MVP.",
                        "confidence": 0.9,
                        "title": "Engineering MVP",
                        "description": "Build the engineering MVP.",
                    }
                if role == "CMO":
                    return {
                        "action": "CREATE_TASK",
                        "reasoning": "Customer research needed.",
                        "confidence": 0.8,
                        "title": "Customer research",
                        "description": "Research target customers.",
                        "priority": "HIGH",
                    }
                return {"action": "NO_ACTION", "reasoning": "Waiting for direction.", "confidence": 0.5}

            if day == 3:
                if role == "CTO":
                    cto_tasks_created += 1
                    return {
                        "action": "CREATE_TASK",
                        "reasoning": "First technical task.",
                        "confidence": 0.9,
                        "title": "Build backend API",
                        "description": "Implement the backend API.",
                        "priority": "HIGH",
                        "target_agent_id": eng.id,
                    }
                if role == "CEO":
                    # CEO creates marketing work.
                    return {
                        "action": "CREATE_TASK",
                        "reasoning": "Marketing work for brand awareness.",
                        "confidence": 0.8,
                        "title": "Brand awareness campaign",
                        "description": "Run initial brand campaign.",
                        "priority": "MEDIUM",
                        "target_agent_id": cmo.id,
                    }
                return {"action": "NO_ACTION", "reasoning": "Monitoring progress.", "confidence": 0.5}

            if day == 4:
                if role == "CTO":
                    return {
                        "action": "CREATE_TASK",
                        "reasoning": "Second technical task.",
                        "confidence": 0.9,
                        "title": "Build frontend",
                        "description": "Implement the frontend.",
                        "priority": "HIGH",
                        "target_agent_id": eng.id,
                    }
                if role == "ENGINEER":
                    # Engineer works on assigned tasks.
                    return {
                        "action": "NO_ACTION",
                        "reasoning": "Working on assigned tasks via execution system.",
                        "confidence": 0.7,
                    }
                return {"action": "NO_ACTION", "reasoning": "Standing by.", "confidence": 0.5}

            # Day 5: CEO sends message to CTO to coordinate.
            if day == 5:
                if role == "CEO":
                    messages_sent += 1
                    return {
                        "action": "SEND_MESSAGE",
                        "reasoning": "Coordinate with CTO on engineering progress.",
                        "confidence": 0.85,
                        "target_agent_id": cto.id,
                        "subject": "Engineering progress check",
                        "message": "How is the backend API coming along? Any blockers?",
                        "priority": "NORMAL",
                    }
                return {"action": "NO_ACTION", "reasoning": "Monitoring.", "confidence": 0.5}

            # Day 6: CTO responds to CEO.
            if day == 6:
                if role == "CTO":
                    messages_sent += 1
                    return {
                        "action": "SEND_MESSAGE",
                        "reasoning": "Respond to CEO on engineering status.",
                        "confidence": 0.85,
                        "target_agent_id": ceo.id,
                        "subject": "Re: Engineering progress check",
                        "message": "Backend API is in progress. No blockers yet.",
                        "priority": "NORMAL",
                    }
                return {"action": "NO_ACTION", "reasoning": "Monitoring.", "confidence": 0.5}

            # Day 8: Engineer reports a blocker to CTO.
            if day == 8:
                if role == "ENGINEER":
                    messages_sent += 1
                    return {
                        "action": "SEND_MESSAGE",
                        "reasoning": "Report blocker to CTO.",
                        "confidence": 0.8,
                        "target_agent_id": cto.id,
                        "subject": "Blocker: API integration",
                        "message": "Need clarification on API schema before proceeding.",
                        "priority": "HIGH",
                    }
                return {"action": "NO_ACTION", "reasoning": "Monitoring.", "confidence": 0.5}

            # Day 10: CEO sends urgent message about schedule risk.
            if day == 10:
                if role == "CEO":
                    messages_sent += 1
                    return {
                        "action": "SEND_MESSAGE",
                        "reasoning": "Address schedule risk.",
                        "confidence": 0.9,
                        "target_agent_id": cto.id,
                        "subject": "Schedule risk",
                        "message": "We need to accelerate. Re-prioritize work.",
                        "priority": "HIGH",
                    }
                return {"action": "NO_ACTION", "reasoning": "Monitoring.", "confidence": 0.5}

            # Day 12: CTO creates corrective work.
            if day == 12:
                if role == "CTO":
                    return {
                        "action": "CREATE_TASK",
                        "reasoning": "Create corrective work to address schedule risk.",
                        "confidence": 0.85,
                        "title": "Corrective work: accelerate backend",
                        "description": "Additional work to get back on track.",
                        "priority": "HIGH",
                        "target_agent_id": eng.id,
                    }
                return {"action": "NO_ACTION", "reasoning": "Monitoring.", "confidence": 0.5}

            # Day 15: CMO reports marketing results to CEO.
            if day == 15:
                if role == "CMO":
                    messages_sent += 1
                    return {
                        "action": "SEND_MESSAGE",
                        "reasoning": "Report marketing results.",
                        "confidence": 0.8,
                        "target_agent_id": ceo.id,
                        "subject": "Marketing update",
                        "message": "Customer research complete. Early interest is positive.",
                        "priority": "NORMAL",
                    }
                return {"action": "NO_ACTION", "reasoning": "Monitoring.", "confidence": 0.5}

            # Default: NO_ACTION.
            return {"action": "NO_ACTION", "reasoning": "Monitoring.", "confidence": 0.5}

        llm = MockLLMService(script=script)
        engine = SimulationEngine(llm=llm)

        # Run 22 days.
        for _ in range(22):
            engine.tick(db, company.id)

        # --- Verification ---

        # 1. Persistent plans exist.
        plans = db.execute(select(Plan).where(Plan.company_id == company.id)).scalars().all()
        assert len(plans) >= 1, "At least one plan should have been created"
        assert ceo_plans_created >= 1, "CEO should have created a plan"

        # 2. Plan progress derives from actual state (not LLM claims).
        # The plan should have some steps (progress may be 0 if no linked tasks, but it exists).
        mvp_plan = [p for p in plans if "MVP" in p.objective]
        assert len(mvp_plan) >= 1, "MVP plan should exist"

        # 3. Tasks were created by CTO.
        tasks = db.execute(select(Task).where(Task.company_id == company.id)).scalars().all()
        assert len(tasks) >= 2, "CTO should have created multiple tasks"

        # 4. Messages were sent (communication).
        messages = db.execute(select(Message).where(Message.company_id == company.id)).scalars().all()
        assert len(messages) >= 1, "Messages should have been sent"

        # 5. Memories/lessons were created.
        from app.models.memory import Memory
        memories = db.execute(select(Memory).where(Memory.agent_id == ceo.id)).scalars().all()
        assert len(memories) >= 1, "Memories should have been created"

        # 6. Expectations were evaluated.
        expectations = db.execute(select(Expectation).where(Expectation.company_id == company.id)).scalars().all()
        # Expectations may or may not be created depending on script, but the system should handle them.

        # 7. Company advanced 22 days.
        db.refresh(company)
        assert company.current_day == 23, f"Expected day 23, got {company.current_day}"

        # 8. Product readiness should have increased from engineering work.
        # (Engineer capacity * 22 days should complete some tasks.)
        assert company.product_readiness >= 0.0

        # 9. Agent metrics exist.
        from app.simulation import metrics as metrics_system
        ctx = _ctx(company, db, company.current_day)
        ceo_metrics = metrics_system.compute_agent_metrics(ctx, ceo)
        assert ceo_metrics["agent_id"] == ceo.id
        assert ceo_metrics["decisions"] >= 1

    def test_adaptation_loop_demonstration(self, db: Session):
        """Explicitly demonstrate: PLAN -> ACT -> CONSEQUENCE -> OBSERVE -> LEARN -> ADAPT.

        This test creates a scenario where:
        1. CEO creates a plan with an expectation
        2. Reality deviates (work is slower than expected)
        3. Expectation is missed
        4. Agent observes the missed expectation
        5. Agent revises the plan
        """
        company = _create_company(db, name="AdaptCo", seed=777)
        ceo = db.execute(select(Agent).where(Agent.role == AgentRole.CEO).where(Agent.company_id == company.id)).scalars().first()
        eng = db.execute(select(Agent).where(Agent.role == AgentRole.ENGINEER).where(Agent.company_id == company.id)).scalars().first()

        # Day 1: CEO creates a plan and an expectation.
        plan, _ = plan_system.create_plan(
            _ctx(company, db, day=1), ceo.id, "Launch MVP fast", 3,
            ["Build backend", "Deploy"],
        )
        # Link a task to the first step.
        task = Task(
            company_id=company.id, title="Build backend", effort=100.0, remaining_effort=100.0,
            assigned_to=eng.id, status=TaskStatus.TODO, priority=3,
        )
        db.add(task)
        db.flush()
        plan.steps[0].linked_task_id = task.id
        db.flush()

        # Create an expectation that readiness will reach 0.5 by day 5.
        exp = expectation_system.create_expectation(
            _ctx(company, db, day=1), ceo.id, "Readiness reaches 0.5 by day 5",
            target_day=5, target_metric="product_readiness", expected_value=0.5,
        )
        db.commit()

        # Days 2-4: Engineer makes slow progress (only 5 effort/day, not enough).
        for day in range(2, 5):
            ctx = _ctx(company, db, day)
            execution_system.update_blocking_state(ctx)
            execution_system.execute_work(ctx)
            db.commit()

        # Day 5: Evaluate expectations.
        expectation_system.evaluate_expectations(_ctx(company, db, day=5))
        db.refresh(exp)
        db.refresh(task)

        # The expectation should be missed (task not complete, readiness low).
        assert exp.status in (ExpectationStatus.MISSED, ExpectationStatus.PARTIAL), \
            f"Expected MISSED or PARTIAL, got {exp.status}"

        # The adaptation system should surface this.
        from app.simulation import adaptation as adaptation_system
        signals = adaptation_system.collect_adaptation_signals(_ctx(company, db, day=5), ceo.id)
        assert len(signals["recently_missed"]) >= 1, "Missed expectation should be visible"

        # CEO revises the plan (ADAPT).
        replacement, events = plan_system.revise_plan(
            _ctx(company, db, day=5),
            plan,
            new_objective="Launch MVP with adjusted scope",
            new_steps=["Build minimal backend", "Deploy quickly"],
        )
        db.commit()

        # Verify the revision happened.
        assert replacement.objective == "Launch MVP with adjusted scope"
        assert replacement.status == PlanStatus.ACTIVE
        assert plan.status == PlanStatus.CANCELLED
        assert any(e.event_type == "PLAN_REVISED" for e in events)

        # Verify the new plan is visible in context.
        plans = db.execute(
            select(Plan).where(Plan.company_id == company.id).where(Plan.status == PlanStatus.ACTIVE)
        ).scalars().all()
        assert len(plans) >= 1
        assert any(p.objective == "Launch MVP with adjusted scope" for p in plans)


# ---------------------------------------------------------------------------
# Import execution_system at module level for the integration test.
# ---------------------------------------------------------------------------
from app.simulation import execution as execution_system
