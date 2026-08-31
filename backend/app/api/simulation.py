from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.expectation import Expectation
from app.models.message import Message
from app.models.plan import Plan
from app.schemas.simulation import (
    AgentMetricsRead,
    ExpectationRead,
    MessageRead,
    PlanRead,
    PlanStepRead,
    SimulationActionResponse,
    SimulationStateRead,
)
from app.simulation.engine import SimulationEngine
from app.simulation.state import _sim_ctx
from app.simulation import metrics as metrics_system

router = APIRouter(prefix="/simulation", tags=["simulation"])

_engine = SimulationEngine()

# --- Simulation speed configuration (in-memory per company) ---
_sim_speed: dict[int, str] = {}  # company_id -> "paused" | "1x" | "2x" | "5x" | "10x"
_sim_task: dict[int, object] = {}  # company_id -> asyncio.Task


def _handle(error: ValueError) -> None:
    msg = str(error)
    if "not found" in msg:
        raise HTTPException(status_code=404, detail=msg)
    raise HTTPException(status_code=400, detail=msg)


@router.post("/{company_id}/start", response_model=SimulationActionResponse)
def start_simulation(company_id: int, db: Session = Depends(get_db)):
    try:
        state = _engine.start(db, company_id)
    except ValueError as exc:
        _handle(exc)
    return SimulationActionResponse(message="Simulation started.", state=state.to_read_model())


@router.post("/{company_id}/pause", response_model=SimulationActionResponse)
def pause_simulation(company_id: int, db: Session = Depends(get_db)):
    try:
        state = _engine.pause(db, company_id)
    except ValueError as exc:
        _handle(exc)
    return SimulationActionResponse(message="Simulation paused.", state=state.to_read_model())


@router.post("/{company_id}/tick", response_model=SimulationActionResponse)
def tick_simulation(company_id: int, db: Session = Depends(get_db)):
    try:
        state = _engine.tick(db, company_id)
    except ValueError as exc:
        _handle(exc)
    return SimulationActionResponse(
        message=f"Simulation advanced to day {state.current_day}.", state=state.to_read_model()
    )


@router.post("/{company_id}/resume", response_model=SimulationActionResponse)
def resume_simulation(company_id: int, speed: str = "1x", db: Session = Depends(get_db)):
    """Start or resume continuous simulation at the given speed.

    Speed options: "1x" (1 day/sec), "2x" (2 days/sec), "5x", "10x".
    """
    import asyncio
    from app.db.database import SessionLocal

    # Cancel any existing task for this company.
    if company_id in _sim_task and not _sim_task[company_id].done():
        _sim_task[company_id].cancel()

    _sim_speed[company_id] = speed

    async def _run_loop():
        # Map speed to interval in seconds.
        interval_map = {"1x": 1.0, "2x": 0.5, "5x": 0.2, "10x": 0.1}
        interval = interval_map.get(speed, 1.0)

        while True:
            session = SessionLocal()
            try:
                state = _engine.tick(session, company_id)
                if state.status not in ("RUNNING",):
                    break
            except Exception:
                break
            finally:
                session.close()
            await asyncio.sleep(interval)

    try:
        loop = asyncio.get_running_loop()
        _sim_task[company_id] = loop.create_task(_run_loop())
    except RuntimeError:
        # No running loop; just tick once.
        state = _engine.tick(db, company_id)
        return SimulationActionResponse(
            message=f"Simulation advanced to day {state.current_day}.", state=state.to_read_model()
        )

    company = _get_company_or_404(db, company_id)
    return SimulationActionResponse(
        message=f"Simulation resumed at {speed} speed.", state=SimulationStateRead(company_id=company.id, status=company.status, current_day=company.current_day, agents=[], recent_events=[], agent_count=0, event_count=0)
    )


