from app.enums import CompanyStatus, EventType


def _create_company(client, name="SimCo"):
    return client.post("/api/companies", json={"name": name, "mission": "m"}).json()


def test_simulation_start(client):
    company = _create_company(client)
    resp = client.post(f"/api/simulation/{company['id']}/start")
    assert resp.status_code == 200
    state = resp.json()["state"]
    assert state["status"] == CompanyStatus.RUNNING.value
    event_types = {e["event_type"] for e in state["recent_events"]}
    assert EventType.SIMULATION_STARTED.value in event_types


def test_simulation_tick(client):
    company = _create_company(client)
    client.post(f"/api/simulation/{company['id']}/start")

    before = client.get(f"/api/companies/{company['id']}/events").json()
    resp = client.post(f"/api/simulation/{company['id']}/tick")
    assert resp.status_code == 200
    state = resp.json()["state"]
    assert state["current_day"] == 2

    after = client.get(f"/api/companies/{company['id']}/events").json()
    assert len(after) > len(before)

    event_types = {e["event_type"] for e in after}
    assert EventType.TICK.value in event_types
    assert EventType.OBSERVE.value in event_types
    assert EventType.ACT.value in event_types


def test_simulation_tick_deterministic(client):
    company = _create_company(client)
    client.post(f"/api/simulation/{company['id']}/start")
    r1 = client.post(f"/api/simulation/{company['id']}/tick").json()["state"]
    # Fresh company for an independent run.
    company2 = _create_company(client, "SimCo2")
    client.post(f"/api/simulation/{company2['id']}/start")
    r2 = client.post(f"/api/simulation/{company2['id']}/tick").json()["state"]
    assert r1["current_day"] == r2["current_day"] == 2
    assert r1["agent_count"] == r2["agent_count"] == 4


def test_simulation_pause(client):
    company = _create_company(client)
    client.post(f"/api/simulation/{company['id']}/start")
    resp = client.post(f"/api/simulation/{company['id']}/pause")
    assert resp.status_code == 200
    assert resp.json()["state"]["status"] == CompanyStatus.PAUSED.value


def test_tick_without_start_rejected(client):
    company = _create_company(client)
    resp = client.post(f"/api/simulation/{company['id']}/tick")
    assert resp.status_code == 400


def test_get_simulation_state(client):
    company = _create_company(client)
    client.post(f"/api/simulation/{company['id']}/start")
    client.post(f"/api/simulation/{company['id']}/tick")
    resp = client.get(f"/api/simulation/{company['id']}")
    assert resp.status_code == 200
    state = resp.json()
    assert state["company_id"] == company["id"]
    assert state["current_day"] == 2
    assert state["agent_count"] == 4


def test_history_endpoint_empty(client):
    """History endpoint returns empty series for new company."""
    company = _create_company(client)
    resp = client.get(f"/api/simulation/{company['id']}/history")
    assert resp.status_code == 200
    data = resp.json()
    assert data["company_id"] == company["id"]
    assert data["data_points"] == 0
    assert data["series"] == []


def test_history_endpoint_with_data(client):
    """History endpoint returns financial time series after simulation ticks."""
    company = _create_company(client)
    client.post(f"/api/simulation/{company['id']}/start")
    client.post(f"/api/simulation/{company['id']}/tick")
    client.post(f"/api/simulation/{company['id']}/tick")

    resp = client.get(f"/api/simulation/{company['id']}/history")
    assert resp.status_code == 200
    data = resp.json()
    assert data["company_id"] == company["id"]
    assert data["data_points"] > 0
    assert len(data["series"]) > 0

    # Verify structure of data points
    point = data["series"][0]
    assert "day" in point
    assert "cash" in point
    assert "revenue" in point
    assert "expenses" in point
    assert "profit" in point


def test_history_endpoint_limit(client):
    """History endpoint respects the limit parameter."""
    company = _create_company(client)
    client.post(f"/api/simulation/{company['id']}/start")
    for _ in range(5):
        client.post(f"/api/simulation/{company['id']}/tick")

    resp = client.get(f"/api/simulation/{company['id']}/history?limit=3")
    assert resp.status_code == 200
    data = resp.json()
    assert data["data_points"] <= 3
    assert len(data["series"]) <= 3


def test_history_endpoint_missing_company(client):
    """History endpoint returns 404 for non-existent company."""
    resp = client.get("/api/simulation/99999/history")
    assert resp.status_code == 404


def test_decisions_endpoint_empty(client):
    """Decisions endpoint returns empty list for new company."""
    company = _create_company(client)
    resp = client.get(f"/api/simulation/{company['id']}/decisions")
    assert resp.status_code == 200
    data = resp.json()
    assert data["company_id"] == company["id"]
    assert data["count"] == 0
    assert data["decisions"] == []


def test_decisions_endpoint_with_data(client):
    """Decisions endpoint returns decisions after simulation ticks."""
    company = _create_company(client)
    client.post(f"/api/simulation/{company['id']}/start")
    client.post(f"/api/simulation/{company['id']}/tick")

    resp = client.get(f"/api/simulation/{company['id']}/decisions")
    assert resp.status_code == 200
    data = resp.json()
    assert data["company_id"] == company["id"]
    assert data["count"] > 0
    assert len(data["decisions"]) > 0

    # Verify structure
    decision = data["decisions"][0]
    assert "id" in decision
    assert "action" in decision
    assert "simulation_day" in decision
    assert "evaluation" in decision


def test_decisions_endpoint_limit(client):
    """Decisions endpoint respects the limit parameter."""
    company = _create_company(client)
    client.post(f"/api/simulation/{company['id']}/start")
    for _ in range(5):
        client.post(f"/api/simulation/{company['id']}/tick")

    resp = client.get(f"/api/simulation/{company['id']}/decisions?limit=5")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] <= 5


def test_decisions_endpoint_missing_company(client):
    """Decisions endpoint returns 404 for non-existent company."""
    resp = client.get("/api/simulation/99999/decisions")
    assert resp.status_code == 404
