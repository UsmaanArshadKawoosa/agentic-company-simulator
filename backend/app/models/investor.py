from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.enums import InvestorStage
from app.models.base import TimestampMixin


class Investor(Base, TimestampMixin):
    __tablename__ = "investors"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    preferred_stage: Mapped[InvestorStage] = mapped_column(
        SAEnum(InvestorStage), nullable=False, index=True
    )
    check_size_min: Mapped[float] = mapped_column(Float, nullable=False)
    check_size_max: Mapped[float] = mapped_column(Float, nullable=False)
    risk_tolerance: Mapped[float] = mapped_column(Float, nullable=False)
    sector_preference: Mapped[str] = mapped_column(String(100), default="")
    ownership_expectation: Mapped[float] = mapped_column(Float, nullable=False)
    reputation: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    interest_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    company: Mapped["Company"] = relationship(  # noqa: F821
        "Company", back_populates="investors"
    )
    funding_rounds: Mapped[list["FundingRound"]] = relationship(  # noqa: F821
        "FundingRound", back_populates="investor"
    )
    pipeline_entries: Mapped[list["FundraisingPipeline"]] = relationship(  # noqa: F821
        "FundraisingPipeline", back_populates="investor"
    )

    def __repr__(self) -> str:
        return f"<Investor id={self.id} name={self.name!r} stage={self.preferred_stage.value}>"
