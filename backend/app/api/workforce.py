from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.enums import EmployeeStatus, JobStatus
from app.models.employee import Employee
from app.models.job_opening import JobOpening
from app.models.candidate import Candidate
from app.simulation.engine import SimulationEngine
from app.simulation import workforce as workforce_system
from app.simulation.state import _sim_ctx

router = APIRouter(prefix="/workforce", tags=["workforce"])
_engine = SimulationEngine()


def _company_or_404(db: Session, company_id: int):
    from app.models.company import Company
    company = db.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found.")
    return company


@router.get("/companies/{company_id}/employees")
def list_employees(company_id: int, db: Session = Depends(get_db), limit: int = 100):
    _company_or_404(db, company_id)
    employees = list(
        db.execute(
            select(Employee).where(Employee.company_id == company_id).limit(limit)
        )
        .scalars()
        .all()
    )
    return [
        {
            "id": e.id,
            "name": e.name,
            "role": e.role,
            "status": e.status.value if hasattr(e.status, "value") else str(e.status),
            "salary": round(e.salary, 2),
            "capacity": round(e.capacity, 2),
            "productivity": round(e.productivity, 2),
            "morale": round(e.morale, 2),
            "performance_score": round(e.performance_score, 2),
            "manager_id": e.manager_id,
            "hired_day": e.hired_day,
        }
        for e in employees
    ]


@router.get("/companies/{company_id}/jobs")
def list_jobs(company_id: int, db: Session = Depends(get_db)):
    _company_or_404(db, company_id)
    jobs = list(
        db.execute(
            select(JobOpening).where(JobOpening.company_id == company_id)
        )
        .scalars()
        .all()
    )
    return [
        {
            "id": j.id,
            "role": j.role,
            "title": j.title,
            "status": j.status.value if hasattr(j.status, "value") else str(j.status),
            "salary_min": round(j.salary_min, 2),
            "salary_max": round(j.salary_max, 2),
            "capacity_required": round(j.capacity_required, 2),
            "created_day": j.created_day,
        }
        for j in jobs
    ]


@router.get("/companies/{company_id}/candidates")
def list_candidates(company_id: int, db: Session = Depends(get_db), limit: int = 100):
    _company_or_404(db, company_id)
    candidates = list(
        db.execute(
            select(Candidate).where(Candidate.company_id == company_id).limit(limit)
        )
        .scalars()
        .all()
    )
    return [
        {
            "id": c.id,
            "name": c.name,
            "role": c.role,
            "skills": c.skills or [],
            "experience": round(c.experience, 1),
            "salary_expectation": round(c.salary_expectation, 2),
            "productivity_potential": round(c.productivity_potential, 2),
            "culture_fit": round(c.culture_fit, 2),
            "reliability": round(c.reliability, 2),
            "hiring_score": round(c.hiring_score, 2),
            "status": c.status.value if hasattr(c.status, "value") else str(c.status),
        }
        for c in candidates
    ]


@router.get("/companies/{company_id}/workforce")
def workforce_summary(company_id: int, db: Session = Depends(get_db)):
    company = _company_or_404(db, company_id)
    ctx = _sim_ctx(db, company, company.current_day)
    employees = list(
        db.execute(
            select(Employee).where(Employee.company_id == company_id)
        )
        .scalars()
        .all()
    )
    active_employees = [
        e for e in employees
        if e.status in (EmployeeStatus.ACTIVE, EmployeeStatus.ONBOARDING, EmployeeStatus.UNDERPERFORMING)
    ]
    overview = {
        "headcount": len(employees),
        "active_count": len([e for e in employees if e.status == EmployeeStatus.ACTIVE]),
        "onboarding_count": len([e for e in employees if e.status == EmployeeStatus.ONBOARDING]),
        "underperforming_count": len([e for e in employees if e.status == EmployeeStatus.UNDERPERFORMING]),
        "payroll": round(workforce_system.total_payroll(ctx), 2),
        "total_capacity": round(sum(workforce_system.total_workforce_capacity(ctx).values()), 2),
        "avg_morale": round(sum(e.morale for e in active_employees) / len(active_employees), 2) if active_employees else 0.0,
        "avg_productivity": round(sum(e.productivity for e in active_employees) / len(active_employees), 2) if active_employees else 0.0,
    }
    return {
        "company_id": company_id,
        "current_day": company.current_day,
        "overview": overview,
        "capacity_by_role": workforce_system.total_workforce_capacity(ctx),
    }


@router.get("/companies/{company_id}/organization")
def organization_hierarchy(company_id: int, db: Session = Depends(get_db)):
    _company_or_404(db, company_id)
    employees = list(
        db.execute(
            select(Employee).where(Employee.company_id == company_id)
        )
        .scalars()
        .all()
    )
    by_manager: dict[int | None, list[dict]] = {}
    for e in employees:
        by_manager.setdefault(e.manager_id, []).append({
            "id": e.id,
            "name": e.name,
            "role": e.role,
            "status": e.status.value if hasattr(e.status, "value") else str(e.status),
        })
    return {
        "company_id": company_id,
        "total_employees": len(employees),
        "hierarchy": by_manager,
    }
