"""Financial health system: deterministic metrics for company financial state."""

from __future__ import annotations

import logging
import math

from app.enums import FinancialHealth
from app.simulation.domain import SimulationContext

logger = logging.getLogger("agent_company_simulator")

# --- Constants ---
RUNWAY_SAFE_DAYS: float = 180.0
RUNWAY_WARNING_DAYS: float = 90.0
RUNWAY_CRITICAL_DAYS: float = 30.0

HEALTH_SCORE_HEALTHY: float = 0.7
HEALTH_SCORE_AT_RISK: float = 0.4
HEALTH_SCORE_CRITICAL: float = 0.2


def _safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    if denominator == 0:
        return default
    return numerator / denominator


def calculate_burn(company) -> float:
    """Daily burn = expenses - revenue. Returns 0 if revenue >= expenses."""
    daily_expenses = company.expenses / max(1, company.current_day)
    daily_revenue = company.revenue / max(1, company.current_day)
    burn = daily_expenses - daily_revenue
    return max(0.0, burn)


def calculate_runway(company) -> float:
    """Days of runway based on current cash and burn rate."""
    if company.cash <= 0:
        return 0.0
    burn = calculate_burn(company)
    if burn <= 0:
        return float("inf")
    return company.cash / burn


def calculate_revenue_growth(company) -> float:
    """Revenue growth rate (per day). Simplified as total revenue / days."""
    if company.current_day <= 1:
        return 0.0
    return company.revenue / (company.current_day - 1)


def calculate_expense_growth(company) -> float:
    """Expense growth rate (per day). Simplified as total expenses / days."""
    if company.current_day <= 1:
        return 0.0
    return company.expenses / (company.current_day - 1)


def calculate_cash_trend(company) -> float:
    """Cash trend: positive if cash is growing, negative if shrinking.
    Based on recent profit trend."""
    if company.current_day <= 1:
        return 0.0
    return (company.revenue - company.expenses) / company.current_day


def calculate_financial_health_score(company) -> float:
    """Deterministic financial health score in [0, 1].

    Factors:
    - Cash adequacy (relative to expenses)
    - Runway
    - Revenue trend
    - Burn rate sustainability
    """
    if company.current_day <= 0:
        return 0.0

    # Cash adequacy: cash / (daily expenses * 30) -> 1 month buffer
    daily_expenses = company.expenses / max(1, company.current_day)
    cash_adequacy = min(1.0, company.cash / max(1.0, daily_expenses * 30))

    # Runway score
    runway = calculate_runway(company)
    if runway == float("inf"):
        runway_score = 1.0
    elif runway <= 0:
        runway_score = 0.0
    else:
        runway_score = min(1.0, runway / RUNWAY_SAFE_DAYS)

    # Revenue trend score
    revenue_growth = calculate_revenue_growth(company)
    revenue_score = min(1.0, max(0.0, revenue_growth / 1000.0))

    # Burn sustainability
    burn = calculate_burn(company)
    if burn <= 0:
        burn_score = 1.0
    else:
        burn_score = max(0.0, 1.0 - (burn / max(1.0, daily_expenses)))

    # Weighted combination
    score = (
        cash_adequacy * 0.3
        + runway_score * 0.3
        + revenue_score * 0.2
        + burn_score * 0.2
    )

    return max(0.0, min(1.0, score))


def determine_financial_health(company) -> FinancialHealth:
    """Determine financial health state from score."""
    score = calculate_financial_health_score(company)

    if company.cash <= 0:
        return FinancialHealth.FAILED

    if score >= HEALTH_SCORE_HEALTHY:
        return FinancialHealth.HEALTHY
    if score >= HEALTH_SCORE_AT_RISK:
        return FinancialHealth.AT_RISK
    if score >= HEALTH_SCORE_CRITICAL:
        return FinancialHealth.CRITICAL
    return FinancialHealth.FAILED


def get_financial_metrics(company) -> dict:
    """Return all deterministic financial metrics for a company."""
    burn = calculate_burn(company)
    runway = calculate_runway(company)
    health_score = calculate_financial_health_score(company)
    health = determine_financial_health(company)

    return {
        "cash": round(company.cash, 2),
        "revenue": round(company.revenue, 2),
        "expenses": round(company.expenses, 2),
        "profit": round(company.revenue - company.expenses, 2),
        "daily_burn": round(burn, 2),
        "runway_days": round(runway, 1) if runway != float("inf") else None,
        "revenue_growth": round(calculate_revenue_growth(company), 4),
        "expense_growth": round(calculate_expense_growth(company), 4),
        "cash_trend": round(calculate_cash_trend(company), 4),
        "financial_health_score": round(health_score, 4),
        "financial_health": health.value,
        "financial_risk_level": _risk_level(health_score, runway),
    }


def _risk_level(health_score: float, runway: float) -> str:
    if runway == float("inf"):
        return "LOW"
    if runway <= 0:
        return "CRITICAL"
    if health_score < HEALTH_SCORE_CRITICAL:
        return "HIGH"
    if health_score < HEALTH_SCORE_AT_RISK:
        return "MEDIUM"
    return "LOW"
