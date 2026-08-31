from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.enums import PlanStatus
from app.models.base import TimestampMixin


class Plan(Base, TimestampMixin):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    agent_id: Mapped[int] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"), index=True, nullable=False
    )
    goal_id: Mapped[int | None] = mapped_column(
        ForeignKey("goals.id", ondelete="SET NULL"), index=True, nullable=True
    )
    objective: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[PlanStatus] = mapped_column(
        SAEnum(PlanStatus), default=PlanStatus.ACTIVE, nullable=False, index=True
    )
    priority: Mapped[int] = mapped_column(default=1, nullable=False)
    created_day: Mapped[int] = mapped_column(default=1, nullable=False)
    completed_day: Mapped[int | None] = mapped_column(nullable=True)
    current_step: Mapped[int] = mapped_column(default=0, nullable=False)

    company: Mapped["Company"] = relationship(  # noqa: F821
        "Company", back_populates="plans"
    )
    agent: Mapped["Agent"] = relationship(  # noqa: F821
        "Agent", back_populates="plans"
    )
    goal: Mapped["Goal | None"] = relationship(  # noqa: F821
        "Goal", back_populates="plans"
    )
    steps: Mapped[list["PlanStep"]] = relationship(  # noqa: F821
        "PlanStep", back_populates="plan", cascade="all, delete-orphan",
        order_by="PlanStep.sequence",
    )

    def __repr__(self) -> str:
        return f"<Plan id={self.id} objective={self.objective!r} status={self.status}>"


class PlanStep(Base, TimestampMixin):
    __tablename__ = "plan_steps"

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("plans.id", ondelete="CASCADE"), index=True, nullable=False
    )
    sequence: Mapped[int] = mapped_column(default=0, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[PlanStatus] = mapped_column(
        SAEnum(PlanStatus), default=PlanStatus.ACTIVE, nullable=False, index=True
    )
    linked_task_id: Mapped[int | None] = mapped_column(
        ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True
    )

    plan: Mapped["Plan"] = relationship(  # noqa: F821
        "Plan", back_populates="steps"
    )

    def __repr__(self) -> str:
        return f"<PlanStep id={self.id} seq={self.sequence} plan_id={self.plan_id}>"
