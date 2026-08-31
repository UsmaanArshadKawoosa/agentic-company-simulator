"""Tests for Phase 9: Organization, Workforce & Autonomous Hiring."""

from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.main import app
from app.models.company import Company
from app.models.agent import Agent
from app.models.employee import Employee
from app.models.job_opening import JobOpening
from app.models.candidate import Candidate
from app.models.decision import Decision
from app.models.event import Event
from app.enums import (
    AgentRole,
    AgentStatus,
    CompanyStatus,
    EmployeeStatus,
    JobStatus,
    EventType,
)
from app.agents.decisions import ActionType
from app.simulation.engine import SimulationEngine
from app.simulation import workforce as workforce_system
from app.simulation import candidates as candidate_system
from app.simulation.domain import SimulationContext, make_rng


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def test_company(client: TestClient) -> dict:
    resp = client.post("/api/companies", json={"name": "TestCo Phase9", "mission": "Test"})
    assert resp.status_code == 201, f"Failed to create company: {resp.text}"
    return resp.json()


@pytest.fixture
def db_with_company(test_company: dict) -> Session:
    from app.db.database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Workforce Model
# ---------------------------------------------------------------------------


class TestEmployeeModel:
    def test_create_employee(self, db_with_company: Session, test_company: dict):
        db = db_with_company
        emp = Employee(
            company_id=test_company["id"],
            name="Alice",
            role="ENGINEER",
            status=EmployeeStatus.ACTIVE,
            salary=3000.0,
            capacity=5.0,
            experience=2.0,
            performance_score=0.5,
            morale=0.7,
            productivity=0.8,
        )
        db.add(emp)
        db.flush()
        assert emp.id is not None
        assert emp.name == "Alice"
        assert emp.role == "ENGINEER"

    def test_employee_hierarchy(self, db_with_company: Session, test_company: dict):
        db = db_with_company
        manager = Employee(
            company_id=test_company["id"],
            name="Bob",
            role="CTO",
            status=EmployeeStatus.ACTIVE,
            salary=5000.0,
            capacity=3.0,
        )
        db.add(manager)
        db.flush()
        subordinate = Employee(
            company_id=test_company["id"],
            name="Carol",
            role="ENGINEER",
            status=EmployeeStatus.ACTIVE,
            salary=3000.0,
            capacity=5.0,
            manager_id=manager.id,
        )
        db.add(subordinate)
        db.flush()
        assert subordinate.manager_id == manager.id
        assert len(manager.subordinates) == 1
        assert manager.subordinates[0].name == "Carol"


# ---------------------------------------------------------------------------
# Job Openings
# ---------------------------------------------------------------------------


class TestJobOpenings:
    def test_create_job_opening(self, db_with_company: Session, test_company: dict):
        db = db_with_company
        job = JobOpening(
            company_id=test_company["id"],
            role="ENGINEER",
            title="Senior Engineer",
            description="Build backend services",
            required_skills=["python", "sql"],
            salary_min=4000.0,
            salary_max=6000.0,
            capacity_required=5.0,
            created_day=1,
            status=JobStatus.OPEN,
        )
        db.add(job)
        db.flush()
        assert job.id is not None
        assert job.status == JobStatus.OPEN

    def test_job_opening_statuses(self, db_with_company: Session, test_company: dict):
        db = db_with_company
        job = JobOpening(
            company_id=test_company["id"],
            role="DESIGNER",
            title="UX Designer",
            description="Design UI",
            required_skills=["figma"],
            salary_min=3000.0,
            salary_max=5000.0,
            capacity_required=4.0,
            created_day=1,
            status=JobStatus.OPEN,
        )
        db.add(job)
        db.flush()
        job.status = JobStatus.FILLED
        db.flush()
        assert job.status == JobStatus.FILLED


# ---------------------------------------------------------------------------
# Candidates
# ---------------------------------------------------------------------------


