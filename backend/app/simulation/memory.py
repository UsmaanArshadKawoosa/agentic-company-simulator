"""Memory system: structured memory categories and relevance retrieval.

Memories are categorized (FACT, DECISION, OUTCOME, LESSON, PREFERENCE,
WARNING, RELATIONSHIP) and retrieved by deterministic relevance scoring:

    score = topic_matches + importance_weight + recency_weight

No embeddings or vector databases are used. Retrieval is deterministic and
bounded to keep prompts compact.
"""

from __future__ import annotations

import logging
import re

from sqlalchemy import select

from app.enums import MemoryType
from app.models.memory import Memory
from app.simulation.domain import SimulationContext

logger = logging.getLogger("agent_company_simulator")

# Maximum memories returned to an agent prompt.
MAX_RETRIEVAL = 5


def store_memory(
    ctx: SimulationContext,
    agent_id: int,
    memory_type: str,
    content: str,
    importance: float = 0.5,
    source_event: str | None = None,
) -> Memory:
    """Persist a structured memory."""
    memory = Memory(
        agent_id=agent_id,
        memory_type=memory_type,
        content=content,
        importance=max(0.0, min(1.0, importance)),
        simulation_day=ctx.day,
        meta={"source": source_event} if source_event else {},
    )
    ctx.db.add(memory)
    ctx.db.flush()
    return memory


def _extract_topics(text: str) -> set[str]:
    """Extract lowercase topic tokens from text (simple keyword extraction)."""
    # Keep alphanumeric tokens of length >= 3 as topics.
    return {t.lower() for t in re.findall(r"[a-z0-9]{3,}", text.lower())}


def _score_memory(memory: Memory, topics: set[str], current_day: int) -> float:
    """Deterministic relevance score for a memory given current topics."""
    content_topics = _extract_topics(memory.content)
    # Topic overlap count.
    topic_score = len(topics & content_topics)
    # Importance weight (0..1 scaled to 0..2).
    importance_score = memory.importance * 2.0
    # Recency: more recent memories score slightly higher. Decay over days.
    days_ago = max(0, current_day - memory.simulation_day)
    recency_score = max(0.0, 1.0 - days_ago * 0.05)
    return topic_score + importance_score + recency_score


def retrieve_memories(
    ctx: SimulationContext,
    agent_id: int,
    query_text: str,
    *,
    memory_type: str | None = None,
    limit: int = MAX_RETRIEVAL,
) -> list[Memory]:
    """Retrieve memories ranked by relevance to the query.

    Deterministic: same query + same memories always produces same ranking.
    """
    stmt = select(Memory).where(Memory.agent_id == agent_id)
    if memory_type is not None:
        stmt = stmt.where(Memory.memory_type == memory_type)
    memories = list(ctx.db.execute(stmt).scalars().all())

    topics = _extract_topics(query_text)
    if not topics:
        # Fall back to recency + importance ordering.
        scored = [(m.importance * 2.0 + max(0, 1 - (ctx.day - m.simulation_day) * 0.05), m) for m in memories]
    else:
        scored = [(_score_memory(m, topics, ctx.day), m) for m in memories]

    # Sort by score descending, then by id descending (most recent first) for ties.
    scored.sort(key=lambda x: (-x[0], -x[1].id))
    return [m for _, m in scored[:limit]]


def retrieve_lessons(
    ctx: SimulationContext,
    agent_id: int,
    query_text: str,
    *,
    limit: int = 3,
) -> list[Memory]:
    """Convenience: retrieve only LESSON-type memories."""
    return retrieve_memories(ctx, agent_id, query_text, memory_type=MemoryType.LESSON.value, limit=limit)


def create_lesson(
    ctx: SimulationContext,
    agent_id: int,
    content: str,
    importance: float = 0.8,
) -> Memory:
    """Create a LESSON memory (bounded importance)."""
    return store_memory(
        ctx,
        agent_id,
        MemoryType.LESSON.value,
        content,
        importance=importance,
        source_event="lesson_learned",
    )
