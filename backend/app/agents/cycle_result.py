"""Shared lifecycle types for agents."""

from dataclasses import dataclass, field

from app.models.decision import Decision
from app.models.event import Event
from app.models.memory import Memory


@dataclass
class CycleResult:
    """Output of a single agent observe/think/decide/act/reflect cycle."""

    events: list[Event] = field(default_factory=list)
    decision: Decision | None = None
    memory: Memory | None = None
