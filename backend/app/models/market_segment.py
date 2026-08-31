from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.enums import SegmentType
from app.models.base import TimestampMixin


class MarketSegment(Base, TimestampMixin):
    __tablename__ = "market_segments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    segment_type: Mapped[SegmentType] = mapped_column(SAEnum(SegmentType), nullable=False, index=True)
    size: Mapped[float] = mapped_column(Float, default=1000.0, nullable=False)
    demand: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    price_sensitivity: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    growth_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    competition_intensity: Mapped[float] = mapped_column(Float, default=0.3, nullable=False)
    avg_customer_value: Mapped[float] = mapped_column(Float, default=1000.0, nullable=False)
    sales_cycle_days: Mapped[int] = mapped_column(default=7, nullable=False)

    def __repr__(self) -> str:
        return f"<MarketSegment id={self.id} name={self.name!r} type={self.segment_type}>"