class TestCandidates:
    def test_deterministic_candidate_generation(self, db_with_company: Session, test_company: dict):
        db = db_with_company
        job = JobOpening(
            company_id=test_company["id"],
            role="ENGINEER",
            title="Engineer",
            description="",
            required_skills=[],
            salary_min=2000.0,
            salary_max=5000.0,
            capacity_required=5.0,
            created_day=1,
            status=JobStatus.OPEN,
        )
        db.add(job)
        db.flush()

        company = db.get(Company, test_company["id"])
        ctx = SimulationContext(db=db, company=company, day=1, rng=make_rng(company.seed, 1))
        batch1 = candidate_system.generate_candidates(ctx, job, count=3)
        db.commit()

        ctx2 = SimulationContext(db=db, company=company, day=1, rng=make_rng(company.seed, 1))
        batch2 = candidate_system.generate_candidates(ctx2, job, count=3)
        db.commit()

        assert len(batch1) == len(batch2) == 3
        for c1, c2 in zip(batch1, batch2):
            assert c1.name == c2.name
            assert c1.salary_expectation == c2.salary_expectation
            assert c1.productivity_potential == c2.productivity_potential

    def test_candidate_evaluation(self, db_with_company: Session, test_company: dict):
        db = db_with_company
        job = JobOpening(
            company_id=test_company["id"],
            role="ENGINEER",
            title="Engineer",
            description="",
            required_skills=["python", "sql"],
            salary_min=2000.0,
            salary_max=5000.0,
            capacity_required=5.0,
            created_day=1,
            status=JobStatus.OPEN,
        )
        db.add(job)
        db.flush()
        candidate = Candidate(
            company_id=test_company["id"],
            job_opening_id=job.id,
            name="Dave",
            role="ENGINEER",
            skills=["python", "sql", "docker"],
            experience=3.0,
            salary_expectation=3500.0,
            productivity_potential=0.8,
            culture_fit=0.9,
            reliability=0.85,
        )
        db.add(candidate)
        db.flush()

        company = db.get(Company, test_company["id"])
        ctx = SimulationContext(db=db, company=company, day=1, rng=make_rng(company.seed, 1))
        evaluated = candidate_system.evaluate_candidate(ctx, candidate, evaluator_agent_id=1)
        assert evaluated.hiring_score > 0.0
        assert evaluated.status == "INTERVIEWING"


# ---------------------------------------------------------------------------
# Workforce Domain Logic
# ---------------------------------------------------------------------------


