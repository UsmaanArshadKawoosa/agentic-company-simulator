"""Fundraising system: funding rounds and pipeline management."""

from __future__ import annotations

import logging

from sqlalchemy import select

from app.enums import FinancialHealth, FundingRoundStatus, InvestorStage
from app.models.funding_round import FundingRound
from app.models.fundraising_pipeline import FundraisingPipeline
from app.models.investor import Investor
from app.simulation.domain import SimulationContext
from app.simulation.financial_health import determine_financial_health
from app.simulation.investors import evaluate_investor_interest

logger = logging.getLogger("agent_company_simulator")

# --- Funding round creation ---


def create_funding_round(
    ctx: SimulationContext,
    stage: InvestorStage,
    amount_requested: float,
    valuation: float,
) -> FundingRound | None:
    """Create a new funding round."""
    if amount_requested <= 0 or valuation <= 0:
        return None

    round_stage = FundingRound(
        company_id=ctx.company.id,
        round_stage=stage,
        amount_requested=round(amount_requested, 2),
        amount_raised=0.0,
        valuation=round(valuation, 2),
        pre_money_valuation=round(valuation, 2),
        post_money_valuation=round(valuation, 2),
        equity_sold=0.0,
        status="OPEN",
        day_opened=ctx.day,
    )
    ctx.db.add(round_stage)
    ctx.db.flush()
    return round_stage


def close_funding_round(
    ctx: SimulationContext,
    round_stage: FundingRound,
    amount_raised: float,
    investor: Investor | None = None,
) -> FundingRound:
    """Close a funding round with the raised amount."""
    round_stage.amount_raised = round(amount_raised, 2)
    round_stage.day_closed = ctx.day

    if amount_raised > 0 and round_stage.valuation > 0:
        # Calculate equity sold
        post_money = round_stage.valuation + amount_raised
        equity_sold = amount_raised / post_money if post_money > 0 else 0.0
        round_stage.equity_sold = round(min(equity_sold, 0.49), 4)  # Cap at 49% per round
        round_stage.post_money_valuation = round(post_money, 2)

    if amount_raised >= round_stage.amount_requested * 0.5:
        round_stage.status = "CLOSED"
    else:
        round_stage.status = "FAILED"

    # Update company cash
    ctx.company.cash += round_stage.amount_raised

    ctx.db.flush()
    return round_stage


# --- Pipeline management ---


def advance_pipeline(ctx: SimulationContext, pipeline_id: int) -> FundraisingPipeline | None:
    """Advance a pipeline entry to the next stage."""
    pipeline = ctx.db.get(FundraisingPipeline, pipeline_id)
    if pipeline is None or pipeline.company_id != ctx.company.id:
        return None

    progression = {
        FundingRoundStatus.DISCOVERED: FundingRoundStatus.CONTACTED,
        FundingRoundStatus.CONTACTED: FundingRoundStatus.INTERESTED,
        FundingRoundStatus.INTERESTED: FundingRoundStatus.DUE_DILIGENCE,
        FundingRoundStatus.DUE_DILIGENCE: FundingRoundStatus.OFFERED,
        FundingRoundStatus.OFFERED: None,  # Terminal - either INVESTED or PASSED
    }

    next_status = progression.get(pipeline.status)
    if next_status is None:
        return pipeline

    pipeline.status = next_status
    pipeline.day_updated = ctx.day

    # If advancing to DUE_DILIGENCE, evaluate investor interest
    if next_status == FundingRoundStatus.DUE_DILIGENCE and pipeline.investor_id is not None:
        investor = ctx.db.get(Investor, pipeline.investor_id)
        if investor:
            pipeline.interest_score = evaluate_investor_interest(
                ctx, investor, pipeline.stage
            )

    ctx.db.flush()
    return pipeline


def make_investment_decision(
    ctx: SimulationContext, pipeline_id: int, invested: bool, amount: float = 0.0
) -> FundraisingPipeline | None:
    """Make final investment decision for a pipeline entry."""
    pipeline = ctx.db.get(FundraisingPipeline, pipeline_id)
    if pipeline is None or pipeline.company_id != ctx.company.id:
        return None
    if pipeline.status != FundingRoundStatus.OFFERED:
        return None

    if invested and amount > 0:
        pipeline.status = FundingRoundStatus.INVESTED
        # Find or create funding round
        round_stage = _get_or_create_active_round(ctx, pipeline.stage)
        if round_stage:
            close_funding_round(ctx, round_stage, amount, pipeline.investor)
    else:
        pipeline.status = FundingRoundStatus.PASSED

    pipeline.day_updated = ctx.day
    ctx.db.flush()
    return pipeline


def _get_or_create_active_round(ctx: SimulationContext, stage: InvestorStage) -> FundingRound | None:
    """Get active funding round for stage or create one."""
    existing = list(
        ctx.db.execute(
            select(FundingRound).where(
                FundingRound.company_id == ctx.company.id,
                FundingRound.round_stage == stage,
                FundingRound.status == "OPEN",
            )
        )
        .scalars()
        .all()
    )
    if existing:
        return existing[0]

    valuation = 1_000_000.0  # Default valuation
    return create_funding_round(ctx, stage, 1_000_000.0, valuation)


# --- Pipeline update ---


def update_pipeline(ctx: SimulationContext) -> list:
    """Update fundraising pipeline based on company state."""
    pipelines = list(
        ctx.db.execute(
            select(FundraisingPipeline).where(
                FundraisingPipeline.company_id == ctx.company.id
            )
        )
        .scalars()
        .all()
    )
    events = []

    for pipeline in pipelines:
        # If company is in critical state, investors may pass
        if pipeline.status == FundingRoundStatus.DUE_DILIGENCE:
            health = determine_financial_health(ctx.company)
            if health == FinancialHealth.CRITICAL:
                pipeline.status = FundingRoundStatus.PASSED
                pipeline.day_updated = ctx.day
                ctx.db.flush()

    return events
