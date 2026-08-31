"""WebSocket endpoint for real-time simulation updates."""

from __future__ import annotations

import json
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.company import Company
from app.services.realtime import Connection, manager

logger = logging.getLogger("agent_company_simulator")

router = APIRouter(tags=["websocket"])


def _get_company_or_404(db: Session, company_id: int) -> Company:
    company = db.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=404, detail=f"Company {company_id} not found")
    return company


@router.websocket("/ws/companies/{company_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    company_id: int,
) -> None:
    """WebSocket endpoint for subscribing to real-time simulation updates.

    Clients connect to this endpoint and receive events as the simulation
    progresses. The endpoint handles graceful disconnects and does not
    allow a broken client to crash the simulation.
    """
    client_id = str(uuid.uuid4())
    conn: Connection | None = None

    try:
        # Accept connection.
        conn = await manager.connect(websocket, client_id)

        # Validate company exists.
        db = next(get_db())
        try:
            _get_company_or_404(db, company_id)
        finally:
            db.close()

        # Subscribe to company updates.
        await manager.subscribe(conn, company_id)

        # Send initial connection acknowledgment.
        await manager.send_to_client(
            client_id,
            {
                "type": "connection.established",
                "client_id": client_id,
                "company_id": company_id,
                "message": "Connected to simulation stream.",
            },
        )

        # Listen for client messages (keep-alive, control commands).
        while True:
            try:
                data = await websocket.receive_text()
                await _handle_client_message(conn, data)
            except WebSocketDisconnect:
                break
            except RuntimeError:
                # Socket already closed.
                break

    except HTTPException:
        # Company not found; reject connection.
        try:
            await websocket.close(code=4004, reason="Company not found")
        except Exception:
            pass
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.warning("WebSocket error for client %s: %s", client_id, exc)
        try:
            await websocket.close(code=1011, reason="Internal error")
        except Exception:
            pass
    finally:
        if conn is not None:
            await manager.disconnect(conn)


async def _handle_client_message(conn: Connection, data: str) -> None:
    """Handle incoming client messages.

    Currently supports ping/pong for keep-alive. Control commands
    (start/pause/tick) are handled via HTTP API, not WebSocket.
    """
    try:
        msg = json.loads(data)
    except json.JSONDecodeError:
        await manager.send_to_client(
            conn.client_id,
            {"type": "error", "message": "Invalid JSON."},
        )
        return

    msg_type = msg.get("type", "")

    if msg_type == "ping":
        await manager.send_to_client(
            conn.client_id,
            {"type": "pong", "timestamp": msg.get("timestamp")},
        )
    elif msg_type == "subscribe":
        # Already subscribed on connect; acknowledge.
        await manager.send_to_client(
            conn.client_id,
            {
                "type": "subscribed",
                "company_id": conn.subscribed_company_id,
            },
        )
    else:
        await manager.send_to_client(
            conn.client_id,
            {"type": "error", "message": f"Unknown message type: {msg_type}"},
        )
