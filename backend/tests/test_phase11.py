"""Phase 11: Advanced Autonomous Company Operations tests."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.orm import Session

from app.agents.decisions import ActionType, AgentDecision
from app.agents.validator import DecisionValidator
from app.enums import (
    AgentRole,
    IncidentStatus,
    IncidentType,
    ObjectiveStatus,
    ObjectiveType,
    ResourceType,
    RiskSeverity,
    RiskStatus,
    TaskStatus,
    TaskType,
)
from app.models.agent import Agent
from app.models.company import Company
from app.models.incident import Incident
from app.models.objective import Objective
from app.models.resource_allocation import ResourceAllocation
from app.models.risk import Risk
from app.models.task import Task
from app.simulation import attention as attention_system
from app.simulation import incident as incident_system
from app.simulation import objective as objective_system
from app.simulation import priority as priority_system
from app.simulation import resource as resource_system
from app.simulation import risk as risk_system
from app.simulation.domain import SimulationContext, make_rng
from app.simulation.engine import SimulationEngine
from app.simulation.state import SimulationState


@pytest.fixture
def db_session(db: Session):
    return db


@pytest.fixture
def company(db_session: Session):
    company = Company(
        name="Phase11TestCo",
        mission="Phase 11 testing",
        seed=42,
        cash=100000.0,
        current_day=1,
    )
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)
    return company


@pytest.fixture
def ctx(db_session: Session, company: Company):
    return SimulationContext(
        db=db_session,
        company=company,
        day=company.current_day,
        rng=make_rng(company.seed, company.current_day),
    )


# --- Objectives ---


class TestObjectives:
    def test_create_objective(self, ctx: SimulationContext):
        objective = objective_system.create_objective(
            ctx, title="Test Objective", description="Test desc", objective_type=ObjectiveType.STRATEGIC, priority=8
        )
        assert objective is not None
        assert objective.title == "Test Objective"
        assert objective.status == ObjectiveStatus.TODO
        assert objective.priority == 8
        assert objective.created_day == ctx.day

    def test_create_objective_empty_title(self, ctx: SimulationContext):
        objective = objective_system.create_objective(ctx, title="")
        assert objective is None

    def test_update_objective_progress(self, ctx: SimulationContext):
        objective = objective_system.create_objective(ctx, title="Test")
        objective_system.update_objective_progress(ctx, objective.id, 50.0)
        ctx.db.refresh(objective)
        assert objective.progress == 50.0
        assert objective.status == ObjectiveStatus.IN_PROGRESS

    def test_update_objective_completes(self, ctx: SimulationContext):
        objective = objective_system.create_objective(ctx, title="Test")
        objective_system.update_objective_progress(ctx, objective.id, 100.0)
        ctx.db.refresh(objective)
        assert objective.status == ObjectiveStatus.ACHIEVED
        assert objective.completed_day == ctx.day

    def test_get_active_objectives(self, ctx: SimulationContext):
        objective_system.create_objective(ctx, title="Obj1")
        objective_system.create_objective(ctx, title="Obj2")
        active = objective_system.get_active_objectives(ctx)
        assert len(active) == 2


# --- Resources ---


class TestResources:
    def test_allocate_resource_cash(self, ctx: SimulationContext):
        allocation = resource_system.allocate_resource(
            ctx, ResourceType.CASH, 5000.0, purpose="test"
        )
        assert allocation is not None
        assert allocation.allocated_amount == 5000.0

    def test_allocate_resource_insufficient(self, ctx: SimulationContext):
        allocation = resource_system.allocate_resource(
            ctx, ResourceType.CASH, 200000.0, purpose="test"
        )
        assert allocation is None

    def test_release_resource(self, ctx: SimulationContext):
        allocation = resource_system.allocate_resource(
            ctx, ResourceType.CASH, 1000.0, purpose="test"
        )
        assert allocation is not None
        released = resource_system.release_resource(ctx, allocation.id)
        assert released is not None
        assert released.allocated_amount == 0.0

    def test_get_resource_utilization(self, ctx: SimulationContext):
        resource_system.allocate_resource(ctx, ResourceType.CASH, 1000.0, purpose="test")
        util = resource_system.get_resource_utilization(ctx)
        assert "CASH" in util
        assert util["CASH"]["total_allocated"] == 1000.0

    def test_negative_resource_amount_rejected(self, ctx: SimulationContext):
        allocation = resource_system.allocate_resource(
            ctx, ResourceType.CASH, -1000.0, purpose="test"
        )
        assert allocation is None


# --- Risks ---


class TestRisks:
    def test_detect_low_cash_risk(self, ctx: SimulationContext):
        ctx.company.cash = 10000.0
        ctx.company.product_quality = 0.8
        risks = risk_system.detect_risks(ctx)
        assert len(risks) == 1
        assert risks[0].risk_type == "low_cash_runway"
        assert risks[0].severity == RiskSeverity.HIGH

    def test_detect_critical_cash_risk(self, ctx: SimulationContext):
        ctx.company.cash = 3000.0
        ctx.company.product_quality = 0.8
        risks = risk_system.detect_risks(ctx)
        assert len(risks) == 1
        assert risks[0].severity == RiskSeverity.CRITICAL

    def test_no_duplicate_risks(self, ctx: SimulationContext):
        ctx.company.cash = 10000.0
        risk_system.detect_risks(ctx)
        risks = risk_system.detect_risks(ctx)
        assert len(risks) == 0

    def test_escalate_risk(self, ctx: SimulationContext):
        ctx.company.cash = 10000.0
        risks = risk_system.detect_risks(ctx)
        risk = risks[0]
        result = risk_system.escalate_risk(ctx, risk.id)
        assert result is not None
        assert result.status == RiskStatus.ESCALATED

    def test_resolve_risk(self, ctx: SimulationContext):
        ctx.company.cash = 10000.0
        risks = risk_system.detect_risks(ctx)
        risk = risks[0]
        result = risk_system.resolve_risk(ctx, risk.id)
        assert result is not None
        assert result.status == RiskStatus.RESOLVED
        assert result.resolved_day == ctx.day


# --- Incidents ---


class TestIncidents:
    def test_detect_incidents_from_risks(self, ctx: SimulationContext):
        ctx.company.cash = 3000.0
        risks = risk_system.detect_risks(ctx)
        incidents = incident_system.detect_incidents_from_risks(ctx, risks)
        assert len(incidents) == 1
        assert incidents[0].incident_type == IncidentType.RUNWAY_CRISIS

    def test_resolve_incident(self, ctx: SimulationContext):
        ctx.company.cash = 3000.0
        risks = risk_system.detect_risks(ctx)
        incidents = incident_system.detect_incidents_from_risks(ctx, risks)
        incident_obj = incidents[0]
        result = incident_system.resolve_incident(ctx, incident_obj.id, root_cause="test")
        assert result is not None
        assert result.status == IncidentStatus.RESOLVED


# --- Priority & Scheduling ---


class TestPriorityScheduling:
    def test_compute_task_priority(self, db_session: Session, company: Company):
        task = Task(
            company_id=company.id,
            title="Test Task",
            status=TaskStatus.TODO,
            priority=5,
            progress=0.0,
            effort=10.0,
            remaining_effort=10.0,
            task_type=TaskType.ENGINEERING,
        )
        db_session.add(task)
        db_session.commit()

        ctx = SimulationContext(db=db_session, company=company, day=1, rng=make_rng(company.seed, 1))
        score = priority_system.compute_task_priority(task, ctx)
        assert score > 0

    def test_prioritized_tasks(self, db_session: Session, company: Company):
        for i in range(3):
            task = Task(
                company_id=company.id,
                title=f"Task {i}",
                status=TaskStatus.TODO,
                priority=i + 1,
                progress=0.0,
                effort=10.0,
                remaining_effort=10.0,
                task_type=TaskType.ENGINEERING,
            )
            db_session.add(task)
        db_session.commit()

        ctx = SimulationContext(db=db_session, company=company, day=1, rng=make_rng(company.seed, 1))
        tasks = priority_system.get_prioritized_tasks(ctx)
        assert len(tasks) == 3


# --- Management Attention ---


class TestManagementAttention:
    def test_compute_attention_no_overload(self, ctx: SimulationContext):
        attention = attention_system.compute_management_attention(ctx)
        assert attention["overloaded"] is False
        assert attention["active_objectives"] == 0

    def test_compute_attention_with_objectives(self, ctx: SimulationContext):
        objective_system.create_objective(ctx, title="Obj1")
        objective_system.create_objective(ctx, title="Obj2")
        attention = attention_system.compute_management_attention(ctx)
        assert attention["active_objectives"] == 2


# --- Decision Validator Phase 11 Actions ---


class TestDecisionValidatorPhase11:
    def test_create_objective_via_validator(self, db_session: Session, company: Company):
        agent = Agent(
            company_id=company.id,
            name="CEO",
            role=AgentRole.CEO,
            authority=8,
        )
        db_session.add(agent)
        db_session.commit()
        db_session.refresh(agent)

        decision = AgentDecision(
            action=ActionType.CREATE_OBJECTIVE,
            reasoning="Need to set strategic direction",
            objective_title="Strategic Growth",
            objective_type="STRATEGIC",
        )
        validator = DecisionValidator(db_session, agent, company)
        result = validator.execute(decision)
        assert result.success is True
        assert "Strategic Growth" in result.message

    def test_allocate_resource_via_validator(self, db_session: Session, company: Company):
        agent = Agent(
            company_id=company.id,
            name="CFO",
            role=AgentRole.CEO,
            authority=8,
        )
        db_session.add(agent)
        db_session.commit()
        db_session.refresh(agent)

        decision = AgentDecision(
            action=ActionType.ALLOCATE_RESOURCE,
            reasoning="Allocate cash for operations",
            resource_type="CASH",
            resource_amount=5000.0,
        )
        validator = DecisionValidator(db_session, agent, company)
        result = validator.execute(decision)
        assert result.success is True

    def test_escalate_risk_via_validator(self, db_session: Session, company: Company):
        agent = Agent(
            company_id=company.id,
            name="CTO",
            role=AgentRole.CEO,
            authority=8,
        )
        db_session.add(agent)
        db_session.commit()
        db_session.refresh(agent)

        risk = Risk(
            company_id=company.id,
            risk_type="test_risk",
            severity=RiskSeverity.HIGH,
            source="test",
            detected_day=1,
        )
        db_session.add(risk)
        db_session.commit()
        db_session.refresh(risk)

        decision = AgentDecision(
            action=ActionType.ESCALATE_RISK,
            reasoning="Risk needs escalation",
            risk_id=risk.id,
        )
        validator = DecisionValidator(db_session, agent, company)
        result = validator.execute(decision)
        assert result.success is True
        assert str(risk.id) in result.message


# --- Integration: 30-day autonomous scenario ---


class TestAutonomousScenario:
    def test_30_day_autonomous_scenario(self, db_session: Session, company: Company):
        engine = SimulationEngine()
        engine.start(db_session, company.id)

        for _ in range(30):
            state = engine.tick(db_session, company.id)
            assert state.current_day <= 31

        db_session.refresh(company)
        assert company.current_day == 31

        state = engine.get_state(db_session, company.id)
        assert hasattr(state, "objectives")
        assert hasattr(state, "risks")
        assert hasattr(state, "incidents")


# --- Determinism ---


class TestDeterminism:
    def test_phase11_determinism(self, db_session):
        state1 = _run_simulation(db_session, seed=12345, days=10)
        state2 = _run_simulation(db_session, seed=12345, days=10)

        assert state1.company.cash == state2.company.cash
        assert state1.company.product_readiness == state2.company.product_readiness
        assert len(state1.objectives) == len(state2.objectives)
        assert len(state1.risks) == len(state2.risks)
        assert len(state1.incidents) == len(state2.incidents)


def _run_simulation(db: Session, seed: int, days: int) -> SimulationState:
    company = Company(
        name=f"DetCo_{seed}_{uuid.uuid4().hex[:8]}",
        mission="det",
        seed=seed,
        cash=100000.0,
        current_day=1,
    )
    db.add(company)
    db.commit()
    db.refresh(company)

    agent = Agent(
        company_id=company.id,
        name="CEO",
        role=AgentRole.CEO,
        authority=8,
    )
    db.add(agent)
    db.commit()

    engine = SimulationEngine()
    engine.start(db, company.id)
    for _ in range(days):
        engine.tick(db, company.id)

    state = engine.get_state(db, company.id)
    return state


# --- Security ---


class TestSecurity:
    def test_cross_company_objective_rejected(self, db_session: Session, company: Company):
        other_company = Company(
            name="OtherCo",
            mission="other",
            seed=99999,
            cash=50000.0,
            current_day=1,
        )
        db_session.add(other_company)
        db_session.commit()
        db_session.refresh(other_company)

        other_ctx = SimulationContext(
            db=db_session,
            company=other_company,
            day=other_company.current_day,
            rng=make_rng(other_company.seed, other_company.current_day),
        )
        objective_system.create_objective(other_ctx, title="Other Objective")
        db_session.commit()

        ctx = SimulationContext(
            db=db_session,
            company=company,
            day=company.current_day,
            rng=make_rng(company.seed, company.current_day),
        )
        result = objective_system.get_active_objectives(ctx)
        assert len(result) == 0
