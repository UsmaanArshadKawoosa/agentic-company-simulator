from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base
from app.enums import CompetitorStrategy, SegmentType
from app.models.base import TimestampMixin


class Competitor(Base, TimestampMixin):
    __tablename__ = "competitors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    market_share: Mapped[float] = mapped_column(Float, default=0.1, nullable=False)
    price: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    product_quality: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    brand_strength: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    target_segment: Mapped[SegmentType] = mapped_column(SAEnum(SegmentType), nullable=False, index=True)
    marketing_strength: Mapped[float] = mapped_column(Float, default=0.3, nullable=False)
    sales_strength: Mapped[float] = mapped_column(Float, default=0.3, nullable=False)
    strategy: Mapped[CompetitorStrategy] = mapped_column(
        SAEnum(CompetitorStrategy), default=CompetitorStrategy.BALANCED, nullable=False
    )

    def __repr__(self) -> str:
        return f"<Competitor id={self.id} name={self.name!r} share={self.market_share}>"