class TestWorkforceLogic:
    def test_hire_employee(self, db_with_company: Session, test_company: dict):
        db = db_with_company
        job = JobOpening(
            company_id=test_company["id"],
            role="ENGINEER",
            title="Engineer",
            description="",
            required_skills=[],
            salary_min=2000.0,
            salary_max=5000.0,
            capacity_required=5.0,
            created_day=1,
            status=JobStatus.OPEN,
        )
        db.add(job)
        db.flush()

        company = db.get(Company, test_company["id"])
        ctx = SimulationContext(db=db, company=company, day=1, rng=make_rng(company.seed, 1))
        emp, events = workforce_system.hire_employee(ctx, job, "Eve", 3000.0)
        assert emp is not None
        assert emp.status == EmployeeStatus.ONBOARDING
        assert emp.capacity == 5.0
        assert job.status == "FILLED"
        assert company.cash < 100000.0  # hiring cost deducted

    def test_terminate_employee(self, db_with_company: Session, test_company: dict):
        db = db_with_company
        emp = Employee(
            company_id=test_company["id"],
            name="Frank",
            role="ENGINEER",
            status=EmployeeStatus.ACTIVE,
            salary=3000.0,
            capacity=5.0,
        )
        db.add(emp)
        db.flush()

        company = db.get(Company, test_company["id"])
        ctx = SimulationContext(db=db, company=company, day=5, rng=make_rng(company.seed, 5))
        events = workforce_system.terminate_employee(ctx, emp, "underperforming")
        assert emp.status == EmployeeStatus.TERMINATED
        assert emp.capacity == 0.0
        assert len(events) == 1

    def test_onboarding_advance(self, db_with_company: Session, test_company: dict):
        db = db_with_company
        emp = Employee(
            company_id=test_company["id"],
            name="Grace",
            role="ENGINEER",
            status=EmployeeStatus.ONBOARDING,
            salary=3000.0,
            capacity=5.0,
            hired_day=1,
            onboarding_factor=0.5,
        )
        db.add(emp)
        db.flush()

        company = db.get(Company, test_company["id"])
        ctx = SimulationContext(db=db, company=company, day=6, rng=make_rng(company.seed, 6))
        events = workforce_system.update_onboarding(ctx)
        assert emp.status == EmployeeStatus.ACTIVE
        assert emp.onboarding_factor == 1.0
        assert len(events) == 1

    def test_capacity_calculation(self, db_with_company: Session, test_company: dict):
        db = db_with_company
        emp1 = Employee(
            company_id=test_company["id"],
            name="Hank",
            role="ENGINEER",
            status=EmployeeStatus.ACTIVE,
            salary=3000.0,
            capacity=5.0,
            productivity=0.8,
            morale=0.9,
            onboarding_factor=1.0,
        )
        emp2 = Employee(
            company_id=test_company["id"],
            name="Ivy",
            role="ENGINEER",
            status=EmployeeStatus.ACTIVE,
            salary=3000.0,
            capacity=5.0,
            productivity=0.7,
            morale=0.8,
            onboarding_factor=1.0,
        )
        db.add_all([emp1, emp2])
        db.flush()

        company = db.get(Company, test_company["id"])
        ctx = SimulationContext(db=db, company=company, day=1, rng=make_rng(company.seed, 1))
        capacity = workforce_system.total_workforce_capacity(ctx)
        expected = 5.0 * 0.8 * 0.9 + 5.0 * 0.7 * 0.8
        assert abs(capacity.get("ENGINEER", 0.0) - expected) < 0.01


# ---------------------------------------------------------------------------
# Decision Validation
# ---------------------------------------------------------------------------


class TestWorkforceDecisions:
    def test_create_job_opening_via_validator(self, db_with_company: Session, test_company: dict):
        db = db_with_company
        company = db.get(Company, test_company["id"])
        agent = db.execute(select(Agent).where(Agent.company_id == company.id)).first()
        if agent is None:
            pytest.skip("No agent found")
        agent = agent[0]
        from app.agents.validator import DecisionValidator
        from app.agents.decisions import AgentDecision

        validator = DecisionValidator(db, agent, company)
        decision = AgentDecision(
            action=ActionType.CREATE_JOB_OPENING,
            reasoning="Need more engineers",
            job_title="Senior Engineer",
            job_role="ENGINEER",
            salary_min=4000,
            salary_max=6000,
        )
        result = validator.execute(decision)
        assert result.success is True
        job = db.execute(select(JobOpening).where(JobOpening.company_id == company.id)).scalar_one_or_none()
        assert job is not None
        assert job.role == "ENGINEER"

    def test_unauthorized_hiring(self, db_with_company: Session, test_company: dict):
        db = db_with_company
        company = db.get(Company, test_company["id"])
        engineer = db.execute(
            select(Agent).where(Agent.company_id == company.id, Agent.role == AgentRole.ENGINEER)
        ).first()
        if engineer is None:
            engineer = db.execute(select(Agent).where(Agent.company_id == company.id)).first()
        if engineer is None:
            pytest.skip("No agent found")
        engineer = engineer[0]
        from app.agents.validator import DecisionValidator
        from app.agents.decisions import AgentDecision

        validator = DecisionValidator(db, engineer, company)
        decision = AgentDecision(
            action=ActionType.MAKE_HIRING_DECISION,
            reasoning="I want to hire",
            candidate_id=1,
        )
        result = validator.execute(decision)
        assert result.success is False

    def test_invalid_employee_id(self, db_with_company: Session, test_company: dict):
        db = db_with_company
        company = db.get(Company, test_company["id"])
        agent_row = db.execute(select(Agent).where(Agent.company_id == company.id)).first()
        if agent_row is None:
            pytest.skip("No agent found")
        agent = agent_row[0]
        from app.agents.validator import DecisionValidator
        from app.agents.decisions import AgentDecision

        validator = DecisionValidator(db, agent, company)
        decision = AgentDecision(
            action=ActionType.TERMINATE_EMPLOYEE,
            reasoning="bye",
            employee_id=99999,
        )
        result = validator.execute(decision)
        assert result.success is False


