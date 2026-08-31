from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.enums import AgentRole, AgentStatus


class AgentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    name: str
    role: AgentRole
    personality: dict | None = None
    skills: list | None = None
    authority: int
    budget: float
    morale: float
    energy: float
    workload: float
    status: AgentStatus
    manager_id: int | None = None
    created_at: datetime
    updated_at: datetime
