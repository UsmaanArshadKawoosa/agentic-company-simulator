from app.enums import AgentRole, AgentStatus, CompanyStatus, EventType
from app.models.agent import Agent
from app.models.company import Company
from app.models.decision import Decision
from app.models.event import Event


def test_company_agent_relationship(db):
    company = Company(name="RelCo", status=CompanyStatus.CREATED)
    db.add(company)
    db.flush()

    ceo = Agent(company_id=company.id, name="CEO", role=AgentRole.CEO)
    db.add(ceo)
    db.flush()

    cto = Agent(company_id=company.id, name="CTO", role=AgentRole.CTO, manager_id=ceo.id)
    db.add(cto)
    db.flush()

    eng = Agent(company_id=company.id, name="Eng", role=AgentRole.ENGINEER, manager_id=cto.id)
    cmo = Agent(company_id=company.id, name="CMO", role=AgentRole.CMO, manager_id=ceo.id)
    db.add_all([eng, cmo])
    db.commit()

    db.refresh(company)
    assert len(company.agents) == 4
    assert ceo.manager is None
    assert cto.manager is ceo
    assert eng.manager is cto
    assert set(s.role for s in ceo.subordinates) == {AgentRole.CTO, AgentRole.CMO}


def test_json_fields_persist(db):
    company = Company(name="JsonRel")
    db.add(company)
    db.flush()
    agent = Agent(
        company_id=company.id,
        name="A",
        role=AgentRole.ENGINEER,
        personality={"creativity": 0.6},
        skills=["coding", "testing"],
        status=AgentStatus.IDLE,
    )
    db.add(agent)
    db.commit()

    reloaded = db.get(Agent, agent.id)
    assert reloaded.personality == {"creativity": 0.6}
    assert reloaded.skills == ["coding", "testing"]


def test_event_decision_relationships(db):
    company = Company(name="EvtCo")
    db.add(company)
    db.flush()
    agent = Agent(company_id=company.id, name="A", role=AgentRole.CEO)
    db.add(agent)
    db.flush()

    event = Event(
        company_id=company.id,
        actor_id=agent.id,
        event_type=EventType.TICK,
        description="day started",
        meta={"k": "v"},
        simulation_day=1,
    )
    decision = Decision(
        company_id=company.id,
        agent_id=agent.id,
        action="set_goal",
        reasoning="strategic",
        context={"priority": "high"},
        simulation_day=1,
    )
    db.add_all([event, decision])
    db.commit()

    db.refresh(company)
    assert len(company.events) == 1
    assert len(company.decisions) == 1
    assert event.actor is agent
    assert decision.agent is agent
    assert event.meta == {"k": "v"}
    assert decision.context == {"priority": "high"}


def test_cascade_delete_company(db):
    company = Company(name="CascadeCo")
    db.add(company)
    db.flush()
    db.add(Agent(company_id=company.id, name="A", role=AgentRole.ENGINEER))
    db.commit()

    db.delete(company)
    db.commit()
    assert db.query(Agent).filter(Agent.company_id == company.id).count() == 0
