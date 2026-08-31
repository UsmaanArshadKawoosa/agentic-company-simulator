"""Task execution system: dependencies, blocking, workforce capacity, and work allocation.

This system is responsible for the deterministic execution of work:

    LLM creates/assigns tasks
            ↓
    Dependencies checked → blocked/unblocked state
            ↓
    Workforce capacity (agents + employees) consumed on eligible tasks
            ↓
    remaining_effort decreases, progress increases
            ↓
    Tasks complete when remaining_effort reaches zero
"""

from __future__ import annotations

import logging

from sqlalchemy import select

from app.enums import EmployeeStatus, TaskStatus, TaskType
from app.models.agent import Agent
from app.models.employee import Employee
from app.models.task import Task
from app.models.task_dependency import TaskDependency
from app.simulation.domain import SimulationContext

logger = logging.getLogger("agent_company_simulator")

# Role categories for task assignment.
ENGINEERING_ROLES = {"ENGINEER", "SENIOR_ENGINEER"}
MARKETING_ROLES = {"MARKETING", "CMO"}
SALES_ROLES = {"SALES"}
DESIGN_ROLES = {"DESIGNER"}
OPERATIONS_ROLES = {"OPERATIONS", "FINANCE", "DATA_ANALYST", "PRODUCT_MANAGER", "CUSTOMER_SUCCESS"}


def load_dependencies(ctx: SimulationContext, tasks: list[Task]) -> list[TaskDependency]:
    """Load all task dependencies for the company."""
    if not tasks:
        return []
    return list(
        ctx.db.execute(
            select(TaskDependency).where(TaskDependency.task_id.in_([t.id for t in tasks]))
        )
        .scalars()
        .all()
    )


def dependency_map(deps: list[TaskDependency]) -> dict[int, list[int]]:
    """Map task_id -> list of depends_on_ids."""
    result: dict[int, list[int]] = {}
    for dep in deps:
        result.setdefault(dep.task_id, []).append(dep.depends_on_id)
    return result


def has_cycle(tasks: list[Task], deps: list[TaskDependency]) -> bool:
    """Detect cycles in the dependency graph using DFS."""
    adj: dict[int, list[int]] = {}
    for dep in deps:
        adj.setdefault(dep.task_id, []).append(dep.depends_on_id)
    task_ids = {t.id for t in tasks}
    for dep in deps:
        task_ids.add(dep.depends_on_id)

    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[int, int] = {tid: WHITE for tid in task_ids}

    def dfs(node: int) -> bool:
        color[node] = GRAY
        for neighbor in adj.get(node, []):
            if color.get(neighbor, WHITE) == GRAY:
                return True
            if color.get(neighbor, WHITE) == WHITE and dfs(neighbor):
                return True
        color[node] = BLACK
        return False

    for tid in task_ids:
        if color.get(tid, WHITE) == WHITE:
            if dfs(tid):
                return True
    return False


def validate_dependency(
    ctx: SimulationContext, task_id: int, depends_on_id: int, tasks: list[Task]
) -> str | None:
    """Validate a proposed dependency. Returns error message or None if valid."""
    if task_id == depends_on_id:
        return "Task cannot depend on itself."
    task_map = {t.id: t for t in tasks}
    if task_id not in task_map:
        return "Task does not exist."
    if depends_on_id not in task_map:
        return "Dependency target does not exist."
    if task_map[task_id].company_id != task_map[depends_on_id].company_id:
        return "Cross-company dependency is not allowed."
    return None


# --- Blocking ---


def is_blocked(task: Task, dep_map: dict[int, list[int]], task_map: dict[int, Task]) -> bool:
    """A task is blocked if any dependency is not completed."""
    for dep_id in dep_map.get(task.id, []):
        dep_task = task_map.get(dep_id)
        if dep_task is None or dep_task.status != TaskStatus.COMPLETED:
            return True
    return False


