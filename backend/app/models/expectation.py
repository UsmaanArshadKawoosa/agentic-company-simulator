from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.enums import ExpectationStatus
from app.models.base import TimestampMixin


class Expectation(Base, TimestampMixin):
    __tablename__ = "expectations"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    agent_id: Mapped[int] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"), index=True, nullable=False
    )
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    target_day: Mapped[int] = mapped_column(default=1, nullable=False)
    target_metric: Mapped[str] = mapped_column(String(128), default="", nullable=False)
    expected_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    actual_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[ExpectationStatus] = mapped_column(
        SAEnum(ExpectationStatus), default=ExpectationStatus.PENDING, nullable=False, index=True
    )
    linked_decision_id: Mapped[int | None] = mapped_column(
        ForeignKey("decisions.id", ondelete="SET NULL"), nullable=True
    )

    company: Mapped["Company"] = relationship(  # noqa: F821
        "Company", back_populates="expectations"
    )
    agent: Mapped["Agent"] = relationship(  # noqa: F821
        "Agent", back_populates="expectations"
    )

    def __repr__(self) -> str:
        return f"<Expectation id={self.id} metric={self.target_metric!r} status={self.status}>"
