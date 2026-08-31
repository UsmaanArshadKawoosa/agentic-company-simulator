"""Resource allocation system: track and allocate company resources."""

from __future__ import annotations

import logging

from sqlalchemy import select

from app.enums import ResourceType
from app.models.resource_allocation import ResourceAllocation
from app.simulation.domain import SimulationContext

logger = logging.getLogger("agent_company_simulator")


def allocate_resource(
    ctx: SimulationContext,
    resource_type: ResourceType,
    allocated_amount: float,
    purpose: str = "",
    owner_id: int | None = None,
) -> ResourceAllocation | None:
    """Allocate a resource. Returns None if allocation would exceed available amount."""
    if allocated_amount <= 0:
        return None

    existing = list(
        ctx.db.execute(
            select(ResourceAllocation).where(
                ResourceAllocation.company_id == ctx.company.id,
                ResourceAllocation.resource_type == resource_type,
            )
        ).scalars().all()
    )

    total_allocated = sum(r.allocated_amount for r in existing)
    available = _get_available_amount(ctx, resource_type)

    if total_allocated + allocated_amount > available:
        return None

    allocation = ResourceAllocation(
        company_id=ctx.company.id,
        resource_type=resource_type,
        allocated_amount=round(allocated_amount, 2),
        available_amount=round(available, 2),
        allocation_day=ctx.day,
        purpose=purpose.strip()[:500] if purpose else "",
        owner_id=owner_id,
    )
    ctx.db.add(allocation)
    ctx.db.flush()
    return allocation


def release_resource(ctx: SimulationContext, allocation_id: int) -> ResourceAllocation | None:
    """Release a resource allocation."""
    allocation = ctx.db.get(ResourceAllocation, allocation_id)
    if allocation is None or allocation.company_id != ctx.company.id:
        return None

    allocation.allocated_amount = 0.0
    ctx.db.flush()
    return allocation


def get_resource_utilization(ctx: SimulationContext, resource_type: ResourceType | None = None) -> dict:
    """Get resource utilization summary."""
    query = select(ResourceAllocation).where(ResourceAllocation.company_id == ctx.company.id)
    if resource_type is not None:
        query = query.where(ResourceAllocation.resource_type == resource_type)

    allocations = list(ctx.db.execute(query).scalars().all())
    result: dict[str, dict] = {}

    for alloc in allocations:
        key = alloc.resource_type.value
        if key not in result:
            result[key] = {
                "total_allocated": 0.0,
                "available": alloc.available_amount,
                "count": 0,
            }
        result[key]["total_allocated"] += alloc.allocated_amount
        result[key]["count"] += 1

    return result


def _get_available_amount(ctx: SimulationContext, resource_type: ResourceType) -> float:
    """Get available amount for a resource type."""
    company = ctx.company
    if resource_type == ResourceType.CASH:
        return max(0.0, company.cash)
    elif resource_type == ResourceType.ENGINEERING_CAPACITY:
        agents = [
            a for a in ctx.company.agents
            if a.role.value == "ENGINEER" and a.status.value == "IDLE"
        ]
        return sum(max(0.0, a.capacity - a.workload) for a in agents)
    elif resource_type == ResourceType.MARKETING_BUDGET:
        return max(0.0, company.cash * 0.1)
    elif resource_type == ResourceType.SALES_CAPACITY:
        return max(0.0, 10.0 - company.sales_effectiveness * 10.0)
    elif resource_type == ResourceType.MANAGEMENT_ATTENTION:
        return max(0.0, 5.0)
    return 0.0
