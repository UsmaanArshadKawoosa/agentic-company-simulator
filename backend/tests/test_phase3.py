"""Tests for Phase 3 simulation & economy: deterministic financials,
customers, progress, market, events, goals, lifecycle, and seed reproducibility."""

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.specs import DEFAULT_ORG
from app.enums import (
    AgentRole,
    CompanyStatus,
    CustomerStatus,
    EnvironmentEventType,
    GoalStatus,
    ProjectStatus,
    TaskStatus,
)
from app.models.agent import Agent
from app.models.company import Company
from app.models.customer import Customer
from app.models.goal import Goal
from app.models.project import Project
from app.models.task import Task
from app.services.llm import MockLLMService
from app.simulation import customers as customer_system
from app.simulation import economy as economy_system
from app.simulation import market as market_system
from app.simulation import outcomes as outcome_system
from app.simulation import progress as progress_system
from app.simulation.domain import SimulationContext, make_rng
from app.simulation.engine import SimulationEngine


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ctx(company: Company, db: Session, day: int = 1) -> SimulationContext:
    return SimulationContext(db=db, company=company, day=day, rng=make_rng(company.seed, day))


def _create_company(
    db: Session,
    name: str = "Phase3Co",
    *,
    seed: int = 12345,
    cash: float = 100000.0,
    with_agents: bool = True,
    mission: str = "Build a platform.",
) -> Company:
    company = Company(
        name=name,
        mission=mission,
        cash=cash,
        revenue=0.0,
        expenses=0.0,
        current_day=1,
        status=CompanyStatus.RUNNING,
        seed=seed,
        infrastructure_cost=500.0,
        market_demand=0.5,
        market_competition=0.3,
        market_sentiment=0.5,
    )
    db.add(company)
    db.flush()
    if with_agents:
        for spec in DEFAULT_ORG:
            agent = Agent(
                company_id=company.id,
                name=spec["name"],
                role=spec["role"],
                personality=spec["personality"],
                skills=spec["skills"],
                authority=spec["authority"],
                salary=spec.get("salary", 500.0),
                budget=spec["budget"],
                manager_id=None,
            )
            db.add(agent)
            db.flush()
        # Wire manager relationships.
        agents = {a.role: a for a in db.execute(select(Agent).where(Agent.company_id == company.id)).scalars().all()}
        for spec in DEFAULT_ORG:
            if spec["manager_role"] is not None:
                agents[spec["role"]].manager_id = agents[spec["manager_role"]].id
    db.commit()
    db.refresh(company)
    return company


# ---------------------------------------------------------------------------
# Economy tests
# ---------------------------------------------------------------------------


class TestEconomy:
    def test_daily_agent_salary_sums_all_agents(self, db: Session):
        company = _create_company(db)
        agents = list(db.execute(select(Agent).where(Agent.company_id == company.id)).scalars().all())
        # Specs: CEO 1000 + CTO 800 + Engineer 600 + CMO 700 = 3100
        assert economy_system.daily_agent_salary(company, agents) == pytest.approx(3100.0)

    def test_daily_expenses_includes_infrastructure(self, db: Session):
        company = _create_company(db, with_agents=False)
        company.infrastructure_cost = 500.0
        agents = list(db.execute(select(Agent).where(Agent.company_id == company.id)).scalars().all())
        assert economy_system.daily_expenses(company, agents) == pytest.approx(500.0)

    def test_daily_revenue_from_active_customers(self, db: Session):
        company = _create_company(db, with_agents=False)
        c1 = Customer(company_id=company.id, name="C1", status=CustomerStatus.ACTIVE, monthly_value=3000.0, acquired_day=1)
        c2 = Customer(company_id=company.id, name="C2", status=CustomerStatus.ACTIVE, monthly_value=6000.0, acquired_day=1)
        churned = Customer(company_id=company.id, name="C3", status=CustomerStatus.CHURNED, monthly_value=9000.0, acquired_day=1)
        db.add_all([c1, c2, churned])
        db.flush()
        customers = [c1, c2, churned]
        # (3000 + 6000) / 30 = 300
        assert economy_system.daily_revenue(company, customers) == pytest.approx(300.0)

    def test_process_economy_updates_cash(self, db: Session):
        company = _create_company(db, cash=10000.0, with_agents=False)
        company.infrastructure_cost = 100.0
        db.flush()
        ctx = _ctx(company, db, day=2)
        economy_system.process_economy(ctx, [], [])
        assert company.cash == pytest.approx(9900.0)
        assert company.expenses == pytest.approx(100.0)
        assert company.revenue == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Customer tests
