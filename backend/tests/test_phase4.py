"""Tests for Phase 4: task execution, dependencies, milestones, features, product."""

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.validator import DecisionValidator
from app.enums import (
    AgentRole,
    CompanyStatus,
    FeatureStatus,
    GoalStatus,
    MilestoneStatus,
    ProjectStatus,
    TaskStatus,
    TaskType,
)
from app.models.agent import Agent
from app.models.company import Company
from app.models.goal import Goal
from app.models.milestone import Milestone
from app.models.product_feature import ProductFeature
from app.models.project import Project
from app.models.task import Task
from app.models.task_dependency import TaskDependency
from app.simulation import execution as execution_system
from app.simulation import milestone as milestone_system
from app.simulation import product as product_system
from app.simulation.domain import SimulationContext, make_rng


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ctx(company: Company, db: Session, day: int = 1) -> SimulationContext:
    return SimulationContext(db=db, company=company, day=day, rng=make_rng(company.seed, day))


def _create_company(db: Session, name: str = "Phase4Co", seed: int = 12345) -> Company:
    company = Company(
        name=name, mission="test", status=CompanyStatus.RUNNING, seed=seed,
    )
    db.add(company)
    db.flush()
    ceo = Agent(company_id=company.id, name="CEO", role=AgentRole.CEO, authority=10, capacity=5.0)
    db.add(ceo)
    db.flush()
    cto = Agent(company_id=company.id, name="CTO", role=AgentRole.CTO, authority=8, capacity=5.0, manager_id=ceo.id)
    db.add(cto)
    db.flush()
    eng = Agent(company_id=company.id, name="Eng", role=AgentRole.ENGINEER, authority=5, capacity=5.0, manager_id=cto.id)
    db.add(eng)
    db.flush()
    cmo = Agent(company_id=company.id, name="CMO", role=AgentRole.CMO, authority=7, capacity=5.0, manager_id=ceo.id)
    db.add(cmo)
    db.commit()
    db.refresh(company)
    return company


# ---------------------------------------------------------------------------
# Task execution tests
# ---------------------------------------------------------------------------


