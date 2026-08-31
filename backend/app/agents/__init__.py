from app.agents.base import BaseAgent
from app.agents.cmo import CMOAgent
from app.agents.cto import CTOAgent
from app.agents.ceo import CEOAgent
from app.agents.engineer import EngineerAgent
from app.enums import AgentRole

_AGENT_REGISTRY: dict[AgentRole, type[BaseAgent]] = {
    AgentRole.CEO: CEOAgent,
    AgentRole.CTO: CTOAgent,
    AgentRole.CMO: CMOAgent,
    AgentRole.ENGINEER: EngineerAgent,
}


def get_agent_class(role: AgentRole) -> type[BaseAgent]:
    return _AGENT_REGISTRY[role]


def instantiate_agent(agent, company, llm=None) -> BaseAgent:
    """Build the typed agent wrapper for an ORM Agent row."""
    cls = _AGENT_REGISTRY.get(agent.role, BaseAgent)
    return cls(agent, company, llm)
