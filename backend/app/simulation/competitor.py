"""Competitor system: manages deterministic competitor behavior."""

from __future__ import annotations

import logging

from sqlalchemy import select

from app.enums import CompetitorStrategy, SegmentType
from app.models.competitor import Competitor
from app.models.event import Event

logger = logging.getLogger("agent_company_simulator")


# Default competitor templates.
DEFAULT_COMPETITORS: list[dict] = [
    {
        "name": "TechCorp",
        "market_share": 0.25,
        "price": 120.0,
        "product_quality": 0.6,
        "brand_strength": 0.7,
        "target_segment": SegmentType.MID_MARKET,
        "marketing_strength": 0.5,
        "sales_strength": 0.5,
        "strategy": CompetitorStrategy.BALANCED,
    },
    {
        "name": "BudgetSoft",
        "market_share": 0.20,
        "price": 60.0,
        "product_quality": 0.4,
        "brand_strength": 0.4,
        "target_segment": SegmentType.SMB,
        "marketing_strength": 0.6,
        "sales_strength": 0.3,
        "strategy": CompetitorStrategy.LOW_COST,
    },
    {
        "name": "EnterprisePlus",
        "market_share": 0.15,
        "price": 500.0,
        "product_quality": 0.8,
        "brand_strength": 0.8,
        "target_segment": SegmentType.ENTERPRISE,
        "marketing_strength": 0.4,
        "sales_strength": 0.7,
        "strategy": CompetitorStrategy.PREMIUM,
    },
]


def ensure_competitors(db) -> list[Competitor]:
    """Ensure competitors exist. Returns all competitors."""
    existing = list(db.execute(select(Competitor)).scalars().all())
    if existing:
        return existing
    competitors = [Competitor(**tpl) for tpl in DEFAULT_COMPETITORS]
    db.add_all(competitors)
    db.flush()
    return competitors


def evolve_competitors(ctx) -> list[Event]:
    """Deterministic competitor evolution. Returns events for significant actions."""
    rng = rng = ctx.rng
    competitors = list(ctx.db.execute(select(Competitor)).scalars().all())
    events: list[Event] = []

    for comp in competitors:
        # Competitors adjust based on strategy.
        if comp.strategy == CompetitorStrategy.LOW_COST:
            # Occasionally drop price.
            if rng.random() < 0.05:
                old_price = comp.price
                comp.price = max(10.0, comp.price * 0.95)
                if old_price - comp.price > 1.0:
                    events.append(Event(
                        company_id=ctx.company.id,
                        event_type="COMPETITOR_ACTION",
                        description=f"Competitor '{comp.name}' dropped price from {old_price:.0f} to {comp.price:.0f}.",
                        target_type="competitor",
                        target_id=comp.id,
                        meta={"price": comp.price, "old_price": old_price, "day": ctx.day},
                        simulation_day=ctx.day,
                    ))
        elif comp.strategy == CompetitorStrategy.GROWTH:
            # Invest in marketing.
            if rng.random() < 0.08:
                comp.marketing_strength = min(1.0, comp.marketing_strength + 0.02)
        elif comp.strategy == CompetitorStrategy.PREMIUM:
            # Improve quality.
            if rng.random() < 0.04:
                comp.product_quality = min(1.0, comp.product_quality + 0.01)

        # Small market share drift.
        share_drift = rng.uniform(-0.005, 0.005)
        comp.market_share = max(0.01, min(0.5, comp.market_share + share_drift))

    return events


def compute_competitive_pressure(ctx, target_segment: SegmentType) -> float:
    """Compute competitive pressure for a target segment (0..1)."""
    competitors = list(ctx.db.execute(select(Competitor)).scalars().all())
    if not competitors:
        return 0.0

    pressure = 0.0
    for comp in competitors:
        if comp.target_segment == target_segment:
            # Direct competitor.
            pressure += comp.market_share * 0.4
            pressure += comp.product_quality * 0.2
            pressure += comp.marketing_strength * 0.2
            pressure += comp.brand_strength * 0.2
        else:
            # Indirect pressure.
            pressure += comp.market_share * 0.1

    return min(1.0, pressure)
