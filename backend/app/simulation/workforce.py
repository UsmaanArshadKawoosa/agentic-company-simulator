"""Workforce system: employee lifecycle, capacity, morale, productivity, performance.

Integrates with the simulation engine to provide dynamic workforce management.
"""

from __future__ import annotations

import logging

from sqlalchemy import select

from app.enums import EmployeeStatus, PerformanceRating
from app.models.employee import Employee
from app.models.event import Event
from app.models.job_opening import JobOpening
from app.enums import EventType
from app.simulation.domain import SimulationContext

logger = logging.getLogger("agent_company_simulator")

# --- Role capacity configuration ---

ROLE_CAPACITY: dict[str, float] = {
    "ENGINEER": 5.0,
    "SENIOR_ENGINEER": 8.0,
    "DESIGNER": 4.0,
    "PRODUCT_MANAGER": 3.0,
    "SALES": 2.0,
    "MARKETING": 3.0,
    "CUSTOMER_SUCCESS": 4.0,
    "DATA_ANALYST": 3.0,
    "FINANCE": 2.0,
    "OPERATIONS": 3.0,
}

ROLE_SALARY: dict[str, float] = {
    "ENGINEER": 3000.0,
    "SENIOR_ENGINEER": 4500.0,
    "DESIGNER": 2800.0,
    "PRODUCT_MANAGER": 4000.0,
    "SALES": 2500.0,
    "MARKETING": 3000.0,
    "CUSTOMER_SUCCESS": 2800.0,
    "DATA_ANALYST": 3200.0,
    "FINANCE": 3500.0,
    "OPERATIONS": 3000.0,
}

HIRING_COST_RATE = 0.5  # recruiting cost as fraction of annual salary
ONBOARDING_COST_RATE = 0.1  # onboarding cost as fraction of annual salary
ONBOARDING_DAYS = 5


# --- Employee lifecycle ---


def hire_employee(
    ctx: SimulationContext,
    job_opening: JobOpening,
    candidate_name: str,
    salary: float,
    manager_id: int | None = None,
) -> tuple[Employee | None, list[Event]]:
    """Hire a candidate into a filled job opening."""
    events: list[Event] = []

    if job_opening.status != "OPEN":
        return None, events

    employee = Employee(
        company_id=ctx.company.id,
        name=candidate_name,
        role=job_opening.role,
        status=EmployeeStatus.ONBOARDING,
        salary=salary,
        capacity=ROLE_CAPACITY.get(job_opening.role, 3.0),
        skills=job_opening.required_skills or [],
        experience=2.0,
        performance_score=0.5,
        morale=0.6,
        productivity=0.5,
        onboarding_factor=0.5,
        hired_day=ctx.day,
        manager_id=manager_id,
    )
    ctx.db.add(employee)
    ctx.db.flush()

    # Close the job opening.
    job_opening.status = "FILLED"
    ctx.db.flush()

    # Hiring costs.
    annual_salary = salary * 365
    hiring_cost = annual_salary * HIRING_COST_RATE
    onboarding_cost = annual_salary * ONBOARDING_COST_RATE
    ctx.company.cash -= (hiring_cost + onboarding_cost)

    events.append(
        Event(
            company_id=ctx.company.id,
            actor_id=None,
            event_type=EventType.EMPLOYEE_HIRED,
            description=f"Employee '{employee.name}' hired as {employee.role}.",
            target_type="employee",
            target_id=employee.id,
            meta={
                "employee_id": employee.id,
                "role": employee.role,
                "salary": salary,
                "hiring_cost": round(hiring_cost, 2),
                "onboarding_cost": round(onboarding_cost, 2),
                "day": ctx.day,
            },
            simulation_day=ctx.day,
        )
    )

    logger.info(
        "Hired %s as %s on day %d (cost=%.2f)",
        employee.name,
        employee.role,
        ctx.day,
        hiring_cost + onboarding_cost,
    )
    return employee, events


def terminate_employee(ctx: SimulationContext, employee: Employee, reason: str = "") -> list[Event]:
    """Terminate an employee. Does not delete from database."""
    events: list[Event] = []

    if employee.status in (EmployeeStatus.TERMINATED, EmployeeStatus.RESIGNED):
        return events

    employee.status = EmployeeStatus.TERMINATED
    employee.fired_day = ctx.day
    employee.capacity = 0.0
    employee.productivity = 0.0
    ctx.db.flush()

    events.append(
        Event(
            company_id=ctx.company.id,
            actor_id=None,
            event_type=EventType.EMPLOYEE_TERMINATED,
            description=f"Employee '{employee.name}' ({employee.role}) terminated. {reason}".strip(),
            target_type="employee",
            target_id=employee.id,
            meta={
                "employee_id": employee.id,
                "role": employee.role,
                "reason": reason,
                "day": ctx.day,
            },
            simulation_day=ctx.day,
        )
    )

    logger.info("Terminated employee %s on day %d", employee.name, ctx.day)
    return events


