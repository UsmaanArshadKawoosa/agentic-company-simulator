from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.enums import ScenarioStatus
from app.models.base import TimestampMixin


class Scenario(Base, TimestampMixin):
    __tablename__ = "scenarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="custom", nullable=False, index=True)
    is_builtin: Mapped[bool] = mapped_column(default=False, nullable=False, index=True)
    configuration: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    runs: Mapped[list["SimulationRun"]] = relationship(
        "SimulationRun", back_populates="scenario", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Scenario id={self.id} name={self.name!r} category={self.category!r}>"


class SimulationRun(Base, TimestampMixin):
    __tablename__ = "simulation_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    scenario_id: Mapped[int] = mapped_column(
        ForeignKey("scenarios.id", ondelete="CASCADE"), index=True, nullable=False
    )
    company_id: Mapped[int | None] = mapped_column(
        ForeignKey("companies.id", ondelete="SET NULL"), index=True, nullable=True
    )
    seed: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[ScenarioStatus] = mapped_column(
        SAEnum(ScenarioStatus), default=ScenarioStatus.PENDING, nullable=False, index=True
    )
    simulation_days: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    configuration_snapshot: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    final_metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    started_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    completed_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_runs_scenario_status", "scenario_id", "status"),
    )

    scenario: Mapped["Scenario"] = relationship("Scenario", back_populates="runs")

    def __repr__(self) -> str:
        return f"<SimulationRun id={self.id} scenario_id={self.scenario_id} status={self.status!r}>"