def update_blocking_state(ctx: SimulationContext) -> list:
    """Update task blocked status based on dependency satisfaction."""
    tasks = list(
        ctx.db.execute(select(Task).where(Task.company_id == ctx.company.id)).scalars().all()
    )
    deps = load_dependencies(ctx, tasks)
    dep_map = dependency_map(deps)
    task_map = {t.id: t for t in tasks}
    events = []
    for task in tasks:
        if task.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED):
            continue
        blocked = is_blocked(task, dep_map, task_map)
        if blocked and task.status != TaskStatus.BLOCKED:
            task.status = TaskStatus.BLOCKED
            from app.models.event import Event
            events.append(
                Event(
                    company_id=ctx.company.id,
                    event_type="TASK_BLOCKED",
                    description=f"Task '{task.title}' is blocked by incomplete dependencies.",
                    target_type="task",
                    target_id=task.id,
                    meta={"day": ctx.day},
                    simulation_day=ctx.day,
                )
            )
        elif not blocked and task.status == TaskStatus.BLOCKED:
            task.status = TaskStatus.TODO
            from app.models.event import Event
            events.append(
                Event(
                    company_id=ctx.company.id,
                    event_type="TASK_UNBLOCKED",
                    description=f"Task '{task.title}' is now unblocked.",
                    target_type="task",
                    target_id=task.id,
                    meta={"day": ctx.day},
                    simulation_day=ctx.day,
                )
            )
    return events


# --- Work allocation ---


def eligible_tasks(tasks: list[Task], dep_map: dict[int, list[int]], task_map: dict[int, Task]) -> list[Task]:
    """Return tasks that are eligible for work."""
    eligible = []
    for task in tasks:
        if task.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED):
            continue
        if task.assigned_to is None and task.assigned_employee_id is None:
            continue
        if is_blocked(task, dep_map, task_map):
            continue
        eligible.append(task)
    return eligible


def sort_tasks_for_work(tasks: list[Task]) -> list[Task]:
    """Deterministic task ordering: higher priority first, then earlier created."""
    return sorted(tasks, key=lambda t: (-t.priority, t.id))


def _worker_capacity(worker: Agent | Employee, task_type: TaskType) -> float:
    """Calculate effective capacity for a worker given a task type."""
    if isinstance(worker, Employee):
        base = worker.capacity
        factor = worker.productivity * worker.morale * worker.onboarding_factor
        role = worker.role.upper()
    else:
        base = worker.capacity
        factor = 1.0
        role = worker.role.value if hasattr(worker.role, "value") else str(worker.role)

    # Role-task type affinity.
    if task_type == TaskType.ENGINEERING and role in ENGINEERING_ROLES:
        pass
    elif task_type == TaskType.MARKETING and role in MARKETING_ROLES:
        pass
    elif task_type == TaskType.RESEARCH and role in ENGINEERING_ROLES:
        pass
    elif task_type == TaskType.DESIGN and role in DESIGN_ROLES:
        pass
    elif task_type == TaskType.OPERATIONS and role in OPERATIONS_ROLES:
        pass
    elif task_type == TaskType.TESTING and role in ENGINEERING_ROLES:
        pass
    else:
        # Mismatch: reduce efficiency.
        factor *= 0.5

    return max(0.0, base * factor)


