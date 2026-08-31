"""Placeholder scheduler.

Reserved for future time-based / event-driven scheduling of agent actions.
Phase 1 does not require scheduling; this keeps an extension point.
"""


class Scheduler:
    def __init__(self) -> None:
        self._tasks: list[dict] = []

    def schedule(self, action: str, due_day: int, payload: dict | None = None) -> None:
        self._tasks.append(
            {"action": action, "due_day": due_day, "payload": payload or {}}
        )

    def pending(self, current_day: int) -> list[dict]:
        return [t for t in self._tasks if t["due_day"] >= current_day]

    def clear(self) -> None:
        self._tasks.clear()
