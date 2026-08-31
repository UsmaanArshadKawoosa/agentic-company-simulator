"""Customer system: deterministic customer acquisition and churn."""

from __future__ import annotations

import logging

from app.enums import CustomerStatus, SegmentType
from app.models.company import Company
from app.models.customer import Customer
from app.models.event import Event
from app.simulation.domain import (
    CUSTOMER_ACQUISITION_BASE_CHANCE,
    CUSTOMER_BASE_MONTHLY_VALUE,
    CUSTOMER_CHURN_BASE_CHANCE,
    SimulationContext,
)

logger = logging.getLogger("agent_company_simulator")


def _active_customers(customers: list[Customer]) -> list[Customer]:
    return [c for c in customers if c.status == CustomerStatus.ACTIVE]


def acquisition_probability(
    ctx: SimulationContext,
    marketing_progress: float,
    product_readiness: float,
) -> float:
    """Deterministic customer acquisition probability for the day.

    Depends on:
    - marketing progress (0..1)
    - product readiness (0..100, normalized to 0..1)
    - market demand (0..1)
    - pricing competitiveness
    - brand strength
    """
    demand = max(0.0, min(1.0, ctx.company.market_demand))
    product_factor = max(0.0, min(1.0, product_readiness / 100.0))
    marketing_factor = max(0.0, min(1.0, marketing_progress))
    brand_factor = max(0.0, min(1.0, ctx.company.brand_strength))

    # Price competitiveness.
    try:
        target_segment = SegmentType(ctx.company.target_segment)
    except ValueError:
        target_segment = SegmentType.SMB

    from app.simulation.segment import get_segment
    from app.simulation.pricing import price_factor

    segment = get_segment(ctx.db, target_segment)
    price_comp = price_factor(ctx, ctx.company, segment) if segment else 0.5

    # Marketing boost from campaigns.
    from app.simulation.marketing import marketing_boost
    mkt_boost = marketing_boost(ctx, target_segment)

    base = CUSTOMER_ACQUISITION_BASE_CHANCE
    prob = base * demand * product_factor * (0.2 + 0.8 * marketing_factor)
    prob *= (0.7 + 0.3 * price_comp)
    prob *= (0.8 + 0.4 * brand_factor)
    prob *= (1.0 + mkt_boost)

    return max(0.0, min(0.8, prob))


def churn_probability(ctx: SimulationContext, product_readiness: float) -> float:
    """Deterministic daily churn probability per active customer.

    Increases with competition, low product readiness, poor sentiment,
    and low customer satisfaction (product quality vs price).
    """
    competition = max(0.0, min(1.0, ctx.company.market_competition))
    sentiment = max(0.0, min(1.0, ctx.company.market_sentiment))
    product_factor = max(0.0, min(1.0, product_readiness / 100.0))
    quality_factor = max(0.0, min(1.0, ctx.company.product_quality))

    raw = CUSTOMER_CHURN_BASE_CHANCE * (1.5 - product_factor) * (1.0 + competition) * (1.0 - 0.5 * sentiment)
    raw *= (1.0 + (1.0 - quality_factor) * 0.5)
    return max(0.0, min(0.5, raw))


def acquire_customers(
    ctx: SimulationContext,
    customers: list[Customer],
    marketing_progress: float,
    product_readiness: float,
) -> list[Customer]:
    """Attempt to acquire new customers for the day.

    Returns the list of newly created customers (not yet persisted).
    """
    prob = acquisition_probability(ctx, marketing_progress, product_readiness)
    new_customers: list[Customer] = []

    # Roll once: either 0 or 1 new customer per day in V1.
    if ctx.rng.random() < prob:
        next_number = len(customers) + 1
        value = CUSTOMER_BASE_MONTHLY_VALUE * (0.8 + 0.4 * ctx.rng.random())
        customer = Customer(
            company_id=ctx.company.id,
            name=f"Customer-{next_number}",
            status=CustomerStatus.ACTIVE,
            monthly_value=round(value, 2),
            acquired_day=ctx.day,
        )
        new_customers.append(customer)
        logger.info(
            "Customer acquired for company %s on day %d (prob=%.3f)",
            ctx.company.id,
            ctx.day,
            prob,
        )
    return new_customers


def process_churn(
    ctx: SimulationContext,
    customers: list[Customer],
    product_readiness: float,
) -> list[Event]:
    """Apply daily churn to active customers. Returns churn events."""
    prob = churn_probability(ctx, product_readiness)
    events: list[Event] = []
    for customer in customers:
        if customer.status != CustomerStatus.ACTIVE:
            continue
        if ctx.rng.random() < prob:
            customer.status = CustomerStatus.CHURNED
            customer.churn_day = ctx.day
            event = Event(
                company_id=ctx.company.id,
                event_type="CUSTOMER_CHURNED",
                description=f"Customer '{customer.name}' churned.",
                target_type="customer",
                target_id=customer.id,
                meta={"churn_probability": round(prob, 4), "day": ctx.day},
                simulation_day=ctx.day,
            )
            events.append(event)
            logger.info(
                "Customer %s churned for company %s on day %d (prob=%.3f)",
                customer.id,
                ctx.company.id,
                ctx.day,
                prob,
            )
    return events