@router.post("/{company_id}/speed", response_model=SimulationActionResponse)
def set_simulation_speed(company_id: int, speed: str = "1x", db: Session = Depends(get_db)):
    """Change the speed of a running continuous simulation."""
    if company_id not in _sim_task or _sim_task[company_id].done():
        raise HTTPException(status_code=400, detail="No running simulation to change speed for.")
    _sim_speed[company_id] = speed
    return SimulationActionResponse(message=f"Speed set to {speed}.", state=_engine.get_state(db, company_id).to_read_model())


@router.get("/{company_id}", response_model=SimulationStateRead)
def get_simulation(company_id: int, db: Session = Depends(get_db)):
    try:
        state = _engine.get_state(db, company_id)
    except ValueError as exc:
        _handle(exc)
    return state.to_read_model()


def _get_company_or_404(db: Session, company_id: int):
    from app.models.company import Company
    company = db.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=404, detail=f"Company {company_id} not found")
    return company


@router.get("/{company_id}/plans", response_model=list[PlanRead])
def list_plans(company_id: int, db: Session = Depends(get_db), limit: int = 100):
    _get_company_or_404(db, company_id)
    plans = list(
        db.execute(select(Plan).where(Plan.company_id == company_id).order_by(Plan.id).limit(limit))
        .scalars()
        .all()
    )
    result = []
    for p in plans:
        steps = sorted(p.steps, key=lambda s: s.sequence)
        result.append(
            PlanRead(
                id=p.id,
                agent_id=p.agent_id,
                goal_id=p.goal_id,
                objective=p.objective,
                status=p.status,
                priority=p.priority,
                progress=round(
                    sum(1 for s in steps if s.status.value == "COMPLETED") / len(steps), 2
                ) if steps else 0.0,
                current_step=p.current_step,
                total_steps=len(steps),
                created_day=p.created_day,
                completed_day=p.completed_day,
                steps=[
                    PlanStepRead(
                        id=s.id, sequence=s.sequence, description=s.description, status=s.status,
                    )
                    for s in steps
                ],
            )
        )
    return result


@router.get("/{company_id}/messages", response_model=list[MessageRead])
def list_messages(company_id: int, db: Session = Depends(get_db), limit: int = 100):
    _get_company_or_404(db, company_id)
    messages = list(
        db.execute(select(Message).where(Message.company_id == company_id).order_by(Message.id).limit(limit))
        .scalars()
        .all()
    )
    return [
        MessageRead(
            id=m.id,
            sender_agent_id=m.sender_agent_id,
            recipient_agent_id=m.recipient_agent_id,
            subject=m.subject,
            content=m.content,
            priority=m.priority,
            created_day=m.created_day,
            read_day=m.read_day,
        )
        for m in messages
    ]


@router.get("/{company_id}/expectations", response_model=list[ExpectationRead])
def list_expectations(company_id: int, db: Session = Depends(get_db), limit: int = 100):
    _get_company_or_404(db, company_id)
    expectations = list(
        db.execute(select(Expectation).where(Expectation.company_id == company_id).order_by(Expectation.id).limit(limit))
        .scalars()
        .all()
    )
    return [
        ExpectationRead(
            id=e.id,
            agent_id=e.agent_id,
            description=e.description,
            target_day=e.target_day,
            target_metric=e.target_metric,
            expected_value=e.expected_value,
            actual_value=e.actual_value,
            status=e.status,
        )
        for e in expectations
    ]


@router.get("/{company_id}/agent-metrics", response_model=list[AgentMetricsRead])
def list_agent_metrics(company_id: int, db: Session = Depends(get_db)):
    from app.models.agent import Agent
    _get_company_or_404(db, company_id)
    agents = list(
        db.execute(select(Agent).where(Agent.company_id == company_id)).scalars().all()
    )
    from app.models.company import Company
    company = db.get(Company, company_id)
    ctx = _sim_ctx(db, company, company.current_day)
    metrics = [metrics_system.compute_agent_metrics(ctx, a) for a in agents]
    return [
        AgentMetricsRead(
            agent_id=m["agent_id"],
            role=m["role"],
            tasks_completed=m["tasks_completed"],
            tasks_blocked=m["tasks_blocked"],
            plans_completed=m["plans_completed"],
            plans_failed=m["plans_failed"],
            decisions=m["decisions"],
            messages_sent=m["messages_sent"],
            messages_received=m["messages_received"],
        )
        for m in metrics
    ]


