"""Tests for API pagination and limit validation."""
import pytest
from fastapi.testclient import TestClient

from app.db.database import engine, Base, SessionLocal
from app.main import app
from app.models.company import Company
from app.models.scenario import Scenario, SimulationRun
from app.models.event import Event
from app.models.employee import Employee
from app.models.agent import Agent
from app.models.job_opening import JobOpening
from app.models.candidate import Candidate
from app.models.risk import Risk
from app.models.incident import Incident
from app.models.objective import Objective
from app.models.resource_allocation import ResourceAllocation
from app.models.campaign import Campaign
from app.models.sales_opportunity import SalesOpportunity
from app.models.investor import Investor
from app.models.funding_round import FundingRound
from app.models.fundraising_pipeline import FundraisingPipeline
from app.models.cap_table import CapTableEntry
from app.models.budget_request import BudgetRequest
from app.enums import (
    AgentRole,
    EventType,
    ScenarioStatus,
    EmployeeStatus,
    JobStatus,
    IncidentType,
    RiskSeverity,
    ResourceType,
    ObjectiveType,
    SalesStage,
    FundingRoundStatus,
    InvestorStage,
    BudgetStatus,
)


@pytest.fixture(autouse=True)
def _reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def company(db):
    c = Company(name="Pagination Co", mission="Test pagination", cash=1000.0, revenue=0.0, expenses=0.0)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@pytest.fixture
def scenario(db):
    s = Scenario(name="Pagination Scenario", description="Test", category="test")
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


