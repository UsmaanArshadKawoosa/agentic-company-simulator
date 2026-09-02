from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.enums import EmployeeStatus
from app.models.base import TimestampMixin


class Candidate(Base, TimestampMixin):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    job_opening_id: Mapped[int | None] = mapped_column(
        ForeignKey("job_openings.id", ondelete="SET NULL"), index=True, nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(100), nullable=False)
    skills: Mapped[list | None] = mapped_column(JSON, default=list)
    experience: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    salary_expectation: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    productivity_potential: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    culture_fit: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    reliability: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    hiring_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[EmployeeStatus] = mapped_column(
        SAEnum(EmployeeStatus), default=EmployeeStatus.CANDIDATE, nullable=False, index=True
    )
    evaluation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    evaluated_by: Mapped[int | None] = mapped_column(
        ForeignKey("agents.id", ondelete="SET NULL"), index=True, nullable=True
    )
    evaluated_day: Mapped[int | None] = mapped_column(Integer, nullable=True)

    __table_args__ = (
        Index("ix_candidates_company_status", "company_id", "status"),
    )

    company: Mapped["Company"] = relationship(  # noqa: F821
        "Company", back_populates="candidates"
    )
    job_opening: Mapped["JobOpening | None"] = relationship(  # noqa: F821
        "JobOpening", back_populates="candidates"
    )

    def __repr__(self) -> str:
        return f"<Candidate id={self.id} name={self.name!r} role={self.role} score={self.hiring_score}>"