# --- Phase 6 market & strategy endpoints ---


@router.get("/{company_id}/market")
def get_market(company_id: int, db: Session = Depends(get_db)):
    """Get market segments and company market position."""
    from app.models.market_segment import MarketSegment
    from app.models.company import Company
    _get_company_or_404(db, company_id)
    segments = list(db.execute(select(MarketSegment)).scalars().all())
    company = db.get(Company, company_id)
    return {
        "segments": [
            {
                "name": s.name,
                "type": s.segment_type.value if hasattr(s.segment_type, "value") else str(s.segment_type),
                "size": s.size,
                "demand": s.demand,
                "price_sensitivity": s.price_sensitivity,
                "avg_customer_value": s.avg_customer_value,
                "sales_cycle_days": s.sales_cycle_days,
            }
            for s in segments
        ],
        "company": {
            "target_segment": company.target_segment,
            "price": company.price,
            "market_share": company.market_share_cache,
            "brand_strength": company.brand_strength,
        },
    }


@router.get("/{company_id}/competitors")
def get_competitors(company_id: int, db: Session = Depends(get_db)):
    """Get all competitors."""
    from app.models.competitor import Competitor
    _get_company_or_404(db, company_id)
    competitors = list(db.execute(select(Competitor)).scalars().all())
    return [
        {
            "id": c.id,
            "name": c.name,
            "market_share": c.market_share,
            "price": c.price,
            "product_quality": c.product_quality,
            "brand_strength": c.brand_strength,
            "target_segment": c.target_segment.value if hasattr(c.target_segment, "value") else str(c.target_segment),
            "strategy": c.strategy.value if hasattr(c.strategy, "value") else str(c.strategy),
        }
        for c in competitors
    ]


@router.get("/{company_id}/strategy")
def get_strategy(company_id: int, db: Session = Depends(get_db)):
    """Get company strategy state."""
    from app.models.company import Company
    _get_company_or_404(db, company_id)
    company = db.get(Company, company_id)
    return {
        "target_segment": company.target_segment,
        "price": company.price,
        "positioning": company.positioning,
        "brand_strength": company.brand_strength,
        "sales_effectiveness": company.sales_effectiveness,
        "market_share": company.market_share_cache,
    }


@router.get("/{company_id}/campaigns")
def get_campaigns(company_id: int, db: Session = Depends(get_db)):
    """Get company campaigns."""
    from app.models.campaign import Campaign
    _get_company_or_404(db, company_id)
    campaigns = list(
        db.execute(select(Campaign).where(Campaign.company_id == company_id).order_by(Campaign.id))
        .scalars()
        .all()
    )
    return [
        {
            "id": c.id,
            "name": c.name,
            "segment": c.segment.value if hasattr(c.segment, "value") else str(c.segment),
            "budget": c.budget,
            "daily_spend": c.daily_spend,
            "days_remaining": c.days_remaining,
            "effectiveness": c.effectiveness,
            "status": c.status.value if hasattr(c.status, "value") else str(c.status),
        }
        for c in campaigns
    ]


@router.get("/{company_id}/sales")
def get_sales(company_id: int, db: Session = Depends(get_db)):
    """Get company sales pipeline."""
    from app.models.sales_opportunity import SalesOpportunity
    _get_company_or_404(db, company_id)
    opportunities = list(
        db.execute(
            select(SalesOpportunity).where(SalesOpportunity.company_id == company_id).order_by(SalesOpportunity.id)
        )
        .scalars()
        .all()
    )
    return [
        {
            "id": o.id,
            "name": o.name,
            "segment": o.segment.value if hasattr(o.segment, "value") else str(o.segment),
            "value": o.value,
            "stage": o.stage.value if hasattr(o.stage, "value") else str(o.stage),
            "created_day": o.created_day,
            "expected_close_day": o.expected_close_day,
        }
        for o in opportunities
    ]


