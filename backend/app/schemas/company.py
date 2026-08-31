from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.enums import CompanyStatus


class CompanyCreate(BaseModel):
    name: str
    mission: str = ""
    seed: int | None = None


class CompanyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    mission: str
    cash: float
    revenue: float
    expenses: float
    current_day: int
    status: CompanyStatus
    seed: int
    created_at: datetime
    updated_at: datetime
