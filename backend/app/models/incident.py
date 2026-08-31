from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.enums import IncidentStatus, IncidentType, RiskSeverity
from app.models.base import TimestampMixin


class Incident(Base, TimestampMixin):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    incident_type: Mapped[IncidentType] = mapped_column(
        SAEnum(IncidentType), nullable=False, index=True
    )
    severity: Mapped[RiskSeverity] = mapped_column(
        SAEnum(RiskSeverity), default=RiskSeverity.MEDIUM, nullable=False, index=True
    )
    description: Mapped[str | None] = mapped_column(Text, default="")
    status: Mapped[IncidentStatus] = mapped_column(
        SAEnum(IncidentStatus), default=IncidentStatus.ACTIVE, nullable=False, index=True
    )
    detected_day: Mapped[int] = mapped_column(default=1, nullable=False)
    resolved_day: Mapped[int | None] = mapped_column(nullable=True)
    root_cause: Mapped[str | None] = mapped_column(Text, default="")
    impact_assessment: Mapped[str | None] = mapped_column(Text, default="")
    related_risk_id: Mapped[int | None] = mapped_column(
        ForeignKey("risks.id", ondelete="SET NULL"), index=True, nullable=True
    )

    company: Mapped["Company"] = relationship(  # noqa: F821
        "Company", back_populates="incidents"
    )
    related_risk: Mapped["Risk | None"] = relationship(  # noqa: F821
        "Risk"
    )

    def __repr__(self) -> str:
        return f"<Incident id={self.id} type={self.incident_type.value} severity={self.severity.value}>"
