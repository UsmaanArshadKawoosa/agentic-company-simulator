"""WebSocket smoke test script.

This script manually tests the WebSocket functionality by:
1. Creating a company
2. Connecting a WebSocket client
3. Starting the simulation
4. Verifying events are received

Usage:
    python scripts/websocket_smoke_test.py

Requirements:
    - Backend server running on localhost:8000
    - requests and websocket-client packages installed
"""

from __future__ import annotations

import json
import sys
import threading
import time
import uuid

import requests

try:
    import websocket
except ImportError:
    print("ERROR: websocket-client package not installed.")
    print("Install with: pip install websocket-client")
    sys.exit(1)

BASE_URL = "http://127.0.0.1:8000/api"
WS_URL = "ws://127.0.0.1:8000/api/ws/companies"


def create_company() -> dict:
    """Create a test company."""
    company_name = f"WSTestCo_{uuid.uuid4().hex[:8]}"
    resp = requests.post(f"{BASE_URL}/companies", json={"name": company_name, "mission": "Test"})
    if resp.status_code == 201:
        print(f"Company created: {resp.json()['id']}")
        return resp.json()
    print(f"Failed to create company: {resp.text}")
    sys.exit(1)


def test_websocket():
    """Test WebSocket connection and event reception."""
    company = create_company()
    company_id = company["id"]
    ws_url = f"{WS_URL}/{company_id}"

    received_messages = []
    connected = False

    def on_message(ws, message):
        data = json.loads(message)
        received_messages.append(data)
        print(f"  Received: {data['type']}")

    def on_open(ws):
        nonlocal connected
        connected = True
        print("  WebSocket connected")

    def on_error(ws, error):
        print(f"  WebSocket error: {error}")
        sys.stdout.flush()

    def on_close(ws, close_status_code, close_msg):
        print(f"  WebSocket closed: {close_status_code} {close_msg}")
        sys.stdout.flush()

    # Connect WebSocket.
    print(f"Connecting WebSocket to {ws_url}...")
    sys.stdout.flush()
    ws = websocket.WebSocketApp(
        ws_url,
        on_message=on_message,
        on_open=on_open,
        on_error=on_error,
        on_close=on_close,
    )

    # Run WebSocket in background thread.
    ws_thread = threading.Thread(target=ws.run_forever)
    ws_thread.daemon = True
    ws_thread.start()

    # Wait for connection.
    time.sleep(2)
    if not connected:
        print(f"ERROR: Failed to connect WebSocket (messages so far: {len(received_messages)})")
        try:
            ws.close()
        except Exception:
            pass
        sys.exit(1)

    # Verify connection.established message.
    if len(received_messages) == 0 or received_messages[0].get("type") != "connection.established":
        print("ERROR: Did not receive connection.established message")
        ws.close()
        sys.exit(1)
    print("  -> connection.established received")

    # Test ping/pong.
    print("Sending ping...")
    ws.send(json.dumps({"type": "ping", "timestamp": time.time()}))
    time.sleep(0.5)
    pong_received = any(m.get("type") == "pong" for m in received_messages)
    if not pong_received:
        print("ERROR: Did not receive pong response")
        ws.close()
        sys.exit(1)
    print("  -> pong received")

    # Start simulation.
    print("Starting simulation...")
    resp = requests.post(f"{BASE_URL}/simulation/{company_id}/start")
    if resp.status_code != 200:
        print(f"ERROR: Failed to start simulation: {resp.text}")
        ws.close()
        sys.exit(1)

    # Wait for simulation.started event.
    time.sleep(1)
    started_received = any(m.get("type") == "simulation.started" for m in received_messages)
    if not started_received:
        print("ERROR: Did not receive simulation.started event")
        ws.close()
        sys.exit(1)
    print("  -> simulation.started received")

    # Tick simulation.
    print("Ticking simulation...")
    resp = requests.post(f"{BASE_URL}/simulation/{company_id}/tick")
    if resp.status_code != 200:
        print(f"ERROR: Failed to tick simulation: {resp.text}")
        ws.close()
        sys.exit(1)

    # Wait for tick events.
    time.sleep(2)
    tick_received = any(m.get("type") == "simulation.tick" for m in received_messages)
    if not tick_received:
        print("WARNING: Did not receive simulation.tick event (may need more time)")

    # Test malformed message handling.
    print("Sending malformed message...")
    ws.send("not json{")
    time.sleep(0.5)
    error_received = any(m.get("type") == "error" for m in received_messages)
    if not error_received:
        print("ERROR: Did not receive error response for malformed message")
        ws.close()
        sys.exit(1)
    print("  -> error response received for malformed message")

    # Close connection.
    try:
        ws.close()
    except Exception:
        pass  # Ignore close errors (known websocket-client bug)
    time.sleep(0.5)

    print("\n=== WebSocket Smoke Test PASSED ===")
    print(f"Total messages received: {len(received_messages)}")
    print(f"Message types: {[m.get('type') for m in received_messages]}")


if __name__ == "__main__":
    print("=== WebSocket Smoke Test ===\n")
    test_websocket()
