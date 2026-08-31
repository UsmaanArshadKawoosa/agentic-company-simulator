"""Shared simulation domain types and constants."""

from __future__ import annotations

import random
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.company import Company


@dataclass
class SimulationContext:
    """Bundle of state passed to each simulation system per tick."""

    db: Session
    company: Company
    day: int
    rng: random.Random


def make_rng(seed: int, day: int) -> random.Random:
    """Create a deterministic RNG for a given company seed and simulation day."""
    return random.Random(seed * 10_000 + day)


# --- Economy constants ---
PROFIT_MARGIN_FLOOR: float = -1_000_000.0  # prevents absurd single-day swings


# --- Market constants ---
MARKET_MIN: float = 0.0
MARKET_MAX: float = 1.0
MARKET_DRIFT_DEMAND: float = 0.05
MARKET_DRIFT_COMPETITION: float = 0.03
MARKET_DRIFT_SENTIMENT: float = 0.04


# --- Customer constants ---
CUSTOMER_BASE_MONTHLY_VALUE: float = 1000.0
CUSTOMER_ACQUISITION_BASE_CHANCE: float = 0.15
CUSTOMER_CHURN_BASE_CHANCE: float = 0.02