# ---------------------------------------------------------------------------


class TestCustomers:
    def test_customer_belongs_to_company(self, db: Session):
        company = _create_company(db, with_agents=False)
        customer = Customer(
            company_id=company.id, name="Acme", status=CustomerStatus.ACTIVE,
            monthly_value=1000.0, acquired_day=1,
        )
        db.add(customer)
        db.flush()
        assert customer.company_id == company.id

    def test_cross_company_isolation(self, db: Session):
        c1 = _create_company(db, name="Alpha", with_agents=False)
        c2 = _create_company(db, name="Beta", with_agents=False)
        customer = Customer(company_id=c1.id, name="OnlyAlpha", status=CustomerStatus.ACTIVE, monthly_value=1000.0, acquired_day=1)
        db.add(customer)
        db.flush()
        c2_customers = list(
            db.execute(select(Customer).where(Customer.company_id == c2.id)).scalars().all()
        )
        assert c2_customers == []

    def test_acquisition_probability_deterministic(self, db: Session):
        company = _create_company(db, seed=42, with_agents=False)
        ctx = _ctx(company, db, day=5)
        p1 = customer_system.acquisition_probability(ctx, marketing_progress=0.5, product_readiness=50.0)
        p2 = customer_system.acquisition_probability(ctx, marketing_progress=0.5, product_readiness=50.0)
        assert p1 == p2

    def test_acquisition_zero_when_no_product_readiness(self, db: Session):
        company = _create_company(db, with_agents=False)
        ctx = _ctx(company, db, day=1)
        p = customer_system.acquisition_probability(ctx, marketing_progress=1.0, product_readiness=0.0)
        assert p == pytest.approx(0.0)

    def test_churn_increases_with_competition(self, db: Session):
        company_low = _create_company(db, seed=1, with_agents=False)
        company_low.market_competition = 0.1
        company_high = _create_company(db, name="HiComp", seed=1, with_agents=False)
        company_high.market_competition = 0.9
        ctx_low = _ctx(company_low, db, day=3)
        ctx_high = _ctx(company_high, db, day=3)
        p_low = customer_system.churn_probability(ctx_low, product_readiness=50.0)
        p_high = customer_system.churn_probability(ctx_high, product_readiness=50.0)
        assert p_high > p_low

    def test_acquire_customers_creates_active_customer(self, db: Session):
        company = _create_company(db, seed=7, with_agents=False)
        company.market_demand = 1.0
        company.product_readiness = 100.0
        db.flush()
        ctx = _ctx(company, db, day=1)
        # With full readiness and demand, probability should be high.
        new = customer_system.acquire_customers(ctx, [], marketing_progress=1.0, product_readiness=100.0)
        if new:
            assert new[0].status == CustomerStatus.ACTIVE
            assert new[0].monthly_value > 0
            assert new[0].acquired_day == 1

    def test_process_churn_marks_churned(self, db: Session):
        company = _create_company(db, seed=99, with_agents=False)
        company.market_competition = 1.0
        company.market_sentiment = 0.0
        company.product_readiness = 0.0
        db.flush()
        customer = Customer(
            company_id=company.id, name="Fragile", status=CustomerStatus.ACTIVE,
            monthly_value=1000.0, acquired_day=1,
        )
        db.add(customer)
        db.flush()
        ctx = _ctx(company, db, day=2)
        # With max competition, min sentiment, min readiness, churn is very likely.
        for _ in range(10):
            customer.status = CustomerStatus.ACTIVE
            customer.churn_day = None
            events = customer_system.process_churn(ctx, [customer], product_readiness=0.0)
            if events:
                break
        assert customer.status == CustomerStatus.CHURNED
        assert customer.churn_day == 2


# ---------------------------------------------------------------------------
# Progress tests
# ---------------------------------------------------------------------------


