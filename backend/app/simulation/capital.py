"""Capital allocation system: budget requests and approvals."""

from __future__ import annotations

import logging

from sqlalchemy import select

from app.enums import BudgetStatus
from app.models.budget_request import BudgetRequest
from app.simulation.domain import SimulationContext

logger = logging.getLogger("agent_company_simulator")

# --- Authority thresholds ---
BUDGET_REQUEST_AUTHORITY: int = 5
BUDGET_APPROVE_AUTHORITY: int = 8

# --- Budget request management ---


def create_budget_request(
    ctx: SimulationContext,
    requester_id: int,
    amount: float,
    purpose: str,
) -> BudgetRequest | None:
    """Create a budget request."""
    if amount <= 0 or not purpose.strip():
        return None

    request = BudgetRequest(
        company_id=ctx.company.id,
        requester_id=requester_id,
        amount=round(amount, 2),
        purpose=purpose[:500],
        status=BudgetStatus.PENDING,
        requested_day=ctx.day,
    )
    ctx.db.add(request)
    ctx.db.flush()
    return request


def approve_budget_request(
    ctx: SimulationContext,
    request_id: int,
    approver_id: int,
    approved_amount: float,
    decision_notes: str = "",
) -> BudgetRequest | None:
    """Approve a budget request and allocate funds."""
    request = ctx.db.get(BudgetRequest, request_id)
    if request is None or request.company_id != ctx.company.id:
        return None
    if request.status != BudgetStatus.PENDING:
        return None

    approved = max(0.0, min(approved_amount, request.amount))
    if approved <= 0:
        return None

    request.approved_amount = round(approved, 2)
    request.approver_id = approver_id
    request.status = BudgetStatus.APPROVED
    request.decided_day = ctx.day
    request.decision_notes = (decision_notes or "")[:500]

    # Allocate capital
    ctx.company.cash -= request.approved_amount
    request.status = BudgetStatus.ALLOCATED

    ctx.db.flush()
    return request


def reject_budget_request(
    ctx: SimulationContext,
    request_id: int,
    approver_id: int,
    decision_notes: str = "",
) -> BudgetRequest | None:
    """Reject a budget request."""
    request = ctx.db.get(BudgetRequest, request_id)
    if request is None or request.company_id != ctx.company.id:
        return None
    if request.status != BudgetStatus.PENDING:
        return None

    request.approver_id = approver_id
    request.status = BudgetStatus.REJECTED
    request.decided_day = ctx.day
    request.decision_notes = (decision_notes or "")[:500]

    ctx.db.flush()
    return request


def get_pending_budget_requests(ctx: SimulationContext) -> list[BudgetRequest]:
    """Get all pending budget requests for the company."""
    return list(
        ctx.db.execute(
            select(BudgetRequest).where(
                BudgetRequest.company_id == ctx.company.id,
                BudgetRequest.status == BudgetStatus.PENDING,
            )
        )
        .scalars()
        .all()
    )


def get_budget_summary(ctx: SimulationContext) -> dict:
    """Get budget request summary."""
    pending = len(get_pending_budget_requests(ctx))
    total_approved = ctx.db.execute(
        select(BudgetRequest).where(
            BudgetRequest.company_id == ctx.company.id,
            BudgetRequest.status == BudgetStatus.ALLOCATED,
        )
    ).scalars().all()
    approved_amount = sum(r.approved_amount for r in total_approved)
    total_pending = ctx.db.execute(
        select(BudgetRequest).where(
            BudgetRequest.company_id == ctx.company.id,
            BudgetRequest.status == BudgetStatus.PENDING,
        )
    ).scalars().all()
    pending_amount = sum(r.amount for r in total_pending)

    return {
        "pending_count": pending,
        "pending_amount": round(pending_amount, 2),
        "total_approved": round(approved_amount, 2),
    }
