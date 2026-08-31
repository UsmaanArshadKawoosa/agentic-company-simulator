"""Incident system: crisis detection and response."""

from __future__ import annotations

import logging

from sqlalchemy import select

from app.enums import IncidentStatus, IncidentType, RiskSeverity
from app.models.incident import Incident
from app.models.risk import Risk
from app.simulation.domain import SimulationContext

logger = logging.getLogger("agent_company_simulator")


def create_incident(
    ctx: SimulationContext,
    incident_type: IncidentType,
    description: str,
    severity: RiskSeverity = RiskSeverity.MEDIUM,
    related_risk_id: int | None = None,
) -> Incident:
    """Create a new incident."""
    incident = Incident(
        company_id=ctx.company.id,
        incident_type=incident_type,
        severity=severity,
        description=description.strip()[:1000],
        status=IncidentStatus.ACTIVE,
        detected_day=ctx.day,
        related_risk_id=related_risk_id,
    )
    ctx.db.add(incident)
    ctx.db.flush()
    return incident


def escalate_incident(ctx: SimulationContext, incident_id: int) -> Incident | None:
    """Escalate an incident."""
    incident = ctx.db.get(Incident, incident_id)
    if incident is None or incident.company_id != ctx.company.id:
        return None

    incident.status = IncidentStatus.ESCALATED
    ctx.db.flush()
    return incident


def resolve_incident(ctx: SimulationContext, incident_id: int, root_cause: str = "") -> Incident | None:
    """Resolve an incident."""
    incident = ctx.db.get(Incident, incident_id)
    if incident is None or incident.company_id != ctx.company.id:
        return None

    incident.status = IncidentStatus.RESOLVED
    incident.resolved_day = ctx.day
    if root_cause:
        incident.root_cause = root_cause.strip()[:1000]
    ctx.db.flush()
    return incident


def detect_incidents_from_risks(ctx: SimulationContext, risks: list[Risk]) -> list[Incident]:
    """Detect incidents from severe risks."""
    incidents: list[Incident] = []
    for risk in risks:
        if risk.severity != RiskSeverity.CRITICAL:
            continue

        # Check if an incident already exists for this risk
        existing = list(
            ctx.db.execute(
                select(Incident).where(
                    Incident.company_id == ctx.company.id,
                    Incident.related_risk_id == risk.id,
                    Incident.status != IncidentStatus.RESOLVED,
                )
            ).scalars().all()
        )
        if existing:
            continue

        incident_type = _map_risk_to_incident(risk.risk_type)
        if incident_type is None:
            continue

        incident = create_incident(
            ctx,
            incident_type=incident_type,
            description=f"Incident derived from risk: {risk.description}",
            severity=RiskSeverity.CRITICAL,
            related_risk_id=risk.id,
        )
        incidents.append(incident)

    return incidents


def _map_risk_to_incident(risk_type: str) -> IncidentType | None:
    mapping = {
        "low_cash_runway": IncidentType.RUNWAY_CRISIS,
        "delayed_milestone": IncidentType.PRODUCT_DELAY,
        "customer_churn": IncidentType.CUSTOMER_CHURN_SPIKE,
        "competitive_pressure": IncidentType.COMPETITIVE_THREAT,
        "employee_underperformance": IncidentType.WORKFORCE_SHORTAGE,
        "declining_product_quality": IncidentType.QUALITY_CRISIS,
        "weak_sales_pipeline": IncidentType.SALES_PIPELINE_CRISIS,
        "high_technical_debt": IncidentType.TECHNICAL_DEBT_CRISIS,
        "market_contraction": IncidentType.MARKET_CONTRACTION_CRISIS,
    }
    return mapping.get(risk_type)


def get_active_incidents(ctx: SimulationContext) -> list[Incident]:
    """Get all active incidents for the company."""
    return list(
        ctx.db.execute(
            select(Incident).where(
                Incident.company_id == ctx.company.id,
                Incident.status.in_([IncidentStatus.ACTIVE, IncidentStatus.MITIGATING, IncidentStatus.ESCALATED]),
            ).order_by(Incident.severity.desc(), Incident.detected_day.desc())
        ).scalars().all()
    )
