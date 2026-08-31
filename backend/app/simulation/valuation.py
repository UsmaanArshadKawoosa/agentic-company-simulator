"""Valuation system: deterministic company valuation model."""

from __future__ import annotations

import logging

from sqlalchemy import select

from app.models.customer import Customer as CustomerModel
from app.simulation.domain import SimulationContext

logger = logging.getLogger("agent_company_simulator")

# --- Valuation constants ---
BASE_MULTIPLE: float = 2.0
REVENUE_MULTIPLIER: float = 3.0
GROWTH_MULTIPLIER: float = 500.0
READINESS_MULTIPLIER: float = 1_000_000.0
QUALITY_MULTIPLIER: float = 500_000.0
MARKET_SHARE_MULTIPLIER: float = 2_000_000.0
CUSTOMER_MULTIPLIER: float = 10_000.0
RUNWAY_PENALTY: float = 0.5
MIN_VALUATION: float = 100_000.0
MAX_VALUATION: float = 100_000_000.0


def calculate_valuation(ctx: SimulationContext) -> dict:
    """Calculate deterministic company valuation.

    Formula components:
    - Base value
    - Revenue multiple
    - Growth multiple
    - Product readiness bonus
    - Product quality bonus
    - Market share bonus
    - Customer count bonus
    - Runway penalty (low runway reduces valuation)
    """
    company = ctx.company

    # Annualized revenue
    annual_revenue = company.revenue / max(1, company.current_day) * 365

    # Growth factor
    revenue_growth = company.revenue / max(1, company.current_day)
    growth_factor = revenue_growth * GROWTH_MULTIPLIER

    # Product factors
    readiness_bonus = company.product_readiness * READINESS_MULTIPLIER
    quality_bonus = company.product_quality * QUALITY_MULTIPLIER

    # Market factors
    market_share_bonus = company.market_share_cache * MARKET_SHARE_MULTIPLIER

    # Customer count
    customers = list(
        ctx.db.execute(
            select(CustomerModel).where(CustomerModel.company_id == company.id)
        )
        .scalars()
        .all()
    )
    active_customers = [c for c in customers if c.status.value == "ACTIVE"]
    customer_bonus = len(active_customers) * CUSTOMER_MULTIPLIER

    # Runway factor
    from app.simulation.financial_health import calculate_runway
    runway = calculate_runway(company)
    if runway < 30:
        runway_factor = RUNWAY_PENALTY
    elif runway < 90:
        runway_factor = 0.8
    else:
        runway_factor = 1.0

    # Calculate valuation
    valuation = (
        BASE_MULTIPLE
        + annual_revenue * REVENUE_MULTIPLIER
        + growth_factor
        + readiness_bonus
        + quality_bonus
        + market_share_bonus
        + customer_bonus
    ) * runway_factor

    valuation = max(MIN_VALUATION, min(MAX_VALUATION, valuation))

    return {
        "valuation": round(valuation, 2),
        "annual_revenue": round(annual_revenue, 2),
        "growth_factor": round(growth_factor, 2),
        "readiness_bonus": round(readiness_bonus, 2),
        "quality_bonus": round(quality_bonus, 2),
        "market_share_bonus": round(market_share_bonus, 2),
        "customer_bonus": round(customer_bonus, 2),
        "runway_factor": round(runway_factor, 2),
    }