def update_onboarding(ctx: SimulationContext) -> list[Event]:
    """Advance onboarding for employees."""
    employees = list(
        ctx.db.execute(
            select(Employee).where(
                Employee.company_id == ctx.company.id,
                Employee.status == EmployeeStatus.ONBOARDING,
            )
        )
        .scalars()
        .all()
    )
    events: list[Event] = []
    for emp in employees:
        if emp.hired_day is not None and (ctx.day - emp.hired_day) >= ONBOARDING_DAYS:
            emp.status = EmployeeStatus.ACTIVE
            emp.onboarding_factor = 1.0
            emp.productivity = min(1.0, emp.productivity + 0.2)
            ctx.db.flush()
            events.append(
                Event(
                    company_id=ctx.company.id,
                    actor_id=None,
                    event_type=EventType.EMPLOYEE_ONBOARDED,
                    description=f"Employee '{emp.name}' completed onboarding.",
                    target_type="employee",
                    target_id=emp.id,
                    meta={"employee_id": emp.id, "day": ctx.day},
                    simulation_day=ctx.day,
                )
            )
    return events


def update_morale(ctx: SimulationContext) -> list[Event]:
    """Update employee morale based on company health and recent events."""
    employees = list(
        ctx.db.execute(
            select(Employee).where(
                Employee.company_id == ctx.company.id,
                Employee.status == EmployeeStatus.ACTIVE,
            )
        )
        .scalars()
        .all()
    )
    events: list[Event] = []
    cash_ratio = max(0.0, min(1.0, ctx.company.cash / 100000.0))

    for emp in employees:
        delta = 0.0
        # Cash pressure reduces morale.
        if cash_ratio < 0.2:
            delta -= 0.05
        # Workload pressure.
        if emp.workload > 1.5:
            delta -= 0.03
        # Recent success boosts morale.
        if emp.performance_score > 0.7:
            delta += 0.02
        # Clamp and apply.
        emp.morale = max(0.0, min(1.0, emp.morale + delta))
        ctx.db.flush()
    return events


def evaluate_performance(ctx: SimulationContext) -> list[Event]:
    """Evaluate employee performance and update status."""
    employees = list(
        ctx.db.execute(
            select(Employee).where(
                Employee.company_id == ctx.company.id,
                Employee.status == EmployeeStatus.ACTIVE,
            )
        )
        .scalars()
        .all()
    )
    events: list[Event] = []
    for emp in employees:
        effective = emp.productivity * emp.morale * emp.onboarding_factor
        if effective < 0.3 and emp.performance_score < 0.4:
            emp.status = EmployeeStatus.UNDERPERFORMING
            ctx.db.flush()
            events.append(
                Event(
                    company_id=ctx.company.id,
                    actor_id=None,
                    event_type=EventType.EMPLOYEE_AT_RISK,
                    description=f"Employee '{emp.name}' ({emp.role}) is underperforming.",
                    target_type="employee",
                    target_id=emp.id,
                    meta={"employee_id": emp.id, "productivity": round(effective, 2), "day": ctx.day},
                    simulation_day=ctx.day,
                )
            )
    return events


def total_workforce_capacity(ctx: SimulationContext) -> dict[str, float]:
    """Return capacity by role for the company."""
    employees = list(
        ctx.db.execute(
            select(Employee).where(
                Employee.company_id == ctx.company.id,
                Employee.status.in_(
                    [EmployeeStatus.ACTIVE, EmployeeStatus.ONBOARDING, EmployeeStatus.UNDERPERFORMING]
                ),
            )
        )
        .scalars()
        .all()
    )
    capacity: dict[str, float] = {}
    for emp in employees:
        effective = emp.capacity * emp.productivity * emp.morale * emp.onboarding_factor
        capacity[emp.role] = capacity.get(emp.role, 0.0) + max(0.0, effective)
    return capacity


def total_payroll(ctx: SimulationContext) -> float:
    """Daily payroll cost for all active employees."""
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


def update_productivity(ctx: SimulationContext) -> list[Event]:
    """Update employee productivity based on experience and outcomes."""
    employees = list(
        ctx.db.execute(
            select(Employee).where(
                Employee.company_id == ctx.company.id,
                Employee.status == EmployeeStatus.ACTIVE,
            )
        )
        .scalars()
        .all()
    )
    events: list[Event] = []
    for emp in employees:
        # Experience slowly increases productivity (bounded).
        if emp.experience < 10.0:
            emp.experience += 0.01
        exp_bonus = min(0.3, emp.experience * 0.01)
        target = min(1.0, 0.5 + exp_bonus)
        emp.productivity = max(0.1, min(1.0, emp.productivity + (target - emp.productivity) * 0.1))
        ctx.db.flush()
    return events