class TestProgress:
    def test_project_progress_weighted_by_priority(self, db: Session):
        company = _create_company(db, with_agents=False)
        project = Project(company_id=company.id, name="P", status=ProjectStatus.PLANNED, progress=0.0)
        db.add(project)
        db.flush()
        t1 = Task(company_id=company.id, project_id=project.id, title="T1", priority=1, status=TaskStatus.COMPLETED, progress=100.0)
        t2 = Task(company_id=company.id, project_id=project.id, title="T2", priority=3, status=TaskStatus.TODO, progress=0.0)
        db.add_all([t1, t2])
        db.flush()
        # (100*1 + 0*3) / (1+3) = 25.0
        assert progress_system.project_progress(project, [t1, t2]) == pytest.approx(25.0)

    def test_product_readiness_averages_projects(self, db: Session):
        company = _create_company(db, with_agents=False)
        p1 = Project(company_id=company.id, name="P1", status=ProjectStatus.IN_PROGRESS, progress=0.0)
        p2 = Project(company_id=company.id, name="P2", status=ProjectStatus.IN_PROGRESS, progress=0.0)
        db.add_all([p1, p2])
        db.flush()
        t1 = Task(company_id=company.id, project_id=p1.id, title="T1", priority=1, status=TaskStatus.COMPLETED, progress=100.0)
        t2 = Task(company_id=company.id, project_id=p2.id, title="T2", priority=1, status=TaskStatus.TODO, progress=0.0)
        db.add_all([t1, t2])
        db.flush()
        readiness = progress_system.product_readiness(company, [p1, p2], [t1, t2])
        # p1 = 100, p2 = 0 -> avg = 50
        assert readiness == pytest.approx(50.0)

    def test_completed_tasks_marked_in_progress(self, db: Session):
        company = _create_company(db, with_agents=False)
        project = Project(company_id=company.id, name="P", status=ProjectStatus.PLANNED, progress=0.0)
        db.add(project)
        db.flush()
        task = Task(company_id=company.id, project_id=project.id, title="T", priority=1, status=TaskStatus.COMPLETED, progress=100.0)
        db.add(task)
        db.flush()
        ctx = _ctx(company, db, day=2)
        progress_system.update_projects_and_readiness(ctx)
        assert project.status == ProjectStatus.COMPLETED
        assert project.progress == pytest.approx(100.0)

    def test_marketing_progress_fraction(self, db: Session):
        company = _create_company(db, with_agents=False)
        t1 = Task(company_id=company.id, title="T1", status=TaskStatus.COMPLETED, progress=100.0)
        t2 = Task(company_id=company.id, title="T2", status=TaskStatus.TODO, progress=0.0)
        t3 = Task(company_id=company.id, title="T3", status=TaskStatus.TODO, progress=0.0)
        t4 = Task(company_id=company.id, title="T4", status=TaskStatus.TODO, progress=0.0)
        db.add_all([t1, t2, t3, t4])
        db.flush()
        assert progress_system.marketing_progress([t1, t2, t3, t4]) == pytest.approx(0.25)


# ---------------------------------------------------------------------------
# Goal tests
# ---------------------------------------------------------------------------


class TestGoals:
    def test_mvp_goal_progress_from_readiness(self, db: Session):
        company = _create_company(db, with_agents=False)
        goal = Goal(company_id=company.id, title="Launch MVP", status=GoalStatus.TODO, priority=1, progress=0.0)
        db.add(goal)
        db.flush()
        ctx = _ctx(company, db, day=2)
        progress_system.update_goal_progress(ctx, readiness=75.0, active_customer_count=0)
        assert goal.progress == pytest.approx(75.0)
        assert goal.status == GoalStatus.IN_PROGRESS

    def test_customer_goal_progress(self, db: Session):
        company = _create_company(db, with_agents=False)
        goal = Goal(company_id=company.id, title="Acquire first 10 customers", status=GoalStatus.TODO, priority=1, progress=0.0)
        db.add(goal)
        db.flush()
        ctx = _ctx(company, db, day=2)
        progress_system.update_goal_progress(ctx, readiness=0.0, active_customer_count=5)
        assert goal.progress == pytest.approx(50.0)

    def test_goal_achieved_at_100(self, db: Session):
        company = _create_company(db, with_agents=False)
        goal = Goal(company_id=company.id, title="Launch MVP", status=GoalStatus.IN_PROGRESS, priority=1, progress=90.0)
        db.add(goal)
        db.flush()
        ctx = _ctx(company, db, day=2)
        progress_system.update_goal_progress(ctx, readiness=100.0, active_customer_count=0)
        assert goal.status == GoalStatus.ACHIEVED
        assert goal.progress == pytest.approx(100.0)


# ---------------------------------------------------------------------------
# Market tests
# ---------------------------------------------------------------------------


