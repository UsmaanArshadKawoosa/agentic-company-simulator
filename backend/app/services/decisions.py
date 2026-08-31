from sqlalchemy.orm import Session

from app.models.decision import Decision


def record_decision(
    db: Session,
    *,
    company_id: int,
    agent_id: int | None,
    action: str,
    reasoning: str = "",
    context: dict | None = None,
    outcome: str | None = None,
    simulation_day: int = 1,
) -> Decision:
    decision = Decision(
        company_id=company_id,
        agent_id=agent_id,
        action=action,
        reasoning=reasoning,
        context=context or {},
        outcome=outcome,
        simulation_day=simulation_day,
    )
    db.add(decision)
    return decision
