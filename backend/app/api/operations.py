from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.enums import IncidentStatus, IncidentType, ObjectiveStatus, ObjectiveType, ResourceType, RiskSeverity, RiskStatus
from app.models.company import Company
from app.models.incident import Incident
from app.models.objective import Objective
from app.models.resource_allocation import ResourceAllocation
from app.models.risk import Risk
from app.schemas.simulation import (
    IncidentRead,
    ObjectiveRead,
    ResourceAllocationRead,
    RiskRead,
)
from app.simulation.engine import SimulationEngine
from app.simulation.state import _sim_ctx

router = APIRouter(prefix="/operations", tags=["operations"])

_engine = SimulationEngine()


def _get_company(db: Session, company_id: int) -> Company:
    company = db.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=404, detail=f"Company {company_id} not found")
    return company


# --- Objectives ---


@router.get("/companies/{company_id}/objectives", response_model=list[ObjectiveRead])
def list_objectives(company_id: int, db: Session = Depends(get_db)):
    _get_company(db, company_id)
    objectives = list(
        db.execute(
            select(Objective).where(Objective.company_id == company_id).order_by(Objective.priority.desc(), Objective.id)
        ).scalars().all()
    )
    return objectives


@router.post("/companies/{company_id}/objectives", response_model=ObjectiveRead)
def create_objective(company_id: int, title: str, description: str = "", objective_type: str = "OPERATIONAL", priority: int = 1, db: Session = Depends(get_db)):
    company = _get_company(db, company_id)
    try:
        obj_type = ObjectiveType(objective_type.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid objective_type: {objective_type}")

    objective = Objective(
        company_id=company.id,
        title=title.strip()[:255],
        description=description.strip()[:2000],
        objective_type=obj_type,
        status=ObjectiveStatus.TODO,
        priority=max(1, min(10, priority)),
        created_day=company.current_day,
    )
    db.add(objective)
    db.commit()
    db.refresh(objective)
    return objective


@router.patch("/companies/{company_id}/objectives/{objective_id}", response_model=ObjectiveRead)
def update_objective(company_id: int, objective_id: int, progress: float | None = None, priority: int | None = None, status: str | None = None, db: Session = Depends(get_db)):
    company = _get_company(db, company_id)
    objective = db.get(Objective, objective_id)
    if objective is None or objective.company_id != company_id:
        raise HTTPException(status_code=404, detail="Objective not found")

    if progress is not None:
        objective.progress = max(0.0, min(100.0, progress))
        if objective.progress >= 100.0:
            objective.status = ObjectiveStatus.ACHIEVED
            objective.completed_day = company.current_day

    if priority is not None:
        objective.priority = max(1, min(10, priority))

    if status is not None:
        try:
            objective.status = ObjectiveStatus(status.upper())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    db.commit()
    db.refresh(objective)
    return objective


# --- Risks ---


@router.get("/companies/{company_id}/risks", response_model=list[RiskRead])
def list_risks(company_id: int, db: Session = Depends(get_db)):
    _get_company(db, company_id)
    risks = list(
        db.execute(
            select(Risk).where(Risk.company_id == company_id).order_by(Risk.severity.desc(), Risk.detected_day.desc())
        ).scalars().all()
    )
    return risks


@router.post("/companies/{company_id}/risks", response_model=RiskRead)
def create_risk(company_id: int, risk_type: str, severity: str = "MEDIUM", source: str = "", description: str = "", db: Session = Depends(get_db)):
    company = _get_company(db, company_id)
    try:
        risk_severity = RiskSeverity(severity.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid severity: {severity}")

    risk = Risk(
        company_id=company.id,
        risk_type=risk_type.strip()[:100],
        severity=risk_severity,
        source=source.strip()[:500],
        description=description.strip()[:1000],
        affected_entity_type="company",
        affected_entity_id=company.id,
        status=RiskStatus.ACTIVE,
        detected_day=company.current_day,
    )
    db.add(risk)
    db.commit()
    db.refresh(risk)
    return risk


@router.patch("/companies/{company_id}/risks/{risk_id}", response_model=RiskRead)
def update_risk(company_id: int, risk_id: int, status: str | None = None, mitigation_actions: str | None = None, db: Session = Depends(get_db)):
    _get_company(db, company_id)
    risk = db.get(Risk, risk_id)
    if risk is None or risk.company_id != company_id:
        raise HTTPException(status_code=404, detail="Risk not found")

    if status is not None:
        try:
            risk.status = RiskStatus(status.upper())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    if mitigation_actions is not None:
        risk.mitigation_actions = mitigation_actions.strip()[:1000]

    db.commit()
    db.refresh(risk)
    return risk


# --- Incidents ---


@router.get("/companies/{company_id}/incidents", response_model=list[IncidentRead])
def list_incidents(company_id: int, db: Session = Depends(get_db)):
    _get_company(db, company_id)
    incidents = list(
        db.execute(
            select(Incident).where(Incident.company_id == company_id).order_by(Incident.severity.desc(), Incident.detected_day.desc())
        ).scalars().all()
    )
    return incidents


@router.post("/companies/{company_id}/incidents", response_model=IncidentRead)
def create_incident(company_id: int, incident_type: str, description: str = "", severity: str = "MEDIUM", related_risk_id: int | None = None, db: Session = Depends(get_db)):
    company = _get_company(db, company_id)
    try:
        incident_type_enum = IncidentType(incident_type.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid incident_type: {incident_type}")

    try:
        incident_severity = RiskSeverity(severity.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid severity: {severity}")

    incident = Incident(
        company_id=company.id,
        incident_type=incident_type_enum,
        severity=incident_severity,
        description=description.strip()[:1000],
        status=IncidentStatus.ACTIVE,
        detected_day=company.current_day,
        related_risk_id=related_risk_id,
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


@router.patch("/companies/{company_id}/incidents/{incident_id}", response_model=IncidentRead)
def update_incident(company_id: int, incident_id: int, status: str | None = None, root_cause: str | None = None, impact_assessment: str | None = None, db: Session = Depends(get_db)):
    _get_company(db, company_id)
    incident = db.get(Incident, incident_id)
    if incident is None or incident.company_id != company_id:
        raise HTTPException(status_code=404, detail="Incident not found")

    if status is not None:
        try:
            incident.status = IncidentStatus(status.upper())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    if root_cause is not None:
        incident.root_cause = root_cause.strip()[:1000]

    if impact_assessment is not None:
        incident.impact_assessment = impact_assessment.strip()[:1000]

    db.commit()
    db.refresh(incident)
    return incident


# --- Resource Allocations ---


@router.get("/companies/{company_id}/resources", response_model=list[ResourceAllocationRead])
def list_resource_allocations(company_id: int, db: Session = Depends(get_db)):
    _get_company(db, company_id)
    allocations = list(
        db.execute(
            select(ResourceAllocation).where(ResourceAllocation.company_id == company_id).order_by(ResourceAllocation.id)
        ).scalars().all()
    )
    return allocations


@router.post("/companies/{company_id}/resources", response_model=ResourceAllocationRead)
def create_resource_allocation(company_id: int, resource_type: str, allocated_amount: float, purpose: str = "", db: Session = Depends(get_db)):
    company = _get_company(db, company_id)
    try:
        res_type = ResourceType(resource_type.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid resource_type: {resource_type}")

    if allocated_amount <= 0:
        raise HTTPException(status_code=400, detail="allocated_amount must be positive")

    allocation = ResourceAllocation(
        company_id=company.id,
        resource_type=res_type,
        allocated_amount=round(allocated_amount, 2),
        available_amount=round(allocated_amount, 2),
        allocation_day=company.current_day,
        purpose=purpose.strip()[:500],
    )
    db.add(allocation)
    db.commit()
    db.refresh(allocation)
    return allocation


# --- Operational Status ---


@router.get("/companies/{company_id}/status")
def operational_status(company_id: int, db: Session = Depends(get_db)):
    company = _get_company(db, company_id)
    from app.simulation import attention as attention_system
    from app.simulation import resource as resource_system
    from app.simulation import risk as risk_system
    from app.simulation import incident as incident_system
    from app.simulation import objective as objective_system

    ctx = _sim_ctx(db, company, company.current_day)

    attention = attention_system.compute_management_attention(ctx)
    resources = resource_system.get_resource_utilization(ctx)
    risks = risk_system.get_active_risks(ctx)
    incidents = incident_system.get_active_incidents(ctx)
    objectives = objective_system.get_active_objectives(ctx)

    return {
        "company_id": company.id,
        "current_day": company.current_day,
        "attention": attention,
        "resources": resources,
        "risks": [
            {
                "id": r.id,
                "risk_type": r.risk_type,
                "severity": r.severity.value,
                "status": r.status.value,
                "detected_day": r.detected_day,
            }
            for r in risks
        ],
        "incidents": [
            {
                "id": i.id,
                "incident_type": i.incident_type.value,
                "severity": i.severity.value,
                "status": i.status.value,
                "detected_day": i.detected_day,
            }
            for i in incidents
        ],
        "objectives": [
            {
                "id": o.id,
                "title": o.title,
                "status": o.status.value,
                "priority": o.priority,
                "progress": o.progress,
            }
            for o in objectives
        ],
    }
