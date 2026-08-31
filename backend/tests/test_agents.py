from app.enums import AgentRole


def test_four_agents_created(client):
    created = client.post("/api/companies", json={"name": "OrgCo", "mission": "m"}).json()
    resp = client.get(f"/api/companies/{created['id']}/agents")
    assert resp.status_code == 200
    agents = resp.json()
    assert len(agents) == 4
    roles = {a["role"] for a in agents}
    assert roles == {
        AgentRole.CEO.value,
        AgentRole.CTO.value,
        AgentRole.CMO.value,
        AgentRole.ENGINEER.value,
    }


def test_agent_hierarchy(client):
    created = client.post("/api/companies", json={"name": "HierCo", "mission": "m"}).json()
    agents = {
        a["role"]: a for a in client.get(f"/api/companies/{created['id']}/agents").json()
    }
    ceo = agents[AgentRole.CEO.value]
    cto = agents[AgentRole.CTO.value]
    cmo = agents[AgentRole.CMO.value]
    engineer = agents[AgentRole.ENGINEER.value]

    assert ceo["manager_id"] is None
    assert cto["manager_id"] == ceo["id"]
    assert cmo["manager_id"] == ceo["id"]
    assert engineer["manager_id"] == cto["id"]

    # Subordinates endpoint reflects the manager relationship.
    subs = client.get(f"/api/agents/{ceo['id']}/subordinates").json()
    sub_roles = {s["role"] for s in subs}
    assert sub_roles == {AgentRole.CTO.value, AgentRole.CMO.value}


def test_agent_fields_and_json(client):
    created = client.post("/api/companies", json={"name": "JsonCo", "mission": "m"}).json()
    ceo = next(
        a for a in client.get(f"/api/companies/{created['id']}/agents").json()
        if a["role"] == AgentRole.CEO.value
    )
    assert isinstance(ceo["personality"], dict) and ceo["personality"]
    assert isinstance(ceo["skills"], list) and ceo["skills"]
    assert ceo["authority"] == 10
    assert ceo["budget"] == 50000.0
