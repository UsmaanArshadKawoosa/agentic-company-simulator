from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.base import TimestampMixin


class CapTableEntry(Base, TimestampMixin):
    __tablename__ = "cap_table"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    owner_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    owner_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    owner_name: Mapped[str] = mapped_column(String(255), nullable=False)
    ownership_percentage: Mapped[float] = mapped_column(Float, nullable=False)
    shares: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    company: Mapped["Company"] = relationship(  # noqa: F821
        "Company", back_populates="cap_table"
    )

    def __repr__(self) -> str:
        return f"<CapTableEntry id={self.id} owner={self.owner_name!r} pct={self.ownership_percentage:.2f}%>"
