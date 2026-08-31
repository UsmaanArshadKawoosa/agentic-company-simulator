from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.memory import Memory


def record_memory(
    db: Session,
    *,
    agent_id: int,
    memory_type: str,
    content: str,
    importance: float = 0.5,
    simulation_day: int = 1,
    metadata: dict | None = None,
) -> Memory:
    memory = Memory(
        agent_id=agent_id,
        memory_type=memory_type,
        content=content,
        importance=importance,
        simulation_day=simulation_day,
        meta=metadata or {},
    )
    db.add(memory)
    return memory


def retrieve_memories(
    db: Session,
    *,
    agent_id: int,
    memory_type: str | None = None,
    limit: int = 50,
) -> list[Memory]:
    stmt = select(Memory).where(Memory.agent_id == agent_id)
    if memory_type is not None:
        stmt = stmt.where(Memory.memory_type == memory_type)
    stmt = stmt.order_by(Memory.importance.desc(), Memory.id.desc()).limit(limit)
    return list(db.execute(stmt).scalars().all())