# --- Phase 8 dashboard endpoints ---


@router.get("/{company_id}/dashboard")
def get_dashboard(company_id: int, db: Session = Depends(get_db)):
    """Get comprehensive dashboard data for the command center."""
    from app.models.agent import Agent
    from app.models.company import Company
    from app.models.customer import Customer
    from app.models.event import Event
    from app.models.task import Task
    from app.models.project import Project
    from app.models.milestone import Milestone
    from app.models.product_feature import ProductFeature
    from app.models.campaign import Campaign
    from app.models.sales_opportunity import SalesOpportunity
    from app.models.market_segment import MarketSegment
    from app.models.competitor import Competitor

    company = _get_company_or_404(db, company_id)

    agents = list(db.execute(select(Agent).where(Agent.company_id == company_id)).scalars().all())
    customers = list(db.execute(select(Customer).where(Customer.company_id == company_id)).scalars().all())
    tasks = list(db.execute(select(Task).where(Task.company_id == company_id)).scalars().all())
    projects = list(db.execute(select(Project).where(Project.company_id == company_id)).scalars().all())
    milestones = list(db.execute(select(Milestone).where(Milestone.company_id == company_id)).scalars().all())
    features = list(db.execute(select(ProductFeature).where(ProductFeature.company_id == company_id)).scalars().all())
    campaigns = list(db.execute(select(Campaign).where(Campaign.company_id == company_id)).scalars().all())
    opportunities = list(db.execute(select(SalesOpportunity).where(SalesOpportunity.company_id == company_id)).scalars().all())
    segments = list(db.execute(select(MarketSegment)).scalars().all())
    competitors = list(db.execute(select(Competitor)).scalars().all())

    active_customers = [c for c in customers if c.status.value == "ACTIVE"]
    churned_customers = [c for c in customers if c.status.value == "CHURNED"]

    return {
        "company": {
            "id": company.id,
            "name": company.name,
            "mission": company.mission,
            "status": company.status.value,
            "current_day": company.current_day,
            "cash": company.cash,
            "revenue": company.revenue,
            "expenses": company.expenses,
            "profit": company.revenue - company.expenses,
            "product_readiness": company.product_readiness,
            "product_quality": company.product_quality,
            "technical_debt": company.technical_debt,
            "target_segment": company.target_segment,
            "price": company.price,
            "positioning": company.positioning,
            "brand_strength": company.brand_strength,
            "market_share": company.market_share_cache,
        },
        "agents": [
            {
                "id": a.id,
                "name": a.name,
                "role": a.role.value,
                "status": a.status.value,
                "authority": a.authority,
                "manager_id": a.manager_id,
                "workload": a.workload,
                "morale": a.morale,
            }
            for a in agents
        ],
        "financials": {
            "cash": company.cash,
            "revenue": company.revenue,
            "expenses": company.expenses,
            "profit": company.revenue - company.expenses,
            "total_customer_value": sum(c.monthly_value for c in active_customers),
        },
        "customers": {
            "total": len(customers),
            "active": len(active_customers),
            "churned": len(churned_customers),
            "list": [
                {
                    "id": c.id,
                    "name": c.name,
                    "status": c.status.value,
                    "monthly_value": c.monthly_value,
                    "acquired_day": c.acquired_day,
                }
                for c in customers[:20]
            ],
        },
        "product": {
            "readiness": company.product_readiness,
            "quality": company.product_quality,
            "technical_debt": company.technical_debt,
            "features": [
                {
                    "id": f.id,
                    "name": f.name,
                    "status": f.status.value,
                    "progress": f.progress,
                    "quality": f.quality,
                    "importance": f.importance,
                }
                for f in features
            ],
            "milestones": [
                {
                    "id": m.id,
                    "name": m.name,
                    "status": m.status.value,
                    "progress": m.progress,
                }
                for m in milestones
            ],
            "projects": [
                {
                    "id": p.id,
                    "name": p.name,
                    "status": p.status.value,
                    "progress": p.progress,
                }
                for p in projects
            ],
        },
        "strategy": {
            "target_segment": company.target_segment,
            "price": company.price,
            "positioning": company.positioning,
            "brand_strength": company.brand_strength,
            "market_share": company.market_share_cache,
            "segments": [
                {
                    "name": s.name,
                    "type": s.segment_type.value if hasattr(s.segment_type, "value") else str(s.segment_type),
                    "demand": s.demand,
                    "competition_intensity": s.competition_intensity,
                }
                for s in segments
            ],
            "competitors": [
                {
                    "name": c.name,
                    "market_share": c.market_share,
                    "price": c.price,
                    "product_quality": c.product_quality,
                    "strategy": c.strategy.value if hasattr(c.strategy, "value") else str(c.strategy),
                }
                for c in competitors
            ],
        },
        "campaigns": [
            {
                "id": c.id,
                "name": c.name,
                "status": c.status.value if hasattr(c.status, "value") else str(c.status),
                "budget": c.budget,
                "days_remaining": c.days_remaining,
            }
            for c in campaigns
        ],
        "sales": [
            {
                "id": o.id,
                "name": o.name,
                "stage": o.stage.value if hasattr(o.stage, "value") else str(o.stage),
                "value": o.value,
            }
            for o in opportunities
        ],
        "tasks": [
            {
                "id": t.id,
                "title": t.title,
                "status": t.status.value,
                "priority": t.priority,
                "progress": t.progress,
                "assigned_to": t.assigned_to,
            }
            for t in tasks[:20]
        ],
    }


