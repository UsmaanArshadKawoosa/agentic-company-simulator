from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.specs import DEFAULT_ORG
from app.db.database import get_db
from app.enums import AgentStatus, CompanyStatus, CustomerStatus, EventType
from app.models.agent import Agent
from app.models.company import Company
from app.models.customer import Customer
from app.models.event import Event
from app.schemas.agent import AgentRead
from app.schemas.company import CompanyCreate, CompanyRead
from app.schemas.simulation import CustomerRead, EventRead, FinancialRead, MarketRead, ProductRead

router = APIRouter(prefix="/companies", tags=["companies"])


def _seed_from_name(name: str) -> int:
    """Derive a stable seed from a company name so unseeded runs are reproducible."""
    return (abs(hash(name)) % 1_000_000) + 1


def seed_initial_organization(db: Session, company: Company) -> list[Agent]:
    """Create the default organization for a company.

    CEO -> CTO -> Engineer, and CEO -> CMO (represented via manager_id).
    """
    created: dict = {}
    agents: list[Agent] = []
    # Preserve the declared order so manager roles resolve correctly.
    for spec in DEFAULT_ORG:
        manager_id = None
        if spec["manager_role"] is not None:
            manager = created.get(spec["manager_role"])
            manager_id = manager.id if manager is not None else None

        agent = Agent(
            company_id=company.id,
            name=spec["name"],
            role=spec["role"],
            personality=spec["personality"],
            skills=spec["skills"],
            authority=spec["authority"],
            salary=spec.get("salary", 500.0),
            budget=spec["budget"],
            status=AgentStatus.IDLE,
            manager_id=manager_id,
        )
        db.add(agent)
        db.flush()  # assign id so subsequent manager lookups resolve
        created[spec["role"]] = agent
        agents.append(agent)
    return agents


@router.post("", response_model=CompanyRead, status_code=201)
def create_company(payload: CompanyCreate, db: Session = Depends(get_db)) -> Company:
    existing = db.execute(
        select(Company).where(Company.name == payload.name)
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail="Company name already exists")

    company = Company(
        name=payload.name,
        mission=payload.mission,
        cash=100000.0,
        revenue=0.0,
        expenses=0.0,
        current_day=1,
        status=CompanyStatus.CREATED,
        seed=payload.seed if payload.seed is not None else _seed_from_name(payload.name),
    )
    db.add(company)
    db.flush()

    agents = seed_initial_organization(db, company)

    db.add(
        Event(
            company_id=company.id,
            actor_id=None,
            event_type=EventType.COMPANY_CREATED,
            description=f"Company '{company.name}' was created.",
            target_type="company",
            target_id=company.id,
            meta={"mission": company.mission},
            simulation_day=company.current_day,
        )
    )
    for agent in agents:
        db.add(
            Event(
                company_id=company.id,
                actor_id=agent.id,
                event_type=EventType.AGENT_SPAWNED,
                description=f"Agent '{agent.name}' ({agent.role.value}) joined the company.",
                target_type="agent",
                target_id=agent.id,
                meta={"role": agent.role.value},
                simulation_day=company.current_day,
            )
        )

    db.commit()
    db.refresh(company)
    return company


@router.get("/{company_id}", response_model=CompanyRead)
def get_company(company_id: int, db: Session = Depends(get_db)) -> Company:
    company = db.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.get("/{company_id}/agents", response_model=list[AgentRead])
def list_agents(company_id: int, db: Session = Depends(get_db), limit: int = 100) -> list[Agent]:
    if db.get(Company, company_id) is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return list(
        db.execute(select(Agent).where(Agent.company_id == company_id).limit(limit))
        .scalars()
        .all()
    )


@router.get("/{company_id}/events", response_model=list[EventRead])
def list_events(
    company_id: int, db: Session = Depends(get_db), limit: int = 100
) -> list[Event]:
    if db.get(Company, company_id) is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return list(
        db.execute(
            select(Event)
            .where(Event.company_id == company_id)
            .order_by(Event.id.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )


@router.get("/{company_id}/customers", response_model=list[CustomerRead])
def list_customers(company_id: int, db: Session = Depends(get_db), limit: int = 100) -> list[Customer]:
    if db.get(Company, company_id) is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return list(
        db.execute(select(Customer).where(Customer.company_id == company_id).limit(limit))
        .scalars()
        .all()
    )


@router.get("/{company_id}/metrics")
def get_metrics(company_id: int, db: Session = Depends(get_db)) -> dict:
    company = db.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    customers = list(
        db.execute(select(Customer).where(Customer.company_id == company_id))
        .scalars()
        .all()
    )
    active = [c for c in customers if c.status == CustomerStatus.ACTIVE]
    return {
        "financial": FinancialRead(
            cash=round(company.cash, 2),
            revenue=round(company.revenue, 2),
            expenses=round(company.expenses, 2),
            profit=round(company.revenue - company.expenses, 2),
        ).model_dump(),
        "market": MarketRead(
            demand=round(company.market_demand, 3),
            competition=round(company.market_competition, 3),
            sentiment=round(company.market_sentiment, 3),
        ).model_dump(),
        "product": ProductRead(readiness=round(company.product_readiness, 2)).model_dump(),
        "customers": {
            "total": len(customers),
            "active": len(active),
            "churned": len(customers) - len(active),
            "total_monthly_value": round(sum(c.monthly_value for c in active), 2),
        },
    }
