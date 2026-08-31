from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

from sqlalchemy import select

from app.agents.context import AgentContext, build_context
from app.agents.decisions import ActionType, AgentDecision
from app.agents.prompts import get_role_prompt
from app.agents.validator import DecisionValidator
from app.enums import AgentStatus, EventType
from app.models.agent import Agent
from app.models.company import Company
from app.models.event import Event
from app.models.goal import Goal
from app.models.memory import Memory
from app.models.project import Project
from app.models.task import Task
from app.services.llm import LLMService, build_decision_from_llm

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = logging.getLogger("agent_company_simulator")


def _sim_ctx(db: "Session", company, day: int):
    """Build a lightweight SimulationContext for system calls within agent code."""
    from app.simulation.domain import SimulationContext, make_rng
    return SimulationContext(db=db, company=company, day=day, rng=make_rng(company.seed, day))


class BaseAgent:
    """Agent with a real observe/think/decide/act/reflect lifecycle.

    The lifecycle uses actual simulation state. The LLM produces structured
    decisions; the DecisionValidator (never the LLM) mutates company state.
    """

    role_name: str = "AGENT"

    def __init__(
        self,
        agent: Agent,
        company: Company,
        llm: LLMService | None = None,
    ) -> None:
        self.agent = agent
        self.company = company
        self.llm = llm
        self._llm_events: list[Event] = []

    # --- context ---

    def _build_context(self, db: "Session") -> AgentContext:
        company_id = self.company.id
        goals = list(
            db.execute(select(Goal).where(Goal.company_id == company_id)).scalars().all()
        )
        projects = list(
            db.execute(select(Project).where(Project.company_id == company_id)).scalars().all()
        )
        tasks = list(
            db.execute(select(Task).where(Task.company_id == company_id)).scalars().all()
        )
        from app.models.decision import Decision
        from app.models.customer import Customer as CustomerModel
        from app.models.milestone import Milestone
        from app.models.product_feature import ProductFeature
        from app.models.plan import Plan
        from app.models.expectation import Expectation

        recent_events = [
            {
                "event_type": e.event_type.value if isinstance(e.event_type, EventType) else str(e.event_type),
                "description": e.description,
                "day": e.simulation_day,
            }
            for e in db.execute(
                select(Event)
                .where(Event.company_id == company_id)
                .order_by(Event.id.desc())
                .limit(5)
            )
            .scalars()
            .all()
        ]
        recent_decisions = [
            {
                "action": d.action,
                "outcome": d.outcome,
                "day": d.simulation_day,
            }
            for d in db.execute(
                select(Decision)
                .where(Decision.company_id == company_id)
                .order_by(Decision.id.desc())
                .limit(5)
            )
            .scalars()
            .all()
        ]
        recent_environmental_events = [
            {
                "event_type": e.event_type.value if isinstance(e.event_type, EventType) else str(e.event_type),
                "description": e.description,
                "day": e.simulation_day,
            }
            for e in db.execute(
                select(Event)
                .where(Event.company_id == company_id)
                .where(Event.event_type == "ENVIRONMENTAL_EVENT")
                .order_by(Event.id.desc())
                .limit(3)
            )
            .scalars()
            .all()
        ]

        customers = list(
            db.execute(select(CustomerModel).where(CustomerModel.company_id == company_id))
            .scalars()
            .all()
        )
        active_customers = [c for c in customers if c.status == "ACTIVE"]
        churned_customers = [c for c in customers if c.status == "CHURNED"]

        milestones = list(
            db.execute(select(Milestone).where(Milestone.company_id == company_id)).scalars().all()
        )
        features = list(
            db.execute(select(ProductFeature).where(ProductFeature.company_id == company_id)).scalars().all()
        )

        # --- Phase 5 autonomy context ---
        plans = list(
            db.execute(
                select(Plan)
                .where(Plan.company_id == company_id)
                .where(Plan.agent_id == self.agent.id)
                .order_by(Plan.created_day.desc())
                .limit(5)
            )
            .scalars()
            .all()
        )
        expectations = list(
            db.execute(
                select(Expectation)
                .where(Expectation.company_id == company_id)
                .where(Expectation.agent_id == self.agent.id)
                .order_by(Expectation.id.desc())
                .limit(5)
            )
            .scalars()
            .all()
        )

        # Relevant memories: retrieve by topic relevance using current goals/tasks.
        from app.simulation import memory as memory_system
        query_parts = [g.title for g in goals[:3]] + [t.title for t in tasks[:5]]
        query_text = " ".join(query_parts) if query_parts else self.role_name
        relevant_memories = memory_system.retrieve_memories(
            _sim_ctx(db, self.company, self.company.current_day),
            self.agent.id,
            query_text,
            limit=5,
        )

        # Unread + recent messages for this agent.
        from app.simulation import communication as comm_system
        ctx = _sim_ctx(db, self.company, self.company.current_day)
        unread_messages = comm_system.get_unread_messages(ctx, self.agent.id, limit=5)
        recent_msgs = comm_system.get_recent_messages(ctx, self.agent.id, limit=3)
        # Merge, deduplicate by id, prioritize unread.
        seen_ids = {m.id: m for m in unread_messages}
        for m in recent_msgs:
            if m.id not in seen_ids:
                seen_ids[m.id] = m
        agent_messages = list(seen_ids.values())

        # Adaptation signals.
        from app.simulation import adaptation as adaptation_system
        adaptation_signals = adaptation_system.collect_adaptation_signals(ctx, self.agent.id)

        # --- Phase 6 market & strategy context ---
        from app.models.market_segment import MarketSegment
        from app.models.competitor import Competitor
        from app.models.campaign import Campaign
        from app.models.sales_opportunity import SalesOpportunity
        from app.simulation import strategy as strategy_system
        from app.simulation import pricing as pricing_system
        from app.simulation import pmf as pmf_system
        from app.simulation import competitor as competitor_system

        segments = list(db.execute(select(MarketSegment)).scalars().all())
        competitors = list(db.execute(select(Competitor)).scalars().all())
        campaigns = list(
            db.execute(
                select(Campaign).where(Campaign.company_id == company_id)
            ).scalars().all()
        )
        sales_opportunities = list(
            db.execute(
                select(SalesOpportunity).where(SalesOpportunity.company_id == company_id)
            ).scalars().all()
        )

        # Build strategy view.
        target_segment_str = self.company.target_segment
        try:
            from app.enums import SegmentType
            target_segment = SegmentType(target_segment_str)
            segment_obj = next((s for s in segments if s.segment_type == target_segment), None)
        except ValueError:
            segment_obj = segments[0] if segments else None
            target_segment = segment_obj.segment_type if segment_obj else None

        strategy = {
            "target_segment": target_segment_str,
            "price": self.company.price,
            "positioning": self.company.positioning,
            "brand_strength": self.company.brand_strength,
            "sales_effectiveness": self.company.sales_effectiveness,
            "market_share": self.company.market_share_cache,
            "product_market_fit": pmf_system.compute_pmf(ctx, self.company, segment_obj) if segment_obj else 0.0,
            "competitive_pressure": competitor_system.compute_competitive_pressure(ctx, target_segment) if target_segment else 0.0,
        }

        # --- Phase 9 workforce context ---
        from app.models.employee import Employee
        from app.models.job_opening import JobOpening
        from app.models.candidate import Candidate
        from app.enums import EmployeeStatus, JobStatus
        from app.simulation import workforce as workforce_system

        employees = list(
            db.execute(
                select(Employee).where(Employee.company_id == self.company.id)
            )
            .scalars()
            .all()
        )
        job_openings = list(
            db.execute(
                select(JobOpening).where(JobOpening.company_id == self.company.id)
            )
            .scalars()
            .all()
        )
        candidates = list(
            db.execute(
                select(Candidate).where(Candidate.company_id == self.company.id)
            )
            .scalars()
            .all()
        )

        active_employees = [
            e for e in employees
            if e.status in (EmployeeStatus.ACTIVE, EmployeeStatus.ONBOARDING, EmployeeStatus.UNDERPERFORMING)
        ]
        workforce_overview = {
            "headcount": len(employees),
            "active_count": len([e for e in employees if e.status == EmployeeStatus.ACTIVE]),
            "onboarding_count": len([e for e in employees if e.status == EmployeeStatus.ONBOARDING]),
            "underperforming_count": len([e for e in employees if e.status == EmployeeStatus.UNDERPERFORMING]),
            "payroll": round(workforce_system.total_payroll(ctx), 2),
            "total_capacity": round(sum(workforce_system.total_workforce_capacity(ctx).values()), 2),
            "avg_morale": round(sum(e.morale for e in active_employees) / len(active_employees), 2) if active_employees else 0.0,
            "avg_productivity": round(sum(e.productivity for e in active_employees) / len(active_employees), 2) if active_employees else 0.0,
        }
        capacity_by_role = workforce_system.total_workforce_capacity(ctx)

        # --- Phase 10: Financial health metrics ---
        from app.simulation.financial_health import get_financial_metrics
        financial_metrics = get_financial_metrics(self.company)

        return build_context(
            company=self.company,
            agent=self.agent,
            goals=goals,
            projects=projects,
            tasks=tasks,
            milestones=milestones,
            features=features,
            recent_events=recent_events,
            recent_decisions=recent_decisions,
            recent_environmental_events=recent_environmental_events,
            customer_active_count=len(active_customers),
            customer_churned_count=len(churned_customers),
            customer_total_monthly_value=sum(c.monthly_value for c in active_customers),
            plans=plans,
            messages=agent_messages,
            memories=relevant_memories,
            expectations=expectations,
            adaptation_signals=adaptation_signals,
            segments=segments,
            competitors=competitors,
            campaigns=campaigns,
            sales_opportunities=sales_opportunities,
            strategy=strategy,
            workforce_overview=workforce_overview,
            employees=employees,
            job_openings=job_openings,
            candidates=candidates,
            capacity_by_role=capacity_by_role,
            financial_metrics=financial_metrics,
        )

    # --- Lifecycle phases ---

    def observe(self, context: AgentContext) -> dict[str, Any]:
        return {
            "agent_id": self.agent.id,
            "role": self.agent.role.value,
            "phase": "observe",
            "company_status": context.company.status,
            "current_day": context.company.current_day,
            "active_tasks": len(context.tasks),
            "active_goals": len(context.goals),
        }

    def think(self, context: AgentContext) -> str:
        """Produce a reasoning string. Default implementation summarizes state.

        Subclasses may override to inject role-specific reasoning.
        """
        goals_summary = ", ".join(g.title for g in context.goals[:3]) or "no active goals"
        tasks_summary = ", ".join(t.title for t in context.tasks[:3]) or "no active tasks"
        return (
            f"{self.role_name} considers: day {context.company.current_day}, "
            f"cash={context.company.cash}, goals=[{goals_summary}], "
            f"tasks=[{tasks_summary}]."
        )

    def decide(self, context: AgentContext) -> AgentDecision | None:
        """Use the LLM to produce a structured decision from context.

        Returns None if the LLM is unavailable or produces invalid output.
        The simulation treats None as NO_ACTION.
        """
        if self.llm is None:
            return AgentDecision(
                action=ActionType.NO_ACTION,
                reasoning="No LLM configured.",
                confidence=0.0,
            )
        prompt = self._build_decision_prompt(context)
        metadata: dict[str, Any] = {
            "agent_id": self.agent.id,
            "role": self.role_name,
            "day": self.company.current_day,
        }
        try:
            start_time = time.time()
            raw = self.llm.structured_generate(
                prompt,
                schema=AgentDecision,
                role=self.role_name,
                day=self.company.current_day,
                context=context,
            )
            latency_ms = round((time.time() - start_time) * 1000, 2)
            metadata["latency_ms"] = latency_ms
            metadata["success"] = True
        except Exception as exc:
            metadata["success"] = False
            metadata["error_type"] = type(exc).__name__
            metadata["error"] = str(exc)
            logger.warning("LLM structured_generate failed for agent %s: %s", self.agent.id, exc)
            self._llm_events.append(self._event(EventType.LLM_DECISION_FAILED, metadata, self.company.current_day))
            return None

        if not isinstance(raw, dict):
            metadata["success"] = False
            metadata["error_type"] = "NonDictOutput"
            logger.warning("LLM returned non-dict for agent %s: %s", self.agent.id, type(raw))
            self._llm_events.append(self._event(EventType.LLM_DECISION_FAILED, metadata, self.company.current_day))
            return None

        decision = build_decision_from_llm(raw)
        if decision is not None:
            metadata["action"] = decision.action.value
            metadata["confidence"] = decision.confidence
            self._llm_events.append(self._event(EventType.LLM_DECISION_RECEIVED, metadata, self.company.current_day))
        return decision

    def act(self, decision: AgentDecision, db: "Session") -> "ActionResult":
        """Validate and execute a decision against live state."""
        validator = DecisionValidator(db, self.agent, self.company)
        return validator.execute(decision)

    def reflect(self, decision: AgentDecision | None, result: "ActionResult | None") -> Memory | None:
        """Persist a reflection as memory when the action was meaningful."""
        if decision is None or result is None:
            return None
        if decision.action == ActionType.NO_ACTION and result.success:
            return None

        if decision.action == ActionType.NO_ACTION:
            content = f"Decided to take no action. Reasoning: {decision.reasoning}"
            importance = 0.2
        elif result.success:
            content = (
                f"Decision: {decision.action.value}. "
                f"Reasoning: {decision.reasoning}. "
                f"Result: {result.message}."
            )
            importance = 0.6
        else:
            content = (
                f"Attempted {decision.action.value} but it was rejected: {result.message}. "
                f"Original reasoning: {decision.reasoning}."
            )
            importance = 0.7

        memory = Memory(
            agent_id=self.agent.id,
            memory_type="reflection",
            content=content,
            importance=importance,
            simulation_day=self.company.current_day,
            meta={
                "action": decision.action.value,
                "success": result.success,
                "confidence": decision.confidence,
            },
        )
        return memory

    # --- Learning ---

    def learn(
        self,
        decision: AgentDecision,
        result: "ActionResult | None",
        context: AgentContext,
    ) -> Memory | None:
        """Create structured lesson memories from significant outcomes.

        Bounded: only creates memories for notable events (failures, major
        milestones, plan-relevant outcomes). Avoids memory spam.
        """
        if decision is None or result is None:
            return None

        # Only learn from significant events.
        significant = False
        content = None
        importance = 0.6

        # Failed decisions produce lessons.
        if not result.success and decision.action != ActionType.NO_ACTION:
            content = (
                f"Attempted {decision.action.value} but was rejected: {result.message}. "
                f"Original reasoning: {decision.reasoning}."
            )
            importance = 0.8
            significant = True

        # Plan-relevant successful actions produce outcome memories.
        if result.success and decision.action in (
            ActionType.CREATE_TASK,
            ActionType.COMPLETE_TASK,
            ActionType.CREATE_PLAN,
            ActionType.CREATE_PROJECT,
        ):
            content = (
                f"Successfully executed {decision.action.value}: {result.message}. "
                f"Reasoning: {decision.reasoning}."
            )
            importance = 0.6
            significant = True

        # Milestone/feature completions produce lessons.
        if result.success and decision.action in (
            ActionType.CREATE_MILESTONE,
            ActionType.CREATE_FEATURE,
        ):
            content = (
                f"Created {decision.action.value.lower().replace('_', ' ')}: "
                f"{decision.title or result.message}."
            )
            importance = 0.7
            significant = True

        if not significant or content is None:
            return None

        memory = Memory(
            agent_id=self.agent.id,
            memory_type="lesson",
            content=content,
            importance=importance,
            simulation_day=self.company.current_day,
            meta={
                "action": decision.action.value,
                "success": result.success,
                "source": "learn",
            },
        )
        return memory

    # --- prompt building ---

    def _build_decision_prompt(self, context: AgentContext) -> str:
        system_prompt = get_role_prompt(self.role_name)
        # Compact context sections for the prompt.
        sections = self._format_context_sections(context)
        return (
            f"{system_prompt}\n\n"
            f"{sections}\n\n"
            "Based on the above information, what single action do you take now? "
            "Respond with a single JSON object matching the decision schema."
        )

    def _format_context_sections(self, context: AgentContext) -> str:
        """Format AgentContext into compact, role-specific sections."""
        sections: list[str] = []

        # Current state.
        sections.append(
            f"CURRENT DAY: {context.company.current_day}\n"
            f"FINANCIAL:\n"
            f"  cash: ${context.financial.cash:,.0f}\n"
            f"  revenue: ${context.financial.revenue:,.0f}\n"
            f"  expenses: ${context.financial.expenses:,.0f}\n"
            f"  profit: ${context.financial.profit:,.0f}\n"
        )

        # Product.
        sections.append(
            f"PRODUCT:\n"
            f"  readiness: {context.product.readiness:.0%}\n"
            f"  quality: {context.product.quality:.0%}\n"
            f"  technical_debt: {context.product.technical_debt:.0%}\n"
        )

        # Market.
        sections.append(
            f"MARKET:\n"
            f"  target_segment: {context.strategy.target_segment}\n"
            f"  price: ${context.strategy.price:,.0f}\n"
            f"  market_share: {context.strategy.market_share:.1%}\n"
            f"  competitive_pressure: {context.strategy.competitive_pressure:.1%}\n"
            f"  product_market_fit: {context.strategy.product_market_fit:.1%}\n"
        )

        # Customers.
        sections.append(
            f"CUSTOMERS:\n"
            f"  active: {context.customers.active_count}\n"
            f"  churned: {context.customers.churned_count}\n"
            f"  monthly_value: ${context.customers.total_monthly_value:,.0f}\n"
        )

        # Plans and objectives.
        if context.agent_state.current_objective:
            sections.append(
                f"PLAN:\n"
                f"  objective: {context.agent_state.current_objective}\n"
                f"  progress: {context.agent_state.current_plan.progress:.0%}\n"
                f"  step {context.agent_state.current_plan.current_step + 1}/{context.agent_state.current_plan.total_steps}\n"
            )
        else:
            sections.append("PLAN: No active plan.\n")

        # Expectations.
        if context.expectations:
            pending = [e for e in context.expectations if e.status == "PENDING"]
            missed = [e for e in context.expectations if e.status in ("MISSED", "PARTIAL")]
            if pending:
                sections.append(f"EXPECTATIONS (pending):\n")
                for e in pending[:3]:
                    sections.append(f"  - {e.description} (by day {e.target_day})\n")
            if missed:
                sections.append(f"EXPECTATIONS (missed):\n")
                for e in missed[:3]:
                    sections.append(f"  - {e.description}\n")
        else:
            sections.append("EXPECTATIONS: None.\n")

        # Memory (bounded).
        if context.memories:
            sections.append("MEMORY:\n")
            for m in context.memories[:5]:
                sections.append(f"  - [{m.memory_type}] {m.content}\n")
        else:
            sections.append("MEMORY: None.\n")

        # Adaptation signals.
        if context.adaptation_signals.at_risk_expectations or context.adaptation_signals.recently_missed:
            sections.append("ADAPTATION SIGNALS:\n")
            for item in context.adaptation_signals.at_risk_expectations[:3]:
                sections.append(f"  - AT RISK: {item.get('description', 'unknown')}\n")
            for item in context.adaptation_signals.recently_missed[:3]:
                sections.append(f"  - MISSED: {item.get('description', 'unknown')}\n")
        else:
            sections.append("ADAPTATION SIGNALS: None.\n")

        # Messages (unread).
        unread = [m for m in context.messages if m.is_unread]
        if unread:
            sections.append("UNREAD MESSAGES:\n")
            for m in unread[:3]:
                sections.append(f"  - from {m.sender_agent_id}: {m.subject}\n")
        else:
            sections.append("MESSAGES: No unread messages.\n")

        # Competitors (summary).
        if context.competitors:
            sections.append("COMPETITORS:\n")
            for c in context.competitors[:3]:
                sections.append(f"  - {c.name}: share={c.market_share:.0%}, price=${c.price:,.0f}, quality={c.product_quality:.0%}\n")

        # Campaigns.
        active_campaigns = [c for c in context.campaigns if c.status == "ACTIVE"]
        if active_campaigns:
            sections.append("ACTIVE CAMPAIGNS:\n")
            for c in active_campaigns[:3]:
                sections.append(f"  - {c.name}: segment={c.segment}, days_left={c.days_remaining}\n")

        # Sales pipeline.
        open_opps = [o for o in context.sales_opportunities if o.stage in ("LEAD", "QUALIFIED", "PROPOSAL")]
        if open_opps:
            sections.append("SALES PIPELINE:\n")
            for o in open_opps[:3]:
                sections.append(f"  - {o.name}: stage={o.stage}, value=${o.value:,.0f}\n")

        return "".join(sections)

    # --- Cycle orchestration ---

    def run_cycle(self, db: "Session", day: int) -> "CycleResult":
        """Run a full lifecycle cycle and return produced events/memories."""
        from app.agents.cycle_result import CycleResult

        events: list[Event] = []
        self._llm_events = []  # Reset LLM events for this cycle.

        # 1. Observe: build structured context.
        context = self._build_context(db)
        obs = self.observe(context)
        events.append(self._event(EventType.OBSERVE, obs, day))

        # 2. Recall: retrieve relevant memories (deterministic, already in context).
        # 3. Evaluate: assess plans/expectations (deterministic, already in context).
        # 4. Plan: agent considers current objective and plan progress.
        thought = self.think(context)
        events.append(self._event(EventType.THINK, {"thought": thought}, day))

        # 5. Decide: produce a structured decision (one LLM call).
        decision = self.decide(context)
        events.extend(self._llm_events)  # Include LLM observability events.
        if decision is None:
            events.append(
                self._event(
                    EventType.DECIDE,
                    {"decision": "LLM produced no valid decision; defaulting to NO_ACTION."},
                    day,
                )
            )
            decision = AgentDecision(
                action=ActionType.NO_ACTION,
                reasoning="LLM produced no valid decision.",
                confidence=0.0,
            )

        events.append(
            self._event(
                EventType.DECIDE,
                {
                    "action": decision.action.value,
                    "reasoning": decision.reasoning,
                    "confidence": decision.confidence,
                },
                day,
            )
        )

        # 6. Act: validate and execute the decision.
        result = self.act(decision, db)
        events.append(
            self._event(
                EventType.ACT,
                {
                    "action": decision.action.value,
                    "success": result.success,
                    "message": result.message,
                },
                day,
            )
        )
        events.extend(result.events)

        # 7. Reflect: persist meaningful memories.
        memory = self.reflect(decision, result)
        reflection_text = memory.content if memory else "No significant reflection."
        events.append(
            self._event(EventType.REFLECT, {"reflection": reflection_text}, day)
        )

        # 8. Learn: create structured memories/lessons from significant outcomes.
        lesson = self.learn(decision, result, context)
        if lesson is not None:
            events.append(
                self._event(
                    EventType.LESSON_LEARNED,
                    {"lesson": lesson.content},
                    day,
                )
            )
            if memory is not None:
                # Persist lesson alongside reflection memory.
                db.add(lesson)
            else:
                memory = lesson

        self.agent.status = AgentStatus.WORKING
        return CycleResult(events=events, decision=result.decision, memory=memory or lesson)

    def _event(self, event_type: EventType, meta: dict, day: int) -> Event:
        description = (
            str(meta.get("thought") or meta.get("reflection") or meta.get("decision")
                 or meta.get("action") or meta.get("observation") or event_type.value)
        )
        return Event(
            company_id=self.company.id,
            actor_id=self.agent.id,
            event_type=event_type,
            description=description,
            target_type="agent",
            target_id=self.agent.id,
            meta=meta,
            simulation_day=day,
        )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} agent_id={self.agent.id}>"
