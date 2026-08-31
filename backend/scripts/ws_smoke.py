"""WebSocket smoke test for Phase 8 verification (using websockets)."""
import asyncio
import json
import time
import requests
import websockets

BASE_URL = "http://localhost:8000/api"
WS_URL = "ws://localhost:8000/api/ws/companies"


async def main():
    import uuid
    name = f"WSTestCo-{uuid.uuid4().hex[:8]}"
    r = requests.post(f"{BASE_URL}/companies", json={"name": name, "mission": "Test"})
    if r.status_code != 201:
        print(f"Failed to create company: {r.status_code} {r.text}")
        return 1
    company = r.json()
    company_id = company["id"]
    print(f"Created company {company_id}")

    received = []

    async with websockets.connect(f"{WS_URL}/{company_id}") as ws:
        # 1. connection.established
        msg = await ws.recv()
        data = json.loads(msg)
        received.append(data)
        print(f"  Received: {data.get('type')}")
        assert data["type"] == "connection.established", f"Expected connection.established, got {data['type']}"
        print("  -> connection.established OK")

        # 2. Ping/pong
        await ws.send(json.dumps({"type": "ping", "timestamp": time.time()}))
        msg = await ws.recv()
        data = json.loads(msg)
        received.append(data)
        print(f"  Received: {data.get('type')}")
        assert data["type"] == "pong", f"Expected pong, got {data['type']}"
        print("  -> pong OK")

        # 3. Start simulation
        r = requests.post(f"{BASE_URL}/simulation/{company_id}/start")
        print(f"Start: {r.status_code}")
        await asyncio.sleep(1)

        # 4. Tick simulation
        r = requests.post(f"{BASE_URL}/simulation/{company_id}/tick")
        print(f"Tick: {r.status_code}")
        await asyncio.sleep(2)

        # Collect all remaining messages
        while True:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=1)
                data = json.loads(msg)
                received.append(data)
                print(f"  Received: {data.get('type')}")
            except asyncio.TimeoutError:
                break

    # Verify expected messages
    types = [m.get("type") for m in received]
    print(f"\nTotal messages: {len(received)}")
    print("Types:", types)

    expected = ["connection.established", "simulation.started", "simulation.tick"]
    missing = [t for t in expected if t not in types]
    if missing:
        print(f"WARNING: Missing expected message types: {missing}")
        return 1

    print("\nAll expected message types received.")
    print("WebSocket smoke test PASSED")
    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
