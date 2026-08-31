from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.enums import BudgetStatus
from app.models.base import TimestampMixin


class BudgetRequest(Base, TimestampMixin):
    __tablename__ = "budget_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    requester_id: Mapped[int] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"), index=True, nullable=False
    )
    approver_id: Mapped[int | None] = mapped_column(
        ForeignKey("agents.id", ondelete="SET NULL"), index=True, nullable=True
    )
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    approved_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[BudgetStatus] = mapped_column(
        SAEnum(BudgetStatus), default=BudgetStatus.PENDING, nullable=False, index=True
    )
    requested_day: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    decided_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    decision_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    company: Mapped["Company"] = relationship(  # noqa: F821
        "Company", back_populates="budget_requests"
    )
    requester: Mapped["Agent"] = relationship(  # noqa: F821
        "Agent", back_populates="requested_budgets", foreign_keys="BudgetRequest.requester_id"
    )
    approver: Mapped["Agent | None"] = relationship(  # noqa: F821
        "Agent", back_populates="approved_budgets", foreign_keys="BudgetRequest.approver_id"
    )

    def __repr__(self) -> str:
        return f"<BudgetRequest id={self.id} amount=${self.amount:.2f} status={self.status.value}>"
