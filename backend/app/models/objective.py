from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.enums import ObjectiveStatus, ObjectiveType
from app.models.base import TimestampMixin


class Objective(Base, TimestampMixin):
    __tablename__ = "objectives"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("objectives.id", ondelete="CASCADE"), index=True, nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, default="")
    objective_type: Mapped[ObjectiveType] = mapped_column(
        SAEnum(ObjectiveType), default=ObjectiveType.OPERATIONAL, nullable=False, index=True
    )
    status: Mapped[ObjectiveStatus] = mapped_column(
        SAEnum(ObjectiveStatus), default=ObjectiveStatus.TODO, nullable=False, index=True
    )
    priority: Mapped[int] = mapped_column(default=1, nullable=False)
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    expected_outcome: Mapped[str | None] = mapped_column(Text, default="")
    owner_id: Mapped[int | None] = mapped_column(
        ForeignKey("agents.id", ondelete="SET NULL"), index=True, nullable=True
    )
    created_day: Mapped[int] = mapped_column(default=1, nullable=False)
    completed_day: Mapped[int | None] = mapped_column(nullable=True)

    company: Mapped["Company"] = relationship(  # noqa: F821
        "Company", back_populates="objectives"
    )
    parent: Mapped["Objective | None"] = relationship(  # noqa: F821
        "Objective", remote_side="Objective.id", back_populates="children"
    )
    children: Mapped[list["Objective"]] = relationship(  # noqa: F821
        "Objective", back_populates="parent"
    )

    def __repr__(self) -> str:
        return f"<Objective id={self.id} title={self.title!r} status={self.status.value}>"
