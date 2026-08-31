from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents import instantiate_agent
from app.agents.cycle_result import CycleResult
from app.enums import CompanyStatus, EventType
from app.models.agent import Agent
from app.models.company import Company
from app.models.customer import Customer as CustomerModel
from app.models.decision import Decision
from app.models.event import Event
from app.models.goal import Goal
from app.models.memory import Memory
from app.models.plan import Plan
from app.models.task import Task
from app.services.broadcaster import SimulationBroadcaster
from app.services.llm import LLMService, MockLLMService, NoOpLLMService, RealLLMService
from app.simulation import communication as communication_system
from app.simulation import competitor as competitor_system
from app.simulation import customers as customer_system
from app.simulation import decision_quality as decision_quality_system
from app.simulation import economy as economy_system
from app.simulation import execution as execution_system
from app.simulation import expectation as expectation_system
from app.simulation import market as market_system
from app.simulation import marketing as marketing_system
from app.simulation import milestone as milestone_system
from app.simulation import outcomes as outcome_system
from app.simulation import plan as plan_system
from app.simulation import product as product_system
from app.simulation import progress as progress_system
from app.simulation import sales as sales_system
from app.simulation import segment as segment_system
from app.simulation import strategy as strategy_system
from app.simulation import workforce as workforce_system
from app.simulation import candidates as candidate_system
from app.simulation import financial_health as financial_health_system
from app.simulation import fundraising as fundraising_system
from app.simulation import capital as capital_system
from app.simulation import objective as objective_system
from app.simulation import resource as resource_system
from app.simulation import priority as priority_system
from app.simulation import risk as risk_system
from app.simulation import incident as incident_system
from app.simulation import attention as attention_system
from app.simulation.domain import SimulationContext, make_rng
from app.simulation.events import EventEmitter
from app.simulation.state import SimulationState

# Deterministic execution order: CEO, CTO, CMO, ENGINEER.
ROLE_ORDER = {"CEO": 0, "CTO": 1, "CMO": 2, "ENGINEER": 3}


