"""Management attention model: bounded executive attention capacity."""

from __future__ import annotations

import logging

from sqlalchemy import select

from app.enums import IncidentStatus, ObjectiveStatus, RiskStatus
from app.models.incident import Incident
from app.models.objective import Objective
from app.models.risk import Risk
from app.simulation.domain import SimulationContext

logger = logging.getLogger("agent_company_simulator")

MAX_ATTENTION_CAPACITY = 5.0


def compute_management_attention(ctx: SimulationContext) -> dict:
    """Compute management attention metrics.

    Returns a dict with:
    - attention_capacity: remaining attention capacity (0.0 to MAX_ATTENTION_CAPACITY)
    - active_objectives: count of active objectives
    - active_risks: count of active risks
    - active_incidents: count of active incidents
    - attention_load: current load (active_objectives + active_risks + active_incidents)
    - overloaded: bool indicating if attention is overloaded
    """
    active_objectives = list(
        ctx.db.execute(
            select(Objective).where(
                Objective.company_id == ctx.company.id,
                Objective.status.in_([ObjectiveStatus.TODO, ObjectiveStatus.IN_PROGRESS]),
            )
        ).scalars().all()
    )
    active_risks = list(
        ctx.db.execute(
            select(Risk).where(
                Risk.company_id == ctx.company.id,
                Risk.status.in_([RiskStatus.ACTIVE, RiskStatus.MITIGATING, RiskStatus.ESCALATED]),
            )
        ).scalars().all()
    )
    active_incidents = list(
        ctx.db.execute(
            select(Incident).where(
                Incident.company_id == ctx.company.id,
                Incident.status != IncidentStatus.RESOLVED,
            )
        ).scalars().all()
    )

    attention_load = len(active_objectives) + len(active_risks) + len(active_incidents)
    remaining = max(0.0, MAX_ATTENTION_CAPACITY - attention_load)

    return {
        "attention_capacity": remaining,
        "active_objectives": len(active_objectives),
        "active_risks": len(active_risks),
        "active_incidents": len(active_incidents),
        "attention_load": attention_load,
        "overloaded": remaining <= 0.0,
    }
