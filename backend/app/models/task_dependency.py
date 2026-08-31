from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.base import TimestampMixin


class TaskDependency(Base, TimestampMixin):
    __tablename__ = "task_dependencies"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), index=True, nullable=False
    )
    depends_on_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), index=True, nullable=False
    )

    __table_args__ = (
        UniqueConstraint("task_id", "depends_on_id", name="uq_task_dependency"),
    )

    def __repr__(self) -> str:
        return f"<TaskDependency task={self.task_id} depends_on={self.depends_on_id}>"
