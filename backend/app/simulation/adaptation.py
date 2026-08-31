"""Adaptation system: detect divergence between plans/expectations and reality.

This system does NOT make agents adapt automatically. Instead, it produces
structured signals (visible in AgentContext) that agents can react to:

    - pending expectations at risk of being missed
    - active plans whose progress lags behind schedule
    - recently missed expectations (lessons)

The LLM decides how to adapt. The simulation only surfaces the signals.
"""

from __future__ import annotations

import logging

from sqlalchemy import select

from app.enums import ExpectationStatus, PlanStatus
from app.models.expectation import Expectation
from app.models.plan import Plan
from app.models.task import Task
from app.simulation.domain import SimulationContext
from app.simulation import plan as plan_system

logger = logging.getLogger("agent_company_simulator")


def at_risk_expectations(
    ctx: SimulationContext,
    agent_id: int,
    *,
    horizon_days: int = 3,
) -> list[Expectation]:
    """Find pending expectations that are due soon or likely to be missed.

    An expectation is "at risk" if:
    - it is PENDING
    - target_day is within horizon_days from now
    - current metric value is below the expected value
    """
    from app.simulation import expectation as expectation_system

    pending = list(
        ctx.db.execute(
            select(Expectation)
            .where(Expectation.company_id == ctx.company.id)
            .where(Expectation.agent_id == agent_id)
            .where(Expectation.status == ExpectationStatus.PENDING)
        )
        .scalars()
        .all()
    )
    at_risk = []
    for exp in pending:
        if exp.target_day - ctx.day > horizon_days:
            continue
        actual = expectation_system._read_metric(ctx, exp.target_metric)
        if actual is not None and actual < exp.expected_value:
            at_risk.append(exp)
    return at_risk


def plan_schedule_risk(
    ctx: SimulationContext,
    plan: Plan,
) -> dict | None:
    """Assess whether an active plan is behind schedule.

    Compares actual progress against elapsed time. A plan with N total steps
    created on created_day is "on track" if progress >= elapsed / expected_duration.

    Returns a risk dict or None if the plan is not active.
    """
    if plan.status != PlanStatus.ACTIVE:
        return None
    from app.models.plan import PlanStep
    steps = list(
        ctx.db.execute(
            select(PlanStep).where(PlanStep.plan_id == plan.id).order_by(PlanStep.sequence)
        ).scalars().all()
    )
    if not steps:
        return None
    progress = plan_system.plan_progress(plan, steps)
    total_steps = len(steps)
    # Expected duration heuristic: assume ~2 days per step minimum.
    expected_duration = max(total_steps * 2, 1)
    days_elapsed = max(ctx.day - plan.created_day, 0)
    expected_progress = min(1.0, days_elapsed / expected_duration)
    behind = progress < expected_progress * 0.8  # 20% tolerance
    return {
        "plan_id": plan.id,
        "objective": plan.objective,
        "progress": round(progress, 2),
        "expected_progress": round(expected_progress, 2),
        "behind": behind,
        "current_step": plan.current_step,
        "total_steps": total_steps,
    }


def collect_adaptation_signals(
    ctx: SimulationContext,
    agent_id: int,
) -> dict:
    """Collect all adaptation signals for an agent.

    Returns a structured dict for inclusion in AgentContext.
    """
    # At-risk expectations.
    risks = at_risk_expectations(ctx, agent_id)

    # Recently missed expectations (lessons to learn from).
    missed = list(
        ctx.db.execute(
            select(Expectation)
            .where(Expectation.company_id == ctx.company.id)
            .where(Expectation.agent_id == agent_id)
            .where(Expectation.status == ExpectationStatus.MISSED)
            .order_by(Expectation.target_day.desc())
            .limit(3)
        )
        .scalars()
        .all()
    )

    # Active plans and their schedule risks.
    active_plans = list(
        ctx.db.execute(
            select(Plan)
            .where(Plan.company_id == ctx.company.id)
            .where(Plan.agent_id == agent_id)
            .where(Plan.status == PlanStatus.ACTIVE)
        )
        .scalars()
        .all()
    )
    plan_risks = []
    for p in active_plans:
        risk = plan_schedule_risk(ctx, p)
        if risk is not None:
            plan_risks.append(risk)

    return {
        "at_risk_expectations": [
            {
                "id": e.id,
                "description": e.description,
                "target_day": e.target_day,
                "target_metric": e.target_metric,
                "expected_value": e.expected_value,
            }
            for e in risks
        ],
        "recently_missed": [
            {
                "id": e.id,
                "description": e.description,
                "target_metric": e.target_metric,
                "expected_value": e.expected_value,
                "actual_value": e.actual_value,
            }
            for e in missed
        ],
        "plan_risks": plan_risks,
    }
