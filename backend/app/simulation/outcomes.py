"""Outcome system: evaluate company success/failure conditions."""

from __future__ import annotations

import logging

from sqlalchemy import select

from app.enums import CompanyStatus, GoalStatus
from app.models.company import Company
from app.models.event import Event
from app.models.goal import Goal
from app.simulation.domain import SimulationContext
from app.simulation.financial_health import determine_financial_health

logger = logging.getLogger("agent_company_simulator")


def evaluate_company(ctx: SimulationContext) -> list[Event]:
    """Evaluate company success/failure conditions.

    Failure: cash <= 0.
    Completion: highest-priority active goal is achieved.
    Financial distress: critically low runway with negative cash trend.

    Returns lifecycle events if a transition occurs.
    """
    events: list[Event] = []
    company = ctx.company

    if company.status != CompanyStatus.RUNNING:
        return events

    if company.cash <= 0:
        company.status = CompanyStatus.FAILED
        event = Event(
            company_id=company.id,
            event_type="COMPANY_FAILED",
            description=f"Company '{company.name}' has run out of cash on day {ctx.day}.",
            target_type="company",
            target_id=company.id,
            meta={"cash": round(company.cash, 2), "day": ctx.day},
            simulation_day=ctx.day,
        )
        events.append(event)
        logger.warning("Company %s FAILED on day %d (cash=%.2f)", company.id, ctx.day, company.cash)
        return events

    health = determine_financial_health(company)
    if health.value == "CRITICAL":
        event = Event(
            company_id=company.id,
            actor_id=None,
            event_type="FINANCIAL_DISTRESS",
            description=f"Company '{company.name}' is in critical financial condition on day {ctx.day}.",
            target_type="company",
            target_id=company.id,
            meta={"health": health.value, "cash": round(company.cash, 2), "day": ctx.day},
            simulation_day=ctx.day,
        )
        events.append(event)
        logger.warning("Company %s in CRITICAL financial state on day %d", company.id, ctx.day)

    goals = list(
        ctx.db.execute(select(Goal).where(Goal.company_id == company.id)).scalars().all()
    )
    if not goals:
        return events
    incomplete = [g for g in goals if g.status not in (GoalStatus.ACHIEVED, GoalStatus.CANCELLED)]
    if not incomplete:
        company.status = CompanyStatus.COMPLETED
        event = Event(
            company_id=company.id,
            event_type="COMPANY_COMPLETED",
            description=f"Company '{company.name}' completed all goals on day {ctx.day}.",
            target_type="company",
            target_id=company.id,
            meta={"day": ctx.day},
            simulation_day=ctx.day,
        )
        events.append(event)
        logger.info("Company %s COMPLETED on day %d", company.id, ctx.day)

    return events
