from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.enums import EventType
from app.models.base import TimestampMixin


class Event(Base, TimestampMixin):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    actor_id: Mapped[int | None] = mapped_column(
        ForeignKey("agents.id", ondelete="SET NULL"), index=True, nullable=True
    )
    event_type: Mapped[EventType] = mapped_column(
        SAEnum(EventType), nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    target_type: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    target_id: Mapped[int | None] = mapped_column(nullable=True, index=True)
    meta: Mapped[dict | None] = mapped_column("metadata", JSON, default=dict)
    simulation_day: Mapped[int] = mapped_column(default=1, nullable=False, index=True)

    company: Mapped["Company"] = relationship(  # noqa: F821
        "Company", back_populates="events"
    )
    actor: Mapped["Agent | None"] = relationship(  # noqa: F821
        "Agent", back_populates="events"
    )

    def __repr__(self) -> str:
        return f"<Event id={self.id} type={self.event_type} day={self.simulation_day}>"