class TestTaskExecution:
    def test_task_has_finite_effort(self, db: Session):
        company = _create_company(db)
        task = Task(company_id=company.id, title="Build API", effort=10.0, remaining_effort=10.0)
        db.add(task)
        db.flush()
        assert task.effort == 10.0
        assert task.remaining_effort == 10.0

    def test_engineer_consumes_capacity(self, db: Session):
        company = _create_company(db)
        eng = db.execute(select(Agent).where(Agent.role == AgentRole.ENGINEER).where(Agent.company_id == company.id)).scalars().first()
        task = Task(
            company_id=company.id, title="Build API", effort=10.0, remaining_effort=10.0,
            assigned_to=eng.id, status=TaskStatus.TODO, priority=1,
        )
        db.add(task)
        db.flush()
        ctx = _ctx(company, db, day=2)
        execution_system.execute_work(ctx)
        assert task.remaining_effort == 5.0  # capacity=5 consumed
        assert task.progress == pytest.approx(0.5)
        assert task.status == TaskStatus.IN_PROGRESS

    def test_task_completes_at_100(self, db: Session):
        company = _create_company(db)
        eng = db.execute(select(Agent).where(Agent.role == AgentRole.ENGINEER).where(Agent.company_id == company.id)).scalars().first()
        eng.capacity = 10.0
        task = Task(
            company_id=company.id, title="Quick task", effort=5.0, remaining_effort=5.0,
            assigned_to=eng.id, status=TaskStatus.TODO, priority=1,
        )
        db.add(task)
        db.flush()
        ctx = _ctx(company, db, day=2)
        execution_system.execute_work(ctx)
        assert task.remaining_effort == 0.0
        assert task.progress == 1.0
        assert task.status == TaskStatus.COMPLETED

    def test_progress_cannot_exceed_100(self, db: Session):
        company = _create_company(db)
        eng = db.execute(select(Agent).where(Agent.role == AgentRole.ENGINEER).where(Agent.company_id == company.id)).scalars().first()
        eng.capacity = 100.0
        task = Task(
            company_id=company.id, title="Tiny task", effort=1.0, remaining_effort=1.0,
            assigned_to=eng.id, status=TaskStatus.TODO, priority=1,
        )
        db.add(task)
        db.flush()
        ctx = _ctx(company, db, day=2)
        execution_system.execute_work(ctx)
        assert task.progress == 1.0
        assert task.remaining_effort == 0.0

    def test_remaining_effort_not_negative(self, db: Session):
        company = _create_company(db)
        eng = db.execute(select(Agent).where(Agent.role == AgentRole.ENGINEER).where(Agent.company_id == company.id)).scalars().first()
        eng.capacity = 100.0
        task = Task(
            company_id=company.id, title="Small task", effort=3.0, remaining_effort=3.0,
            assigned_to=eng.id, status=TaskStatus.TODO, priority=1,
        )
        db.add(task)
        db.flush()
        ctx = _ctx(company, db, day=2)
        execution_system.execute_work(ctx)
        assert task.remaining_effort >= 0.0

    def test_unassigned_task_not_worked(self, db: Session):
        company = _create_company(db)
        task = Task(company_id=company.id, title="Unassigned", effort=10.0, remaining_effort=10.0, status=TaskStatus.TODO)
        db.add(task)
        db.flush()
        ctx = _ctx(company, db, day=2)
        execution_system.execute_work(ctx)
        assert task.remaining_effort == 10.0
        assert task.status == TaskStatus.TODO

    def test_priority_ordering(self, db: Session):
        company = _create_company(db)
        eng = db.execute(select(Agent).where(Agent.role == AgentRole.ENGINEER).where(Agent.company_id == company.id)).scalars().first()
        eng.capacity = 5.0
        low = Task(company_id=company.id, title="Low", effort=10.0, remaining_effort=10.0, assigned_to=eng.id, status=TaskStatus.TODO, priority=1)
        high = Task(company_id=company.id, title="High", effort=10.0, remaining_effort=10.0, assigned_to=eng.id, status=TaskStatus.TODO, priority=3)
        db.add_all([low, high])
        db.flush()
        ctx = _ctx(company, db, day=2)
        execution_system.execute_work(ctx)
        # High priority should have been worked on first.
        assert high.remaining_effort == 5.0
        assert low.remaining_effort == 10.0


# ---------------------------------------------------------------------------
# Dependency tests
# ---------------------------------------------------------------------------


