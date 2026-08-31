from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.enums import CustomerStatus
from app.models.base import TimestampMixin


class Customer(Base, TimestampMixin):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[CustomerStatus] = mapped_column(
        SAEnum(CustomerStatus), default=CustomerStatus.ACTIVE, nullable=False, index=True
    )
    monthly_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    acquired_day: Mapped[int] = mapped_column(default=1, nullable=False, index=True)
    churn_day: Mapped[int | None] = mapped_column(nullable=True, index=True)

    company: Mapped["Company"] = relationship(  # noqa: F821
        "Company", back_populates="customers"
    )

    def __repr__(self) -> str:
        return f"<Customer id={self.id} name={self.name!r} status={self.status}>"
