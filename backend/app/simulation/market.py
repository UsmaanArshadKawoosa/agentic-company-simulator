"""Market system: deterministic market evolution and environmental events."""

from __future__ import annotations

import logging

from app.enums import EnvironmentEventType
from app.models.company import Company
from app.models.event import Event
from app.simulation.domain import (
    MARKET_DRIFT_COMPETITION,
    MARKET_DRIFT_DEMAND,
    MARKET_DRIFT_SENTIMENT,
    MARKET_MAX,
    MARKET_MIN,
    SimulationContext,
)

logger = logging.getLogger("agent_company_simulator")


def _clamp(value: float, lo: float = MARKET_MIN, hi: float = MARKET_MAX) -> float:
    return max(lo, min(hi, value))


def evolve_market(ctx: SimulationContext) -> dict:
    """Deterministic random-walk evolution of market conditions.

    Returns a dict describing the changes.
    """
    company = ctx.company
    rng = ctx.rng

    d_demand = rng.uniform(-MARKET_DRIFT_DEMAND, MARKET_DRIFT_DEMAND)
    d_competition = rng.uniform(-MARKET_DRIFT_COMPETITION, MARKET_DRIFT_COMPETITION)
    d_sentiment = rng.uniform(-MARKET_DRIFT_SENTIMENT, MARKET_DRIFT_SENTIMENT)

    old = {
        "demand": round(company.market_demand, 4),
        "competition": round(company.market_competition, 4),
        "sentiment": round(company.market_sentiment, 4),
    }

    company.market_demand = _clamp(company.market_demand + d_demand)
    company.market_competition = _clamp(company.market_competition + d_competition)
    company.market_sentiment = _clamp(company.market_sentiment + d_sentiment)

    new = {
        "demand": round(company.market_demand, 4),
        "competition": round(company.market_competition, 4),
        "sentiment": round(company.market_sentiment, 4),
    }
    return {"old": old, "new": new}


# Each environmental event type defines a probability weight and an apply function.
# Probabilities are relative; the system normalizes them.


def _apply_market_boom(company: Company) -> str:
    company.market_demand = _clamp(company.market_demand + 0.2)
    company.market_sentiment = _clamp(company.market_sentiment + 0.1)
    return "Market demand surged (+0.20) and sentiment improved (+0.10)."


def _apply_market_downturn(company: Company) -> str:
    company.market_demand = _clamp(company.market_demand - 0.2)
    company.market_sentiment = _clamp(company.market_sentiment - 0.1)
    return "Market demand dropped (-0.20) and sentiment worsened (-0.10)."


def _apply_competitor_launch(company: Company) -> str:
    company.market_competition = _clamp(company.market_competition + 0.15)
    company.market_sentiment = _clamp(company.market_sentiment - 0.05)
    return "A competitor launched (+0.15 competition, -0.05 sentiment)."


def _apply_customer_surge(company: Company) -> str:
    company.market_demand = _clamp(company.market_demand + 0.15)
    return "Customer interest surged (+0.15 demand)."


def _apply_customer_decline(company: Company) -> str:
    company.market_demand = _clamp(company.market_demand - 0.15)
    return "Customer interest declined (-0.15 demand)."


def _apply_infrastructure_cost_increase(company: Company) -> str:
    before = company.infrastructure_cost
    company.infrastructure_cost = round(company.infrastructure_cost * 1.10, 2)
    delta = company.infrastructure_cost - before
    return f"Infrastructure costs increased by 10% (+{delta:.2f}/day)."


def _apply_competitor_price_drop(company: Company) -> str:
    company.market_competition = _clamp(company.market_competition + 0.1)
    company.market_sentiment = _clamp(company.market_sentiment - 0.05)
    return "A competitor dropped prices (+0.10 competition, -0.05 sentiment)."


def _apply_market_expansion(company: Company) -> str:
    company.market_demand = _clamp(company.market_demand + 0.2)
    return "Market expanded: more customers entering (+0.20 demand)."


def _apply_market_contraction(company: Company) -> str:
    company.market_demand = _clamp(company.market_demand - 0.2)
    return "Market contracted: fewer customers (-0.20 demand)."


def _apply_customer_trend_shift(company: Company) -> str:
    company.market_sentiment = _clamp(company.market_sentiment + 0.1)
    return "Customer preferences shifted in your favor (+0.10 sentiment)."


def _apply_regulatory_pressure(company: Company) -> str:
    company.infrastructure_cost = round(company.infrastructure_cost * 1.05, 2)
    return "Regulatory compliance costs increased (+5% infrastructure)."


def _apply_technology_shift(company: Company) -> str:
    company.market_demand = _clamp(company.market_demand + 0.1)
    company.market_competition = _clamp(company.market_competition + 0.05)
    return "Technology shift creates opportunity (+0.10 demand, +0.05 competition)."


_EVENT_TABLE: list[tuple[EnvironmentEventType, float, callable]] = [
    (EnvironmentEventType.MARKET_BOOM, 0.02, _apply_market_boom),
    (EnvironmentEventType.MARKET_DOWNTURN, 0.02, _apply_market_downturn),
    (EnvironmentEventType.COMPETITOR_LAUNCH, 0.015, _apply_competitor_launch),
    (EnvironmentEventType.CUSTOMER_SURGE, 0.02, _apply_customer_surge),
    (EnvironmentEventType.CUSTOMER_DECLINE, 0.02, _apply_customer_decline),
    (EnvironmentEventType.INFRASTRUCTURE_COST_INCREASE, 0.01, _apply_infrastructure_cost_increase),
    (EnvironmentEventType.COMPETITOR_PRICE_DROP, 0.015, _apply_competitor_price_drop),
    (EnvironmentEventType.MARKET_EXPANSION, 0.01, _apply_market_expansion),
    (EnvironmentEventType.MARKET_CONTRACTION, 0.01, _apply_market_contraction),
    (EnvironmentEventType.CUSTOMER_TREND_SHIFT, 0.01, _apply_customer_trend_shift),
    (EnvironmentEventType.REGULATORY_PRESSURE, 0.005, _apply_regulatory_pressure),
    (EnvironmentEventType.TECHNOLOGY_SHIFT, 0.01, _apply_technology_shift),
]

# Probabilities are evaluated independently per event type per day.
# This means multiple environmental events may occur on the same day,
# and the effective per-day event rate is the sum of the individual probabilities.


def generate_environmental_events(ctx: SimulationContext) -> list[Event]:
    """Possibly generate environmental events for the day.

    Each event type in ``_EVENT_TABLE`` has an independent probability of
    occurring.  Probabilities are evaluated separately, so multiple distinct
    event types may trigger on the same day.  Uses the seeded RNG so
    outcomes are reproducible.
    """
    events: list[Event] = []
    for event_type, probability, apply_fn in _EVENT_TABLE:
        if ctx.rng.random() < probability:
            description = apply_fn(ctx.company)
            event = Event(
                company_id=ctx.company.id,
                event_type="ENVIRONMENTAL_EVENT",
                description=description,
                target_type="market",
                meta={
                    "environment_event_type": event_type.value,
                    "day": ctx.day,
                },
                simulation_day=ctx.day,
            )
            events.append(event)
            logger.info(
                "Environmental event for company %s on day %d: %s",
                ctx.company.id,
                ctx.day,
                event_type.value,
            )
    return events
