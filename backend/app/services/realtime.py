"""Real-time WebSocket connection manager.

Manages WebSocket connections for live simulation updates.
Each company can have multiple connected clients.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger("agent_company_simulator")


@dataclass
class Connection:
    """Represents a single WebSocket connection."""
    websocket: WebSocket
    client_id: str
    subscribed_company_id: int | None = None


@dataclass
class CompanyRoom:
    """Represents a company's WebSocket room with connected clients."""
    company_id: int
    connections: list[Connection] = field(default_factory=list)

    def add(self, conn: Connection) -> None:
        self.connections.append(conn)
        conn.subscribed_company_id = self.company_id

    def remove(self, conn: Connection) -> None:
        self.connections = [c for c in self.connections if c.client_id != conn.client_id]
        conn.subscribed_company_id = None

    @property
    def is_empty(self) -> bool:
        return len(self.connections) == 0


class ConnectionManager:
    """Manages all WebSocket connections across companies.

    Supports multiple clients per company and graceful disconnects.
    """

    def __init__(self) -> None:
        self._rooms: dict[int, CompanyRoom] = {}
        self._connections: dict[str, Connection] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, client_id: str) -> Connection:
        """Accept a new WebSocket connection."""
        await websocket.accept()
        conn = Connection(websocket=websocket, client_id=client_id)
        self._connections[client_id] = conn
        logger.info("Client %s connected.", client_id)
        return conn

    async def subscribe(self, conn: Connection, company_id: int) -> None:
        """Subscribe a connection to a company's updates."""
        async with self._lock:
            # Remove from previous room if any.
            if conn.subscribed_company_id is not None:
                await self._leave_room(conn)

            # Create room if needed.
            if company_id not in self._rooms:
                self._rooms[company_id] = CompanyRoom(company_id=company_id)

            self._rooms[company_id].add(conn)
            logger.info("Client %s subscribed to company %d.", conn.client_id, company_id)

    async def disconnect(self, conn: Connection) -> None:
        """Handle client disconnect gracefully."""
        async with self._lock:
            await self._leave_room(conn)
            self._connections.pop(conn.client_id, None)
        logger.info("Client %s disconnected.", conn.client_id)

    async def _leave_room(self, conn: Connection) -> None:
        """Remove connection from its current room."""
        if conn.subscribed_company_id is None:
            return
        company_id = conn.subscribed_company_id
        room = self._rooms.get(company_id)
        if room is not None:
            room.remove(conn)
            if room.is_empty:
                del self._rooms[company_id]
        conn.subscribed_company_id = None

    async def broadcast(self, company_id: int, event: dict[str, Any]) -> None:
        """Broadcast an event to all clients subscribed to a company."""
        room = self._rooms.get(company_id)
        if room is None:
            return

        payload = json.dumps(event)
        disconnected: list[Connection] = []

        for conn in room.connections:
            try:
                await conn.websocket.send_text(payload)
            except Exception:
                # Mark for removal; don't modify list during iteration.
                disconnected.append(conn)

        # Clean up disconnected clients.
        for conn in disconnected:
            await self.disconnect(conn)

    async def send_to_client(self, client_id: str, event: dict[str, Any]) -> bool:
        """Send an event to a specific client."""
        conn = self._connections.get(client_id)
        if conn is None:
            return False
        try:
            await conn.websocket.send_text(json.dumps(event))
            return True
        except Exception:
            await self.disconnect(conn)
            return False

    def get_subscriber_count(self, company_id: int) -> int:
        """Get the number of subscribers for a company."""
        room = self._rooms.get(company_id)
        return len(room.connections) if room else 0


# Global singleton instance.
manager = ConnectionManager()