class TestDependencies:
    def test_self_dependency_rejected(self, db: Session):
        company = _create_company(db)
        task = Task(company_id=company.id, title="T1", effort=10.0, remaining_effort=10.0)
        db.add(task)
        db.flush()
        tasks = [task]
        err = execution_system.validate_dependency(_ctx(company, db), task.id, task.id, tasks)
        assert err is not None
        assert "itself" in err.lower()

    def test_circular_dependency_rejected(self, db: Session):
        company = _create_company(db)
        a = Task(company_id=company.id, title="A", effort=5.0, remaining_effort=5.0)
        b = Task(company_id=company.id, title="B", effort=5.0, remaining_effort=5.0)
        c = Task(company_id=company.id, title="C", effort=5.0, remaining_effort=5.0)
        db.add_all([a, b, c])
        db.flush()
        # A→B, B→C, C→A (cycle)
        db.add_all([
            TaskDependency(task_id=a.id, depends_on_id=b.id),
            TaskDependency(task_id=b.id, depends_on_id=c.id),
            TaskDependency(task_id=c.id, depends_on_id=a.id),
        ])
        db.flush()
        tasks = [a, b, c]
        deps = list(db.execute(select(TaskDependency).where(TaskDependency.task_id.in_([t.id for t in tasks]))).scalars().all())
        assert execution_system.has_cycle(tasks, deps) is True

    def test_dependent_task_blocked(self, db: Session):
        company = _create_company(db)
        eng = db.execute(select(Agent).where(Agent.role == AgentRole.ENGINEER).where(Agent.company_id == company.id)).scalars().first()
        dep = Task(company_id=company.id, title="Dep", effort=10.0, remaining_effort=10.0, status=TaskStatus.IN_PROGRESS)
        dependent = Task(company_id=company.id, title="Dependent", effort=10.0, remaining_effort=10.0, assigned_to=eng.id, status=TaskStatus.TODO)
        db.add_all([dep, dependent])
        db.flush()
        db.add(TaskDependency(task_id=dependent.id, depends_on_id=dep.id))
        db.flush()
        ctx = _ctx(company, db, day=2)
        events = execution_system.update_blocking_state(ctx)
        assert dependent.status == TaskStatus.BLOCKED
        assert any(e.event_type == "TASK_BLOCKED" for e in events)

    def test_dependency_completion_unblocks(self, db: Session):
        company = _create_company(db)
        eng = db.execute(select(Agent).where(Agent.role == AgentRole.ENGINEER).where(Agent.company_id == company.id)).scalars().first()
        dep = Task(company_id=company.id, title="Dep", effort=10.0, remaining_effort=0.0, status=TaskStatus.COMPLETED)
        dependent = Task(company_id=company.id, title="Dependent", effort=10.0, remaining_effort=10.0, assigned_to=eng.id, status=TaskStatus.BLOCKED)
        db.add_all([dep, dependent])
        db.flush()
        db.add(TaskDependency(task_id=dependent.id, depends_on_id=dep.id))
        db.flush()
        ctx = _ctx(company, db, day=2)
        events = execution_system.update_blocking_state(ctx)
        assert dependent.status == TaskStatus.TODO
        assert any(e.event_type == "TASK_UNBLOCKED" for e in events)

    def test_cross_company_dependency_rejected(self, db: Session):
        c1 = _create_company(db, name="C1")
        c2 = _create_company(db, name="C2")
        t1 = Task(company_id=c1.id, title="T1", effort=5.0, remaining_effort=5.0)
        t2 = Task(company_id=c2.id, title="T2", effort=5.0, remaining_effort=5.0)
        db.add_all([t1, t2])
        db.flush()
        tasks = list(db.execute(select(Task).where(Task.company_id.in_([c1.id, c2.id]))).scalars().all())
        err = execution_system.validate_dependency(_ctx(c1, db), t1.id, t2.id, tasks)
        assert err is not None
        assert "cross-company" in err.lower()


# ---------------------------------------------------------------------------
# Milestone tests
# ---------------------------------------------------------------------------


class TestMilestones:
    def test_milestone_progress_from_tasks(self, db: Session):
        company = _create_company(db)
        project = Project(company_id=company.id, name="P1", status=ProjectStatus.PLANNED)
        db.add(project)
        db.flush()
        ms = Milestone(company_id=company.id, project_id=project.id, name="MVP", status=MilestoneStatus.PLANNED)
        db.add(ms)
        db.flush()
        t1 = Task(company_id=company.id, title="T1", milestone_id=ms.id, status=TaskStatus.COMPLETED, progress=1.0)
        t2 = Task(company_id=company.id, title="T2", milestone_id=ms.id, status=TaskStatus.IN_PROGRESS, progress=0.5)
        db.add_all([t1, t2])
        db.flush()
        progress = milestone_system.milestone_progress(ms, [t1, t2])
        assert progress == pytest.approx(0.75)

    def test_milestone_completes_when_all_tasks_done(self, db: Session):
        company = _create_company(db)
        project = Project(company_id=company.id, name="P1", status=ProjectStatus.PLANNED)
        db.add(project)
        db.flush()
        ms = Milestone(company_id=company.id, project_id=project.id, name="MVP", status=MilestoneStatus.PLANNED)
        db.add(ms)
        db.flush()
        t1 = Task(company_id=company.id, title="T1", milestone_id=ms.id, status=TaskStatus.COMPLETED, progress=1.0)
        t2 = Task(company_id=company.id, title="T2", milestone_id=ms.id, status=TaskStatus.COMPLETED, progress=1.0)
        db.add_all([t1, t2])
        db.flush()
        ctx = _ctx(company, db, day=2)
        events = milestone_system.update_milestones(ctx)
        assert ms.status == MilestoneStatus.COMPLETED
        assert any(e.event_type == "MILESTONE_COMPLETED" for e in events)


