from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.base import TimestampMixin


class Memory(Base, TimestampMixin):
    __tablename__ = "memories"

    id: Mapped[int] = mapped_column(primary_key=True)
    agent_id: Mapped[int] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"), index=True, nullable=False
    )
    memory_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, default="", nullable=False)
    importance: Mapped[float] = mapped_column(default=0.5, nullable=False)
    simulation_day: Mapped[int] = mapped_column(default=1, nullable=False, index=True)
    meta: Mapped[dict | None] = mapped_column("metadata", JSON, default=dict)

    agent: Mapped["Agent"] = relationship(  # noqa: F821
        "Agent", back_populates="memories"
    )

    def __repr__(self) -> str:
        return f"<Memory id={self.id} type={self.memory_type!r} agent={self.agent_id}>"
