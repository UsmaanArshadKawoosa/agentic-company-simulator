from datetime import datetime

from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.enums import GoalStatus
from app.models.base import TimestampMixin


class Goal(Base, TimestampMixin):
    __tablename__ = "goals"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, default="")
    status: Mapped[GoalStatus] = mapped_column(
        SAEnum(GoalStatus), default=GoalStatus.TODO, nullable=False, index=True
    )
    priority: Mapped[int] = mapped_column(default=1, nullable=False)
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    deadline: Mapped[datetime | None] = mapped_column(nullable=True)

    company: Mapped["Company"] = relationship(  # noqa: F821
        "Company", back_populates="goals"
    )
    plans: Mapped[list["Plan"]] = relationship(  # noqa: F821
        "Plan", back_populates="goal"
    )

    def __repr__(self) -> str:
        return f"<Goal id={self.id} title={self.title!r} status={self.status}>"
