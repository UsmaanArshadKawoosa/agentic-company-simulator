from app.enums import EventType
from app.models.event import Event


class EventEmitter:
    """Small helper to construct persisted Event objects during a simulation.

    It does not commit; the engine owns the session and flushes batched events.
    """

    def __init__(self, company_id: int, simulation_day: int) -> None:
        self.company_id = company_id
        self.simulation_day = simulation_day

    def emit(
        self,
        event_type: EventType,
        description: str,
        *,
        actor_id: int | None = None,
        target_type: str | None = None,
        target_id: int | None = None,
        metadata: dict | None = None,
    ) -> Event:
        return Event(
            company_id=self.company_id,
            actor_id=actor_id,
            event_type=event_type,
            description=description,
            target_type=target_type,
            target_id=target_id,
            meta=metadata or {},
            simulation_day=self.simulation_day,
        )
