"""Pricing system: deterministic pricing effects on business outcomes."""

from __future__ import annotations

from app.enums import SegmentType
from app.models.company import Company
from app.models.market_segment import MarketSegment
from app.simulation.domain import SimulationContext


def price_factor(ctx: SimulationContext, company: Company, segment: MarketSegment) -> float:
    """Compute a price competitiveness factor (0..1+).

    Higher when company price is competitive vs segment expectations.
    Lower when company price is too high for the segment.
    """
    if segment.avg_customer_value <= 0:
        return 0.5

    # Ratio of company price to segment average value.
    ratio = company.price / segment.avg_customer_value

    # Segment price sensitivity determines how much ratio matters.
    sensitivity = segment.price_sensitivity

    # If ratio < 1 (price below avg), factor > 1 (advantage).
    # If ratio > 1 (price above avg), factor < 1 (disadvantage).
    if ratio <= 1.0:
        # Cheaper than average: advantage scales with sensitivity.
        advantage = (1.0 - ratio) * sensitivity
        return min(1.5, 1.0 + advantage)
    else:
        # More expensive: penalty scales with sensitivity.
        penalty = (ratio - 1.0) * sensitivity
        return max(0.1, 1.0 - penalty)


def price_competitiveness_vs_competitors(
    ctx: SimulationContext, company: Company, segment_type: SegmentType
) -> float:
    """Compare company price to competitors in the same segment (0..1)."""
    from sqlalchemy import select
    from app.models.competitor import Competitor

    competitors = list(
        ctx.db.execute(
            select(Competitor).where(Competitor.target_segment == segment_type)
        ).scalars().all()
    )
    if not competitors:
        return 0.5

    avg_competitor_price = sum(c.price for c in competitors) / len(competitors)
    if avg_competitor_price <= 0:
        return 0.5

    ratio = company.price / avg_competitor_price
    if ratio <= 1.0:
        return min(1.0, 0.5 + (1.0 - ratio) * 0.5)
    else:
        return max(0.1, 0.5 - (ratio - 1.0) * 0.3)
