from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.enums import JobStatus
from app.models.base import TimestampMixin


class JobOpening(Base, TimestampMixin):
    __tablename__ = "job_openings"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    role: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    required_skills: Mapped[list | None] = mapped_column(JSON, default=list)
    salary_min: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    salary_max: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    capacity_required: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_day: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[JobStatus] = mapped_column(
        SAEnum(JobStatus), default=JobStatus.OPEN, nullable=False, index=True
    )
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("agents.id", ondelete="SET NULL"), index=True, nullable=True
    )

    company: Mapped["Company"] = relationship(  # noqa: F821
        "Company", back_populates="job_openings"
    )
    candidates: Mapped[list["Candidate"]] = relationship(  # noqa: F821
        "Candidate", back_populates="job_opening"
    )

    def __repr__(self) -> str:
        return f"<JobOpening id={self.id} role={self.role} status={self.status}>"
