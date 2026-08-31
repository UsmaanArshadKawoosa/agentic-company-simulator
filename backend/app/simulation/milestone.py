"""Milestone system: derive milestone progress from associated tasks."""

from __future__ import annotations

import logging

from sqlalchemy import select

from app.enums import MilestoneStatus, TaskStatus
from app.models.event import Event
from app.models.milestone import Milestone
from app.models.task import Task
from app.simulation.domain import SimulationContext

logger = logging.getLogger("agent_company_simulator")


def milestone_progress(milestone: Milestone, tasks: list[Task]) -> float:
    """Milestone progress = average progress of its non-cancelled tasks.

    If no tasks are associated, progress is 0.
    """
    ms_tasks = [t for t in tasks if t.milestone_id == milestone.id and t.status != TaskStatus.CANCELLED]
    if not ms_tasks:
        return 0.0
    return sum(t.progress for t in ms_tasks) / len(ms_tasks)


def update_milestones(ctx: SimulationContext) -> list[Event]:
    """Recompute milestone progress and status. Returns completion events."""
    milestones = list(
        ctx.db.execute(select(Milestone).where(Milestone.company_id == ctx.company.id))
        .scalars()
        .all()
    )
    tasks = list(
        ctx.db.execute(select(Task).where(Task.company_id == ctx.company.id)).scalars().all()
    )
    events: list[Event] = []
    for ms in milestones:
        if ms.status in (MilestoneStatus.COMPLETED, MilestoneStatus.CANCELLED):
            continue
        progress = milestone_progress(ms, tasks)
        ms.progress = round(progress, 2)
        if progress > 0 and ms.status == MilestoneStatus.PLANNED:
            ms.status = MilestoneStatus.IN_PROGRESS
        if progress >= 1.0 and ms.status != MilestoneStatus.COMPLETED:
            ms.status = MilestoneStatus.COMPLETED
            events.append(
                Event(
                    company_id=ctx.company.id,
                    event_type="MILESTONE_COMPLETED",
                    description=f"Milestone '{ms.name}' completed.",
                    target_type="milestone",
                    target_id=ms.id,
                    meta={"day": ctx.day},
                    simulation_day=ctx.day,
                )
            )
    return events
