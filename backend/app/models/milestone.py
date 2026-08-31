from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.enums import MilestoneStatus
from app.models.base import TimestampMixin


class Milestone(Base, TimestampMixin):
    __tablename__ = "milestones"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, default="")
    sequence: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[MilestoneStatus] = mapped_column(
        SAEnum(MilestoneStatus), default=MilestoneStatus.PLANNED, nullable=False, index=True
    )
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    company: Mapped["Company"] = relationship(  # noqa: F821
        "Company", back_populates="milestones"
    )
    project: Mapped["Project"] = relationship(  # noqa: F821
        "Project", back_populates="milestones"
    )
    tasks: Mapped[list["Task"]] = relationship(  # noqa: F821
        "Task", back_populates="milestone"
    )

    def __repr__(self) -> str:
        return f"<Milestone id={self.id} name={self.name!r} status={self.status}>"
