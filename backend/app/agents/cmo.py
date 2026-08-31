from app.agents.base import BaseAgent
from app.agents.context import AgentContext


class CMOAgent(BaseAgent):
    role_name = "CMO"

    def think(self, context: AgentContext) -> str:
        marketing_tasks = [t for t in context.tasks if t.status in ("TODO", "IN_PROGRESS")]
        projects_summary = ", ".join(p.name for p in context.projects[:3]) or "no projects"
        return (
            f"CMO evaluates market position on day {context.company.current_day}: "
            f"projects=[{projects_summary}], open_marketing_tasks={len(marketing_tasks)}. "
            f"Planning customer research and acquisition initiatives."
        )

    def decide(self, context: AgentContext):
        return super().decide(context)
