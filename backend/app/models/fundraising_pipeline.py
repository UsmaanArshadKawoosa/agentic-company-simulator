from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.enums import FundingRoundStatus, InvestorStage
from app.models.base import TimestampMixin


class FundraisingPipeline(Base, TimestampMixin):
    __tablename__ = "fundraising_pipeline"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    investor_id: Mapped[int | None] = mapped_column(
        ForeignKey("investors.id", ondelete="SET NULL"), index=True, nullable=True
    )
    funding_round_id: Mapped[int | None] = mapped_column(
        ForeignKey("funding_rounds.id", ondelete="SET NULL"), index=True, nullable=True
    )
    status: Mapped[FundingRoundStatus] = mapped_column(
        SAEnum(FundingRoundStatus), default=FundingRoundStatus.DISCOVERED, nullable=False, index=True
    )
    stage: Mapped[InvestorStage] = mapped_column(
        SAEnum(InvestorStage), nullable=False, index=True
    )
    interest_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    day_updated: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    company: Mapped["Company"] = relationship(  # noqa: F821
        "Company", back_populates="fundraising_pipeline"
    )
    investor: Mapped["Investor | None"] = relationship(  # noqa: F821
        "Investor", back_populates="pipeline_entries"
    )
    funding_round: Mapped["FundingRound | None"] = relationship(  # noqa: F821
        "FundingRound", back_populates="pipeline_entries"
    )

    def __repr__(self) -> str:
        return f"<FundraisingPipeline id={self.id} status={self.status.value} stage={self.stage.value}>"
