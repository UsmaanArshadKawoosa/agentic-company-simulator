"""Investor system: deterministic investor generation and evaluation."""

from __future__ import annotations

import logging

from sqlalchemy import select

from app.enums import InvestorStage
from app.models.investor import Investor
from app.simulation.domain import SimulationContext

logger = logging.getLogger("agent_company_simulator")

# --- Deterministic investor generation ---

_INVESTOR_NAMES = [
    "Apex Ventures",
    "Borealis Capital",
    "Catalyst Fund",
    "Delta Partners",
    "Evergreen Investments",
    "Forge Capital",
    "Genesis Fund",
    "Horizon Ventures",
    "Ironwood Capital",
    "Jade Street Partners",
    "Keystone Fund",
    "Lumen Ventures",
    "Meridian Capital",
    "Nexus Partners",
    "Oak Tree Ventures",
    "Pinnacle Fund",
    "Quantum Capital",
    "Redwood Partners",
    "Summit Ventures",
    "Trident Fund",
]

_SECTOR_PREFERENCES = [
    "SaaS",
    "FinTech",
    "HealthTech",
    "EdTech",
    "CleanTech",
    "E-commerce",
    "AI/ML",
    "Cybersecurity",
    "DevTools",
    "Marketplace",
]


def generate_investors(ctx: SimulationContext, count: int = 5) -> list[Investor]:
    """Generate deterministic investors for the company.

    Uses company seed + day for reproducibility.
    """
    rng = ctx.rng
    company = ctx.company
    investors: list[Investor] = []

    stages = [InvestorStage.PRE_SEED, InvestorStage.SEED, InvestorStage.SERIES_A, InvestorStage.SERIES_B]

    for i in range(count):
        name = _INVESTOR_NAMES[rng.randint(0, len(_INVESTOR_NAMES) - 1)]
        stage = stages[rng.randint(0, len(stages) - 1)]

        # Check size based on stage
        if stage == InvestorStage.PRE_SEED:
            check_min = 50_000.0
            check_max = 500_000.0
        elif stage == InvestorStage.SEED:
            check_min = 500_000.0
            check_max = 3_000_000.0
        elif stage == InvestorStage.SERIES_A:
            check_min = 3_000_000.0
            check_max = 15_000_000.0
        else:
            check_min = 15_000_000.0
            check_max = 100_000_000.0

        check_size_min = round(check_min + rng.random() * (check_max - check_min) * 0.3, 2)
        check_size_max = round(check_size_min + rng.random() * (check_max - check_min) * 0.7 + 100_000.0, 2)

        risk_tolerance = round(0.2 + rng.random() * 0.6, 2)
        sector = _SECTOR_PREFERENCES[rng.randint(0, len(_SECTOR_PREFERENCES) - 1)]
        ownership_expectation = round(0.1 + rng.random() * 0.4, 2)
        reputation = round(0.3 + rng.random() * 0.7, 2)

        investor = Investor(
            company_id=company.id,
            name=f"{name} {i+1}",
            preferred_stage=stage,
            check_size_min=check_size_min,
            check_size_max=check_size_max,
            risk_tolerance=risk_tolerance,
            sector_preference=sector,
            ownership_expectation=ownership_expectation,
            reputation=reputation,
            interest_score=0.0,
        )
        ctx.db.add(investor)
        investors.append(investor)

    return investors


def evaluate_investor_interest(ctx: SimulationContext, investor: Investor, funding_round_stage: InvestorStage) -> float:
    """Calculate deterministic interest score for an investor.

    Factors:
    - Stage match
    - Company financial health
    - Valuation alignment
    - Risk tolerance match
    """
    from app.simulation.financial_health import calculate_financial_health_score
    from app.simulation.valuation import calculate_valuation

    rng = ctx.rng
    company = ctx.company

    # Stage match (0.0 - 1.0)
    stage_match = 1.0 if investor.preferred_stage == funding_round_stage else 0.3

    # Financial health (0.0 - 1.0)
    health_score = calculate_financial_health_score(company)

    # Valuation alignment
    valuation_data = calculate_valuation(ctx)
    company_valuation = valuation_data["valuation"]
    check_size_alignment = 1.0
    if company_valuation > 0:
        check_ratio = investor.check_size_min / company_valuation
        if check_ratio > 0.5:
            check_size_alignment = 0.5
        elif check_ratio > 0.2:
            check_size_alignment = 0.8
        else:
            check_size_alignment = 1.0

    # Risk tolerance match (higher health = lower risk tolerance needed)
    risk_match = 1.0 - abs(investor.risk_tolerance - (1.0 - health_score))

    # Deterministic noise
    noise = (rng.random() - 0.5) * 0.2

    interest = (
        stage_match * 0.3
        + health_score * 0.3
        + check_size_alignment * 0.2
        + max(0.0, risk_match) * 0.2
        + noise
    )

    return max(0.0, min(1.0, round(interest, 4)))


def get_or_generate_investors(ctx: SimulationContext, count: int = 5) -> list[Investor]:
    """Get existing investors or generate new ones if none exist."""
    existing = list(
        ctx.db.execute(
            select(Investor).where(Investor.company_id == ctx.company.id)
        )
        .scalars()
        .all()
    )
    if existing:
        return existing
    return generate_investors(ctx, count)
