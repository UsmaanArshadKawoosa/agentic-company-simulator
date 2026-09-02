from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# --- Scenario Schemas ---


class ScenarioConfiguration(BaseModel):
    """Configuration for a scenario's initial company conditions."""

    name: str = "Startup"
    mission: str = "Build a great product"
    cash: float = Field(default=100000.0, ge=0, le=10_000_000)
    seed: int | None = Field(default=None, ge=1, le=1_000_000_000)
    market_demand: float = Field(default=0.5, ge=0.0, le=1.0)
    market_competition: float = Field(default=0.3, ge=0.0, le=1.0)
    product_readiness: float = Field(default=0.0, ge=0.0, le=1.0)
    technical_debt: float = Field(default=0.0, ge=0.0, le=1.0)
    target_segment: str = "SMB"
    price: float = Field(default=100.0, ge=0, le=100_000)


class ScenarioCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    category: str = "custom"
    configuration: ScenarioConfiguration | None = None


class ScenarioUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    category: str | None = None
    configuration: ScenarioConfiguration | None = None


class ScenarioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    category: str
    is_builtin: bool
    configuration: dict
    run_count: int = 0
    created_at: str | None = None
    updated_at: str | None = None


# --- Simulation Run Schemas ---


class SimulationRunCreate(BaseModel):
    seed: int | None = Field(default=None, ge=1, le=1_000_000_000)
    simulation_days: int = Field(default=50, ge=1, le=1000)


class SimulationRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    scenario_id: int
    company_id: int | None
    seed: int
    status: str
    simulation_days: int
    configuration_snapshot: dict
    final_metrics: dict | None
    started_at: str | None
    completed_at: str | None
    error_message: str | None
    created_at: str | None = None


# --- Experiment Results Schemas ---


class RunResult(BaseModel):
    run_id: int
    seed: int
    status: str
    simulation_days: int
    final_day: int
    metrics: dict


class MetricSummary(BaseModel):
    best: float
    worst: float
    average: float
    median: float


class ExperimentResult(BaseModel):
    scenario_id: int
    scenario_name: str
    total_runs: int
    completed_runs: int
    runs: list[RunResult]
    summary: dict[str, MetricSummary]
