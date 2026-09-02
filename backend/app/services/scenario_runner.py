"""Service for executing simulation runs for scenarios."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.companies import seed_initial_organization
from app.enums import CompanyStatus, EventType, ScenarioStatus
from app.models.company import Company
from app.models.customer import Customer
from app.models.event import Event
from app.models.scenario import Scenario, SimulationRun
from app.simulation.engine import SimulationEngine

_engine = SimulationEngine()


def _generate_run_name(scenario_name: str, seed: int) -> int:
    """Generate a unique suffix for company name based on seed."""
    return (seed % 10000) + 1


def execute_run(db: Session, run: SimulationRun) -> None:
    """Execute a single simulation run."""
    now = datetime.now(timezone.utc).isoformat()
    run.started_at = now
    run.status = ScenarioStatus.RUNNING
    db.commit()

    try:
        config = run.configuration_snapshot or {}
        seed = run.seed

        # Create a new company for this run
        company_name = f"{config.get('name', 'Run')}_{seed}_{run.id}"
        company = Company(
            name=company_name,
            mission=config.get("mission", "Experiment run"),
            cash=config.get("cash", 100000.0),
            revenue=0.0,
            expenses=0.0,
            current_day=1,
            status=CompanyStatus.CREATED,
            seed=seed,
            market_demand=config.get("market_demand", 0.5),
            market_competition=config.get("market_competition", 0.3),
            product_readiness=config.get("product_readiness", 0.0),
            technical_debt=config.get("technical_debt", 0.0),
            target_segment=config.get("target_segment", "SMB"),
            price=config.get("price", 100.0),
        )
        db.add(company)
        db.flush()

        # Seed organization
        agents = seed_initial_organization(db, company)

        # Log company creation event
        db.add(
            Event(
                company_id=company.id,
                actor_id=None,
                event_type=EventType.COMPANY_CREATED,
                description=f"Company '{company.name}' created for experiment.",
                target_type="company",
                target_id=company.id,
                meta={"experiment_run_id": run.id, "seed": seed},
                simulation_day=1,
            )
        )
        db.commit()

        # Link run to company
        run.company_id = company.id
        db.commit()

        # Start simulation
        company.status = CompanyStatus.RUNNING
        db.add(
            Event(
                company_id=company.id,
                actor_id=None,
                event_type=EventType.SIMULATION_STARTED,
                description=f"Simulation started for experiment run.",
                simulation_day=1,
            )
        )
        db.commit()

        # Run simulation ticks
        for _ in range(run.simulation_days):
            _engine.tick(db, company.id)

        # Collect final metrics
        db.refresh(company)
        final_metrics = _collect_final_metrics(db, company)
        run.final_metrics = final_metrics
        run.status = ScenarioStatus.COMPLETED
        run.completed_at = datetime.now(timezone.utc).isoformat()
        db.commit()

    except Exception as exc:
        db.rollback()
        run.status = ScenarioStatus.FAILED
        run.error_message = str(exc)
        run.completed_at = datetime.now(timezone.utc).isoformat()
        db.commit()
        raise


def _collect_final_metrics(db: Session, company: Company) -> dict:
    """Collect final metrics from a completed simulation."""
    from app.models.customer import Customer
    from app.enums import CustomerStatus

    customers = list(
        db.execute(select(Customer).where(Customer.company_id == company.id))
        .scalars()
        .all()
    )
    active = [c for c in customers if c.status == CustomerStatus.ACTIVE]

    return {
        "current_day": company.current_day,
        "cash": round(company.cash, 2),
        "revenue": round(company.revenue, 2),
        "expenses": round(company.expenses, 2),
        "profit": round(company.revenue - company.expenses, 2),
        "active_customers": len(active),
        "total_customers": len(customers),
        "market_share": round(company.market_share_cache, 4),
        "product_readiness": round(company.product_readiness, 3),
        "product_quality": round(company.product_quality, 3),
        "brand_strength": round(company.brand_strength, 3),
        "market_demand": round(company.market_demand, 3),
        "market_competition": round(company.market_competition, 3),
        "valuation": _estimate_valuation(company),
    }


def _estimate_valuation(company: Company) -> float:
    """Estimate company valuation based on metrics."""
    if company.revenue <= 0:
        return company.cash
    annual_revenue = company.revenue * 12
    multiple = 5.0 + (company.product_readiness * 3.0) + (company.brand_strength * 2.0)
    return round(annual_revenue * multiple + company.cash, 2)


# --- Built-in Scenarios ---


BUILT_IN_SCENARIOS: list[dict] = [
    {
        "name": "Normal Startup",
        "description": "Balanced starting conditions for a typical startup.",
        "category": "startup",
        "configuration": {
            "name": "Startup",
            "mission": "Build a great product",
            "cash": 100000.0,
            "market_demand": 0.5,
            "market_competition": 0.3,
            "product_readiness": 0.2,
            "technical_debt": 0.1,
            "target_segment": "SMB",
            "price": 100.0,
        },
    },
    {
        "name": "High Growth",
        "description": "Higher growth opportunity with increased operating pressure.",
        "category": "growth",
        "configuration": {
            "name": "GrowthCo",
            "mission": "Scale rapidly and capture market share",
            "cash": 150000.0,
            "market_demand": 0.8,
            "market_competition": 0.2,
            "product_readiness": 0.3,
            "technical_debt": 0.15,
            "target_segment": "Enterprise",
            "price": 250.0,
        },
    },
    {
        "name": "Cash Crisis",
        "description": "Limited cash and high burn rate from the start.",
        "category": "financial",
        "configuration": {
            "name": "StrugglingCo",
            "mission": "Survive with limited resources",
            "cash": 30000.0,
            "market_demand": 0.4,
            "market_competition": 0.5,
            "product_readiness": 0.1,
            "technical_debt": 0.3,
            "target_segment": "SMB",
            "price": 75.0,
        },
    },
    {
        "name": "Market Downturn",
        "description": "Weak market conditions with low demand.",
        "category": "market",
        "configuration": {
            "name": "RecessionCo",
            "mission": "Navigate challenging market conditions",
            "cash": 80000.0,
            "market_demand": 0.2,
            "market_competition": 0.7,
            "product_readiness": 0.2,
            "technical_debt": 0.2,
            "target_segment": "Enterprise",
            "price": 150.0,
        },
    },
    {
        "name": "Aggressive Competition",
        "description": "Strong competitive pressure from established players.",
        "category": "market",
        "configuration": {
            "name": "ChallengerCo",
            "mission": "Compete against established competitors",
            "cash": 120000.0,
            "market_demand": 0.6,
            "market_competition": 0.9,
            "product_readiness": 0.3,
            "technical_debt": 0.1,
            "target_segment": "SMB",
            "price": 50.0,
        },
    },
]


def seed_builtin_scenarios(db: Session) -> None:
    """Create built-in scenarios if they don't exist."""
    for builtin in BUILT_IN_SCENARIOS:
        existing = db.execute(
            select(Scenario).where(Scenario.name == builtin["name"])
        ).scalar_one_or_none()
        if existing is None:
            scenario = Scenario(
                name=builtin["name"],
                description=builtin["description"],
                category=builtin["category"],
                is_builtin=True,
                configuration=builtin["configuration"],
            )
            db.add(scenario)
    db.commit()
