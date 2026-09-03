"""Real LLM demo script.

Creates a temporary company, seeds deterministic simulation state,
runs several ticks using the configured RealLLMService, and prints
each agent's decision and resulting company state.

Usage:
    LLM_PROVIDER=anthropic LLM_API_KEY=sk-... python scripts/run_real_llm_demo.py
    LLM_PROVIDER=openai LLM_API_KEY=sk-... python scripts/run_real_llm_demo.py
    LLM_PROVIDER=gemini LLM_API_KEY= sk-... python scripts/run_real_llm_demo.py
    LLM_PROVIDER=ollama LLM_MODEL=gemma2 python scripts/run_real_llm_demo.py

Environment variables:
    LLM_PROVIDER   - "anthropic", "openai", "gemini", or "ollama"
    LLM_MODEL      - model id (optional)
    LLM_API_KEY    - provider API key (required for anthropic/openai/gemini,
                    not required for ollama)
    LLM_MAX_TOKENS - max tokens (optional, default 1024)
    LLM_TEMPERATURE - sampling temperature (optional, default 0.0)
    LLM_TIMEOUT    - timeout in seconds (optional, default 30)
    DEMO_DAYS      - number of days to simulate (optional, default 5)
"""

from __future__ import annotations

import os
import sys

# Configure a local SQLite database before importing the application.
os.environ.setdefault("DATABASE_URL", "sqlite:///./demo_real_llm.db")
os.environ.setdefault("ENVIRONMENT", "demo")

from sqlalchemy import select

from app.db.database import Base, SessionLocal, engine
from app.enums import AgentRole, CompanyStatus
from app.models.agent import Agent
from app.models.company import Company
from app.simulation.engine import SimulationEngine
from app.services.llm import RealLLMService


def create_demo_company(db) -> Company:
    """Create a demo company with initial state."""
    company = Company(
        name="DemoCo",
        mission="Build and launch an AI-powered customer support platform.",
        status=CompanyStatus.RUNNING,
        seed=42,
        cash=50000.0,
    )
    db.add(company)
    db.flush()

    # Create agents.
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


def print_agent_decisions(db, day: int):
    """Print agent decisions for a given day."""
    from app.models.event import Event

    decisions = db.execute(
        select(Event)
        .where(Event.simulation_day == day)
        .where(Event.event_type == "DECIDE")
        .order_by(Event.id)
    ).scalars().all()

    for d in decisions:
        meta = d.meta or {}
        action = meta.get("action", "?")
        reasoning = meta.get("reasoning", "")
        confidence = meta.get("confidence", "?")
        print(f"  {d.description.split(' ')[0] if d.description else 'Agent'}: {action}")
        if reasoning:
            print(f"    Reason: {reasoning[:100]}")
        if confidence != "?":
            print(f"    Confidence: {confidence}")


def print_company_state(company: Company):
    """Print current company state."""
    print(f"  Day: {company.current_day}")
    print(f"  Cash: ${company.cash:,.0f}")
    print(f"  Revenue: ${company.revenue:,.0f}")
    print(f"  Expenses: ${company.expenses:,.0f}")
    print(f"  Product Readiness: {company.product_readiness:.0%}")
    print(f"  Product Quality: {company.product_quality:.0%}")
    print(f"  Target Segment: {company.target_segment}")
    print(f"  Price: ${company.price:,.0f}")
    print(f"  Market Share: {company.market_share_cache:.1%}")


def main():
    # Validate configuration.
    provider = os.getenv("LLM_PROVIDER", "")
    api_key = os.getenv("LLM_API_KEY", "")
    keyed_providers = ("anthropic", "openai", "gemini")

    if not provider or provider not in (keyed_providers + ("ollama",)):
        print(f"ERROR: Set LLM_PROVIDER to one of: {', '.join(['noop'] + list(keyed_providers) + ['ollama'])}")
        sys.exit(1)
    if provider in keyed_providers and not api_key:
        print("ERROR: Set LLM_API_KEY environment variable")
        sys.exit(1)

    days = int(os.getenv("DEMO_DAYS", "5"))

    # Initialize database.
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Create company.
        company = create_demo_company(db)
        print(f"Created company: {company.name} (seed={company.seed})")
        print(f"Initial state:")
        print_company_state(company)
        print()

        # Create LLM service.
        llm = RealLLMService()
        engine = SimulationEngine(llm=llm)

        # Run simulation.
        for day in range(1, days + 1):
            print(f"--- Day {day} ---")
            engine.tick(db, company.id)
            print_agent_decisions(db, company.current_day)
            print()

        # Final state.
        db.refresh(company)
        print("=== Final State ===")
        print_company_state(company)

        # Print summary statistics.
        from app.models.event import Event
        from app.models.memory import Memory
        from app.models.plan import Plan
        from app.models.task import Task

        event_count = db.execute(select(Event)).scalars().all().__len__()
        memory_count = db.execute(select(Memory)).scalars().all().__len__()
        plan_count = db.execute(select(Plan)).scalars().all().__len__()
        task_count = db.execute(select(Task)).scalars().all().__len__()

        print(f"\n=== Summary ===")
        print(f"Total events: {event_count}")
        print(f"Total memories: {memory_count}")
        print(f"Total plans: {plan_count}")
        print(f"Total tasks: {task_count}")

    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


if __name__ == "__main__":
    main()
