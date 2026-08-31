"""Progress system: propagate task → project → product readiness and goals."""

from __future__ import annotations

import logging

from sqlalchemy import select

from app.enums import GoalStatus, ProjectStatus, TaskStatus
from app.models.company import Company
from app.models.event import Event
from app.models.goal import Goal
from app.models.project import Project
from app.models.task import Task
from app.simulation.domain import SimulationContext

logger = logging.getLogger("agent_company_simulator")


def project_progress(project: Project, tasks: list[Task]) -> float:
    """Weighted average progress of a project's tasks.

    Completed tasks count as 100. Tasks weighted by priority.
    """
    project_tasks = [t for t in tasks if t.project_id == project.id and t.status != TaskStatus.CANCELLED]
    if not project_tasks:
        return 0.0
    total_weight = sum(t.priority for t in project_tasks)
    if total_weight == 0:
        return 0.0
    weighted = sum(t.progress * t.priority for t in project_tasks)
    return weighted / total_weight


def product_readiness(company: Company, projects: list[Project], tasks: list[Task]) -> float:
    """Overall product/MVP readiness = average progress across all projects.

    Projects without tasks contribute 0.
    """
    active_projects = [p for p in projects if p.status != ProjectStatus.CANCELLED]
    if not active_projects:
        return 0.0
    total = sum(project_progress(p, tasks) for p in active_projects)
    return total / len(active_projects)


def marketing_progress(tasks: list[Task]) -> float:
    """Fraction of non-cancelled tasks that are completed.

    Used as a proxy for marketing execution readiness.
    """
    relevant = [t for t in tasks if t.status != TaskStatus.CANCELLED]
    if not relevant:
        return 0.0
    completed = sum(1 for t in relevant if t.status == TaskStatus.COMPLETED)
    return completed / len(relevant)


def update_projects_and_readiness(ctx: SimulationContext) -> float:
    """Recompute project progress and product readiness. Returns readiness."""
    projects = list(
        ctx.db.execute(select(Project).where(Project.company_id == ctx.company.id)).scalars().all()
    )
    tasks = list(
        ctx.db.execute(select(Task).where(Task.company_id == ctx.company.id)).scalars().all()
    )
    readiness = product_readiness(ctx.company, projects, tasks)

    for project in projects:
        progress = project_progress(project, tasks)
        project.progress = round(progress, 2)
        if progress > 0 and project.status == ProjectStatus.PLANNED:
            project.status = ProjectStatus.IN_PROGRESS
        if progress >= 100.0 and project.status != ProjectStatus.COMPLETED:
            project.status = ProjectStatus.COMPLETED

    ctx.company.product_readiness = round(readiness, 2)
    return readiness


def _goal_progress_from_state(goal: Goal, readiness: float, active_customer_count: int) -> float | None:
    """Derive goal progress from simulation state where possible.

    Returns None if the goal type is not auto-derived.
    """
    title = goal.title.lower()
    if "mvp" in title or "launch" in title or "product" in title:
        return min(100.0, readiness)
    if "customer" in title:
        # Look for a number in the title like "acquire first 10 customers".
        import re

        match = re.search(r"(\d+)", goal.title)
        target = int(match.group(1)) if match else 10
        if target <= 0:
            target = 10
        return min(100.0, (active_customer_count / target) * 100.0)
    return None


def update_goal_progress(ctx: SimulationContext, readiness: float, active_customer_count: int) -> list[Event]:
    """Update goals based on measurable simulation state. Returns progress events."""
    goals = list(
        ctx.db.execute(select(Goal).where(Goal.company_id == ctx.company.id)).scalars().all()
    )
    events: list[Event] = []
    for goal in goals:
        if goal.status in (GoalStatus.ACHIEVED, GoalStatus.CANCELLED):
            continue
        derived = _goal_progress_from_state(goal, readiness, active_customer_count)
        if derived is None:
            continue
        new_progress = round(max(goal.progress, derived), 2)
        if new_progress != goal.progress:
            goal.progress = new_progress
            if goal.status == GoalStatus.TODO and new_progress > 0:
                goal.status = GoalStatus.IN_PROGRESS
            if new_progress >= 100.0:
                goal.status = GoalStatus.ACHIEVED
            events.append(
                Event(
                    company_id=ctx.company.id,
                    event_type="GOAL_PROGRESS",
                    description=f"Goal '{goal.title}' progress is now {new_progress:.1f}%.",
                    target_type="goal",
                    target_id=goal.id,
                    meta={"progress": new_progress, "day": ctx.day},
                    simulation_day=ctx.day,
                )
            )
    return events