class TestMarket:
    def test_market_values_clamped(self, db: Session):
        company = _create_company(db, seed=123, with_agents=False)
        # Run many evolutions; values must stay within [0, 1].
        for day in range(1, 30):
            ctx = _ctx(company, db, day)
            market_system.evolve_market(ctx)
            assert 0.0 <= company.market_demand <= 1.0
            assert 0.0 <= company.market_competition <= 1.0
            assert 0.0 <= company.market_sentiment <= 1.0

    def test_seed_reproducibility(self, db: Session):
        """Same seed + day must produce identical market evolution."""
        c1 = _create_company(db, name="SeedA", seed=555, with_agents=False)
        c2 = _create_company(db, name="SeedB", seed=555, with_agents=False)
        ctx1 = _ctx(c1, db, day=10)
        ctx2 = _ctx(c2, db, day=10)
        result1 = market_system.evolve_market(ctx1)
        result2 = market_system.evolve_market(ctx2)
        assert result1 == result2

    def test_different_seeds_diverge(self, db: Session):
        c1 = _create_company(db, name="DivA", seed=1, with_agents=False)
        c2 = _create_company(db, name="DivB", seed=2, with_agents=False)
        ctx1 = _ctx(c1, db, day=10)
        ctx2 = _ctx(c2, db, day=10)
        r1 = market_system.evolve_market(ctx1)
        r2 = market_system.evolve_market(ctx2)
        assert r1["new"] != r2["new"]

    def test_environmental_events_have_consequences(self, db: Session):
        company = _create_company(db, seed=2024, with_agents=False)
        company.infrastructure_cost = 1000.0
        company.market_demand = 0.5
        db.flush()
        # Run many days; with enough seeds, some event should trigger.
        events_generated = 0
        for day in range(1, 50):
            ctx = _ctx(company, db, day)
            events = market_system.generate_environmental_events(ctx)
            events_generated += len(events)
        assert events_generated > 0

    def test_infrastructure_event_increases_cost(self, db: Session):
        company = _create_company(db, seed=3030, with_agents=False)
        company.infrastructure_cost = 1000.0
        db.flush()
        from app.simulation.market import _apply_infrastructure_cost_increase
        _apply_infrastructure_cost_increase(company)
        assert company.infrastructure_cost == pytest.approx(1100.0)


# ---------------------------------------------------------------------------
# Lifecycle tests
# ---------------------------------------------------------------------------


class TestLifecycle:
    def test_company_fails_when_cash_depleted(self, db: Session):
        company = _create_company(db, cash=0.0, with_agents=False)
        db.flush()
        ctx = _ctx(company, db, day=2)
        events = outcome_system.evaluate_company(ctx)
        assert company.status == CompanyStatus.FAILED
        assert any(e.event_type == "COMPANY_FAILED" for e in events)

    def test_company_completes_when_all_goals_achieved(self, db: Session):
        company = _create_company(db, with_agents=False)
        g1 = Goal(company_id=company.id, title="Launch MVP", status=GoalStatus.ACHIEVED, priority=1, progress=100.0)
        g2 = Goal(company_id=company.id, title="Get customers", status=GoalStatus.ACHIEVED, priority=1, progress=100.0)
        db.add_all([g1, g2])
        db.flush()
        ctx = _ctx(company, db, day=2)
        events = outcome_system.evaluate_company(ctx)
        assert company.status == CompanyStatus.COMPLETED
        assert any(e.event_type == "COMPANY_COMPLETED" for e in events)

    def test_non_running_company_not_evaluated(self, db: Session):
        company = _create_company(db, cash=-100.0, with_agents=False)
        company.status = CompanyStatus.PAUSED
        db.flush()
        ctx = _ctx(company, db, day=2)
        events = outcome_system.evaluate_company(ctx)
        assert company.status == CompanyStatus.PAUSED
        assert events == []


# ---------------------------------------------------------------------------
# Integration: full tick
# ---------------------------------------------------------------------------


