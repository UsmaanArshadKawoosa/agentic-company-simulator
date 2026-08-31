from app.enums import AgentRole, CompanyStatus
from app.schemas.company import CompanyRead


def test_create_company(client):
    resp = client.post("/api/companies", json={"name": "Acme Inc", "mission": "Build great products"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Acme Inc"
    assert data["cash"] == 100000.0
    assert data["revenue"] == 0.0
    assert data["expenses"] == 0.0
    assert data["current_day"] == 1
    assert data["status"] == CompanyStatus.CREATED.value


def test_create_company_duplicate(client):
    payload = {"name": "Dup Co", "mission": "x"}
    assert client.post("/api/companies", json=payload).status_code == 201
    assert client.post("/api/companies", json=payload).status_code == 409


def test_get_company(client):
    created = client.post("/api/companies", json={"name": "GetCo", "mission": "m"}).json()
    resp = client.get(f"/api/companies/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


def test_get_company_not_found(client):
    assert client.get("/api/companies/9999").status_code == 404


def test_company_defaults_via_schema():
    # Ensures the read schema validates the expected defaults shape.
    CompanyRead(
        id=1, name="x", mission="", cash=100000.0, revenue=0.0, expenses=0.0,
        current_day=1, status=CompanyStatus.CREATED, seed=12345,
        created_at="2026-01-01T00:00:00", updated_at="2026-01-01T00:00:00",
    )
    assert AgentRole.CEO.value == "CEO"
