"""Sales pipeline system: manages opportunities and sales cycles."""

from __future__ import annotations

import logging

from sqlalchemy import select

from app.enums import SalesStage, SegmentType
from app.models.company import Company
from app.models.event import Event
from app.models.market_segment import MarketSegment
from app.models.sales_opportunity import SalesOpportunity
from app.simulation.domain import SimulationContext

logger = logging.getLogger("agent_company_simulator")


def create_opportunity(
    ctx: SimulationContext,
    company: Company,
    segment: SegmentType,
    name: str,
    value: float,
) -> tuple[SalesOpportunity | None, list[Event]]:
    """Create a new sales opportunity."""
    from app.simulation.segment import get_segment

    segment_obj = get_segment(ctx.db, segment)
    sales_cycle = segment_obj.sales_cycle_days if segment_obj else 14

    opportunity = SalesOpportunity(
        company_id=company.id,
        segment=segment,
        name=name,
        value=value,
        stage=SalesStage.LEAD,
        created_day=ctx.day,
        expected_close_day=ctx.day + sales_cycle,
    )
    ctx.db.add(opportunity)
    ctx.db.flush()

    event = Event(
        company_id=company.id,
        event_type="SALES_OPPORTUNITY_CREATED",
        description=f"Sales opportunity '{name}' created for {segment.value} (${value:.0f}).",
        target_type="sales_opportunity",
        target_id=opportunity.id,
        meta={"segment": segment.value, "value": value, "day": ctx.day},
        simulation_day=ctx.day,
    )
    return opportunity, [event]


def advance_pipeline(ctx: SimulationContext) -> list[Event]:
    """Advance all open opportunities through the pipeline.

    Progresses stages based on segment sales cycle and company effectiveness.
    Returns events for stage changes.
    """
    from app.simulation.segment import get_segment

    opportunities = list(
        ctx.db.execute(
            select(SalesOpportunity).where(
                SalesOpportunity.company_id == ctx.company.id,
            ).where(
                SalesOpportunity.stage.in_([SalesStage.LEAD, SalesStage.QUALIFIED, SalesStage.PROPOSAL])
            )
        ).scalars().all()
    )
    events: list[Event] = []
    company = ctx.company

    for opp in opportunities:
        segment_obj = get_segment(ctx.db, opp.segment)
        sales_cycle = segment_obj.sales_cycle_days if segment_obj else 14

        # Days since creation.
        days_active = ctx.day - opp.created_day

        # Progression probability based on company sales effectiveness and time.
        base_progress_prob = 0.15 + company.sales_effectiveness * 0.2
        time_factor = min(1.5, days_active / max(1, sales_cycle * 0.5))
        progress_prob = base_progress_prob * (0.5 + 0.5 * time_factor)

        if ctx.rng.random() > progress_prob:
            continue

        old_stage = opp.stage
        if opp.stage == SalesStage.LEAD:
            opp.stage = SalesStage.QUALIFIED
        elif opp.stage == SalesStage.QUALIFIED:
            opp.stage = SalesStage.PROPOSAL
        elif opp.stage == SalesStage.PROPOSAL:
            # Close: win or lose.
            win_prob = 0.3 + company.sales_effectiveness * 0.3 + company.brand_strength * 0.2
            if ctx.rng.random() < win_prob:
                opp.stage = SalesStage.WON
                opp.won_day = ctx.day
                events.append(Event(
                    company_id=company.id,
                    event_type="SALES_OPPORTUNITY_WON",
                    description=f"Sales opportunity '{opp.name}' WON (${opp.value:.0f}).",
                    target_type="sales_opportunity",
                    target_id=opp.id,
                    meta={"value": opp.value, "segment": opp.segment.value, "day": ctx.day},
                    simulation_day=ctx.day,
                ))
            else:
                opp.stage = SalesStage.LOST
                opp.lost_day = ctx.day
                events.append(Event(
                    company_id=company.id,
                    event_type="SALES_OPPORTUNITY_LOST",
                    description=f"Sales opportunity '{opp.name}' lost.",
                    target_type="sales_opportunity",
                    target_id=opp.id,
                    meta={"segment": opp.segment.value, "day": ctx.day},
                    simulation_day=ctx.day,
                ))

        if opp.stage != old_stage and opp.stage not in (SalesStage.WON, SalesStage.LOST):
            events.append(Event(
                company_id=company.id,
                event_type="DECISION",
                description=f"Opportunity '{opp.name}' advanced from {old_stage.value} to {opp.stage.value}.",
                target_type="sales_opportunity",
                target_id=opp.id,
                meta={"old_stage": old_stage.value, "new_stage": opp.stage.value, "day": ctx.day},
                simulation_day=ctx.day,
            ))

    return events
