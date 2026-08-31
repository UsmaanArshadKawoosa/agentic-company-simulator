"""Communication system: internal agent-to-agent messages.

Messages are persisted and affect future agent context. Unread messages are
delivered to recipients so they can react on their next tick.

Validation rules:
- sender and recipient must belong to the same company
- message content is bounded
- priority affects ordering in context
"""

from __future__ import annotations

import logging

from sqlalchemy import select

from app.enums import EventType, MessagePriority
from app.models.event import Event
from app.models.message import Message
from app.simulation.domain import SimulationContext

logger = logging.getLogger("agent_company_simulator")

MAX_MESSAGE_LENGTH = 1000
MAX_SUBJECT_LENGTH = 255


def send_message(
    ctx: SimulationContext,
    sender_agent_id: int,
    recipient_agent_id: int,
    subject: str,
    content: str,
    priority: str = MessagePriority.NORMAL.value,
) -> tuple[Message | None, list[Event]]:
    """Persist an internal message. Returns (message, events) or None if invalid.

    Caller is responsible for validating that both agents belong to the
    company (the DecisionValidator does this before calling here).
    """
    if not content or not content.strip():
        return None, []

    # Bound message size.
    content = content[:MAX_MESSAGE_LENGTH]
    subject = (subject or "")[:MAX_SUBJECT_LENGTH]

    msg = Message(
        company_id=ctx.company.id,
        sender_agent_id=sender_agent_id,
        recipient_agent_id=recipient_agent_id,
        subject=subject,
        content=content,
        priority=priority,
        created_day=ctx.day,
        read_day=None,
    )
    ctx.db.add(msg)
    ctx.db.flush()

    event = Event(
        company_id=ctx.company.id,
        actor_id=sender_agent_id,
        event_type=EventType.MESSAGE_SENT,
        description=f"Message sent: {subject}" if subject else "Message sent.",
        target_type="message",
        target_id=msg.id,
        meta={
            "message_id": msg.id,
            "recipient_id": recipient_agent_id,
            "priority": priority,
            "day": ctx.day,
        },
        simulation_day=ctx.day,
    )
    ctx.db.add(event)
    return msg, [event]


def get_unread_messages(
    ctx: SimulationContext,
    agent_id: int,
    *,
    limit: int = 10,
) -> list[Message]:
    """Get unread messages for an agent, ordered by priority then recency."""
    priority_order = {
        MessagePriority.URGENT.value: 0,
        MessagePriority.HIGH.value: 1,
        MessagePriority.NORMAL.value: 2,
        MessagePriority.LOW.value: 3,
    }
    messages = list(
        ctx.db.execute(
            select(Message)
            .where(Message.company_id == ctx.company.id)
            .where(Message.recipient_agent_id == agent_id)
            .where(Message.read_day.is_(None))
            .order_by(Message.created_day.desc(), Message.id.desc())
        )
        .scalars()
        .all()
    )
    # Sort by priority (urgent first), then by recency.
    messages.sort(key=lambda m: (priority_order.get(m.priority, 2), m.created_day, m.id))
    return messages[:limit]


def mark_messages_read(
    ctx: SimulationContext,
    agent_id: int,
    *,
    max_messages: int = 20,
) -> list[Event]:
    """Mark an agent's unread messages as read. Returns read events."""
    unread = get_unread_messages(ctx, agent_id, limit=max_messages)
    events: list[Event] = []
    for msg in unread:
        msg.read_day = ctx.day
        events.append(
            Event(
                company_id=ctx.company.id,
                actor_id=agent_id,
                event_type=EventType.MESSAGE_RECEIVED,
                description=f"Message read: {msg.subject}" if msg.subject else "Message read.",
                target_type="message",
                target_id=msg.id,
                meta={
                    "message_id": msg.id,
                    "sender_id": msg.sender_agent_id,
                    "day": ctx.day,
                },
                simulation_day=ctx.day,
            )
        )
    ctx.db.flush()
    return events


def get_recent_messages(
    ctx: SimulationContext,
    agent_id: int,
    *,
    limit: int = 5,
) -> list[Message]:
    """Get recent messages (read or unread) involving the agent."""
    messages = list(
        ctx.db.execute(
            select(Message)
            .where(Message.company_id == ctx.company.id)
            .where(
                (Message.recipient_agent_id == agent_id)
                | (Message.sender_agent_id == agent_id)
            )
            .order_by(Message.created_day.desc(), Message.id.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )
    return messages
