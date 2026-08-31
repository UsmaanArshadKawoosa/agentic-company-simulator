from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.enums import ProjectStatus
from app.models.base import TimestampMixin


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, default="")
    status: Mapped[ProjectStatus] = mapped_column(
        SAEnum(ProjectStatus), default=ProjectStatus.PLANNED, nullable=False, index=True
    )
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    company: Mapped["Company"] = relationship(  # noqa: F821
        "Company", back_populates="projects"
    )
    tasks: Mapped[list["Task"]] = relationship(  # noqa: F821
        "Task", back_populates="project"
    )
    milestones: Mapped[list["Milestone"]] = relationship(  # noqa: F821
        "Milestone", back_populates="project", cascade="all, delete-orphan"
    )
    features: Mapped[list["ProductFeature"]] = relationship(  # noqa: F821
        "ProductFeature", back_populates="project"
    )

    def __repr__(self) -> str:
        return f"<Project id={self.id} name={self.name!r} status={self.status}>"
