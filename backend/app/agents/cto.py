from app.agents.base import BaseAgent
from app.agents.context import AgentContext


class CTOAgent(BaseAgent):
    role_name = "CTO"

    def think(self, context: AgentContext) -> str:
        eng_tasks = [t for t in context.tasks if t.status in ("TODO", "IN_PROGRESS")]
        projects_summary = ", ".join(p.name for p in context.projects[:3]) or "no projects"
        return (
            f"CTO reviews technical work on day {context.company.current_day}: "
            f"projects=[{projects_summary}], open_engineering_tasks={len(eng_tasks)}. "
            f"Planning engineering initiatives and delegation to the Engineer."
        )

    def decide(self, context: AgentContext):
        return super().decide(context)
