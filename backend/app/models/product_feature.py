from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.enums import FeatureStatus
from app.models.base import TimestampMixin


class ProductFeature(Base, TimestampMixin):
    __tablename__ = "product_features"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    project_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), index=True, nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, default="")
    status: Mapped[FeatureStatus] = mapped_column(
        SAEnum(FeatureStatus), default=FeatureStatus.PLANNED, nullable=False, index=True
    )
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    quality: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    importance: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    company: Mapped["Company"] = relationship(  # noqa: F821
        "Company", back_populates="features"
    )
    project: Mapped["Project | None"] = relationship(  # noqa: F821
        "Project", back_populates="features"
    )
    tasks: Mapped[list["Task"]] = relationship(  # noqa: F821
        "Task", back_populates="feature"
    )

    def __repr__(self) -> str:
        return f"<ProductFeature id={self.id} name={self.name!r} status={self.status}>"
