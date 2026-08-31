from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.enums import CampaignStatus, SegmentType
from app.models.base import TimestampMixin


class Campaign(Base, TimestampMixin):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    segment: Mapped[SegmentType] = mapped_column(SAEnum(SegmentType), nullable=False, index=True)
    budget: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    daily_spend: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, default=7, nullable=False)
    days_remaining: Mapped[int] = mapped_column(Integer, default=7, nullable=False)
    effectiveness: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    status: Mapped[CampaignStatus] = mapped_column(
        SAEnum(CampaignStatus), default=CampaignStatus.ACTIVE, nullable=False, index=True
    )
    created_day: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    company: Mapped["Company"] = relationship(  # noqa: F821
        "Company", back_populates="campaigns"
    )

    def __repr__(self) -> str:
        return f"<Campaign id={self.id} name={self.name!r} status={self.status}>"
