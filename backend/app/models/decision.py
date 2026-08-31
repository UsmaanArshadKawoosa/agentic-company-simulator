from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.base import TimestampMixin


class Decision(Base, TimestampMixin):
    __tablename__ = "decisions"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    agent_id: Mapped[int | None] = mapped_column(
        ForeignKey("agents.id", ondelete="SET NULL"), index=True, nullable=True
    )
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    reasoning: Mapped[str | None] = mapped_column(Text, default="")
    context: Mapped[dict | None] = mapped_column(JSON, default=dict)
    outcome: Mapped[str | None] = mapped_column(Text, default=None)
    simulation_day: Mapped[int] = mapped_column(default=1, nullable=False, index=True)

    company: Mapped["Company"] = relationship(  # noqa: F821
        "Company", back_populates="decisions"
    )
    agent: Mapped["Agent | None"] = relationship(  # noqa: F821
        "Agent", back_populates="decisions"
    )

    def __repr__(self) -> str:
        return f"<Decision id={self.id} action={self.action!r} day={self.simulation_day}>"
