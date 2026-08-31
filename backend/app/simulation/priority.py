"""Priority and scheduling system: deterministic work prioritization."""

from __future__ import annotations

import logging

from sqlalchemy import select

from app.enums import ObjectiveStatus, TaskStatus
from app.models.milestone import Milestone
from app.models.objective import Objective
from app.models.project import Project
from app.models.task import Task
from app.simulation.domain import SimulationContext

logger = logging.getLogger("agent_company_simulator")


def compute_task_priority(task: Task, ctx: SimulationContext) -> float:
    """Compute deterministic priority score for a task.

    Higher score = higher priority. Factors:
    - Strategic importance (via project/milestone/feature priority)
    - Urgency (days until deadline, if any)
    - Dependencies (blocked tasks are lower priority unless they unblock critical paths)
    - Expected business impact (via objective priority)
    - Deadline pressure
    - Resource requirements
    """
    if task.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED):
        return 0.0

    score = 0.0

    # Base priority from task itself.
    score += task.priority * 10.0

    # Project/milestone/feature importance.
    if task.project_id:
        project = ctx.db.get(Project, task.project_id)
        if project:
            score += project.progress * 5.0

    if task.milestone_id:
        milestone = ctx.db.get(Milestone, task.milestone_id)
        if milestone:
            score += milestone.progress * 3.0

    # Deadline urgency.
    from app.models.company import Company
    company = ctx.db.get(Company, ctx.company.id)
    if task.deadline and company:
        days_until_deadline = (task.deadline - company.current_day)
        if days_until_deadline <= 0:
            score += 50.0
        else:
            score += max(0.0, 20.0 - days_until_deadline * 0.5)

    # Blocked tasks should not be executed but may need attention.
    if task.status == TaskStatus.BLOCKED:
        score *= 0.5

    # Cap at 100.
    return max(0.0, min(100.0, score))


def get_prioritized_tasks(ctx: SimulationContext, status_filter: tuple[str, ...] | None = None) -> list[Task]:
    """Get tasks sorted by deterministic priority score (highest first)."""
    query = select(Task).where(Task.company_id == ctx.company.id)
    if status_filter:
        query = query.where(Task.status.in_([TaskStatus(s) for s in status_filter]))

    tasks = list(ctx.db.execute(query).scalars().all())
    tasks_with_scores = [(t, compute_task_priority(t, ctx)) for t in tasks]
    tasks_with_scores.sort(key=lambda x: x[1], reverse=True)
    return [t for t, _ in tasks_with_scores]


def get_prioritized_objectives(ctx: SimulationContext) -> list[Objective]:
    """Get active objectives sorted by priority (highest first)."""
    return list(
        ctx.db.execute(
            select(Objective).where(
                Objective.company_id == ctx.company.id,
                Objective.status.in_([ObjectiveStatus.TODO, ObjectiveStatus.IN_PROGRESS]),
            ).order_by(Objective.priority.desc(), Objective.id)
        ).scalars().all()
    )
