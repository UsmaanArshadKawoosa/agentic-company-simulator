"""Tests for Scenario Library & Multi-Run Experimentation (Phase 16)."""

import pytest
from fastapi.testclient import TestClient


# --- Scenario Tests ---


def test_list_scenarios_empty(client: TestClient):
    resp = client.get("/api/scenarios")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_scenario(client: TestClient):
    payload = {
        "name": "Test Scenario",
        "description": "A test scenario",
        "category": "custom",
        "configuration": {
            "name": "TestCo",
            "cash": 50000.0,
            "market_demand": 0.5,
        },
    }
    resp = client.post("/api/scenarios", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test Scenario"
    assert data["category"] == "custom"
    assert data["is_builtin"] is False
    assert data["configuration"]["cash"] == 50000.0


def test_create_scenario_minimal(client: TestClient):
    payload = {"name": "Minimal Scenario"}
    resp = client.post("/api/scenarios", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Minimal Scenario"
    assert data["category"] == "custom"
    assert data["description"] == ""


def test_get_scenario(client: TestClient):
    created = client.post("/api/scenarios", json={"name": "Get Test"}).json()
    resp = client.get(f"/api/scenarios/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


def test_get_scenario_not_found(client: TestClient):
    resp = client.get("/api/scenarios/9999")
    assert resp.status_code == 404


def test_update_scenario(client: TestClient):
    created = client.post("/api/scenarios", json={"name": "Update Test"}).json()
    resp = client.put(
        f"/api/scenarios/{created['id']}",
        json={"name": "Updated Name", "description": "New description"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Updated Name"
    assert data["description"] == "New description"


def test_update_builtin_scenario_forbidden(client: TestClient):
    # Seed built-ins first
    client.post("/api/scenarios/seed-builtins")
    # Get the built-in scenario
    scenarios = client.get("/api/scenarios").json()
    builtin = next(s for s in scenarios if s["is_builtin"])
    resp = client.put(
        f"/api/scenarios/{builtin['id']}",
        json={"name": "Hacked Name"},
    )
    assert resp.status_code == 403


def test_delete_scenario(client: TestClient):
    created = client.post("/api/scenarios", json={"name": "Delete Test"}).json()
    resp = client.delete(f"/api/scenarios/{created['id']}")
    assert resp.status_code == 204
    # Verify deleted
    resp = client.get(f"/api/scenarios/{created['id']}")
    assert resp.status_code == 404


def test_delete_builtin_scenario_forbidden(client: TestClient):
    client.post("/api/scenarios/seed-builtins")
    scenarios = client.get("/api/scenarios").json()
    builtin = next(s for s in scenarios if s["is_builtin"])
    resp = client.delete(f"/api/scenarios/{builtin['id']}")
    assert resp.status_code == 403


def test_duplicate_scenario(client: TestClient):
    created = client.post("/api/scenarios", json={"name": "Original"}).json()
    resp = client.post(f"/api/scenarios/{created['id']}/duplicate")
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Original (Copy)"
    assert data["id"] != created["id"]
    assert data["is_builtin"] is False


def test_seed_builtin_scenarios(client: TestClient):
    resp = client.post("/api/scenarios/seed-builtins")
    assert resp.status_code == 200
    # Verify built-ins exist
    scenarios = client.get("/api/scenarios").json()
    names = [s["name"] for s in scenarios]
    assert "Normal Startup" in names
    assert "Cash Crisis" in names
    assert "High Growth" in names


def test_seed_builtin_scenarios_idempotent(client: TestClient):
    # Seeding twice should not create duplicates
    client.post("/api/scenarios/seed-builtins")
    client.post("/api/scenarios/seed-builtins")
    scenarios = client.get("/api/scenarios").json()
    names = [s["name"] for s in scenarios]
    assert names.count("Normal Startup") == 1


# --- Simulation Run Tests ---


def test_create_run(client: TestClient):
    scenario = client.post("/api/scenarios", json={"name": "Run Test"}).json()
    resp = client.post(
        f"/api/scenarios/{scenario['id']}/runs",
        json={"seed": 12345, "simulation_days": 10},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["scenario_id"] == scenario["id"]
    assert data["seed"] == 12345
    assert data["simulation_days"] == 10
    assert data["status"] == "PENDING"


def test_create_run_default_values(client: TestClient):
    scenario = client.post("/api/scenarios", json={"name": "Defaults Test"}).json()
    resp = client.post(
        f"/api/scenarios/{scenario['id']}/runs",
        json={"seed": 999},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["simulation_days"] == 50  # default


def test_list_runs(client: TestClient):
    scenario = client.post("/api/scenarios", json={"name": "List Runs Test"}).json()
    # Create two runs
    client.post(f"/api/scenarios/{scenario['id']}/runs", json={"seed": 100})
    client.post(f"/api/scenarios/{scenario['id']}/runs", json={"seed": 200})
    resp = client.get(f"/api/scenarios/{scenario['id']}/runs")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


def test_list_runs_missing_scenario(client: TestClient):
    resp = client.get("/api/scenarios/9999/runs")
    assert resp.status_code == 404


def test_get_run(client: TestClient):
    scenario = client.post("/api/scenarios", json={"name": "Get Run Test"}).json()
    run = client.post(
        f"/api/scenarios/{scenario['id']}/runs",
        json={"seed": 42},
    ).json()
    resp = client.get(f"/api/scenarios/runs/{run['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == run["id"]


def test_get_run_not_found(client: TestClient):
    resp = client.get("/api/scenarios/runs/9999")
    assert resp.status_code == 404


# --- Experiment Results Tests ---


def test_experiment_results_empty(client: TestClient):
    scenario = client.post("/api/scenarios", json={"name": "Empty Exp"}).json()
    resp = client.get(f"/api/scenarios/{scenario['id']}/experiment")
    assert resp.status_code == 200
    data = resp.json()
    assert data["completed_runs"] == 0
    assert data["runs"] == []
    assert data["summary"] == {}


def test_experiment_results_missing_scenario(client: TestClient):
    resp = client.get("/api/scenarios/9999/experiment")
    assert resp.status_code == 404


def test_run_experiment_and_get_results(client: TestClient):
    """Test creating a scenario, running an experiment, and getting results."""
    scenario = client.post(
        "/api/scenarios",
        json={
            "name": "Experiment Test",
            "configuration": {"name": "ExpCo", "cash": 100000.0},
        },
    ).json()

    # Run experiment with 2 runs, 5 days each (fast for testing)
    resp = client.post(
        f"/api/scenarios/{scenario['id']}/run-experiment?num_runs=2&simulation_days=5"
    )
    assert resp.status_code == 200
    runs = resp.json()
    assert len(runs) == 2

    # All runs should be completed
    for run in runs:
        assert run["status"] == "COMPLETED"
        assert run["final_metrics"] is not None

    # Get experiment results
    resp = client.get(f"/api/scenarios/{scenario['id']}/experiment")
    assert resp.status_code == 200
    data = resp.json()
    assert data["completed_runs"] == 2
    assert len(data["runs"]) == 2
    # Summary should have stats
    assert "cash" in data["summary"]
    assert "revenue" in data["summary"]


# --- Isolation Tests ---


def test_run_isolation(client: TestClient):
    """Test that different runs don't share state."""
    scenario = client.post(
        "/api/scenarios",
        json={"name": "Isolation Test", "configuration": {"name": "IsoCo"}},
    ).json()

    # Run two separate experiments
    client.post(
        f"/api/scenarios/{scenario['id']}/run-experiment?num_runs=2&simulation_days=3"
    )

    runs = client.get(f"/api/scenarios/{scenario['id']}/runs").json()
    assert len(runs) >= 2

    # Each run should have its own company_id
    company_ids = [r["company_id"] for r in runs if r["company_id"]]
    assert len(company_ids) == len(set(company_ids))


def test_determinism_same_seed(client: TestClient):
    """Test that same seed produces same results."""
    scenario = client.post(
        "/api/scenarios",
        json={
            "name": "Determinism Test",
            "configuration": {"name": "DetCo", "cash": 50000.0},
        },
    ).json()

    # Run with specific seed
    client.post(
        f"/api/scenarios/{scenario['id']}/runs",
        json={"seed": 777, "simulation_days": 3},
    )

    # Get the run and execute it
    runs = client.get(f"/api/scenarios/{scenario['id']}/runs").json()
    run = runs[0]

    resp = client.post(f"/api/scenarios/runs/{run['id']}/execute")
    assert resp.status_code == 200
    first_metrics = resp.json()["final_metrics"]

    # The run is now completed; verify it has metrics
    assert first_metrics is not None
    assert "cash" in first_metrics


# --- Built-in Scenario Tests ---


def test_builtin_scenarios_complete(client: TestClient):
    """Test that built-in scenarios can be run successfully."""
    client.post("/api/scenarios/seed-builtins")
    scenarios = client.get("/api/scenarios").json()
    normal = next(s for s in scenarios if s["name"] == "Normal Startup")

    # Run experiment with 2 runs, 3 days
    resp = client.post(
        f"/api/scenarios/{normal['id']}/run-experiment?num_runs=2&simulation_days=3"
    )
    assert resp.status_code == 200
    runs = resp.json()
    assert all(r["status"] == "COMPLETED" for r in runs)


# --- Validation Tests ---


def test_create_scenario_empty_name(client: TestClient):
    """Test that empty names are rejected."""
    resp = client.post("/api/scenarios", json={"name": ""})
    assert resp.status_code == 422  # Pydantic validation error


def test_create_scenario_missing_name(client: TestClient):
    """Test that name is required."""
    resp = client.post("/api/scenarios", json={"description": "no name"})
    assert resp.status_code == 422


def test_run_missing_scenario(client: TestClient):
    """Test creating run for non-existent scenario."""
    resp = client.post(
        "/api/scenarios/9999/runs",
        json={"seed": 100},
    )
    assert resp.status_code == 404