# ---------------------------------------------------------------------------
# Product tests
# ---------------------------------------------------------------------------


class TestProduct:
    def test_feature_progress_from_tasks(self, db: Session):
        company = _create_company(db)
        feature = ProductFeature(company_id=company.id, name="Auth", status=FeatureStatus.PLANNED)
        db.add(feature)
        db.flush()
        t1 = Task(company_id=company.id, title="T1", feature_id=feature.id, status=TaskStatus.COMPLETED, progress=1.0)
        t2 = Task(company_id=company.id, title="T2", feature_id=feature.id, status=TaskStatus.IN_PROGRESS, progress=0.5)
        db.add_all([t1, t2])
        db.flush()
        progress = product_system.feature_progress(feature, [t1, t2])
        assert progress == pytest.approx(0.75)

    def test_feature_quality_bounded(self, db: Session):
        company = _create_company(db)
        feature = ProductFeature(company_id=company.id, name="Auth", status=FeatureStatus.PLANNED)
        db.add(feature)
        db.flush()
        t1 = Task(company_id=company.id, title="T1", feature_id=feature.id, status=TaskStatus.COMPLETED, progress=1.0)
        db.add(t1)
        db.flush()
        quality = product_system.feature_quality(feature, [t1])
        assert 0.0 <= quality <= 1.0

    def test_product_readiness_from_features(self, db: Session):
        company = _create_company(db)
        f1 = ProductFeature(company_id=company.id, name="F1", status=FeatureStatus.IN_PROGRESS, progress=1.0)
        f2 = ProductFeature(company_id=company.id, name="F2", status=FeatureStatus.PLANNED, progress=0.0)
        db.add_all([f1, f2])
        db.flush()
        readiness = product_system.compute_product_readiness(company, [f1, f2])
        assert readiness == pytest.approx(0.5)

    def test_product_quality_minus_debt(self, db: Session):
        company = _create_company(db)
        company.technical_debt = 0.2
        f1 = ProductFeature(company_id=company.id, name="F1", status=FeatureStatus.COMPLETED, quality=1.0)
        db.add(f1)
        db.flush()
        quality = product_system.compute_product_quality(company, [f1])
        assert quality == pytest.approx(0.8)
        assert 0.0 <= quality <= 1.0

    def test_technical_debt_accumulates(self, db: Session):
        company = _create_company(db)
        feature = ProductFeature(company_id=company.id, name="F1", status=FeatureStatus.IN_PROGRESS, progress=0.5)
        db.add(feature)
        db.flush()
        ctx = _ctx(company, db, day=2)
        product_system.update_product(ctx)
        assert company.technical_debt > 0.0


# ---------------------------------------------------------------------------
# Integration: full work→product→readiness chain
# ---------------------------------------------------------------------------


