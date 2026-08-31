"""Marketing campaign system: manages campaigns and their effects."""

from __future__ import annotations

import logging

from sqlalchemy import select

from app.enums import CampaignStatus, SegmentType
from app.models.campaign import Campaign
from app.models.company import Company
from app.models.event import Event
from app.simulation.domain import SimulationContext

logger = logging.getLogger("agent_company_simulator")


def create_campaign(
    ctx: SimulationContext,
    company: Company,
    name: str,
    segment: SegmentType,
    budget: float,
    duration_days: int,
) -> tuple[Campaign | None, list[Event]]:
    """Create a new marketing campaign."""
    if budget <= 0 or duration_days <= 0:
        return None, []

    daily_spend = budget / duration_days
    campaign = Campaign(
        company_id=company.id,
        name=name,
        segment=segment,
        budget=budget,
        daily_spend=daily_spend,
        duration_days=duration_days,
        days_remaining=duration_days,
        effectiveness=0.5,
        status=CampaignStatus.ACTIVE,
        created_day=ctx.day,
    )
    ctx.db.add(campaign)
    ctx.db.flush()

    event = Event(
        company_id=company.id,
        event_type="CAMPAIGN_CREATED",
        description=f"Campaign '{name}' created for {segment.value} (${budget:.0f} over {duration_days} days).",
        target_type="campaign",
        target_id=campaign.id,
        meta={"segment": segment.value, "budget": budget, "duration": duration_days, "day": ctx.day},
        simulation_day=ctx.day,
    )
    return campaign, [event]


def update_campaigns(ctx: SimulationContext) -> list[Event]:
    """Update active campaigns: spend budget, decrement duration, complete if done."""
    campaigns = list(
        ctx.db.execute(
            select(Campaign).where(
                Campaign.company_id == ctx.company.id,
                Campaign.status == CampaignStatus.ACTIVE,
            )
        ).scalars().all()
    )
    events: list[Event] = []

    for camp in campaigns:
        camp.days_remaining -= 1

        # Effectiveness grows slightly over time (learning).
        camp.effectiveness = min(1.0, camp.effectiveness + 0.02)

        if camp.days_remaining <= 0:
            camp.status = CampaignStatus.COMPLETED
            events.append(Event(
                company_id=ctx.company.id,
                event_type="CAMPAIGN_COMPLETED",
                description=f"Campaign '{camp.name}' completed.",
                target_type="campaign",
                target_id=camp.id,
                meta={"segment": camp.segment.value, "day": ctx.day},
                simulation_day=ctx.day,
            ))

    return events


def total_campaign_spend(ctx: SimulationContext) -> float:
    """Total daily spend across all active campaigns."""
    campaigns = list(
        ctx.db.execute(
            select(Campaign).where(
                Campaign.company_id == ctx.company.id,
                Campaign.status == CampaignStatus.ACTIVE,
            )
        ).scalars().all()
    )
    return sum(c.daily_spend for c in campaigns)


def marketing_boost(ctx: SimulationContext, target_segment: SegmentType) -> float:
    """Compute marketing boost (0..1) for a target segment from active campaigns."""
    campaigns = list(
        ctx.db.execute(
            select(Campaign).where(
                Campaign.company_id == ctx.company.id,
                Campaign.status == CampaignStatus.ACTIVE,
                Campaign.segment == target_segment,
            )
        ).scalars().all()
    )
    if not campaigns:
        return 0.0

    # Sum effectiveness of campaigns targeting this segment.
    boost = sum(c.effectiveness * 0.3 for c in campaigns)
    return min(0.5, boost)
