from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.enums import EmployeeStatus, JobStatus, PerformanceRating
from app.models.base import TimestampMixin


class Employee(Base, TimestampMixin):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[EmployeeStatus] = mapped_column(
        SAEnum(EmployeeStatus), default=EmployeeStatus.CANDIDATE, nullable=False, index=True
    )
    salary: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    capacity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    skills: Mapped[list | None] = mapped_column(JSON, default=list)
    personality: Mapped[dict | None] = mapped_column(JSON, default=dict)
    experience: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    performance_score: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    morale: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    productivity: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    onboarding_factor: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    workload: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    hired_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fired_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    manager_id: Mapped[int | None] = mapped_column(
        ForeignKey("employees.id", ondelete="SET NULL"), index=True, nullable=True
    )

    __table_args__ = (
        Index("ix_employees_company_status", "company_id", "status"),
    )

    company: Mapped["Company"] = relationship(  # noqa: F821
        "Company", back_populates="employees"
    )
    manager: Mapped["Employee | None"] = relationship(
        "Employee", remote_side=[id], back_populates="subordinates"
    )
    subordinates: Mapped[list["Employee"]] = relationship(
        "Employee", back_populates="manager"
    )

    def __repr__(self) -> str:
        return f"<Employee id={self.id} name={self.name!r} role={self.role} status={self.status}>"
