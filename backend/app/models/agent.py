from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.enums import AgentRole, AgentStatus
from app.models.base import TimestampMixin


class Agent(Base, TimestampMixin):
    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[AgentRole] = mapped_column(
        SAEnum(AgentRole), nullable=False, index=True
    )
    personality: Mapped[dict | None] = mapped_column(JSON, default=dict)
    skills: Mapped[list | None] = mapped_column(JSON, default=list)
    authority: Mapped[int] = mapped_column(default=5, nullable=False)
    salary: Mapped[float] = mapped_column(Float, default=500.0, nullable=False)
    capacity: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)
    budget: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    morale: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    energy: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    workload: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[AgentStatus] = mapped_column(
        SAEnum(AgentStatus), default=AgentStatus.IDLE, nullable=False, index=True
    )
    manager_id: Mapped[int | None] = mapped_column(
        ForeignKey("agents.id", ondelete="SET NULL"), index=True, nullable=True
    )

    company: Mapped["Company"] = relationship(  # noqa: F821
        "Company", back_populates="agents"
    )
    manager: Mapped["Agent | None"] = relationship(
        "Agent", remote_side=[id], back_populates="subordinates"
    )
    subordinates: Mapped[list["Agent"]] = relationship(
        "Agent", back_populates="manager"
    )
    created_tasks: Mapped[list["Task"]] = relationship(
        "Task", back_populates="creator", foreign_keys="Task.created_by"  # noqa: F821
    )
    assigned_tasks: Mapped[list["Task"]] = relationship(
        "Task", back_populates="assignee", foreign_keys="Task.assigned_to"  # noqa: F821
    )
    events: Mapped[list["Event"]] = relationship(  # noqa: F821
        "Event", back_populates="actor"
    )
    decisions: Mapped[list["Decision"]] = relationship(  # noqa: F821
        "Decision", back_populates="agent"
    )
    memories: Mapped[list["Memory"]] = relationship(  # noqa: F821
        "Memory", back_populates="agent", cascade="all, delete-orphan"
    )
    plans: Mapped[list["Plan"]] = relationship(  # noqa: F821
        "Plan", back_populates="agent", cascade="all, delete-orphan"
    )
    expectations: Mapped[list["Expectation"]] = relationship(  # noqa: F821
        "Expectation", back_populates="agent", cascade="all, delete-orphan"
    )
    sent_messages: Mapped[list["Message"]] = relationship(  # noqa: F821
        "Message", back_populates="sender", cascade="all, delete-orphan",
        foreign_keys="Message.sender_agent_id"
    )
    received_messages: Mapped[list["Message"]] = relationship(  # noqa: F821
        "Message", back_populates="recipient", cascade="all, delete-orphan",
        foreign_keys="Message.recipient_agent_id"
    )

    # --- Phase 10: Budget authority relationships ---
    requested_budgets: Mapped[list["BudgetRequest"]] = relationship(  # noqa: F821
        "BudgetRequest", back_populates="requester", foreign_keys="BudgetRequest.requester_id"
    )
    approved_budgets: Mapped[list["BudgetRequest"]] = relationship(  # noqa: F821
        "BudgetRequest", back_populates="approver", foreign_keys="BudgetRequest.approver_id"
    )

    def __repr__(self) -> str:
        return f"<Agent id={self.id} name={self.name!r} role={self.role}>"