def execute_work(ctx: SimulationContext) -> list:
    """Execute one day of work across all workforce (agents + employees).

    Workers consume capacity on eligible tasks. Returns events generated.
    """
    from app.models.event import Event

    tasks = list(
        ctx.db.execute(select(Task).where(Task.company_id == ctx.company.id)).scalars().all()
    )
    deps = load_dependencies(ctx, tasks)
    dep_map = dependency_map(deps)
    task_map = {t.id: t for t in tasks}
    agents = list(
        ctx.db.execute(select(Agent).where(Agent.company_id == ctx.company.id)).scalars().all()
    )
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
    events = []

    # Process agents (AI agents like Engineer).
    for agent in agents:
        role_str = agent.role.value if hasattr(agent.role, "value") else str(agent.role)
        if role_str not in ENGINEERING_ROLES:
            continue
        capacity = agent.capacity
        my_tasks = [t for t in tasks if t.assigned_to == agent.id]
        my_eligible = [
            t for t in my_tasks
            if t.status not in (TaskStatus.COMPLETED, TaskStatus.CANCELLED)
            and not is_blocked(t, dep_map, task_map)
        ]
        my_eligible = sort_tasks_for_work(my_eligible)

        for task in my_eligible:
            if capacity <= 0:
                break
            if task.remaining_effort <= 0:
                continue

            if task.status == TaskStatus.TODO:
                task.status = TaskStatus.IN_PROGRESS
                events.append(
                    Event(
                        company_id=ctx.company.id,
                        actor_id=agent.id,
                        event_type="TASK_STARTED",
                        description=f"Task '{task.title}' started by {agent.name}.",
                        target_type="task",
                        target_id=task.id,
                        meta={"day": ctx.day},
                        simulation_day=ctx.day,
                    )
                )

            consumed = min(capacity, task.remaining_effort)
            task.remaining_effort = max(0.0, task.remaining_effort - consumed)
            capacity -= consumed

            if task.effort > 0:
                task.progress = max(task.progress, (1.0 - task.remaining_effort / task.effort))
            task.progress = max(0.0, min(1.0, task.progress))

            if task.remaining_effort <= 0:
                task.status = TaskStatus.COMPLETED
                task.progress = 1.0
                events.append(
                    Event(
                        company_id=ctx.company.id,
                        actor_id=agent.id,
                        event_type="TASK_COMPLETED",
                        description=f"Task '{task.title}' completed by {agent.name}.",
                        target_type="task",
                        target_id=task.id,
                        meta={"day": ctx.day},
                        simulation_day=ctx.day,
                    )
                )

    # Process employees.
    for emp in employees:
        capacity = _worker_capacity(emp, TaskType.ENGINEERING)
        my_tasks = [t for t in tasks if t.assigned_employee_id == emp.id]
        my_eligible = [
            t for t in my_tasks
            if t.status not in (TaskStatus.COMPLETED, TaskStatus.CANCELLED)
            and not is_blocked(t, dep_map, task_map)
        ]
        my_eligible = sort_tasks_for_work(my_eligible)

        for task in my_eligible:
            if capacity <= 0:
                break
            if task.remaining_effort <= 0:
                continue

            if task.status == TaskStatus.TODO:
                task.status = TaskStatus.IN_PROGRESS
                events.append(
                    Event(
                        company_id=ctx.company.id,
                        actor_id=None,
                        event_type="TASK_STARTED",
                        description=f"Task '{task.title}' started by {emp.name}.",
                        target_type="task",
                        target_id=task.id,
                        meta={"day": ctx.day, "employee_id": emp.id},
                        simulation_day=ctx.day,
                    )
                )

            consumed = min(capacity, task.remaining_effort)
            task.remaining_effort = max(0.0, task.remaining_effort - consumed)
            capacity -= consumed

            if task.effort > 0:
                task.progress = max(task.progress, (1.0 - task.remaining_effort / task.effort))
            task.progress = max(0.0, min(1.0, task.progress))

            if task.remaining_effort <= 0:
                task.status = TaskStatus.COMPLETED
                task.progress = 1.0
                events.append(
                    Event(
                        company_id=ctx.company.id,
                        actor_id=None,
                        event_type="TASK_COMPLETED",
                        description=f"Task '{task.title}' completed by {emp.name}.",
                        target_type="task",
                        target_id=task.id,
                        meta={"day": ctx.day, "employee_id": emp.id},
                        simulation_day=ctx.day,
                    )
                )

    return events