# ---------------------------------------------------------------------------
# Integration: Hiring affects execution
# ---------------------------------------------------------------------------


class TestHiringExecutionIntegration:
    def test_employee_capacity_contributes_to_tasks(self, db_with_company: Session, test_company: dict):
        db = db_with_company
        company = db.get(Company, test_company["id"])
        agent = db.execute(
            select(Agent).where(Agent.company_id == company.id, Agent.role == AgentRole.ENGINEER)
        ).scalar_one_or_none()
        if agent is None:
            pytest.skip("No engineer agent found")

        emp = Employee(
            company_id=company.id,
            name="Jack",
            role="ENGINEER",
            status=EmployeeStatus.ACTIVE,
            salary=3000.0,
            capacity=5.0,
            productivity=1.0,
            morale=1.0,
            onboarding_factor=1.0,
            hired_day=1,
        )
        db.add(emp)
        db.flush()

        from app.models.task import Task
        from app.enums import TaskStatus
        task = Task(
            company_id=company.id,
            title="Build feature",
            description="",
            created_by=agent.id,
            assigned_employee_id=emp.id,
            status=TaskStatus.TODO,
            progress=0.0,
            effort=10.0,
            remaining_effort=10.0,
        )
        db.add(task)
        db.flush()

        ctx = SimulationContext(db=db, company=company, day=1, rng=make_rng(company.seed, 1))
        from app.simulation import execution as execution_system
        work_events = execution_system.execute_work(ctx)
        db.refresh(task)
        assert task.progress > 0.0 or task.remaining_effort < 10.0 or len(work_events) > 0



# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------


class TestWorkforceAPI:
    def test_list_employees(self, client: TestClient, test_company: dict):
        resp = client.get(f"/api/workforce/companies/{test_company['id']}/employees")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_jobs(self, client: TestClient, test_company: dict):
        resp = client.get(f"/api/workforce/companies/{test_company['id']}/jobs")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_candidates(self, client: TestClient, test_company: dict):
        resp = client.get(f"/api/workforce/companies/{test_company['id']}/candidates")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_workforce_summary(self, client: TestClient, test_company: dict):
        resp = client.get(f"/api/workforce/companies/{test_company['id']}/workforce")
        assert resp.status_code == 200
        data = resp.json()
        assert "overview" in data
        assert "capacity_by_role" in data

    def test_organization_hierarchy(self, client: TestClient, test_company: dict):
        resp = client.get(f"/api/workforce/companies/{test_company['id']}/organization")
        assert resp.status_code == 200
        data = resp.json()
        assert "hierarchy" in data


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


class TestDeterminism:
    def test_deterministic_workforce_scenario(self, db_with_company: Session, test_company: dict):
        db = db_with_company
        company = db.get(Company, test_company["id"])
        job = JobOpening(
            company_id=company.id,
            role="ENGINEER",
            title="Engineer",
            description="",
            required_skills=[],
            salary_min=2000.0,
            salary_max=5000.0,
            capacity_required=5.0,
            created_day=1,
            status=JobStatus.OPEN,
        )
        db.add(job)
        db.flush()
        db.commit()

        results = []
        for _ in range(2):
            db.expire_all()
            company = db.get(Company, test_company["id"])
            job = db.get(JobOpening, job.id)
            assert job is not None
            ctx = SimulationContext(db=db, company=company, day=1, rng=make_rng(company.seed, 1))
            candidates = candidate_system.generate_candidates(ctx, job, count=3)
            db.commit()
            results.append([c.name for c in candidates])

        assert results[0] == results[1]