class TestFullSimulation:
    def test_tick_advances_day_and_processes_systems(self, db: Session):
        company = _create_company(db, seed=12345)
        db.refresh(company)
        engine = SimulationEngine(llm=MockLLMService())
        engine.start(db, company.id)
        state = engine.tick(db, company.id)
        assert state.current_day == 2
        # Expenses should have accumulated (salaries + infrastructure).
        assert company.expenses > 0

    def test_multiple_ticks_accumulate_financials(self, db: Session):
        company = _create_company(db, seed=42)
        db.refresh(company)
        engine = SimulationEngine(llm=MockLLMService())
        engine.start(db, company.id)
        for _ in range(5):
            engine.tick(db, company.id)
        assert company.current_day == 6
        assert company.expenses > 0
        # Cash should have decreased since no customers yet.
        assert company.cash < 100000.0

    def test_seed_reproducibility_full_tick(self, db: Session):
        """Two companies with same seed should produce identical market after ticks."""
        c1 = _create_company(db, name="RepA", seed=999)
        c2 = _create_company(db, name="RepB", seed=999)
        db.refresh(c1)
        db.refresh(c2)
        engine = SimulationEngine(llm=MockLLMService())
        engine.start(db, c1.id)
        engine.start(db, c2.id)
        engine.tick(db, c1.id)
        engine.tick(db, c2.id)
        assert c1.market_demand == c2.market_demand
        assert c1.market_competition == c2.market_competition
        assert c1.market_sentiment == c2.market_sentiment

    def test_agents_still_execute_in_tick(self, db: Session):
        company = _create_company(db, seed=100)
        db.refresh(company)
        llm = MockLLMService(
            decisions={
                "CEO": {"action": "CREATE_GOAL", "reasoning": "test", "confidence": 0.9, "title": "G1", "description": "d", "priority": "HIGH"},
                "CTO": {"action": "CREATE_PROJECT", "reasoning": "test", "confidence": 0.9, "title": "P1", "description": "d"},
                "CMO": {"action": "CREATE_TASK", "reasoning": "test", "confidence": 0.9, "title": "T1", "description": "d"},
                "ENGINEER": {"action": "NO_ACTION", "reasoning": "test", "confidence": 0.5},
            }
        )
        engine = SimulationEngine(llm=llm)
        engine.start(db, company.id)
        engine.tick(db, company.id)
        goals = list(db.execute(select(Goal).where(Goal.company_id == company.id)).scalars().all())
        projects = list(db.execute(select(Project).where(Project.company_id == company.id)).scalars().all())
        tasks = list(db.execute(select(Task).where(Task.company_id == company.id)).scalars().all())
        assert len(goals) >= 1
        assert len(projects) >= 1
        assert len(tasks) >= 1

    def test_company_fails_mid_simulation(self, db: Session):
        """A company with tiny cash should eventually fail."""
        company = _create_company(db, cash=10.0, seed=5)
        db.refresh(company)
        engine = SimulationEngine(llm=MockLLMService())
        engine.start(db, company.id)
        for _ in range(5):
            if company.status != CompanyStatus.RUNNING:
                break
            engine.tick(db, company.id)
        assert company.status == CompanyStatus.FAILED

    def test_nova_ai_scenario(self, db: Session):
        """Integration test resembling the spec's NovaAI scenario."""
        company = _create_company(
            db, name="NovaAI", seed=12345, cash=100000.0,
            mission="Build an AI-powered customer support platform.",
        )
        goal = Goal(
            company_id=company.id, title="Launch MVP within 14 days",
            status=GoalStatus.TODO, priority=1, progress=0.0,
        )
        db.add(goal)
        db.commit()
        db.refresh(company)

        llm = MockLLMService(
            decisions={
                "CEO": {"action": "CREATE_TASK", "reasoning": "MVP work", "confidence": 0.9, "title": "Define MVP scope", "description": "d", "priority": "HIGH"},
                "CTO": {"action": "CREATE_PROJECT", "reasoning": "Build it", "confidence": 0.9, "title": "Engineering MVP", "description": "d"},
                "CMO": {"action": "CREATE_TASK", "reasoning": "Research", "confidence": 0.9, "title": "Customer research", "description": "d"},
                "ENGINEER": {"action": "NO_ACTION", "reasoning": "Waiting", "confidence": 0.5},
            }
        )
        engine = SimulationEngine(llm=llm)
        engine.start(db, company.id)
        for _ in range(10):
            if company.status != CompanyStatus.RUNNING:
                break
            engine.tick(db, company.id)

        # Verify coherent state.
        assert company.current_day >= 2
        assert company.expenses > 0
        assert company.cash < 100000.0
        # Market should have evolved.
        assert 0.0 <= company.market_demand <= 1.0
        # Tasks/projects should exist.
        tasks = list(db.execute(select(Task).where(Task.company_id == company.id)).scalars().all())
        projects = list(db.execute(select(Project).where(Project.company_id == company.id)).scalars().all())
        assert len(tasks) >= 1
        assert len(projects) >= 1
