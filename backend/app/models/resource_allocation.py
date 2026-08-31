from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.enums import ResourceType
from app.models.base import TimestampMixin


class ResourceAllocation(Base, TimestampMixin):
    __tablename__ = "resource_allocations"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    resource_type: Mapped[ResourceType] = mapped_column(
        SAEnum(ResourceType), nullable=False, index=True
    )
    allocated_amount: Mapped[float] = mapped_column(Float, nullable=False)
    available_amount: Mapped[float] = mapped_column(Float, nullable=False)
    allocation_day: Mapped[int] = mapped_column(default=1, nullable=False)
    purpose: Mapped[str | None] = mapped_column(Text, default="")
    owner_id: Mapped[int | None] = mapped_column(
        ForeignKey("agents.id", ondelete="SET NULL"), index=True, nullable=True
    )

    company: Mapped["Company"] = relationship(  # noqa: F821
        "Company", back_populates="resource_allocations"
    )

    def __repr__(self) -> str:
        return f"<ResourceAllocation id={self.id} type={self.resource_type.value} amount={self.allocated_amount}>"
