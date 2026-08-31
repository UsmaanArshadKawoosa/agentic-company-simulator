"""Simulation event broadcaster.

Integrates with the simulation engine to broadcast real-time events
to WebSocket clients when meaningful state changes occur.
"""

from __future__ import annotations

import logging
from typing import Any

from app.services.realtime import manager

logger = logging.getLogger("agent_company_simulator")


class SimulationBroadcaster:
    """Broadcasts simulation events to WebSocket subscribers.

    This class is designed to be called from the simulation engine
    after each meaningful state change. It is non-blocking and
    failures are logged but never propagated to the simulation.
    """

    @staticmethod
    async def broadcast(company_id: int, event: dict[str, Any]) -> None:
        """Broadcast an event to all subscribers of a company.

        This method never raises. Failures are logged and swallowed
        to ensure the simulation continues regardless of WebSocket state.
        """
        try:
            await manager.broadcast(company_id, event)
        except Exception as exc:
            logger.warning("Failed to broadcast event to company %d: %s", company_id, exc)

    @staticmethod
    def create_event(
        event_type: str,
        company_id: int,
        day: int,
        payload: dict[str, Any] | None = None,
        agent_id: int | None = None,
        agent_role: str | None = None,
    ) -> dict[str, Any]:
        """Create a standardized event envelope for WebSocket transmission."""
        event: dict[str, Any] = {
            "type": event_type,
            "company_id": company_id,
            "day": day,
            "payload": payload or {},
        }
        if agent_id is not None:
            event["agent_id"] = agent_id
        if agent_role is not None:
            event["agent_role"] = agent_role
        return event


# Synchronous wrapper for use in synchronous simulation code.
class SyncBroadcaster:
    """Synchronous wrapper for broadcasting events from sync code.

    Uses asyncio to schedule the broadcast without blocking the
    simulation thread.
    """

    @staticmethod
    def broadcast(company_id: int, event: dict[str, Any]) -> None:
        """Schedule an event broadcast without blocking."""
        try:
            loop = asyncio.get_running_loop()
            # We're in an async context; create a task.
            loop.create_task(SimulationBroadcaster.broadcast(company_id, event))
        except RuntimeError:
            # No running loop; try to schedule in a new loop.
            try:
                asyncio.run(SimulationBroadcaster.broadcast(company_id, event))
            except Exception as exc:
                logger.warning("Failed to schedule broadcast: %s", exc)


import asyncio  # noqa: E402 - placed at end to avoid circular import issues

# Global singleton.
broadcaster = SyncBroadcaster()
