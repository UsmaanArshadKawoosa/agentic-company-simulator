"""Economy system: deterministic financial consequences for a company."""

from __future__ import annotations

import logging

from sqlalchemy import select

from app.models.agent import Agent
from app.models.company import Company
from app.models.customer import Customer
from app.models.employee import Employee
from app.enums import CustomerStatus, EmployeeStatus
from app.simulation.domain import SimulationContext

logger = logging.getLogger("agent_company_simulator")


def daily_agent_salary(company: Company, agents: list[Agent]) -> float:
    """Total daily operating cost of all agents."""
    return sum(agent.salary for agent in agents)


def daily_employee_salary(ctx: SimulationContext) -> float:
    """Total daily payroll for active employees."""
    employees = list(
        ctx.db.execute(
            select(Employee).where(
                Employee.company_id == ctx.company.id,
                Employee.status.in_(
                    [
                        EmployeeStatus.ACTIVE,
                        EmployeeStatus.ONBOARDING,
                        EmployeeStatus.UNDERPERFORMING,
                    ]
                ),
            )
        )
        .scalars()
        .all()
    )
    return sum(emp.salary for emp in employees)


def daily_infrastructure_cost(company: Company) -> float:
    return company.infrastructure_cost


def daily_expenses(company: Company, agents: list[Agent], ctx: SimulationContext | None = None) -> float:
    """Total daily operating expenses (salaries + infrastructure + employee payroll)."""
    total = daily_agent_salary(company, agents) + daily_infrastructure_cost(company)
    if ctx is not None:
        total += daily_employee_salary(ctx)
    return total


def daily_revenue(company: Company, customers: list[Customer]) -> float:
    """Daily revenue from active customers.

    Each active customer contributes monthly_value / 30 per day.
    """
    active = [c for c in customers if c.status == CustomerStatus.ACTIVE]
    return sum(c.monthly_value / 30.0 for c in active)


def process_economy(ctx: SimulationContext, agents: list[Agent], customers: list[Customer], extra_expenses: float = 0.0) -> dict:
    """Apply one day of financial consequences.

    Updates company revenue, expenses, and cash. Returns a summary dict
    for event persistence and logging.

    extra_expenses: additional daily costs (e.g., campaign spend).
    """
    revenue = daily_revenue(ctx.company, customers)
    expenses = daily_expenses(ctx.company, agents, ctx) + extra_expenses
    profit = revenue - expenses

    ctx.company.revenue += revenue
    ctx.company.expenses += expenses
    ctx.company.cash += profit

    summary = {
        "day": ctx.day,
        "revenue": round(revenue, 2),
        "expenses": round(expenses, 2),
        "profit": round(profit, 2),
        "cash": round(ctx.company.cash, 2),
        "active_customers": sum(1 for c in customers if c.status == CustomerStatus.ACTIVE),
        "daily_salary": round(daily_agent_salary(ctx.company, agents), 2),
        "daily_infrastructure": round(daily_infrastructure_cost(ctx.company), 2),
        "daily_employee_payroll": round(daily_employee_salary(ctx), 2),
        "extra_expenses": round(extra_expenses, 2),
    }

    logger.info(
        "Economy day %d for company %s: revenue=%.2f expenses=%.2f profit=%.2f cash=%.2f",
        ctx.day,
        ctx.company.id,
        revenue,
        expenses,
        profit,
        ctx.company.cash,
    )
    return summary


def load_agents_and_customers(ctx: SimulationContext) -> tuple[list[Agent], list[Customer]]:
    """Load agents and customers for the current company."""
    agents = list(
        ctx.db.execute(select(Agent).where(Agent.company_id == ctx.company.id)).scalars().all()
    )
    customers = list(
        ctx.db.execute(select(Customer).where(Customer.company_id == ctx.company.id))
        .scalars()
        .all()
    )
    return agents, customers
