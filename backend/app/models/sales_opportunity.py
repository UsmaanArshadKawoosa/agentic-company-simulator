from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.enums import SalesStage, SegmentType
from app.models.base import TimestampMixin


class SalesOpportunity(Base, TimestampMixin):
    __tablename__ = "sales_opportunities"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    segment: Mapped[SegmentType] = mapped_column(SAEnum(SegmentType), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    stage: Mapped[SalesStage] = mapped_column(
        SAEnum(SalesStage), default=SalesStage.LEAD, nullable=False, index=True
    )
    created_day: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    expected_close_day: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    won_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lost_day: Mapped[int | None] = mapped_column(Integer, nullable=True)

    company: Mapped["Company"] = relationship(  # noqa: F821
        "Company", back_populates="sales_opportunities"
    )

    def __repr__(self) -> str:
        return f"<SalesOpportunity id={self.id} name={self.name!r} stage={self.stage}>"
