"""Strategy system: manages company positioning, market share, and customer satisfaction."""

from __future__ import annotations

import logging

from sqlalchemy import select

from app.enums import SegmentType
from app.models.company import Company
from app.models.customer import Customer
from app.models.market_segment import MarketSegment
from app.simulation.domain import SimulationContext

logger = logging.getLogger("agent_company_simulator")


def compute_market_share(
    ctx: SimulationContext,
    company: Company,
    segment: MarketSegment,
) -> float:
    """Compute company market share in a segment (0..1).

    Based on PMF, price competitiveness, brand strength, marketing, and competition.
    """
    from app.simulation.pmf import compute_pmf
    from app.simulation.pricing import price_competitiveness_vs_competitors
    from app.simulation.competitor import compute_competitive_pressure

    pmf = compute_pmf(ctx, company, segment)
    price_comp = price_competitiveness_vs_competitors(ctx, company, segment.segment_type)
    comp_pressure = compute_competitive_pressure(ctx, segment.segment_type)

    # Base share from PMF and price.
    raw_share = pmf * 0.4 + price_comp * 0.3 + company.brand_strength * 0.2 + company.marketing_effectiveness * 0.1

    # Competition reduces share.
    share = raw_share * (1.0 - comp_pressure * 0.5)

    # Bounded and gradual (share can't exceed remaining market).
    remaining = 1.0 - sum(
        c.market_share for c in ctx.db.execute(
            select(__import__("app.models.competitor", fromlist=["Competitor"]).Competitor).where(
                __import__("app.models.competitor", fromlist=["Competitor"]).Competitor.target_segment == segment.segment_type
            )
        ).scalars().all()
    )
    return max(0.0, min(max(0.0, remaining), share))


def compute_customer_satisfaction(
    ctx: SimulationContext,
    company: Company,
    segment: MarketSegment,
) -> float:
    """Compute customer satisfaction (0..1) based on product and price/value."""
    quality = max(0.0, min(1.0, company.product_quality))
    readiness = max(0.0, min(1.0, company.product_readiness / 100.0))

    # Price/value: lower price vs value = higher satisfaction.
    if segment.avg_customer_value > 0:
        price_ratio = company.price / segment.avg_customer_value
        if price_ratio <= 1.0:
            price_sat = 0.8 + 0.2 * (1.0 - price_ratio)
        else:
            price_sat = max(0.3, 1.0 - (price_ratio - 1.0) * segment.price_sensitivity * 0.5)
    else:
        price_sat = 0.5

    satisfaction = quality * 0.4 + readiness * 0.3 + price_sat * 0.3
    return max(0.0, min(1.0, satisfaction))


def update_market_share_cache(ctx: SimulationContext) -> None:
    """Update the company's cached market share for its target segment."""
    from app.simulation.segment import get_segment

    try:
        target = SegmentType(ctx.company.target_segment)
    except ValueError:
        target = SegmentType.SMB

    segment = get_segment(ctx.db, target)
    if segment is None:
        return

    share = compute_market_share(ctx, ctx.company, segment)
    # Gradual transition.
    old_share = ctx.company.market_share_cache
    ctx.company.market_share_cache = old_share + (share - old_share) * 0.2
