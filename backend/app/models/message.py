from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.enums import MessagePriority
from app.models.base import TimestampMixin


class Message(Base, TimestampMixin):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    sender_agent_id: Mapped[int] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"), index=True, nullable=False
    )
    recipient_agent_id: Mapped[int] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"), index=True, nullable=False
    )
    subject: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    content: Mapped[str] = mapped_column(Text, default="", nullable=False)
    priority: Mapped[MessagePriority] = mapped_column(
        SAEnum(MessagePriority), default=MessagePriority.NORMAL, nullable=False, index=True
    )
    created_day: Mapped[int] = mapped_column(default=1, nullable=False)
    read_day: Mapped[int | None] = mapped_column(nullable=True)

    company: Mapped["Company"] = relationship(  # noqa: F821
        "Company", back_populates="messages"
    )
    sender: Mapped["Agent"] = relationship(  # noqa: F821
        "Agent", back_populates="sent_messages", foreign_keys=[sender_agent_id]
    )
    recipient: Mapped["Agent"] = relationship(  # noqa: F821
        "Agent", back_populates="received_messages", foreign_keys=[recipient_agent_id]
    )

    def __repr__(self) -> str:
        return f"<Message id={self.id} from={self.sender_agent_id} to={self.recipient_agent_id}>"
