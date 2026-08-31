from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.enums import RiskSeverity, RiskStatus
from app.models.base import TimestampMixin


class Risk(Base, TimestampMixin):
    __tablename__ = "risks"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    risk_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    severity: Mapped[RiskSeverity] = mapped_column(
        SAEnum(RiskSeverity), default=RiskSeverity.MEDIUM, nullable=False, index=True
    )
    source: Mapped[str | None] = mapped_column(Text, default="")
    description: Mapped[str | None] = mapped_column(Text, default="")
    affected_entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    affected_entity_id: Mapped[int | None] = mapped_column(nullable=True)
    status: Mapped[RiskStatus] = mapped_column(
        SAEnum(RiskStatus), default=RiskStatus.ACTIVE, nullable=False, index=True
    )
    mitigation_actions: Mapped[str | None] = mapped_column(Text, default="")
    detected_day: Mapped[int] = mapped_column(default=1, nullable=False)
    resolved_day: Mapped[int | None] = mapped_column(nullable=True)

    company: Mapped["Company"] = relationship(  # noqa: F821
        "Company", back_populates="risks"
    )

    def __repr__(self) -> str:
        return f"<Risk id={self.id} type={self.risk_type} severity={self.severity.value}>"
