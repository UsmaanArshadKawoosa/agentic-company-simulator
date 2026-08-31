"""Decision evaluation system: classify decision quality based on outcomes.

After an outcome occurs, a decision can be classified:

    SUCCESSFUL   - expected outcome fully met
    PARTIAL      - expected outcome partially met
    INEFFECTIVE  - decision had no measurable effect
    FAILED       - expected outcome missed
    UNKNOWN      - cannot yet be determined

Evaluation is deterministic where possible. For decisions linked to
expectations, the expectation's status drives the evaluation.
"""

from __future__ import annotations

import logging

from sqlalchemy import select

from app.enums import DecisionEvaluation, ExpectationStatus, EventType
from app.models.decision import Decision
from app.models.event import Event
from app.models.expectation import Expectation
from app.simulation.domain import SimulationContext

logger = logging.getLogger("agent_company_simulator")


def evaluate_decision(
    ctx: SimulationContext,
    decision: Decision,
) -> DecisionEvaluation:
    """Evaluate a decision's quality based on its outcome and linked expectation."""
    # If the decision has a linked expectation, use its status.
    linked = list(
        ctx.db.execute(
            select(Expectation)
            .where(Expectation.linked_decision_id == decision.id)
            .where(Expectation.status != ExpectationStatus.PENDING)
        )
        .scalars()
        .all()
    )
    if linked:
        # Use the most relevant (most recently resolved) expectation.
        exp = linked[-1]
        if exp.status == ExpectationStatus.MET:
            return DecisionEvaluation.SUCCESSFUL
        if exp.status == ExpectationStatus.PARTIAL:
            return DecisionEvaluation.PARTIAL
        if exp.status == ExpectationStatus.MISSED:
            return DecisionEvaluation.FAILED

    # Fallback: evaluate based on the decision's recorded outcome text.
    outcome = (decision.outcome or "").lower()
    if "rejected" in outcome:
        return DecisionEvaluation.FAILED
    if "created" in outcome or "completed" in outcome or "assigned" in outcome:
        return DecisionEvaluation.SUCCESSFUL
    if "updated" in outcome:
        return DecisionEvaluation.PARTIAL
    return DecisionEvaluation.UNKNOWN


def evaluate_pending_decisions(ctx: SimulationContext) -> list[Event]:
    """Evaluate decisions that have a resolved linked expectation but no evaluation yet.

    First evaluates any pending expectations, then evaluates decisions linked
    to resolved expectations. Returns evaluation events. Each decision is
    evaluated at most once.
    """
    # First, resolve any pending expectations.
    from app.simulation import expectation as expectation_system
    expectation_system.evaluate_expectations(ctx)

    # Find decisions linked to resolved expectations.
    resolved = list(
        ctx.db.execute(
            select(Expectation)
            .where(Expectation.company_id == ctx.company.id)
            .where(Expectation.linked_decision_id.isnot(None))
            .where(Expectation.status != ExpectationStatus.PENDING)
        )
        .scalars()
        .all()
    )
    events: list[Event] = []
    seen_decision_ids: set[int] = set()
    for exp in resolved:
        if exp.linked_decision_id in seen_decision_ids:
            continue
        seen_decision_ids.add(exp.linked_decision_id)
        decision = ctx.db.get(Decision, exp.linked_decision_id)
        if decision is None:
            continue
        evaluation = evaluate_decision(ctx, decision)
        events.append(
            Event(
                company_id=ctx.company.id,
                actor_id=decision.agent_id,
                event_type=EventType.DECISION_EVALUATED,
                description=(
                    f"Decision '{decision.action}' evaluated: {evaluation.value}."
                ),
                target_type="decision",
                target_id=decision.id,
                meta={
                    "decision_id": decision.id,
                    "evaluation": evaluation.value,
                    "expectation_id": exp.id,
                    "day": ctx.day,
                },
                simulation_day=ctx.day,
            )
        )
    return events
