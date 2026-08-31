from app.enums import AgentRole, CompanyStatus, EventType


def test_end_to_end_flow(client):
    # Create company -> 4 agents seeded automatically.
    company = client.post(
        "/api/companies", json={"name": "E2ECo", "mission": "end to end"}
    ).json()
    assert company["status"] == CompanyStatus.CREATED.value

    agents = client.get(f"/api/companies/{company['id']}/agents").json()
    assert len(agents) == 4

    # Start and advance the simulation.
    assert client.post(f"/api/simulation/{company['id']}/start").status_code == 200
    assert client.post(f"/api/simulation/{company['id']}/tick").status_code == 200

    # Events are persisted and queryable.
    events = client.get(f"/api/companies/{company['id']}/events").json()
    types = {e["event_type"] for e in events}
    assert EventType.COMPANY_CREATED.value in types
    assert EventType.AGENT_SPAWNED.value in types
    assert EventType.SIMULATION_STARTED.value in types
    assert EventType.TICK.value in types

    # State reflects progress.
    state = client.get(f"/api/simulation/{company['id']}").json()
    assert state["current_day"] == 2
    assert state["status"] == CompanyStatus.RUNNING.value
    assert state["event_count"] == len(events)


def test_list_companies(client):
    # Create two companies.
    c1 = client.post("/api/companies", json={"name": "ListCo1", "mission": "m1"}).json()
    c2 = client.post("/api/companies", json={"name": "ListCo2", "mission": "m2"}).json()

    # List endpoint returns both.
    resp = client.get("/api/companies")
    assert resp.status_code == 200
    companies = resp.json()
    names = {c["name"] for c in companies}
    assert "ListCo1" in names
    assert "ListCo2" in names

    # Each company has expected fields.
    for c in companies:
        assert "id" in c
        assert "name" in c
        assert "status" in c
        assert "cash" in c


def test_list_companies_empty(client):
    # No companies created in this test - but other tests may have created some.
    # Just verify the endpoint works.
    resp = client.get("/api/companies")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_agents_endpoint_404(client):
    assert client.get("/api/companies/12345/agents").status_code == 404


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_event_type_enum_has_required_members():
    required = {
        "COMPANY_CREATED", "AGENT_SPAWNED", "SIMULATION_STARTED",
        "SIMULATION_PAUSED", "TICK", "OBSERVE", "THINK", "DECIDE",
        "ACT", "REFLECT", "DECISION",
    }
    assert required.issubset({m.name for m in EventType})


def test_agent_role_enum_has_required_members():
    assert {AgentRole.CEO.value, AgentRole.CTO.value, AgentRole.CMO.value, AgentRole.ENGINEER.value} == {
        "CEO", "CTO", "CMO", "ENGINEER"
    }
