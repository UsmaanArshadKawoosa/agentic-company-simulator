"""Product-market fit system: deterministic PMF calculation."""

from __future__ import annotations

from app.models.company import Company
from app.models.market_segment import MarketSegment
from app.simulation.domain import SimulationContext


def compute_pmf(ctx: SimulationContext, company: Company, segment: MarketSegment) -> float:
    """Compute product-market fit (0..1) for a company in a segment.

    PMF derives from:
    - product quality
    - product readiness
    - price/value relationship
    - segment alignment
    """
    quality = max(0.0, min(1.0, company.product_quality))
    readiness = max(0.0, min(1.0, company.product_readiness / 100.0))

    # Price/value: how well does price match segment expectations?
    if segment.avg_customer_value > 0:
        price_ratio = company.price / segment.avg_customer_value
        # Ideal ratio is around 0.5-1.0 of avg customer value.
        if price_ratio <= 1.0:
            price_factor = 0.7 + 0.3 * (1.0 - price_ratio)
        else:
            price_factor = max(0.3, 1.0 - (price_ratio - 1.0) * segment.price_sensitivity)
    else:
        price_factor = 0.5

    # Weighted combination.
    pmf = (
        quality * 0.35
        + readiness * 0.30
        + price_factor * 0.25
        + segment.demand * 0.10
    )
    return max(0.0, min(1.0, pmf))
