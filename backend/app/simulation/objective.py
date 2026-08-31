"""Objective system: hierarchical company objectives."""

from __future__ import annotations

import logging

from sqlalchemy import select

from app.enums import ObjectiveStatus, ObjectiveType
from app.models.objective import Objective
from app.simulation.domain import SimulationContext

logger = logging.getLogger("agent_company_simulator")


def create_objective(
    ctx: SimulationContext,
    title: str,
    description: str = "",
    objective_type: ObjectiveType = ObjectiveType.OPERATIONAL,
    priority: int = 1,
    owner_id: int | None = None,
    parent_id: int | None = None,
    expected_outcome: str = "",
) -> Objective | None:
    """Create a new company objective."""
    if not title.strip():
        return None

    objective = Objective(
        company_id=ctx.company.id,
        parent_id=parent_id,
        title=title.strip()[:255],
        description=description.strip()[:2000],
        objective_type=objective_type,
        status=ObjectiveStatus.TODO,
        priority=max(1, min(10, priority)),
        expected_outcome=expected_outcome.strip()[:1000],
        owner_id=owner_id,
        created_day=ctx.day,
    )
    ctx.db.add(objective)
    ctx.db.flush()
    return objective


def update_objective_progress(ctx: SimulationContext, objective_id: int, progress: float) -> Objective | None:
    """Update objective progress."""
    objective = ctx.db.get(Objective, objective_id)
    if objective is None or objective.company_id != ctx.company.id:
        return None

    objective.progress = max(0.0, min(100.0, progress))
    if objective.progress >= 100.0:
        objective.status = ObjectiveStatus.ACHIEVED
        objective.completed_day = ctx.day
    elif objective.status == ObjectiveStatus.TODO and progress > 0:
        objective.status = ObjectiveStatus.IN_PROGRESS

    ctx.db.flush()
    return objective


def get_company_objectives(ctx: SimulationContext, objective_type: ObjectiveType | None = None) -> list[Objective]:
    """Get all objectives for the company, optionally filtered by type."""
    query = select(Objective).where(Objective.company_id == ctx.company.id)
    if objective_type is not None:
        query = query.where(Objective.objective_type == objective_type)
    return list(query.order_by(Objective.priority.desc(), Objective.id).all())


def get_active_objectives(ctx: SimulationContext) -> list[Objective]:
    """Get active (non-completed, non-cancelled) objectives."""
    return list(
        ctx.db.execute(
            select(Objective).where(
                Objective.company_id == ctx.company.id,
                Objective.status.in_([ObjectiveStatus.TODO, ObjectiveStatus.IN_PROGRESS]),
            ).order_by(Objective.priority.desc(), Objective.id)
        ).scalars().all()
    )
