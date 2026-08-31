"""Phase 10.5 Integration, Architecture & Reliability Audit tests."""

from __future__ import annotations

import math

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.decisions import ActionType, AgentDecision
from app.enums import (
    AgentRole,
    AgentStatus,
    CompanyStatus,
    CustomerStatus,
    EmployeeStatus,
    FinancialHealth,
    FundingRoundStatus,
    InvestorStage,
    TaskStatus,
    TaskType,
)
from app.models.agent import Agent
from app.models.company import Company
from app.models.customer import Customer
from app.models.employee import Employee
from app.models.fundraising_pipeline import FundraisingPipeline
from app.models.investor import Investor
from app.models.task import Task
from app.simulation import capital as capital_system
from app.simulation import financial_health as financial_health_system
from app.simulation import fundraising as fundraising_system
from app.simulation import investors as investor_system
from app.simulation.domain import SimulationContext, make_rng
from app.simulation.engine import SimulationEngine
from app.simulation.outcomes import evaluate_company
from app.agents.validator import DecisionValidator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_company(db: Session, name: str = "AuditCo", seed: int = 12345) -> Company:
    company = Company(
        name=name,
        mission="Audit mission",
        cash=100000.0,
        revenue=0.0,
        expenses=0.0,
        current_day=1,
        status=CompanyStatus.RUNNING,
        seed=seed,
    )
    db.add(company)
    db.flush()
    return company


def _seed_agents(db: Session, company: Company) -> None:
    agents = [
        Agent(
            company_id=company.id,
            name="CEO",
            role=AgentRole.CEO,
            authority=10,
            salary=1000.0,
            budget=50000.0,
            status=AgentStatus.IDLE,
        ),
        Agent(
            company_id=company.id,
            name="CTO",
            role=AgentRole.CTO,
            authority=8,
            salary=800.0,
            budget=30000.0,
            status=AgentStatus.IDLE,
        ),
        Agent(
            company_id=company.id,
            name="CMO",
            role=AgentRole.CMO,
            authority=7,
            salary=700.0,
            budget=20000.0,
            status=AgentStatus.IDLE,
        ),
        Agent(
            company_id=company.id,
            name="Engineer",
            role=AgentRole.ENGINEER,
            authority=5,
            salary=600.0,
            budget=10000.0,
            status=AgentStatus.IDLE,
        ),
    ]
    db.add_all(agents)
    db.flush()


def _ctx(company: Company, db: Session, day: int = 1) -> SimulationContext:
    return SimulationContext(db=db, company=company, day=day, rng=make_rng(company.seed, day))


# ---------------------------------------------------------------------------
# TestSimulationInvariants
# ---------------------------------------------------------------------------