class SimulationEngine:
    """Deterministic single-company simulation engine.

    A tick advances time, evolves the world (market, economy, customers,
    work execution, progress, outcomes), then runs each agent through a full
    observe/think/decide/act/reflect cycle in deterministic role order.

    Tick order:
        1. advance day
        2. update market
        3. generate environmental events
        4. update task dependency/blocking state
        5. execute available work (engineer capacity)
        6. update task progress
        7. update milestones
        8. update projects
        9. update product features
        10. calculate product readiness + quality
        11. customer acquisition/churn
        12. revenue, expenses, cash
        13. agents observe updated state and act
        14. evaluate goals
        15. evaluate company success/failure

    Tasks created during step 13 (agent decisions) are NOT available for work
    execution until the following day (step 5 of the next tick). This prevents
    unrealistic same-tick cascading.
    """

    def __init__(self, llm: LLMService | None = None) -> None:
        self.llm = llm or _build_llm_from_config()

    # --- internals ---

    def _get_company(self, db: Session, company_id: int) -> Company:
        company = db.get(Company, company_id)
        if company is None:
            raise ValueError(f"Company {company_id} not found")
        return company

    def _get_agents_ordered(self, db: Session, company_id: int) -> list[Agent]:
        agents = list(
            db.execute(select(Agent).where(Agent.company_id == company_id))
            .scalars()
            .all()
        )
        agents.sort(key=lambda a: ROLE_ORDER.get(a.role.value, 99))
        return agents

    def _ctx(self, db: Session, company: Company, day: int) -> SimulationContext:
        return SimulationContext(
            db=db,
            company=company,
            day=day,
            rng=make_rng(company.seed, day),
        )

    def _broadcast_event(self, company_id: int, day: int, event_type: str, payload: dict, agent_id: int | None = None, agent_role: str | None = None) -> None:
        """Broadcast an event to WebSocket subscribers (non-blocking, never raises)."""
        try:
            event = SimulationBroadcaster.create_event(
                event_type=event_type,
                company_id=company_id,
                day=day,
                payload=payload,
                agent_id=agent_id,
                agent_role=agent_role,
            )
            from app.main import _main_loop
            if _main_loop is not None and _main_loop.is_running():
                import asyncio
                asyncio.run_coroutine_threadsafe(
                    SimulationBroadcaster.broadcast(company_id, event),
                    _main_loop,
                )
        except Exception:
            pass  # Never let broadcast failures affect simulation.

    # --- lifecycle ---

    def start(self, db: Session, company_id: int) -> SimulationState:
        company = self._get_company(db, company_id)
        company.status = CompanyStatus.RUNNING
        emitter = EventEmitter(company.id, company.current_day)
        db.add(
            emitter.emit(
                EventType.SIMULATION_STARTED,
                f"Simulation started for company '{company.name}'.",
            )
        )
        db.commit()
        db.refresh(company)
        self._broadcast_event(
            company.id, company.current_day, "simulation.started",
            {"company_name": company.name, "status": "RUNNING"},
        )
        return SimulationState.from_company(db, company)

    def pause(self, db: Session, company_id: int) -> SimulationState:
        company = self._get_company(db, company_id)
        company.status = CompanyStatus.PAUSED
        emitter = EventEmitter(company.id, company.current_day)
        db.add(
            emitter.emit(
                EventType.SIMULATION_PAUSED,
                f"Simulation paused for company '{company.name}'.",
            )
        )
        db.commit()
        db.refresh(company)
        self._broadcast_event(
            company.id, company.current_day, "simulation.paused",
            {"status": "PAUSED"},
        )
        return SimulationState.from_company(db, company)

    def tick(self, db: Session, company_id: int) -> SimulationState:
        company = self._get_company(db, company_id)
        if company.status != CompanyStatus.RUNNING:
            raise ValueError(
                f"Cannot tick: company {company_id} is not running "
                f"(status={company.status.value}). Call start() first."
            )

        company.current_day += 1
        day = company.current_day
        emitter = EventEmitter(company.id, day)
        all_events: list[Event] = [
            emitter.emit(EventType.TICK, f"Simulation day {day} started.")
        ]
        all_decisions: list[Decision] = []
        all_memories: list[Memory] = []

        ctx = self._ctx(db, company, day)

        # --- Phase 6: Ensure market segments and competitors exist ---
        segment_system.ensure_segments(db)
        competitor_system.ensure_competitors(db)

        # 2. Evolve market conditions.
        market_update = market_system.evolve_market(ctx)
        all_events.append(
            emitter.emit(
                EventType.MARKET_UPDATE,
                f"Market evolved: demand={market_update['new']['demand']:.3f}, "
                f"competition={market_update['new']['competition']:.3f}, "
                f"sentiment={market_update['new']['sentiment']:.3f}.",
                metadata={"market": market_update},
            )
        )

        # 3. Evolve market segments.
        segment_system.evolve_segments(db, ctx.rng)

        # 4. Evolve competitors.
        all_events.extend(competitor_system.evolve_competitors(ctx))

        # 5. Generate environmental events (extended with Phase 6 events).
        all_events.extend(market_system.generate_environmental_events(ctx))

        # 6. Update task dependency/blocking state.
        all_events.extend(execution_system.update_blocking_state(ctx))

        # 6b. Phase 11: Update priorities and detect resource constraints.
        company_tasks = list(
            db.execute(select(Task).where(Task.company_id == company.id)).scalars().all()
        )
        prioritized_tasks = priority_system.get_prioritized_tasks(ctx)
        resource_utilization = resource_system.get_resource_utilization(ctx)
        for rt, util in resource_utilization.items():
            if util.get("total_allocated", 0) > util.get("available", 0) * 0.8:
                all_events.append(
                    emitter.emit(
                        EventType.RESOURCE_CONSTRAINED,
                        f"Resource {rt} is heavily utilized.",
                        metadata={"resource_type": rt, "utilization": util},
                    )
                )

        # 6a. Phase 9: Update workforce onboarding, morale, productivity, performance.
        all_events.extend(workforce_system.update_onboarding(ctx))
        all_events.extend(workforce_system.update_morale(ctx))
        all_events.extend(workforce_system.update_productivity(ctx))
        all_events.extend(workforce_system.evaluate_performance(ctx))

        # 7. Execute available work (engineer capacity + employee capacity).
        all_events.extend(execution_system.execute_work(ctx))

        # 8-9. Update milestones and projects.
        all_events.extend(milestone_system.update_milestones(ctx))
        progress_system.update_projects_and_readiness(ctx)
        all_events.append(
            emitter.emit(
                EventType.PRODUCT_PROGRESS,
                f"Product readiness is now {company.product_readiness:.1f}%.",
                metadata={"readiness": round(company.product_readiness, 4)},
            )
        )

        # 10-11. Update product features, readiness, quality.
        all_events.extend(product_system.update_features(ctx))
        all_events.extend(product_system.update_product(ctx))

        # 12. Phase 6: Update campaigns (spend, completion).
        all_events.extend(marketing_system.update_campaigns(ctx))

        # 13. Phase 6: Advance sales pipeline.
        all_events.extend(sales_system.advance_pipeline(ctx))

        # 14. Phase 6: Update market share cache.
        strategy_system.update_market_share_cache(ctx)

        # 15. Customer acquisition/churn.
        agents = self._get_agents_ordered(db, company_id)
        existing_customers = list(
            db.execute(select(CustomerModel).where(CustomerModel.company_id == company.id))
            .scalars()
            .all()
        )
        company_tasks = list(
            db.execute(select(Task).where(Task.company_id == company.id)).scalars().all()
        )
        mkt_progress = progress_system.marketing_progress(company_tasks)
        new_customers = customer_system.acquire_customers(
            ctx, existing_customers, mkt_progress, company.product_readiness
        )
        for nc in new_customers:
            db.add(nc)
            db.flush()
            all_events.append(
                emitter.emit(
                    EventType.CUSTOMER_ACQUIRED,
                    f"New customer '{nc.name}' acquired (monthly value ${nc.monthly_value:.2f}).",
                    target_type="customer",
                    target_id=nc.id,
                    metadata={"monthly_value": nc.monthly_value, "day": day},
                )
            )
        churn_events = customer_system.process_churn(ctx, existing_customers, company.product_readiness)
        all_events.extend(churn_events)

        # 16. Economy: revenue, expenses, cash (includes campaign spend).
        all_customers = list(
            db.execute(select(CustomerModel).where(CustomerModel.company_id == company.id))
            .scalars()
            .all()
        )
        campaign_spend = marketing_system.total_campaign_spend(ctx)
        financial = economy_system.process_economy(ctx, agents, all_customers, extra_expenses=campaign_spend)
        all_events.append(
            emitter.emit(
                EventType.FINANCIAL_SUMMARY,
                f"Day {day}: revenue=${financial['revenue']:.2f}, "
                f"expenses=${financial['expenses']:.2f}, "
                f"profit=${financial['profit']:.2f}, "
                f"cash=${financial['cash']:.2f}.",
                metadata={"financial": financial},
            )
        )

        # 16a. Phase 10: Calculate financial health metrics.
        financial_metrics = financial_health_system.get_financial_metrics(company)
        all_events.append(
            emitter.emit(
                EventType.FINANCIAL_SUMMARY,
                f"Financial health: {financial_metrics['financial_health']} "
                f"(score={financial_metrics['financial_health_score']:.2f}, "
                f"runway={financial_metrics['runway_days']} days, "
                f"burn=${financial_metrics['daily_burn']:.2f}/day).",
                metadata={"financial_metrics": financial_metrics},
            )
        )

        # 16b. Phase 10: Update fundraising pipeline.
        all_events.extend(fundraising_system.update_pipeline(ctx))

        # 17. Phase 11: Detect risks.
        detected_risks = risk_system.detect_risks(ctx)
        all_events.extend(
            [
                emitter.emit(
                    EventType.RISK_DETECTED,
                    f"Risk detected: {r.risk_type} (severity={r.severity.value}).",
                    target_type="risk",
                    target_id=r.id,
                    metadata={"risk_type": r.risk_type, "severity": r.severity.value, "day": day},
                )
                for r in detected_risks
            ]
        )

        # 17a. Phase 11: Detect incidents from critical risks.
        active_risks = risk_system.get_active_risks(ctx)
        detected_incidents = incident_system.detect_incidents_from_risks(ctx, active_risks)
        all_events.extend(
            [
                emitter.emit(
                    EventType.INCIDENT_CREATED,
                    f"Incident created: {i.incident_type.value} (severity={i.severity.value}).",
                    target_type="incident",
                    target_id=i.id,
                    metadata={"incident_type": i.incident_type.value, "severity": i.severity.value, "day": day},
                )
                for i in detected_incidents
            ]
        )

        # 18. Phase 5: evaluate expectations from previous decisions.
        all_events.extend(expectation_system.evaluate_expectations(ctx))

        # 19. Phase 5: advance plans deterministically based on step completion.
        all_events.extend(plan_system.update_plans(ctx))

        # 19a. Phase 11: Update objectives progress based on plan completion.
        active_plans = list(
            db.execute(
                select(Plan).where(Plan.company_id == company.id, Plan.status == "ACTIVE")
            ).scalars().all()
        )
        for plan in active_plans:
            if plan.goal_id:
                goal = db.get(Goal, plan.goal_id)
                if goal:
                    goal.progress = min(100.0, goal.progress + plan.progress * 0.1)
                    db.flush()

        # 19b. Phase 11: Update management attention metrics.
        attention_metrics = attention_system.compute_management_attention(ctx)
        all_events.append(
            emitter.emit(
                EventType.PRIORITY_CHANGED,
                f"Management attention: {attention_metrics['active_objectives']} objectives, "
                f"{attention_metrics['active_risks']} risks, {attention_metrics['active_incidents']} incidents. "
                f"Overloaded: {attention_metrics['overloaded']}",
                metadata=attention_metrics,
            )
        )

        # 20. Phase 5: evaluate decision quality for resolved expectations.
        all_events.extend(decision_quality_system.evaluate_pending_decisions(ctx))

        # 20. Agents observe updated state and act.
        for agent in agents:
            wrapper = instantiate_agent(agent, company, self.llm)
            try:
                result: CycleResult = wrapper.run_cycle(db, day)
            except Exception as exc:  # one agent failure must not kill the tick
                all_events.append(
                    Event(
                        company_id=company.id,
                        actor_id=agent.id,
                        event_type=EventType.DECIDE,
                        description=f"Agent {agent.role.value} cycle failed: {exc}",
                        target_type="agent",
                        target_id=agent.id,
                        meta={"error": str(exc)},
                        simulation_day=day,
                    )
                )
                continue
            all_events.extend(result.events)
            if result.decision is not None:
                all_decisions.append(result.decision)
            if result.memory is not None:
                all_memories.append(result.memory)
            # Mark agent's unread messages as read after they act.
            all_events.extend(
                communication_system.mark_messages_read(ctx, agent.id)
            )

        # 21. Evaluate goals.
        active_customer_count = sum(1 for c in all_customers if c.status.value == "ACTIVE")
        goal_events = progress_system.update_goal_progress(ctx, company.product_readiness, active_customer_count)
        all_events.extend(goal_events)

        # 22. Evaluate company success/failure.
        lifecycle_events = outcome_system.evaluate_company(ctx)
        all_events.extend(lifecycle_events)

        db.add_all(all_events)
        db.add_all(all_decisions)
        db.add_all(all_memories)
        db.commit()
        db.refresh(company)

        # --- Broadcast tick completion to WebSocket subscribers ---
        self._broadcast_event(
            company.id, day, "simulation.tick",
            {
                "day": day,
                "status": company.status.value,
                "cash": round(company.cash, 2),
                "revenue": round(company.revenue, 2),
                "expenses": round(company.expenses, 2),
                "product_readiness": round(company.product_readiness, 4),
                "customer_count": active_customer_count,
                "market_share": round(company.market_share_cache, 4),
            },
        )

        # Broadcast agent decisions.
        for agent in agents:
            agent_events = [e for e in all_events if e.actor_id == agent.id and e.event_type == EventType.DECIDE]
            for ae in agent_events:
                self._broadcast_event(
                    company.id, day, "agent.decision",
                    {
                        "agent_id": agent.id,
                        "agent_role": agent.role.value,
                        "action": ae.meta.get("action") if ae.meta else None,
                        "reasoning": ae.meta.get("reasoning") if ae.meta else None,
                        "confidence": ae.meta.get("confidence") if ae.meta else None,
                    },
                    agent_id=agent.id,
                    agent_role=agent.role.value,
                )

        # Broadcast Phase 11 operational events.
        for event in all_events:
            if event.event_type == EventType.RISK_DETECTED:
                self._broadcast_event(
                    company.id, day, "risk.detected",
                    {
                        "risk_id": event.target_id,
                        "risk_type": event.meta.get("risk_type") if event.meta else None,
                        "severity": event.meta.get("severity") if event.meta else None,
                        "day": day,
                    },
                )
            elif event.event_type == EventType.INCIDENT_CREATED:
                self._broadcast_event(
                    company.id, day, "incident.created",
                    {
                        "incident_id": event.target_id,
                        "incident_type": event.meta.get("incident_type") if event.meta else None,
                        "severity": event.meta.get("severity") if event.meta else None,
                        "day": day,
                    },
                )
            elif event.event_type == EventType.OBJECTIVE_CREATED:
                self._broadcast_event(
                    company.id, day, "objective.created",
                    {
                        "objective_id": event.target_id,
                        "description": event.description,
                        "day": day,
                    },
                )
            elif event.event_type == EventType.RESOURCE_ALLOCATED:
                self._broadcast_event(
                    company.id, day, "resource.allocated",
                    {
                        "resource_type": event.meta.get("resource_type") if event.meta else None,
                        "amount": event.meta.get("amount") if event.meta else None,
                        "day": day,
                    },
                )
            elif event.event_type == EventType.PRIORITY_CHANGED:
                self._broadcast_event(
                    company.id, day, "priority.changed",
                    {
                        "description": event.description,
                        "attention": event.meta,
                        "day": day,
                    },
                )

        return SimulationState.from_company(db, company)

    def get_state(self, db: Session, company_id: int) -> SimulationState:
        company = self._get_company(db, company_id)
        return SimulationState.from_company(db, company)


def _build_llm_from_config() -> LLMService:
    """Construct the appropriate LLM service from environment configuration."""
    from app.config import settings

    provider = settings.LLM_PROVIDER.lower()
    if provider == "noop":
        return NoOpLLMService()
    if provider == "mock":
        return MockLLMService()
    if provider in ("anthropic", "openai"):
        return RealLLMService(
            provider=provider,
            model=settings.LLM_MODEL or None,
            api_key=settings.LLM_API_KEY or None,
            max_tokens=settings.LLM_MAX_TOKENS,
        )
    return NoOpLLMService()
