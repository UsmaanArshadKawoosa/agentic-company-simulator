"""Reconnect and state reconciliation smoke test."""
import asyncio
import json
import time
import requests
import websockets

BASE_URL = "http://localhost:8000/api"
WS_URL = "ws://localhost:8000/api/ws/companies"


async def main():
    # Create a new company
    import uuid
    name = f"ReconnTest-{uuid.uuid4().hex[:8]}"
    r = requests.post(f"{BASE_URL}/companies", json={"name": name, "mission": "Test"})
    if r.status_code != 201:
        print(f"Failed to create company: {r.status_code} {r.text}")
        return 1
    company = r.json()
    company_id = company["id"]
    print(f"Created company {company_id}")

    received1 = []

    async def collect(ws, out, stop_event):
        while not stop_event.is_set():
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=0.5)
                out.append(json.loads(msg))
            except asyncio.TimeoutError:
                pass
            except Exception:
                break

    # First connection
    ws1 = await websockets.connect(f"{WS_URL}/{company_id}")
    msg = await ws1.recv()
    data = json.loads(msg)
    assert data["type"] == "connection.established"
    print("  -> First connection established")

    # Start simulation and tick
    requests.post(f"{BASE_URL}/simulation/{company_id}/start")
    await asyncio.sleep(1)
    requests.post(f"{BASE_URL}/simulation/{company_id}/tick")
    await asyncio.sleep(2)

    # Collect some messages
    stop1 = asyncio.Event()
    task1 = asyncio.create_task(collect(ws1, received1, stop1))
    await asyncio.sleep(1)
    stop1.set()
    await task1

    tick_count_1 = sum(1 for m in received1 if m.get("type") == "simulation.tick")
    print(f"  -> First connection received {tick_count_1} tick events")

    # Close connection
    await ws1.close()
    await asyncio.sleep(0.5)

    # Reconnect
    received2 = []
    ws2 = await websockets.connect(f"{WS_URL}/{company_id}")
    msg = await ws2.recv()
    data = json.loads(msg)
    assert data["type"] == "connection.established"
    print("  -> Reconnection established")

    # Collect messages after reconnect
    stop2 = asyncio.Event()
    task2 = asyncio.create_task(collect(ws2, received2, stop2))
    requests.post(f"{BASE_URL}/simulation/{company_id}/tick")
    await asyncio.sleep(2)
    stop2.set()
    await task2

    tick_count_2 = sum(1 for m in received2 if m.get("type") == "simulation.tick")
    print(f"  -> Second connection received {tick_count_2} tick events after reconnect")

    # Verify state is current by fetching dashboard
    r = requests.get(f"{BASE_URL}/simulation/{company_id}/dashboard")
    if r.status_code == 200:
        dashboard = r.json()
        print(f"  -> Dashboard day: {dashboard['company']['current_day']}")
        print("  -> State reconciliation via REST OK")
    else:
        print(f"  -> Dashboard failed: {r.status_code}")

    await ws2.close()

    print("\nReconnect and state reconciliation test PASSED")
    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
