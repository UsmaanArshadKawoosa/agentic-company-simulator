"""Market segment system: manages market segments and their deterministic parameters."""

from __future__ import annotations

import logging

from sqlalchemy import select

from app.enums import SegmentType
from app.models.market_segment import MarketSegment

logger = logging.getLogger("agent_company_simulator")


# Default segment templates used to initialize segments if none exist.
DEFAULT_SEGMENTS: list[dict] = [
    {
        "name": "SMB",
        "segment_type": SegmentType.SMB,
        "size": 5000.0,
        "demand": 0.6,
        "price_sensitivity": 0.8,
        "growth_rate": 0.02,
        "competition_intensity": 0.6,
        "avg_customer_value": 500.0,
        "sales_cycle_days": 3,
    },
    {
        "name": "MID_MARKET",
        "segment_type": SegmentType.MID_MARKET,
        "size": 2000.0,
        "demand": 0.5,
        "price_sensitivity": 0.5,
        "growth_rate": 0.015,
        "competition_intensity": 0.5,
        "avg_customer_value": 2000.0,
        "sales_cycle_days": 14,
    },
    {
        "name": "ENTERPRISE",
        "segment_type": SegmentType.ENTERPRISE,
        "size": 500.0,
        "demand": 0.4,
        "price_sensitivity": 0.2,
        "growth_rate": 0.01,
        "competition_intensity": 0.4,
        "avg_customer_value": 10000.0,
        "sales_cycle_days": 30,
    },
    {
        "name": "STARTUP",
        "segment_type": SegmentType.STARTUP,
        "size": 3000.0,
        "demand": 0.7,
        "price_sensitivity": 0.9,
        "growth_rate": 0.03,
        "competition_intensity": 0.7,
        "avg_customer_value": 200.0,
        "sales_cycle_days": 2,
    },
]


def ensure_segments(db) -> list[MarketSegment]:
    """Ensure market segments exist in the database. Returns all segments."""
    existing = list(db.execute(select(MarketSegment)).scalars().all())
    if existing:
        return existing
    segments = [MarketSegment(**tpl) for tpl in DEFAULT_SEGMENTS]
    db.add_all(segments)
    db.flush()
    return segments


def get_segment(db, segment_type: SegmentType) -> MarketSegment | None:
    """Get a market segment by type."""
    return db.execute(
        select(MarketSegment).where(MarketSegment.segment_type == segment_type)
    ).scalars().first()


def evolve_segments(db, rng) -> None:
    """Deterministic evolution of segment demand and competition."""
    segments = list(db.execute(select(MarketSegment)).scalars().all())
    for seg in segments:
        # Small random walk on demand.
        drift = rng.uniform(-0.02, 0.02)
        seg.demand = max(0.1, min(1.0, seg.demand + drift + seg.growth_rate * 0.1))
        # Competition drifts slightly.
        comp_drift = rng.uniform(-0.01, 0.01)
        seg.competition_intensity = max(0.1, min(0.9, seg.competition_intensity + comp_drift))
