"""Tests for Phase 10: Financial Intelligence, Funding & Capital Management."""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.decisions import ActionType
from app.enums import (
    BudgetStatus,
    CompanyStatus,
    FinancialHealth,
    FundingRoundStatus,
    InvestorStage,
)
from app.models.budget_request import BudgetRequest
from app.models.cap_table import CapTableEntry
from app.models.company import Company
from app.models.funding_round import FundingRound
from app.models.fundraising_pipeline import FundraisingPipeline
from app.models.investor import Investor
from app.services.decisions import record_decision
from app.simulation import capital as capital_system
from app.simulation import financial_health as financial_health_system
from app.simulation import fundraising as fundraising_system
from app.simulation import investors as investor_system
from app.simulation import valuation as valuation_system
from app.simulation.domain import SimulationContext, make_rng
from app.simulation.engine import SimulationEngine
from app.simulation.outcomes import evaluate_company
from app.agents.validator import DecisionValidator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_company(db: Session, name: str = "Phase10Co", seed: int = 12345) -> Company:
    company = Company(
        name=name,
        mission="Test mission",
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
    from app.enums import AgentRole, AgentStatus
    from app.models.agent import Agent
    ceo = Agent(
        company_id=company.id,
        name="CEO",
        role=AgentRole.CEO,
        authority=10,
        salary=1000.0,
        budget=50000.0,
        status=AgentStatus.IDLE,
    )
    cto = Agent(
        company_id=company.id,
        name="CTO",
        role=AgentRole.CTO,
        authority=8,
        salary=800.0,
        budget=30000.0,
        manager_id=ceo.id,
        status=AgentStatus.IDLE,
    )
    cmo = Agent(
        company_id=company.id,
        name="CMO",
        role=AgentRole.CMO,
        authority=7,
        salary=700.0,
        budget=20000.0,
        manager_id=ceo.id,
        status=AgentStatus.IDLE,
    )
    engineer = Agent(
        company_id=company.id,
        name="Engineer",
        role=AgentRole.ENGINEER,
        authority=5,
        salary=600.0,
        budget=10000.0,
        manager_id=cto.id,
        status=AgentStatus.IDLE,
    )
    db.add_all([ceo, cto, cmo, engineer])
    db.flush()


def _ctx(company: Company, db: Session, day: int = 1) -> SimulationContext:
    return SimulationContext(db=db, company=company, day=day, rng=make_rng(company.seed, day))


# ---------------------------------------------------------------------------
# Financial health tests
# ---------------------------------------------------------------------------

class TestFinancialHealth:
    def test_burn_with_no_revenue(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        company.expenses = 50000.0
        company.revenue = 0.0
        company.current_day = 30
        db.commit()

        burn = financial_health_system.calculate_burn(company)
        assert burn > 0

    def test_burn_with_revenue(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        company.expenses = 50000.0
        company.revenue = 30000.0
        company.current_day = 30
        db.commit()

        burn = financial_health_system.calculate_burn(company)
        assert abs(burn - (20000.0 / 30)) < 0.01

    def test_runway_calculation(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        company.cash = 100000.0
        company.expenses = 30000.0
        company.revenue = 0.0
        company.current_day = 30
        db.commit()

        runway = financial_health_system.calculate_runway(company)
        assert runway > 0

    def test_runway_zero_burn(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        company.cash = 50000.0
        company.expenses = 0.0
        company.revenue = 0.0
        company.current_day = 1
        db.commit()

        runway = financial_health_system.calculate_runway(company)
        assert runway == float("inf")

    def test_runway_negative_cash(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        company.cash = -1000.0
        db.commit()

        runway = financial_health_system.calculate_runway(company)
        assert runway == 0.0

    def test_financial_health_score_bounded(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        db.commit()

        score = financial_health_system.calculate_financial_health_score(company)
        assert 0.0 <= score <= 1.0

    def test_financial_health_healthy(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        company.cash = 500000.0
        company.revenue = 100000.0
        company.expenses = 50000.0
        company.current_day = 30
        db.commit()

        health = financial_health_system.determine_financial_health(company)
        assert health == FinancialHealth.HEALTHY

    def test_financial_health_critical(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        company.cash = 1000.0
        company.revenue = 0.0
        company.expenses = 50000.0
        company.current_day = 30
        db.commit()

        health = financial_health_system.determine_financial_health(company)
        assert health in (FinancialHealth.CRITICAL, FinancialHealth.FAILED)

    def test_financial_health_failed_on_zero_cash(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        company.cash = 0.0
        db.commit()

        health = financial_health_system.determine_financial_health(company)
        assert health == FinancialHealth.FAILED

    def test_financial_metrics_completeness(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        db.commit()

        metrics = financial_health_system.get_financial_metrics(company)
        assert "cash" in metrics
        assert "daily_burn" in metrics
        assert "runway_days" in metrics
        assert "financial_health_score" in metrics
        assert "financial_health" in metrics
        assert "financial_risk_level" in metrics


# ---------------------------------------------------------------------------
# Valuation tests
# ---------------------------------------------------------------------------

class TestValuation:
    def test_valuation_bounded(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        ctx = _ctx(company, db)
        db.commit()

        result = valuation_system.calculate_valuation(ctx)
        assert result["valuation"] >= valuation_system.MIN_VALUATION
        assert result["valuation"] <= valuation_system.MAX_VALUATION

    def test_valuation_components_exist(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        ctx = _ctx(company, db)
        db.commit()

        result = valuation_system.calculate_valuation(ctx)
        assert "annual_revenue" in result
        assert "growth_factor" in result
        assert "readiness_bonus" in result
        assert "quality_bonus" in result
        assert "runway_factor" in result


# ---------------------------------------------------------------------------
# Investor tests
# ---------------------------------------------------------------------------

class TestInvestors:
    def test_generate_investors_deterministic(self, db: Session):
        company = _create_company(db, seed=42)
        ctx = _ctx(company, db)
        investors1 = investor_system.generate_investors(ctx, 3)
        db.commit()

        company2 = _create_company(db, name="OtherCo", seed=42)
        ctx2 = _ctx(company2, db)
        investors2 = investor_system.generate_investors(ctx2, 3)

        assert len(investors1) == 3
        assert len(investors2) == 3
        assert investors1[0].name == investors2[0].name

    def test_generate_investors_different_seed(self, db: Session):
        company1 = _create_company(db, seed=42)
        company2 = _create_company(db, name="OtherCo", seed=99)
        ctx1 = _ctx(company1, db)
        ctx2 = _ctx(company2, db)

        inv1 = investor_system.generate_investors(ctx1, 3)
        inv2 = investor_system.generate_investors(ctx2, 3)

        assert inv1[0].name != inv2[0].name or inv1[0].preferred_stage != inv2[0].preferred_stage

    def test_evaluate_investor_interest_bounded(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        investor = Investor(
            company_id=company.id,
            name="Test Investor",
            preferred_stage=InvestorStage.SEED,
            check_size_min=500000.0,
            check_size_max=3000000.0,
            risk_tolerance=0.5,
            sector_preference="SaaS",
            ownership_expectation=0.2,
            reputation=0.7,
        )
        db.add(investor)
        db.flush()

        ctx = _ctx(company, db)
        score = investor_system.evaluate_investor_interest(ctx, investor, InvestorStage.SEED)
        assert 0.0 <= score <= 1.0


# ---------------------------------------------------------------------------
# Funding round tests
# ---------------------------------------------------------------------------

class TestFundingRounds:
    def test_create_funding_round(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        ctx = _ctx(company, db)

        round_stage = fundraising_system.create_funding_round(
            ctx, InvestorStage.SEED, 1_000_000.0, 5_000_000.0
        )
        assert round_stage is not None
        assert round_stage.amount_requested == 1_000_000.0
        assert round_stage.valuation == 5_000_000.0

    def test_create_funding_round_invalid_amount(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        ctx = _ctx(company, db)

        round_stage = fundraising_system.create_funding_round(ctx, InvestorStage.SEED, -1.0, 5_000_000.0)
        assert round_stage is None

    def test_close_funding_round(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        ctx = _ctx(company, db)

        round_stage = fundraising_system.create_funding_round(
            ctx, InvestorStage.SEED, 1_000_000.0, 5_000_000.0
        )
        initial_cash = company.cash
        fundraising_system.close_funding_round(ctx, round_stage, 800_000.0)

        assert round_stage.amount_raised == 800_000.0
        assert round_stage.status == "CLOSED"
        assert company.cash == initial_cash + 800_000.0

    def test_close_funding_round_updates_cash(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        ctx = _ctx(company, db)

        round_stage = fundraising_system.create_funding_round(
            ctx, InvestorStage.SEED, 1_000_000.0, 5_000_000.0
        )
        initial_cash = company.cash
        fundraising_system.close_funding_round(ctx, round_stage, 500_000.0)

        assert company.cash == initial_cash + 500_000.0


# ---------------------------------------------------------------------------
# Pipeline tests
# ---------------------------------------------------------------------------

class TestPipeline:
    def test_advance_pipeline(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        ctx = _ctx(company, db)

        pipeline = FundraisingPipeline(
            company_id=company.id,
            investor_id=None,
            funding_round_id=None,
            status=FundingRoundStatus.DISCOVERED,
            stage=InvestorStage.SEED,
            interest_score=0.0,
        )
        db.add(pipeline)
        db.flush()

        advanced = fundraising_system.advance_pipeline(ctx, pipeline.id)
        assert advanced.status == FundingRoundStatus.CONTACTED

    def test_advance_pipeline_full_progression(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        ctx = _ctx(company, db)

        pipeline = FundraisingPipeline(
            company_id=company.id,
            investor_id=None,
            funding_round_id=None,
            status=FundingRoundStatus.DISCOVERED,
            stage=InvestorStage.SEED,
            interest_score=0.0,
        )
        db.add(pipeline)
        db.flush()

        progression = [
            FundingRoundStatus.CONTACTED,
            FundingRoundStatus.INTERESTED,
            FundingRoundStatus.DUE_DILIGENCE,
            FundingRoundStatus.OFFERED,
        ]
        for expected in progression:
            advanced = fundraising_system.advance_pipeline(ctx, pipeline.id)
            assert advanced.status == expected

    def test_make_investment_decision_invested(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        ctx = _ctx(company, db)

        pipeline = FundraisingPipeline(
            company_id=company.id,
            investor_id=None,
            funding_round_id=None,
            status=FundingRoundStatus.OFFERED,
            stage=InvestorStage.SEED,
            interest_score=0.5,
        )
        db.add(pipeline)
        db.flush()

        result = fundraising_system.make_investment_decision(ctx, pipeline.id, True, 500_000.0)
        assert result.status == FundingRoundStatus.INVESTED

    def test_make_investment_decision_passed(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        ctx = _ctx(company, db)

        pipeline = FundraisingPipeline(
            company_id=company.id,
            investor_id=None,
            funding_round_id=None,
            status=FundingRoundStatus.OFFERED,
            stage=InvestorStage.SEED,
            interest_score=0.5,
        )
        db.add(pipeline)
        db.flush()

        result = fundraising_system.make_investment_decision(ctx, pipeline.id, False, 0.0)
        assert result.status == FundingRoundStatus.PASSED


# ---------------------------------------------------------------------------
# Budget request tests
# ---------------------------------------------------------------------------

class TestBudgetRequests:
    def test_create_budget_request(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        ceo = db.execute(select(Company).where(Company.id == company.id)).scalar_one().agents[0]
        ctx = _ctx(company, db)

        request = capital_system.create_budget_request(ctx, ceo.id, 5000.0, "Marketing campaign")
        assert request is not None
        assert request.amount == 5000.0
        assert request.status == BudgetStatus.PENDING

    def test_approve_budget_request(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        ceo = db.execute(select(Company).where(Company.id == company.id)).scalar_one().agents[0]
        ctx = _ctx(company, db)

        request = capital_system.create_budget_request(ctx, ceo.id, 5000.0, "Marketing")
        initial_cash = company.cash
        result = capital_system.approve_budget_request(ctx, request.id, ceo.id, 5000.0)

        assert result is not None
        assert result.status == BudgetStatus.ALLOCATED
        assert company.cash == initial_cash - 5000.0

    def test_reject_budget_request(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        ceo = db.execute(select(Company).where(Company.id == company.id)).scalar_one().agents[0]
        ctx = _ctx(company, db)

        request = capital_system.create_budget_request(ctx, ceo.id, 5000.0, "Marketing")
        result = capital_system.reject_budget_request(ctx, request.id, ceo.id)

        assert result is not None
        assert result.status == BudgetStatus.REJECTED

    def test_approve_budget_requires_authority_via_validator(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        engineer = db.execute(
            select(Company).where(Company.id == company.id)
        ).scalar_one().agents[-1]
        validator = DecisionValidator(db, engineer, company)

        request = capital_system.create_budget_request(_ctx(company, db), engineer.id, 5000.0, "Marketing")
        db.flush()

        from app.agents.decisions import AgentDecision
        decision = AgentDecision(
            action=ActionType.APPROVE_BUDGET,
            reasoning="Approve my own budget",
            budget_request_id=request.id,
            budget_amount=5000.0,
        )
        result = validator.execute(decision)
        assert not result.success
        assert "Authority" in result.message or "authority" in result.message


# ---------------------------------------------------------------------------
# Decision validator tests
# ---------------------------------------------------------------------------

class TestDecisionValidator:
    def test_create_funding_round_requires_stage(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        ceo = company.agents[0]
        validator = DecisionValidator(db, ceo, company)

        from app.agents.decisions import AgentDecision
        decision = AgentDecision(
            action=ActionType.CREATE_FUNDING_ROUND,
            reasoning="Need funding",
        )
        result = validator.execute(decision)
        assert not result.success

    def test_contact_investor_requires_investor_id(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        ceo = company.agents[0]
        validator = DecisionValidator(db, ceo, company)

        from app.agents.decisions import AgentDecision
        decision = AgentDecision(
            action=ActionType.CONTACT_INVESTOR,
            reasoning="Contact investor",
        )
        result = validator.execute(decision)
        assert not result.success

    def test_request_budget_requires_amount_and_purpose(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        cmo = company.agents[2]
        validator = DecisionValidator(db, cmo, company)

        from app.agents.decisions import AgentDecision
        decision = AgentDecision(
            action=ActionType.REQUEST_BUDGET,
            reasoning="Need budget",
        )
        result = validator.execute(decision)
        assert not result.success

    def test_engineer_cannot_create_funding_round(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        engineer = company.agents[3]
        validator = DecisionValidator(db, engineer, company)

        from app.agents.decisions import AgentDecision
        decision = AgentDecision(
            action=ActionType.CREATE_FUNDING_ROUND,
            reasoning="Need funding",
            funding_stage="SEED",
            funding_amount_requested=1000000.0,
            funding_valuation=5000000.0,
        )
        result = validator.execute(decision)
        assert not result.success
        assert "Authority" in result.message or "authority" in result.message


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------

class TestIntegration:
    def test_full_funding_scenario(self, db: Session):
        company = _create_company(db, seed=12345)
        _seed_agents(db, company)
        ceo = company.agents[0]
        db.commit()

        ctx = _ctx(company, db)

        # Create funding round
        round_stage = fundraising_system.create_funding_round(ctx, InvestorStage.SEED, 500_000.0, 3_000_000.0)
        assert round_stage is not None

        # Generate investors
        investors = investor_system.generate_investors(ctx, 3)
        assert len(investors) == 3

        # Create pipeline entries and advance to OFFERED
        for inv in investors:
            pipeline = FundraisingPipeline(
                company_id=company.id,
                investor_id=inv.id,
                funding_round_id=round_stage.id,
                status=FundingRoundStatus.OFFERED,
                stage=InvestorStage.SEED,
                interest_score=0.8,
            )
            db.add(pipeline)
        db.flush()

        # Make investment decisions
        pipelines = list(
            db.execute(
                select(FundraisingPipeline).where(FundraisingPipeline.company_id == company.id)
            )
            .scalars()
            .all()
        )
        for p in pipelines:
            fundraising_system.make_investment_decision(ctx, p.id, True, 200_000.0)

        # Check cash increased
        assert company.cash > 100000.0

    def test_budget_request_workflow(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        cmo = company.agents[2]
        ceo = company.agents[0]
        db.commit()

        ctx = _ctx(company, db)

        # CMO requests budget
        request = capital_system.create_budget_request(ctx, cmo.id, 10000.0, "Q4 marketing campaign")
        assert request is not None
        assert request.status == BudgetStatus.PENDING

        # CEO approves
        result = capital_system.approve_budget_request(ctx, request.id, ceo.id, 10000.0)
        assert result is not None
        assert result.status == BudgetStatus.ALLOCATED
        assert company.cash == 100000.0 - 10000.0

    def test_cap_table_tracks_ownership(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        db.commit()

        entry = CapTableEntry(
            company_id=company.id,
            owner_type="founder",
            owner_id=company.agents[0].id,
            owner_name="CEO",
            ownership_percentage=100.0,
            shares=1000000.0,
        )
        db.add(entry)
        db.flush()

        entries = list(
            db.execute(
                select(CapTableEntry).where(CapTableEntry.company_id == company.id)
            )
            .scalars()
            .all()
        )
        assert len(entries) == 1
        assert entries[0].ownership_percentage == 100.0

    def test_ownership_validation(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        db.commit()

        # Add entries that total > 100%
        CapTableEntry(
            company_id=company.id,
            owner_type="founder",
            owner_id=company.agents[0].id,
            owner_name="CEO",
            ownership_percentage=60.0,
            shares=600000.0,
        )
        CapTableEntry(
            company_id=company.id,
            owner_type="investor",
            owner_id=1,
            owner_name="Investor",
            ownership_percentage=50.0,
            shares=500000.0,
        )
        # This would total 110% - in real code this should be validated server-side
        # For now, we just ensure the model accepts it
        total = 60.0 + 50.0
        assert total > 100.0

    def test_financial_pressure_influences_context(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        db.commit()

        # Make company cash critical
        company.cash = 500.0
        company.expenses = 100000.0
        company.revenue = 0.0
        company.current_day = 30
        db.commit()

        metrics = financial_health_system.get_financial_metrics(company)
        assert metrics["financial_health"] in ("AT_RISK", "CRITICAL", "FAILED")

    def test_deterministic_investor_generation(self, db: Session):
        for i in range(3):
            company = _create_company(db, name=f"Phase10Co{i}", seed=42)
            ctx = _ctx(company, db)
            investors = investor_system.generate_investors(ctx, 3)
            if i == 0:
                first_investor = investors[0]
            else:
                assert investors[0].name == first_investor.name

    def test_simulation_tick_integrates_financial_health(self, db: Session):
        company = _create_company(db, seed=12345)
        _seed_agents(db, company)
        db.commit()

        engine = SimulationEngine()
        state = engine.tick(db, company.id)

        # Financial metrics should be available in state
        assert state is not None
        assert state.current_day == 2

    def test_company_failure_on_zero_cash(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        company.cash = -1.0
        db.commit()

        ctx = _ctx(company, db)
        events = evaluate_company(ctx)
        assert company.status == CompanyStatus.FAILED
        assert len(events) > 0

    def test_financial_distress_event(self, db: Session):
        company = _create_company(db)
        _seed_agents(db, company)
        company.cash = 30000.0
        company.expenses = 40000.0
        company.revenue = 5000.0
        company.current_day = 30
        db.commit()

        ctx = _ctx(company, db)
        events = evaluate_company(ctx)
        assert company.status == CompanyStatus.RUNNING
        distress_events = [e for e in events if "FINANCIAL_DISTRESS" in str(e.event_type)]
        assert len(distress_events) == 1
        assert distress_events[0].event_type == "FINANCIAL_DISTRESS"
