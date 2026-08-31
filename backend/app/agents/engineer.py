from app.agents.base import BaseAgent
from app.agents.context import AgentContext


class EngineerAgent(BaseAgent):
    role_name = "ENGINEER"

    def think(self, context: AgentContext) -> str:
        my_tasks = [t for t in context.tasks if t.assigned_to == context.organization.agent_id]
        in_progress = [t for t in my_tasks if t.status == "IN_PROGRESS"]
        todo = [t for t in my_tasks if t.status == "TODO"]
        return (
            f"Engineer assesses assigned work on day {context.company.current_day}: "
            f"{len(my_tasks)} assigned, {len(in_progress)} in progress, "
            f"{len(todo)} todo. Focusing on executing the highest priority task."
        )

    def decide(self, context: AgentContext):
        return super().decide(context)
