"""Expectation system: structured outcome tracking.

Agents form expectations such as "product readiness will reach 0.5 by day 10".
The simulation evaluates these against actual results deterministically:

    actual >= expected         -> MET
    actual >= 0.5 * expected   -> PARTIAL
    otherwise                  -> MISSED
    not yet at target_day      -> PENDING
"""

from __future__ import annotations

import logging

from sqlalchemy import select

from app.enums import ExpectationStatus, EventType
from app.models.event import Event
from app.models.expectation import Expectation
from app.simulation.domain import SimulationContext

logger = logging.getLogger("agent_company_simulator")

# Metric name -> callable that reads the current value from context.
# Each callable receives (ctx) and returns a float.
METRIC_READERS: dict[str, "callable"] = {}


def register_metric(name: str):
    """Decorator to register a metric reader function."""
    def decorator(fn):
        METRIC_READERS[name] = fn
        return fn
    return decorator


@register_metric("product_readiness")
def _read_product_readiness(ctx: SimulationContext) -> float:
    return ctx.company.product_readiness


@register_metric("product_quality")
def _read_product_quality(ctx: SimulationContext) -> float:
    return ctx.company.product_quality


@register_metric("cash")
def _read_cash(ctx: SimulationContext) -> float:
    return ctx.company.cash


@register_metric("revenue")
def _read_revenue(ctx: SimulationContext) -> float:
    return ctx.company.revenue


@register_metric("technical_debt")
def _read_technical_debt(ctx: SimulationContext) -> float:
    return ctx.company.technical_debt


@register_metric("customer_count")
def _read_customer_count(ctx: SimulationContext) -> float:
    from app.models.customer import Customer as CustomerModel
    return float(
        ctx.db.execute(
            select(CustomerModel).where(CustomerModel.company_id == ctx.company.id)
        ).scalars().all().__len__()
    )


def create_expectation(
    ctx: SimulationContext,
    agent_id: int,
    description: str,
    target_day: int,
    target_metric: str,
    expected_value: float,
    linked_decision_id: int | None = None,
) -> Expectation:
    """Persist a structured expectation."""
    exp = Expectation(
        company_id=ctx.company.id,
        agent_id=agent_id,
        description=description,
        target_day=target_day,
        target_metric=target_metric,
        expected_value=expected_value,
        status=ExpectationStatus.PENDING,
        linked_decision_id=linked_decision_id,
    )
    ctx.db.add(exp)
    ctx.db.flush()
    return exp


def _read_metric(ctx: SimulationContext, metric: str) -> float | None:
    reader = METRIC_READERS.get(metric)
    if reader is None:
        return None
    try:
        return float(reader(ctx))
    except Exception:
        return None


def evaluate_expectations(ctx: SimulationContext) -> list[Event]:
    """Evaluate all pending expectations against current reality.

    An expectation is evaluated only when current_day >= target_day.
    Returns events for newly resolved expectations.
    """
    pending = list(
        ctx.db.execute(
            select(Expectation)
            .where(Expectation.company_id == ctx.company.id)
            .where(Expectation.status == ExpectationStatus.PENDING)
        )
        .scalars()
        .all()
    )
    events: list[Event] = []
    for exp in pending:
        if ctx.day < exp.target_day:
            continue
        actual = _read_metric(ctx, exp.target_metric)
        if actual is None:
            continue
        exp.actual_value = round(actual, 4)
        if actual >= exp.expected_value:
            exp.status = ExpectationStatus.MET
            event_type = EventType.EXPECTATION_MET
            desc = (
                f"Expectation met: {exp.description} "
                f"(expected {exp.expected_value:.2f}, got {actual:.2f})."
            )
        elif actual >= 0.5 * exp.expected_value:
            exp.status = ExpectationStatus.PARTIAL
            event_type = EventType.EXPECTATION_MET
            desc = (
                f"Expectation partially met: {exp.description} "
                f"(expected {exp.expected_value:.2f}, got {actual:.2f})."
            )
        else:
            exp.status = ExpectationStatus.MISSED
            event_type = EventType.EXPECTATION_MISSED
            desc = (
                f"Expectation missed: {exp.description} "
                f"(expected {exp.expected_value:.2f}, got {actual:.2f})."
            )
        events.append(
            Event(
                company_id=ctx.company.id,
                actor_id=exp.agent_id,
                event_type=event_type,
                description=desc,
                target_type="expectation",
                target_id=exp.id,
                meta={
                    "expectation_id": exp.id,
                    "metric": exp.target_metric,
                    "expected": exp.expected_value,
                    "actual": exp.actual_value,
                    "status": exp.status.value,
                    "day": ctx.day,
                },
                simulation_day=ctx.day,
            )
        )
    ctx.db.flush()
    return events