class TestPaginationLimits:
    def test_list_events_default_limit(self, client, company, db):
        for i in range(5):
            e = Event(company_id=company.id, event_type=EventType.TICK, description=f"Event {i}", simulation_day=i + 1)
            db.add(e)
        db.commit()

        response = client.get(f"/api/companies/{company.id}/events")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 100

    def test_list_events_custom_limit(self, client, company, db):
        for i in range(10):
            e = Event(company_id=company.id, event_type=EventType.TICK, description=f"Event {i}", simulation_day=i + 1)
            db.add(e)
        db.commit()

        response = client.get(f"/api/companies/{company.id}/events?limit=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 3

    def test_list_events_max_limit(self, client, company, db):
        for i in range(10):
            e = Event(company_id=company.id, event_type=EventType.TICK, description=f"Event {i}", simulation_day=i + 1)
            db.add(e)
        db.commit()

        response = client.get(f"/api/companies/{company.id}/events?limit=9999")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 1000

    def test_list_employees_with_limit(self, client, company, db):
        agent = Agent(company_id=company.id, role=AgentRole.CEO, name="CEO Agent")
        db.add(agent)
        db.commit()
        db.refresh(agent)

        for i in range(5):
            e = Employee(company_id=company.id, name=f"Emp {i}", role="ENGINEER", status=EmployeeStatus.ACTIVE)
            db.add(e)
        db.commit()

        response = client.get(f"/api/workforce/companies/{company.id}/employees?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

    def test_list_jobs_with_limit(self, client, company, db):
        for i in range(5):
            j = JobOpening(company_id=company.id, role="ENGINEER", title=f"Job {i}", status=JobStatus.OPEN, created_day=1)
            db.add(j)
        db.commit()

        response = client.get(f"/api/workforce/companies/{company.id}/jobs?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

    def test_list_candidates_with_limit(self, client, company, db):
        for i in range(5):
            c = Candidate(company_id=company.id, name=f"Cand {i}", role="ENGINEER", status=EmployeeStatus.CANDIDATE)
            db.add(c)
        db.commit()

        response = client.get(f"/api/workforce/companies/{company.id}/candidates?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

    def test_list_scenarios_with_limit(self, client, db):
        for i in range(5):
            s = Scenario(name=f"Scenario {i}", description="Test", category="test")
            db.add(s)
        db.commit()

        response = client.get("/api/scenarios?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

    def test_list_runs_with_limit(self, client, scenario, company, db):
        for i in range(5):
            r = SimulationRun(scenario_id=scenario.id, company_id=company.id, seed=i, status=ScenarioStatus.COMPLETED)
            db.add(r)
        db.commit()

        response = client.get(f"/api/scenarios/{scenario.id}/runs?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

    def test_list_objectives_with_limit(self, client, company, db):
        for i in range(5):
            o = Objective(company_id=company.id, title=f"Obj {i}", objective_type=ObjectiveType.OPERATIONAL, priority=1, status="TODO", progress=0.0, created_day=1)
            db.add(o)
        db.commit()

        response = client.get(f"/api/operations/companies/{company.id}/objectives?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

    def test_list_risks_with_limit(self, client, company, db):
        for i in range(5):
            r = Risk(company_id=company.id, risk_type="MARKET", severity=RiskSeverity.MEDIUM, status="ACTIVE", detected_day=1)
            db.add(r)
        db.commit()

        response = client.get(f"/api/operations/companies/{company.id}/risks?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

    def test_list_incidents_with_limit(self, client, company, db):
        for i in range(5):
            inc = Incident(company_id=company.id, incident_type=IncidentType.RUNWAY_CRISIS, severity=RiskSeverity.MEDIUM, status="ACTIVE", detected_day=1)
            db.add(inc)
        db.commit()

        response = client.get(f"/api/operations/companies/{company.id}/incidents?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

    def test_list_resources_with_limit(self, client, company, db):
        for i in range(5):
            ra = ResourceAllocation(company_id=company.id, resource_type=ResourceType.CASH, allocated_amount=100.0, available_amount=100.0, allocation_day=1)
            db.add(ra)
        db.commit()

        response = client.get(f"/api/operations/companies/{company.id}/resources?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

    def test_list_campaigns_with_limit(self, client, company, db):
        for i in range(5):
            c = Campaign(company_id=company.id, name=f"Campaign {i}", segment="ENTERPRISE", budget=1000.0, daily_spend=100.0, days_remaining=10, effectiveness=0.5, status="ACTIVE")
            db.add(c)
        db.commit()

        response = client.get(f"/api/simulation/{company.id}/campaigns?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

    def test_list_sales_with_limit(self, client, company, db):
        for i in range(5):
            s = SalesOpportunity(company_id=company.id, name=f"Opp {i}", segment="ENTERPRISE", value=5000.0, stage=SalesStage.PROPOSAL, created_day=1, expected_close_day=10)
            db.add(s)
        db.commit()

        response = client.get(f"/api/simulation/{company.id}/sales?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

    def test_list_investors_with_limit(self, client, company, db):
        for i in range(5):
            inv = Investor(company_id=company.id, name=f"Inv {i}", preferred_stage=InvestorStage.SEED, check_size_min=100000.0, check_size_max=500000.0, risk_tolerance=0.5, sector_preference="TECH", ownership_expectation=0.1, reputation=0.5, interest_score=0.5)
            db.add(inv)
        db.commit()

        response = client.get(f"/api/simulation/{company.id}/investors?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

    def test_list_funding_rounds_with_limit(self, client, company, db):
        for i in range(5):
            fr = FundingRound(company_id=company.id, round_stage=InvestorStage.SEED, amount_requested=1000000.0, status=FundingRoundStatus.DISCOVERED, day_opened=1)
            db.add(fr)
        db.commit()

        response = client.get(f"/api/simulation/{company.id}/funding-rounds?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

    def test_list_pipeline_with_limit(self, client, company, db):
        for i in range(5):
            p = FundraisingPipeline(company_id=company.id, investor_id=i+1, funding_round_id=i+1, status=FundingRoundStatus.DISCOVERED, stage=InvestorStage.SEED, interest_score=0.5, day_updated=1)
            db.add(p)
        db.commit()

        response = client.get(f"/api/simulation/{company.id}/pipeline?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

    def test_list_cap_table_with_limit(self, client, company, db):
        for i in range(5):
            ct = CapTableEntry(company_id=company.id, owner_type="FOUNDER", owner_id=i+1, owner_name=f"Founder {i}", ownership_percentage=50.0, shares=500000)
            db.add(ct)
        db.commit()

        response = client.get(f"/api/simulation/{company.id}/cap-table?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

    def test_list_budget_requests_with_limit(self, client, company, db):
        agent = Agent(company_id=company.id, role=AgentRole.CEO, name="CEO")
        db.add(agent)
        db.commit()
        db.refresh(agent)
        for i in range(5):
            br = BudgetRequest(company_id=company.id, requester_id=agent.id, amount=1000.0, purpose=f"Request {i}", status=BudgetStatus.PENDING, requested_day=1)
            db.add(br)
        db.commit()

        response = client.get(f"/api/simulation/{company.id}/budget-requests?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2