@router.get("/{company_id}/timeline")
def get_timeline(
    company_id: int,
    day: int | None = None,
    event_type: str | None = None,
    agent_id: int | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Get simulation timeline with optional filtering."""
    from app.models.event import Event

    _get_company_or_404(db, company_id)

    query = select(Event).where(Event.company_id == company_id)

    if day is not None:
        query = query.where(Event.simulation_day == day)
    if event_type is not None:
        query = query.where(Event.event_type == event_type)
    if agent_id is not None:
        query = query.where(Event.actor_id == agent_id)

    query = query.order_by(Event.simulation_day.desc(), Event.id.desc()).limit(limit)
    events = list(db.execute(query).scalars().all())

    return [
        {
            "id": e.id,
            "day": e.simulation_day,
            "event_type": e.event_type.value if hasattr(e.event_type, "value") else str(e.event_type),
            "description": e.description,
            "actor_id": e.actor_id,
            "meta": e.meta,
        }
        for e in events
    ]


# --- Phase 10: Financial Intelligence, Funding & Capital Management endpoints ---


@router.get("/{company_id}/financials")
def get_financials(company_id: int, db: Session = Depends(get_db)):
    """Get detailed financial metrics."""
    from app.models.company import Company
    from app.simulation.financial_health import get_financial_metrics
    _get_company_or_404(db, company_id)
    company = db.get(Company, company_id)
    metrics = get_financial_metrics(company)
    return metrics


@router.get("/{company_id}/valuation")
def get_valuation(company_id: int, db: Session = Depends(get_db)):
    """Get company valuation."""
    from app.models.company import Company
    from app.simulation.domain import SimulationContext, make_rng
    from app.simulation.valuation import calculate_valuation
    _get_company_or_404(db, company_id)
    company = db.get(Company, company_id)
    ctx = SimulationContext(db=db, company=company, day=company.current_day, rng=make_rng(company.seed, company.current_day))
    return calculate_valuation(ctx)


@router.get("/{company_id}/investors")
def get_investors(company_id: int, db: Session = Depends(get_db)):
    """Get all investors for the company."""
    from app.models.investor import Investor
    _get_company_or_404(db, company_id)
    investors = list(
        db.execute(select(Investor).where(Investor.company_id == company_id).order_by(Investor.id))
        .scalars()
        .all()
    )
    return [
        {
            "id": i.id,
            "name": i.name,
            "preferred_stage": i.preferred_stage.value if hasattr(i.preferred_stage, "value") else str(i.preferred_stage),
            "check_size_min": i.check_size_min,
            "check_size_max": i.check_size_max,
            "risk_tolerance": i.risk_tolerance,
            "sector_preference": i.sector_preference,
            "ownership_expectation": i.ownership_expectation,
            "reputation": i.reputation,
            "interest_score": i.interest_score,
        }
        for i in investors
    ]


@router.get("/{company_id}/funding-rounds")
def get_funding_rounds(company_id: int, db: Session = Depends(get_db)):
    """Get all funding rounds."""
    from app.models.funding_round import FundingRound
    _get_company_or_404(db, company_id)
    rounds = list(
        db.execute(select(FundingRound).where(FundingRound.company_id == company_id).order_by(FundingRound.id))
        .scalars()
        .all()
    )
    return [
        {
            "id": r.id,
            "round_stage": r.round_stage.value if hasattr(r.round_stage, "value") else str(r.round_stage),
            "amount_requested": r.amount_requested,
            "amount_raised": r.amount_raised,
            "valuation": r.valuation,
            "pre_money_valuation": r.pre_money_valuation,
            "post_money_valuation": r.post_money_valuation,
            "equity_sold": r.equity_sold,
            "status": r.status,
            "day_opened": r.day_opened,
            "day_closed": r.day_closed,
        }
        for r in rounds
    ]


@router.get("/{company_id}/pipeline")
def get_pipeline(company_id: int, db: Session = Depends(get_db)):
    """Get fundraising pipeline."""
    from app.models.fundraising_pipeline import FundraisingPipeline
    _get_company_or_404(db, company_id)
    pipelines = list(
        db.execute(select(FundraisingPipeline).where(FundraisingPipeline.company_id == company_id).order_by(FundraisingPipeline.id))
        .scalars()
        .all()
    )
    return [
        {
            "id": p.id,
            "investor_id": p.investor_id,
            "funding_round_id": p.funding_round_id,
            "status": p.status.value if hasattr(p.status, "value") else str(p.status),
            "stage": p.stage.value if hasattr(p.stage, "value") else str(p.stage),
            "interest_score": p.interest_score,
            "notes": p.notes,
            "day_updated": p.day_updated,
        }
        for p in pipelines
    ]


@router.get("/{company_id}/cap-table")
def get_cap_table(company_id: int, db: Session = Depends(get_db)):
    """Get cap table."""
    from app.models.cap_table import CapTableEntry
    _get_company_or_404(db, company_id)
    entries = list(
        db.execute(select(CapTableEntry).where(CapTableEntry.company_id == company_id).order_by(CapTableEntry.id))
        .scalars()
        .all()
    )
    return [
        {
            "id": e.id,
            "owner_type": e.owner_type,
            "owner_id": e.owner_id,
            "owner_name": e.owner_name,
            "ownership_percentage": e.ownership_percentage,
            "shares": e.shares,
            "notes": e.notes,
        }
        for e in entries
    ]


@router.get("/{company_id}/budget-requests")
def get_budget_requests(company_id: int, db: Session = Depends(get_db)):
    """Get budget requests."""
    from app.models.budget_request import BudgetRequest
    _get_company_or_404(db, company_id)
    requests = list(
        db.execute(select(BudgetRequest).where(BudgetRequest.company_id == company_id).order_by(BudgetRequest.id))
        .scalars()
        .all()
    )
    return [
        {
            "id": r.id,
            "requester_id": r.requester_id,
            "approver_id": r.approver_id,
            "amount": r.amount,
            "approved_amount": r.approved_amount,
            "purpose": r.purpose,
            "status": r.status.value if hasattr(r.status, "value") else str(r.status),
            "requested_day": r.requested_day,
            "decided_day": r.decided_day,
            "decision_notes": r.decision_notes,
        }
        for r in requests
    ]
