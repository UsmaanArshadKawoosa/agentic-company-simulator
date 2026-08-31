from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.enums import CompanyStatus
from app.models.base import TimestampMixin


class Company(Base, TimestampMixin):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    mission: Mapped[str | None] = mapped_column(Text, default="")
    cash: Mapped[float] = mapped_column(Float, default=100000.0, nullable=False)
    revenue: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    expenses: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    current_day: Mapped[int] = mapped_column(default=1, nullable=False)
    status: Mapped[CompanyStatus] = mapped_column(
        SAEnum(CompanyStatus), default=CompanyStatus.CREATED, nullable=False, index=True
    )

    # --- Phase 3 simulation state ---
    seed: Mapped[int] = mapped_column(Integer, default=12345, nullable=False)
    infrastructure_cost: Mapped[float] = mapped_column(Float, default=500.0, nullable=False)
    market_demand: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    market_competition: Mapped[float] = mapped_column(Float, default=0.3, nullable=False)
    market_sentiment: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    product_readiness: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # --- Phase 4 product/work state ---
    product_quality: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    technical_debt: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    marketing_effectiveness: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    agents: Mapped[list["Agent"]] = relationship(  # noqa: F821
        "Agent", back_populates="company", cascade="all, delete-orphan"
    )
    goals: Mapped[list["Goal"]] = relationship(  # noqa: F821
        "Goal", back_populates="company", cascade="all, delete-orphan"
    )
    projects: Mapped[list["Project"]] = relationship(  # noqa: F821
        "Project", back_populates="company", cascade="all, delete-orphan"
    )
    tasks: Mapped[list["Task"]] = relationship(  # noqa: F821
        "Task", back_populates="company", cascade="all, delete-orphan"
    )
    customers: Mapped[list["Customer"]] = relationship(  # noqa: F821
        "Customer", back_populates="company", cascade="all, delete-orphan"
    )
    milestones: Mapped[list["Milestone"]] = relationship(  # noqa: F821
        "Milestone", back_populates="company", cascade="all, delete-orphan"
    )
    features: Mapped[list["ProductFeature"]] = relationship(  # noqa: F821
        "ProductFeature", back_populates="company", cascade="all, delete-orphan"
    )
    events: Mapped[list["Event"]] = relationship(  # noqa: F821
        "Event", back_populates="company", cascade="all, delete-orphan"
    )
    decisions: Mapped[list["Decision"]] = relationship(  # noqa: F821
        "Decision", back_populates="company", cascade="all, delete-orphan"
    )
    plans: Mapped[list["Plan"]] = relationship(  # noqa: F821
        "Plan", back_populates="company", cascade="all, delete-orphan"
    )
    messages: Mapped[list["Message"]] = relationship(  # noqa: F821
        "Message", back_populates="company", cascade="all, delete-orphan"
    )
    expectations: Mapped[list["Expectation"]] = relationship(  # noqa: F821
        "Expectation", back_populates="company", cascade="all, delete-orphan"
    )

    # --- Phase 6 market & strategy state ---
    target_segment: Mapped[str] = mapped_column(String(50), default="SMB", nullable=False)
    price: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    positioning: Mapped[str] = mapped_column(Text, default="", nullable=False)
    brand_strength: Mapped[float] = mapped_column(Float, default=0.1, nullable=False)
    sales_effectiveness: Mapped[float] = mapped_column(Float, default=0.1, nullable=False)
    market_share_cache: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    sales_opportunities: Mapped[list["SalesOpportunity"]] = relationship(  # noqa: F821
        "SalesOpportunity", back_populates="company", cascade="all, delete-orphan"
    )
    campaigns: Mapped[list["Campaign"]] = relationship(  # noqa: F821
        "Campaign", back_populates="company", cascade="all, delete-orphan"
    )
    employees: Mapped[list["Employee"]] = relationship(  # noqa: F821
        "Employee", back_populates="company", cascade="all, delete-orphan"
    )
    job_openings: Mapped[list["JobOpening"]] = relationship(  # noqa: F821
        "JobOpening", back_populates="company", cascade="all, delete-orphan"
    )
    candidates: Mapped[list["Candidate"]] = relationship(  # noqa: F821
        "Candidate", back_populates="company", cascade="all, delete-orphan"
    )

    # --- Phase 10: Financial Intelligence, Funding & Capital Management ---
    investors: Mapped[list["Investor"]] = relationship(  # noqa: F821
        "Investor", back_populates="company", cascade="all, delete-orphan"
    )
    funding_rounds: Mapped[list["FundingRound"]] = relationship(  # noqa: F821
        "FundingRound", back_populates="company", cascade="all, delete-orphan"
    )
    fundraising_pipeline: Mapped[list["FundraisingPipeline"]] = relationship(  # noqa: F821
        "FundraisingPipeline", back_populates="company", cascade="all, delete-orphan"
    )
    cap_table: Mapped[list["CapTableEntry"]] = relationship(  # noqa: F821
        "CapTableEntry", back_populates="company", cascade="all, delete-orphan"
    )
    budget_requests: Mapped[list["BudgetRequest"]] = relationship(  # noqa: F821
        "BudgetRequest", back_populates="company", cascade="all, delete-orphan"
    )

    # --- Phase 11: Advanced Autonomous Company Operations ---
    objectives: Mapped[list["Objective"]] = relationship(  # noqa: F821
        "Objective", back_populates="company", cascade="all, delete-orphan"
    )
    resource_allocations: Mapped[list["ResourceAllocation"]] = relationship(  # noqa: F821
        "ResourceAllocation", back_populates="company", cascade="all, delete-orphan"
    )
    risks: Mapped[list["Risk"]] = relationship(  # noqa: F821
        "Risk", back_populates="company", cascade="all, delete-orphan"
    )
    incidents: Mapped[list["Incident"]] = relationship(  # noqa: F821
        "Incident", back_populates="company", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Company id={self.id} name={self.name!r} status={self.status}>"
