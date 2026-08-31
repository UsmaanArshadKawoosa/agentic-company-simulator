from app.agents.base import BaseAgent
from app.agents.decisions import ActionType, AgentDecision
from app.agents.context import AgentContext


class CEOAgent(BaseAgent):
    role_name = "CEO"

    def think(self, context: AgentContext) -> str:
        goals_summary = ", ".join(g.title for g in context.goals[:3]) or "no active goals"
        open_tasks = sum(1 for t in context.tasks if t.status in ("TODO", "IN_PROGRESS"))
        reports = ", ".join(
            context.organization.direct_report_ids and ["CTO", "CMO"] or []
        )
        return (
            f"CEO evaluates strategy on day {context.company.current_day}: "
            f"cash={context.company.cash}, goals=[{goals_summary}], "
            f"open_tasks={open_tasks}. Considering prioritization and delegation "
            f"to direct reports."
        )

    def decide(self, context: AgentContext) -> AgentDecision | None:
        # CEO-specific strategic logic runs through the LLM with the CEO prompt.
        # The superclass already restricts actions via the role prompt.
        return super().decide(context)
