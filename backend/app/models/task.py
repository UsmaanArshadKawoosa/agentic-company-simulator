from datetime import datetime

from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.enums import TaskStatus, TaskType
from app.models.base import TimestampMixin


class Task(Base, TimestampMixin):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    project_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), index=True, nullable=True
    )
    milestone_id: Mapped[int | None] = mapped_column(
        ForeignKey("milestones.id", ondelete="SET NULL"), index=True, nullable=True
    )
    feature_id: Mapped[int | None] = mapped_column(
        ForeignKey("product_features.id", ondelete="SET NULL"), index=True, nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, default="")
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("agents.id", ondelete="SET NULL"), index=True, nullable=True
    )
    assigned_to: Mapped[int | None] = mapped_column(
        ForeignKey("agents.id", ondelete="SET NULL"), index=True, nullable=True
    )
    assigned_employee_id: Mapped[int | None] = mapped_column(
        ForeignKey("employees.id", ondelete="SET NULL"), index=True, nullable=True
    )
    priority: Mapped[int] = mapped_column(default=1, nullable=False)
    task_type: Mapped[TaskType] = mapped_column(
        SAEnum(TaskType), default=TaskType.ENGINEERING, nullable=False, index=True
    )
    status: Mapped[TaskStatus] = mapped_column(
        SAEnum(TaskStatus), default=TaskStatus.TODO, nullable=False, index=True
    )
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    effort: Mapped[float] = mapped_column(Float, default=10.0, nullable=False)
    remaining_effort: Mapped[float] = mapped_column(Float, default=10.0, nullable=False)
    deadline: Mapped[datetime | None] = mapped_column(nullable=True)
    result: Mapped[str | None] = mapped_column(Text, default=None)

    __table_args__ = (
        Index("ix_tasks_company_status", "company_id", "status"),
    )

    company: Mapped["Company"] = relationship(  # noqa: F821
        "Company", back_populates="tasks"
    )
    project: Mapped["Project | None"] = relationship(  # noqa: F821
        "Project", back_populates="tasks"
    )
    milestone: Mapped["Milestone | None"] = relationship(  # noqa: F821
        "Milestone", back_populates="tasks"
    )
    feature: Mapped["ProductFeature | None"] = relationship(  # noqa: F821
        "ProductFeature", back_populates="tasks"
    )
    creator: Mapped["Agent | None"] = relationship(  # noqa: F821
        "Agent", back_populates="created_tasks", foreign_keys=[created_by]
    )
    assignee: Mapped["Agent | None"] = relationship(  # noqa: F821
        "Agent", back_populates="assigned_tasks", foreign_keys=[assigned_to]
    )
    assigned_employee: Mapped["Employee | None"] = relationship(  # noqa: F821
        "Employee", foreign_keys=[assigned_employee_id]
    )

    def __repr__(self) -> str:
        return f"<Task id={self.id} title={self.title!r} status={self.status}>"
