"""Product system: features, product readiness, quality, and technical debt.

Progress propagation:
    Tasks → Features → Product readiness
    Feature completion quality → Product quality
    Technical debt → reduces quality and future efficiency
"""

from __future__ import annotations

import logging

from sqlalchemy import select

from app.enums import FeatureStatus, TaskStatus
from app.models.event import Event
from app.models.product_feature import ProductFeature
from app.models.task import Task
from app.simulation.domain import SimulationContext

logger = logging.getLogger("agent_company_simulator")


def feature_progress(feature: ProductFeature, tasks: list[Task]) -> float:
    """Feature progress = average progress of its non-cancelled tasks."""
    f_tasks = [t for t in tasks if t.feature_id == feature.id and t.status != TaskStatus.CANCELLED]
    if not f_tasks:
        return 0.0
    return sum(t.progress for t in f_tasks) / len(f_tasks)


def feature_quality(feature: ProductFeature, tasks: list[Task]) -> float:
    """Feature quality = fraction of tasks completed.

    In V1, quality is simply the completion rate of the feature's tasks.
    """
    f_tasks = [t for t in tasks if t.feature_id == feature.id and t.status != TaskStatus.CANCELLED]
    if not f_tasks:
        return 0.0
    completed = sum(1 for t in f_tasks if t.status == TaskStatus.COMPLETED)
    return completed / len(f_tasks)


def update_features(ctx: SimulationContext) -> list[Event]:
    """Recompute feature progress and quality. Returns completion events."""
    features = list(
        ctx.db.execute(select(ProductFeature).where(ProductFeature.company_id == ctx.company.id))
        .scalars()
        .all()
    )
    tasks = list(
        ctx.db.execute(select(Task).where(Task.company_id == ctx.company.id)).scalars().all()
    )
    events: list[Event] = []
    for f in features:
        if f.status in (FeatureStatus.COMPLETED, FeatureStatus.CANCELLED):
            continue
        progress = feature_progress(f, tasks)
        quality = feature_quality(f, tasks)
        f.progress = round(progress, 2)
        f.quality = round(quality, 2)
        if progress > 0 and f.status == FeatureStatus.PLANNED:
            f.status = FeatureStatus.IN_PROGRESS
        if progress >= 1.0 and f.status != FeatureStatus.COMPLETED:
            f.status = FeatureStatus.COMPLETED
            events.append(
                Event(
                    company_id=ctx.company.id,
                    event_type="FEATURE_COMPLETED",
                    description=f"Feature '{f.name}' completed.",
                    target_type="feature",
                    target_id=f.id,
                    meta={"quality": f.quality, "day": ctx.day},
                    simulation_day=ctx.day,
                )
            )
    return events


def compute_product_readiness(company, features: list[ProductFeature]) -> float:
    """Product readiness = average feature progress across all features.

    Bounded 0..1. If no features, readiness is 0.
    """
    active = [f for f in features if f.status != FeatureStatus.CANCELLED]
    if not active:
        return 0.0
    return sum(f.progress for f in active) / len(active)


def compute_product_quality(company, features: list[ProductFeature]) -> float:
    """Product quality = average feature quality minus technical debt penalty.

    Bounded 0..1.
    """
    active = [f for f in features if f.status != FeatureStatus.CANCELLED]
    if not active:
        return 0.0
    avg_quality = sum(f.quality for f in active) / len(active)
    debt_penalty = company.technical_debt
    return max(0.0, min(1.0, avg_quality - debt_penalty))


def update_product(ctx: SimulationContext) -> list[Event]:
    """Update product readiness, quality, and technical debt. Returns events."""
    features = list(
        ctx.db.execute(select(ProductFeature).where(ProductFeature.company_id == ctx.company.id))
        .scalars()
        .all()
    )
    events: list[Event] = []

    readiness = compute_product_readiness(ctx.company, features)
    quality = compute_product_quality(ctx.company, features)

    old_readiness = ctx.company.product_readiness
    old_quality = ctx.company.product_quality

    ctx.company.product_readiness = round(readiness, 4)
    ctx.company.product_quality = round(quality, 4)

    # Technical debt slowly accumulates from incomplete work and decays slightly.
    # Simple model: debt increases when features are partially done (rushed work).
    incomplete_features = [f for f in features if 0 < f.progress < 1.0]
    if incomplete_features:
        debt_increase = 0.01 * len(incomplete_features)
        old_debt = ctx.company.technical_debt
        ctx.company.technical_debt = min(1.0, ctx.company.technical_debt + debt_increase)
        if ctx.company.technical_debt != old_debt:
            events.append(
                Event(
                    company_id=ctx.company.id,
                    event_type="TECHNICAL_DEBT_INCREASED",
                    description=f"Technical debt increased to {ctx.company.technical_debt:.3f}.",
                    meta={"technical_debt": round(ctx.company.technical_debt, 4), "day": ctx.day},
                    simulation_day=ctx.day,
                )
            )

    if abs(readiness - old_readiness) > 0.001 or abs(quality - old_quality) > 0.001:
        events.append(
            Event(
                company_id=ctx.company.id,
                event_type="PRODUCT_QUALITY_UPDATE",
                description=(
                    f"Product readiness={readiness:.3f}, quality={quality:.3f}, "
                    f"debt={ctx.company.technical_debt:.3f}."
                ),
                meta={
                    "readiness": round(readiness, 4),
                    "quality": round(quality, 4),
                    "technical_debt": round(ctx.company.technical_debt, 4),
                    "day": ctx.day,
                },
                simulation_day=ctx.day,
            )
        )

    return events
