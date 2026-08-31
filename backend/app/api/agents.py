from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.agent import Agent
from app.models.company import Company
from app.schemas.agent import AgentRead

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/{agent_id}", response_model=AgentRead)
def get_agent(agent_id: int, db: Session = Depends(get_db)) -> Agent:
    agent = db.get(Agent, agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.get("/{agent_id}/subordinates", response_model=list[AgentRead])
def list_subordinates(agent_id: int, db: Session = Depends(get_db)) -> list[Agent]:
    agent = db.get(Agent, agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return list(agent.subordinates)