# ---------------------------------------------------------------------------
# Failure Isolation
# ---------------------------------------------------------------------------


class TestFailureIsolation:
    def test_invalid_hiring_decision_does_not_crash(self, db_with_company: Session, test_company: dict):
        db = db_with_company
        company = db.get(Company, test_company["id"])
        agent_row = db.execute(select(Agent).where(Agent.company_id == company.id)).first()
        if agent_row is None:
            pytest.skip("No agent found")
        agent = agent_row[0]
        from app.agents.validator import DecisionValidator
        from app.agents.decisions import AgentDecision

        validator = DecisionValidator(db, agent, company)
        for _ in range(5):
            decision = AgentDecision(
                action=ActionType.MAKE_HIRING_DECISION,
                reasoning="invalid",
                candidate_id=99999,
            )
            result = validator.execute(decision)
            assert result.success is False


# ---------------------------------------------------------------------------
# Economy Integration
# ---------------------------------------------------------------------------


class TestEconomyIntegration:
    def test_hiring_cost_deducted(self, db_with_company: Session, test_company: dict):
        db = db_with_company
        company = db.get(Company, test_company["id"])
        initial_cash = company.cash
        job = JobOpening(
            company_id=company.id,
            role="ENGINEER",
            title="Engineer",
            description="",
            required_skills=[],
            salary_min=2000.0,
            salary_max=5000.0,
            capacity_required=5.0,
            created_day=1,
            status=JobStatus.OPEN,
        )
        db.add(job)
        db.flush()
        ctx = SimulationContext(db=db, company=company, day=1, rng=make_rng(company.seed, 1))
        workforce_system.hire_employee(ctx, job, "Kate", 3000.0)
        db.commit()
        db.refresh(company)
        assert company.cash < initial_cash

    def test_termination_stops_salary(self, db_with_company: Session, test_company: dict):
        db = db_with_company
        company = db.get(Company, test_company["id"])
        emp = Employee(
            company_id=company.id,
            name="Liam",
            role="ENGINEER",
            status=EmployeeStatus.ACTIVE,
            salary=3000.0,
            capacity=5.0,
        )
        db.add(emp)
        db.flush()
        ctx = SimulationContext(db=db, company=company, day=1, rng=make_rng(company.seed, 1))
        workforce_system.terminate_employee(ctx, emp)
        payroll = workforce_system.total_payroll(ctx)
        assert payroll == 0.0


# ---------------------------------------------------------------------------
# Performance & Morale
# ---------------------------------------------------------------------------


class TestPerformanceMorale:
    def test_morale_update(self, db_with_company: Session, test_company: dict):
        db = db_with_company
        company = db.get(Company, test_company["id"])
        emp = Employee(
            company_id=company.id,
            name="Maya",
            role="ENGINEER",
            status=EmployeeStatus.ACTIVE,
            salary=3000.0,
            capacity=5.0,
            morale=0.5,
            productivity=0.5,
        )
        db.add(emp)
        db.flush()
        ctx = SimulationContext(db=db, company=company, day=1, rng=make_rng(company.seed, 1))
        workforce_system.update_morale(ctx)
        db.refresh(emp)
        assert 0.0 <= emp.morale <= 1.0

    def test_performance_evaluation_marks_underperforming(self, db_with_company: Session, test_company: dict):
        db = db_with_company
        company = db.get(Company, test_company["id"])
        emp = Employee(
            company_id=company.id,
            name="Noah",
            role="ENGINEER",
            status=EmployeeStatus.ACTIVE,
            salary=3000.0,
            capacity=5.0,
            productivity=0.1,
            morale=0.1,
            performance_score=0.2,
        )
        db.add(emp)
        db.flush()
        ctx = SimulationContext(db=db, company=company, day=1, rng=make_rng(company.seed, 1))
        events = workforce_system.evaluate_performance(ctx)
        db.refresh(emp)
        assert emp.status == EmployeeStatus.UNDERPERFORMING
