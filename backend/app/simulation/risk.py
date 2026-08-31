"""Risk system: detect, track, and manage company risks."""

from __future__ import annotations

import logging

from sqlalchemy import select

from app.enums import RiskSeverity, RiskStatus
from app.models.risk import Risk
from app.simulation.domain import SimulationContext

logger = logging.getLogger("agent_company_simulator")

RISK_TYPES = [
    "low_cash_runway",
    "missed_expectation",
    "delayed_milestone",
    "blocked_critical_task",
    "declining_product_quality",
    "high_technical_debt",
    "employee_underperformance",
    "customer_churn",
    "competitive_pressure",
    "poor_pmf",
    "weak_sales_pipeline",
    "market_contraction",
]


def detect_risks(ctx: SimulationContext) -> list[Risk]:
    """Detect risks based on current company state."""
    company = ctx.company
    risks: list[Risk] = []
    day = ctx.day

    existing_risks = list(
        ctx.db.execute(select(Risk).where(Risk.company_id == company.id)).scalars().all()
    )
    existing_types = {r.risk_type for r in existing_risks if r.status != RiskStatus.RESOLVED}

    # Low cash runway
    if company.cash < 20000 and "low_cash_runway" not in existing_types:
        risk = Risk(
            company_id=company.id,
            risk_type="low_cash_runway",
            severity=RiskSeverity.CRITICAL if company.cash < 5000 else RiskSeverity.HIGH,
            source="financial_system",
            description=f"Company cash is low (${company.cash:.2f}).",
            affected_entity_type="company",
            affected_entity_id=company.id,
            status=RiskStatus.ACTIVE,
            detected_day=day,
        )
        ctx.db.add(risk)
        risks.append(risk)

    # High technical debt
    if company.technical_debt > 0.7 and "high_technical_debt" not in existing_types:
        risk = Risk(
            company_id=company.id,
            risk_type="high_technical_debt",
            severity=RiskSeverity.MEDIUM,
            source="product_system",
            description=f"Technical debt is high ({company.technical_debt:.2f}).",
            affected_entity_type="company",
            affected_entity_id=company.id,
            status=RiskStatus.ACTIVE,
            detected_day=day,
        )
        ctx.db.add(risk)
        risks.append(risk)

    # Declining product quality
    if company.product_quality < 0.3 and "declining_product_quality" not in existing_types:
        risk = Risk(
            company_id=company.id,
            risk_type="declining_product_quality",
            severity=RiskSeverity.HIGH,
            source="product_system",
            description=f"Product quality is low ({company.product_quality:.2f}).",
            affected_entity_type="company",
            affected_entity_id=company.id,
            status=RiskStatus.ACTIVE,
            detected_day=day,
        )
        ctx.db.add(risk)
        risks.append(risk)

    ctx.db.flush()
    return risks


def escalate_risk(ctx: SimulationContext, risk_id: int) -> Risk | None:
    """Escalate a risk."""
    risk = ctx.db.get(Risk, risk_id)
    if risk is None or risk.company_id != ctx.company.id:
        return None

    risk.status = RiskStatus.ESCALATED
    ctx.db.flush()
    return risk


def resolve_risk(ctx: SimulationContext, risk_id: int) -> Risk | None:
    """Resolve a risk."""
    risk = ctx.db.get(Risk, risk_id)
    if risk is None or risk.company_id != ctx.company.id:
        return None

    risk.status = RiskStatus.RESOLVED
    risk.resolved_day = ctx.day
    ctx.db.flush()
    return risk


def get_active_risks(ctx: SimulationContext) -> list[Risk]:
    """Get all active risks for the company."""
    return list(
        ctx.db.execute(
            select(Risk).where(
                Risk.company_id == ctx.company.id,
                Risk.status.in_([RiskStatus.ACTIVE, RiskStatus.MITIGATING, RiskStatus.ESCALATED]),
            ).order_by(Risk.severity.desc(), Risk.detected_day.desc())
        ).scalars().all()
    )
