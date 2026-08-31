"""Agent metrics: observational performance counters.

These metrics are computed deterministically from persisted state. They are
observational only and do not buff/nerf agents.
"""

from __future__ import annotations

from sqlalchemy import select

from app.enums import PlanStatus, TaskStatus
from app.models.agent import Agent
from app.models.company import Company
from app.models.decision import Decision
from app.models.message import Message
from app.models.plan import Plan
from app.models.task import Task
from app.simulation.domain import SimulationContext


def compute_agent_metrics(ctx: SimulationContext, agent: Agent) -> dict:
    """Compute observational metrics for an agent."""
    company_id = ctx.company.id
    agent_id = agent.id

    # Tasks completed by this agent.
    tasks_completed = (
        ctx.db.execute(
            select(Task)
            .where(Task.company_id == company_id)
            .where(Task.assigned_to == agent_id)
            .where(Task.status == TaskStatus.COMPLETED)
        )
        .scalars()
        .all()
    ).__len__()

    # Tasks currently blocked.
    tasks_blocked = (
        ctx.db.execute(
            select(Task)
            .where(Task.company_id == company_id)
            .where(Task.assigned_to == agent_id)
            .where(Task.status == TaskStatus.BLOCKED)
        )
        .scalars()
        .all()
    ).__len__()

    # Plans completed.
    plans_completed = (
        ctx.db.execute(
            select(Plan)
            .where(Plan.company_id == company_id)
            .where(Plan.agent_id == agent_id)
            .where(Plan.status == PlanStatus.COMPLETED)
        )
        .scalars()
        .all()
    ).__len__()

    # Plans failed.
    plans_failed = (
        ctx.db.execute(
            select(Plan)
            .where(Plan.company_id == company_id)
            .where(Plan.agent_id == agent_id)
            .where(Plan.status == PlanStatus.FAILED)
        )
        .scalars()
        .all()
    ).__len__()

    # Total decisions.
    decisions_count = (
        ctx.db.execute(
            select(Decision)
            .where(Decision.company_id == company_id)
            .where(Decision.agent_id == agent_id)
        )
        .scalars()
        .all()
    ).__len__()

    # Messages sent/received.
    messages_sent = (
        ctx.db.execute(
            select(Message)
            .where(Message.company_id == company_id)
            .where(Message.sender_agent_id == agent_id)
        )
        .scalars()
        .all()
    ).__len__()

    messages_received = (
        ctx.db.execute(
            select(Message)
            .where(Message.company_id == company_id)
            .where(Message.recipient_agent_id == agent_id)
        )
        .scalars()
        .all()
    ).__len__()

    return {
        "agent_id": agent_id,
        "role": agent.role.value,
        "tasks_completed": tasks_completed,
        "tasks_blocked": tasks_blocked,
        "plans_completed": plans_completed,
        "plans_failed": plans_failed,
        "decisions": decisions_count,
        "messages_sent": messages_sent,
        "messages_received": messages_received,
    }