class TestWorkToProductChain:
    def test_engineer_work_updates_project_and_product(self, db: Session):
        company = _create_company(db, seed=42)
        eng = db.execute(select(Agent).where(Agent.role == AgentRole.ENGINEER).where(Agent.company_id == company.id)).scalars().first()
        eng.capacity = 5.0
        project = Project(company_id=company.id, name="EngProject", status=ProjectStatus.PLANNED)
        db.add(project)
        db.flush()
        feature = ProductFeature(company_id=company.id, name="Auth", project_id=project.id, status=FeatureStatus.PLANNED)
        db.add(feature)
        db.flush()
        ms = Milestone(company_id=company.id, project_id=project.id, name="MVP Backend", status=MilestoneStatus.PLANNED)
        db.add(ms)
        db.flush()
        task = Task(
            company_id=company.id, title="Implement auth", effort=10.0, remaining_effort=10.0,
            assigned_to=eng.id, status=TaskStatus.TODO, priority=3,
            project_id=project.id, milestone_id=ms.id, feature_id=feature.id,
        )
        db.add(task)
        db.flush()
        # Run 3 days of work.
        for day in range(2, 5):
            ctx = _ctx(company, db, day)
            execution_system.update_blocking_state(ctx)
            execution_system.execute_work(ctx)
            milestone_system.update_milestones(ctx)
            product_system.update_features(ctx)
            product_system.update_product(ctx)
        # Task should be complete (5 capacity * 3 days = 15 > 10 effort).
        assert task.status == TaskStatus.COMPLETED
        assert task.progress == 1.0
        # Milestone should be complete.
        assert ms.status == MilestoneStatus.COMPLETED
        # Feature should be complete.
        assert feature.status == FeatureStatus.COMPLETED
        # Product readiness should be 1.0.
        assert company.product_readiness == pytest.approx(1.0)

    def test_dependent_work_chain(self, db: Session):
        company = _create_company(db, seed=99)
        eng = db.execute(select(Agent).where(Agent.role == AgentRole.ENGINEER).where(Agent.company_id == company.id)).scalars().first()
        eng.capacity = 10.0
        t1 = Task(company_id=company.id, title="Design", effort=10.0, remaining_effort=10.0, assigned_to=eng.id, status=TaskStatus.TODO, priority=3)
        t2 = Task(company_id=company.id, title="Implement", effort=10.0, remaining_effort=10.0, assigned_to=eng.id, status=TaskStatus.TODO, priority=3)
        db.add_all([t1, t2])
        db.flush()
        db.add(TaskDependency(task_id=t2.id, depends_on_id=t1.id))
        db.flush()
        # Day 2: work on t1 (t2 blocked).
        ctx = _ctx(company, db, day=2)
        execution_system.update_blocking_state(ctx)
        execution_system.execute_work(ctx)
        assert t1.status == TaskStatus.COMPLETED
        assert t2.status == TaskStatus.BLOCKED
        # Day 3: t2 unblocked, work on it → completes.
        ctx = _ctx(company, db, day=3)
        execution_system.update_blocking_state(ctx)
        assert t2.status == TaskStatus.TODO
        execution_system.execute_work(ctx)
        assert t2.status == TaskStatus.COMPLETED

    def test_tasks_created_today_available_next_day(self, db: Session):
        """Tasks created during agent phase should be available for work next tick."""
        company = _create_company(db, seed=10)
        eng = db.execute(select(Agent).where(Agent.role == AgentRole.ENGINEER).where(Agent.company_id == company.id)).scalars().first()
        eng.capacity = 5.0
        # Simulate agent creating a task on day 2.
        task = Task(
            company_id=company.id, title="New task", effort=10.0, remaining_effort=10.0,
            assigned_to=eng.id, status=TaskStatus.TODO, priority=1,
        )
        db.add(task)
        db.flush()
        # Day 3: work should be available.
        ctx = _ctx(company, db, day=3)
        execution_system.update_blocking_state(ctx)
        execution_system.execute_work(ctx)
        assert task.remaining_effort == 5.0
        assert task.status == TaskStatus.IN_PROGRESS


# ---------------------------------------------------------------------------
# Determinism test
# ---------------------------------------------------------------------------


class TestDeterminism:
    def test_same_seed_same_work_outcome(self, db: Session):
        c1 = _create_company(db, name="DetA", seed=333)
        c2 = _create_company(db, name="DetB", seed=333)
        for company in [c1, c2]:
            eng = db.execute(select(Agent).where(Agent.role == AgentRole.ENGINEER).where(Agent.company_id == company.id)).scalars().first()
            eng.capacity = 5.0
            task = Task(
                company_id=company.id, title="Work", effort=10.0, remaining_effort=10.0,
                assigned_to=eng.id, status=TaskStatus.TODO, priority=1,
            )
            db.add(task)
        db.flush()
        for day in range(2, 5):
            for company in [c1, c2]:
                ctx = _ctx(company, db, day)
                execution_system.update_blocking_state(ctx)
                execution_system.execute_work(ctx)
        t1 = db.execute(select(Task).where(Task.company_id == c1.id)).scalars().first()
        t2 = db.execute(select(Task).where(Task.company_id == c2.id)).scalars().first()
        assert t1.remaining_effort == t2.remaining_effort
        assert t1.progress == t2.progress