class TestSimulationInvariants:
    def test_cash_never_nan(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        db.commit()

        engine = SimulationEngine()
        for _ in range(5):
            state = engine.tick(db, company.id)
            assert not math.isnan(state.company.cash), "cash became NaN"

    def test_runway_not_nan_or_infinite_when_burn_positive(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        company.expenses = 50000.0
        company.revenue = 0.0
        company.current_day = 30
        db.commit()

        metrics = financial_health_system.get_financial_metrics(company)
        if metrics["daily_burn"] > 0:
            assert metrics["runway_days"] is not None
            assert not math.isinf(metrics["runway_days"])
            assert not math.isnan(metrics["runway_days"])

    def test_product_readiness_bounded(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        db.commit()

        engine = SimulationEngine()
        for _ in range(10):
            state = engine.tick(db, company.id)
            assert 0.0 <= state.company.product_readiness <= 1.0

    def test_product_quality_bounded(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        db.commit()

        engine = SimulationEngine()
        for _ in range(10):
            state = engine.tick(db, company.id)
            assert 0.0 <= state.company.product_quality <= 1.0

    def test_technical_debt_bounded(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        db.commit()

        engine = SimulationEngine()
        for _ in range(10):
            state = engine.tick(db, company.id)
            assert 0.0 <= state.company.technical_debt <= 1.0

    def test_market_values_bounded(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        db.commit()

        engine = SimulationEngine()
        for _ in range(10):
            state = engine.tick(db, company.id)
            assert 0.0 <= state.company.market_demand <= 1.0
            assert 0.0 <= state.company.market_competition <= 1.0
            assert 0.0 <= state.company.market_sentiment <= 1.0

    def test_task_progress_bounded(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        db.commit()

        engine = SimulationEngine()
        for _ in range(5):
            state = engine.tick(db, company.id)
            for task in state.tasks:
                assert 0.0 <= task.progress <= 100.0

    def test_milestone_progress_bounded(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        db.commit()

        engine = SimulationEngine()
        for _ in range(5):
            state = engine.tick(db, company.id)
            for ms in state.milestones:
                assert 0.0 <= ms.progress <= 100.0

    def test_feature_progress_bounded(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        db.commit()

        engine = SimulationEngine()
        for _ in range(5):
            state = engine.tick(db, company.id)
            for f in state.features:
                assert 0.0 <= f.progress <= 100.0

    def test_employee_capacity_not_negative(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        db.commit()

        engine = SimulationEngine()
        for _ in range(5):
            state = engine.tick(db, company.id)
            for agent in state.agents:
                assert agent.capacity >= 0.0

    def test_terminated_employee_no_payroll(self, db: Session):
        from app.models.employee import Employee

        company = _create_company(db)
        _seed_agents(db, company)
        emp = Employee(
            company_id=company.id,
            name="TestEmp",
            role="ENGINEER",
            status=EmployeeStatus.ACTIVE,
            salary=3000.0,
            capacity=5.0,
            experience=2.0,
            performance_score=0.5,
            morale=0.5,
            productivity=0.5,
            onboarding_factor=1.0,
            hired_day=1,
        )
        db.add(emp)
        db.flush()
        db.commit()

        ctx = _ctx(company, db)
        from app.simulation import workforce as workforce_system
        workforce_system.terminate_employee(ctx, emp, "audit")

        payroll = workforce_system.total_payroll(ctx)
        assert payroll == 0.0

    def test_completed_task_not_executed(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        db.commit()

        task = Task(
            company_id=company.id,
            title="Completed task",
            status=TaskStatus.COMPLETED,
            progress=100.0,
            effort=10.0,
            remaining_effort=0.0,
            task_type=TaskType.ENGINEERING,
        )
        db.add(task)
        db.flush()

        from app.simulation import execution as execution_system
        ctx = _ctx(company, db)
        events = execution_system.execute_work(ctx)
        for ev in events:
            if hasattr(ev, 'meta') and ev.meta and ev.meta.get("task_id") == task.id:
                pytest.fail("Completed task was executed")

    def test_financial_metrics_numerically_valid(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        db.commit()

        engine = SimulationEngine()
        for _ in range(5):
            state = engine.tick(db, company.id)
            metrics = financial_health_system.get_financial_metrics(state.company)
            for key in ["cash", "revenue", "expenses", "profit", "daily_burn"]:
                assert not math.isnan(metrics[key])
                assert not math.isinf(metrics[key])
            if metrics["runway_days"] is not None:
                assert not math.isnan(metrics["runway_days"])
                assert not math.isinf(metrics["runway_days"])
            assert 0.0 <= metrics["financial_health_score"] <= 1.0


# ---------------------------------------------------------------------------
# TestDeterminism
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_multi_day_determinism(self, db: Session):
        from app.services.llm import MockLLMService

        llm = MockLLMService(decisions={
            "CEO": {"action": "NO_ACTION", "reasoning": "audit", "confidence": 0.5},
            "CTO": {"action": "NO_ACTION", "reasoning": "audit", "confidence": 0.5},
            "CMO": {"action": "NO_ACTION", "reasoning": "audit", "confidence": 0.5},
            "ENGINEER": {"action": "NO_ACTION", "reasoning": "audit", "confidence": 0.5},
        })

        company1 = _create_company(db, name="DetCo1", seed=12345)
        _seed_agents(db, company1)
        db.commit()

        engine = SimulationEngine(llm=llm)
        for _ in range(5):
            engine.tick(db, company1.id)

        snap1 = {
            "cash": company1.cash,
            "revenue": company1.revenue,
            "expenses": company1.expenses,
            "product_readiness": company1.product_readiness,
            "market_demand": company1.market_demand,
            "market_competition": company1.market_competition,
            "market_sentiment": company1.market_sentiment,
            "current_day": company1.current_day,
        }

        company2 = _create_company(db, name="DetCo2", seed=12345)
        _seed_agents(db, company2)
        db.commit()

        engine2 = SimulationEngine(llm=llm)
        for _ in range(5):
            engine2.tick(db, company2.id)

        snap2 = {
            "cash": company2.cash,
            "revenue": company2.revenue,
            "expenses": company2.expenses,
            "product_readiness": company2.product_readiness,
            "market_demand": company2.market_demand,
            "market_competition": company2.market_competition,
            "market_sentiment": company2.market_sentiment,
            "current_day": company2.current_day,
        }

        assert snap1 == snap2

    def test_financial_determinism(self, db: Session):
        company = _create_company(db, seed=42)
        _seed_agents(db, company)
        company.cash = 50000.0
        company.expenses = 10000.0
        company.revenue = 5000.0
        company.current_day = 30
        db.commit()

        m1 = financial_health_system.get_financial_metrics(company)

        company2 = _create_company(db, name="DetFin", seed=42)
        _seed_agents(db, company2)
        company2.cash = 50000.0
        company2.expenses = 10000.0
        company2.revenue = 5000.0
        company2.current_day = 30
        db.commit()

        m2 = financial_health_system.get_financial_metrics(company2)
        assert m1 == m2


# ---------------------------------------------------------------------------
# TestCompanyIsolation
# ---------------------------------------------------------------------------

class TestCompanyIsolation:
    def test_cross_company_agent_access_blocked(self, db: Session):
        company_a = _create_company(db, name="CoA")
        company_b = _create_company(db, name="CoB")
        _seed_agents(db, company_a)
        _seed_agents(db, company_b)
        db.commit()

        agent_a = company_a.agents[0]
        validator = DecisionValidator(db, agent_a, company_a)

        decision = AgentDecision(
            action=ActionType.CREATE_TASK,
            reasoning="cross-company",
            title="Evil task",
            description="should fail",
            target_agent_id=company_b.agents[0].id,
        )
        result = validator.execute(decision)
        assert not result.success
        assert "does not belong to the company" in result.message

    def test_cross_company_task_access_blocked(self, db: Session):
        company_a = _create_company(db, name="CoA")
        company_b = _create_company(db, name="CoB")
        _seed_agents(db, company_a)
        _seed_agents(db, company_b)
        db.commit()

        task = Task(
            company_id=company_b.id,
            title="CoB task",
            status=TaskStatus.TODO,
            progress=0.0,
            effort=10.0,
            remaining_effort=10.0,
            task_type=TaskStatus.TODO,
        )
        db.add(task)
        db.flush()

        agent_a = company_a.agents[0]
        validator = DecisionValidator(db, agent_a, company_a)

        decision = AgentDecision(
            action=ActionType.UPDATE_TASK,
            reasoning="cross-company",
            task_id=task.id,
            status="COMPLETED",
        )
        result = validator.execute(decision)
        assert not result.success
        assert "does not exist or belongs to another company" in result.message

    def test_cross_company_investor_access_blocked(self, db: Session):
        company_a = _create_company(db, name="CoA")
        company_b = _create_company(db, name="CoB")
        _seed_agents(db, company_a)
        _seed_agents(db, company_b)
        db.commit()

        investor = Investor(
            company_id=company_b.id,
            name="CoB Investor",
            preferred_stage=InvestorStage.SEED,
            check_size_min=100000.0,
            check_size_max=1000000.0,
            risk_tolerance=0.5,
            sector_preference="SaaS",
            ownership_expectation=0.2,
            reputation=0.7,
        )
        db.add(investor)
        db.flush()

        agent_a = company_a.agents[0]
        validator = DecisionValidator(db, agent_a, company_a)

        decision = AgentDecision(
            action=ActionType.CONTACT_INVESTOR,
            reasoning="cross-company",
            investor_id=investor.id,
        )
        result = validator.execute(decision)
        assert not result.success
        assert "does not exist or belongs to another company" in result.message


# ---------------------------------------------------------------------------
# TestDecisionSecurity
# ---------------------------------------------------------------------------

class TestDecisionSecurity:
    def test_malicious_strings_in_decisions(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        ceo = company.agents[0]
        validator = DecisionValidator(db, ceo, company)
        db.commit()

        malicious_inputs = [
            "'; DROP TABLE agents; --",
            "<script>alert('xss')</script>",
            "{{7*7}}",
            "../../etc/passwd",
            "\x00\x01\x02",
        ]
        for malicious in malicious_inputs:
            decision = AgentDecision(
                action=ActionType.CREATE_TASK,
                reasoning=malicious,
                title="Task",
                description="Desc",
            )
            result = validator.execute(decision)
            assert result.success or result.success is False
            assert "Internal error" not in result.message

    def test_negative_budget_rejected(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        ceo = company.agents[0]
        validator = DecisionValidator(db, ceo, company)

        decision = AgentDecision(
            action=ActionType.REQUEST_BUDGET,
            reasoning="negative",
            budget_amount=-1000.0,
            budget_purpose="test",
        )
        result = validator.execute(decision)
        assert not result.success

    def test_zero_funding_rejected(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        ceo = company.agents[0]
        validator = DecisionValidator(db, ceo, company)

        decision = AgentDecision(
            action=ActionType.CREATE_FUNDING_ROUND,
            reasoning="zero",
            funding_stage="SEED",
            funding_amount_requested=0.0,
            funding_valuation=1000000.0,
        )
        result = validator.execute(decision)
        assert not result.success

    def test_invalid_funding_stage_rejected(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        ceo = company.agents[0]
        validator = DecisionValidator(db, ceo, company)

        decision = AgentDecision(
            action=ActionType.CREATE_FUNDING_ROUND,
            reasoning="invalid",
            funding_stage="INVALID_STAGE",
            funding_amount_requested=1000000.0,
            funding_valuation=5000000.0,
        )
        result = validator.execute(decision)
        assert not result.success


# ---------------------------------------------------------------------------
# TestFinancialEdgeCases
# ---------------------------------------------------------------------------

class TestFinancialEdgeCases:
    def test_negative_cash_health_failed(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        company.cash = -100.0
        db.commit()

        health = financial_health_system.determine_financial_health(company)
        assert health == FinancialHealth.FAILED

    def test_zero_burn_infinite_runway(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        company.cash = 50000.0
        company.expenses = 0.0
        company.revenue = 0.0
        company.current_day = 1
        db.commit()

        runway = financial_health_system.calculate_runway(company)
        assert runway == float("inf")

    def test_huge_revenue_bounded(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        company.revenue = 1e9
        company.expenses = 1e6
        company.current_day = 30
        db.commit()

        metrics = financial_health_system.get_financial_metrics(company)
        assert not math.isnan(metrics["cash"])
        assert not math.isinf(metrics["cash"])

    def test_funding_round_equity_capped(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        ctx = _ctx(company, db)

        round_obj = fundraising_system.create_funding_round(ctx, InvestorStage.SEED, 1000000.0, 100000.0)
        fundraising_system.close_funding_round(ctx, round_obj, 1000000.0)

        assert round_obj.equity_sold <= 0.49

    def test_budget_approval_reduces_cash(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        ceo = company.agents[0]
        ctx = _ctx(company, db)

        request = capital_system.create_budget_request(ctx, ceo.id, 5000.0, "test")
        initial_cash = company.cash
        capital_system.approve_budget_request(ctx, request.id, ceo.id, 5000.0)

        assert company.cash == initial_cash - 5000.0

    def test_budget_approval_cannot_approve_more_than_requested(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        ceo = company.agents[0]
        ctx = _ctx(company, db)

        request = capital_system.create_budget_request(ctx, ceo.id, 5000.0, "test")
        result = capital_system.approve_budget_request(ctx, request.id, ceo.id, 10000.0)

        assert result.approved_amount == 5000.0

    def test_multiple_funding_rounds(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        ctx = _ctx(company, db)

        r1 = fundraising_system.create_funding_round(ctx, InvestorStage.SEED, 500000.0, 2000000.0)
        r2 = fundraising_system.create_funding_round(ctx, InvestorStage.SERIES_A, 2000000.0, 10000000.0)

        assert r1 is not None
        assert r2 is not None
        assert r1.id != r2.id
        assert r1.amount_requested == 500000.0
        assert r2.amount_requested == 2000000.0


# ---------------------------------------------------------------------------
# TestWebSocketLifecycle
# ---------------------------------------------------------------------------

class TestWebSocketLifecycle:
    def test_broadcast_does_not_crash_simulation(self, db: Session):
        from app.services.broadcaster import SyncBroadcaster

        company = _create_company(db)
        _seed_agents(db, company)
        db.commit()

        for _ in range(3):
            try:
                SyncBroadcaster.broadcast(company.id, {"type": "test", "day": 1})
            except Exception:
                pytest.fail("Broadcast should not raise")

    def test_realtime_manager_cleanup(self, db: Session):
        from app.services.realtime import Connection, ConnectionManager

        manager = ConnectionManager()
        conn = Connection(websocket=None, client_id="test-client")
        manager._connections["test-client"] = conn

        assert "test-client" in manager._connections
        manager._connections.pop("test-client", None)
        assert "test-client" not in manager._connections


# ---------------------------------------------------------------------------
# TestAPIRouting
# ---------------------------------------------------------------------------

class TestAPIRouting:
    def test_missing_company_returns_404(self, db: Session, client):
        from fastapi.testclient import TestClient
        response = client.get("/api/simulation/99999")
        assert response.status_code == 404

    def test_cross_company_simulation_access(self, db: Session, client):
        company_a = _create_company(db, name="API_CoA")
        _seed_agents(db, company_a)
        db.commit()

        company_b = _create_company(db, name="API_CoB")
        _seed_agents(db, company_b)
        db.commit()

        response = client.get(f"/api/simulation/{company_b.id}")
        assert response.status_code == 200
        assert response.json()["company_id"] == company_b.id
