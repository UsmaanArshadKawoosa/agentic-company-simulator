from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.enums import InvestorStage
from app.models.base import TimestampMixin


class FundingRound(Base, TimestampMixin):
    __tablename__ = "funding_rounds"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    round_stage: Mapped[InvestorStage] = mapped_column(
        SAEnum(InvestorStage), nullable=False, index=True
    )
    amount_requested: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    amount_raised: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    valuation: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    pre_money_valuation: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    post_money_valuation: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    equity_sold: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="OPEN", nullable=False, index=True)
    day_opened: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    day_closed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    investor_id: Mapped[int | None] = mapped_column(
        ForeignKey("investors.id", ondelete="SET NULL"), index=True, nullable=True
    )

    company: Mapped["Company"] = relationship(  # noqa: F821
        "Company", back_populates="funding_rounds"
    )
    investor: Mapped["Investor | None"] = relationship(  # noqa: F821
        "Investor", back_populates="funding_rounds"
    )
    pipeline_entries: Mapped[list["FundraisingPipeline"]] = relationship(  # noqa: F821
        "FundraisingPipeline", back_populates="funding_round"
    )

    def __repr__(self) -> str:
        return f"<FundingRound id={self.id} stage={self.round_stage.value} raised=${self.amount_raised:.2f}>"
