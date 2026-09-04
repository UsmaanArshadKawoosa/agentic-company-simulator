# Engineering System

## Engineering Capacity

Capacity is the finite resource that drives product development.

### Capacity Calculation
```text
total_capacity = sum(engineer.capacity for engineer in engineers)
  - time spent on bug fixes
  - time spent on maintenance (tech debt paydown)
  - time lost to meetings/overhead (10%)
```

Each engineer has `capacity` (default: 1.0 per step, reduced by morale/quality factors).

## Task Management

### Task Types
- **Feature implementation**: core product work
- **Bug fix**: address defects
- **Tech debt**: refactoring, cleanup
- **Infrastructure**: setup, scaling, security
- **Research**: spike, prototyping

### Task Lifecycle
```text
todo → in_progress → blocked | completed | cancelled
```

- Tasks are assigned by the CTO.
- Engineers pull from their assigned queue.
- Blocked tasks require escalation.
- Overdue tasks create pressure.

### Task Complexity
| Complexity | Capacity required | Steps to complete (1 engineer) |
|------------|-------------------|-------------------------------|
| Small | 0.5 | 1 |
| Medium | 1.0 | 1 |
| Large | 2.0 | 2 |
| Epic | 4.0+ | 3+ |

## Engineering Work Model

### Per Step
1. CTO reviews open tasks and capacity.
2. CTO assigns tasks based on priority.
3. Engineers execute: pull task → work → report progress.
4. Task progress = min(1.0, capacity_allocated / task_complexity).
5. Completed tasks advance features.

### Quality Factors
- **Adequate capacity**: quality = 1.0
- **Overloaded (1.1-1.5x)**: quality × 0.8
- **Severely overloaded (>1.5x)**: quality × 0.5, risk of bugs

### Blockers
- When a task is blocked, the LLM notes the blocker type (dependency, resource, knowledge).
- CTO escalates critical blockers to CEO.
- Unresolved blockers after 2 steps create operational risk.

## Engineering Constraints

- Cannot assign more work than total capacity (causes burnout).
- Cannot start new work while overloaded.
- Tech debt paydown competes with feature work.
- Hiring engineers takes 3-5 steps (recruitment cycle).
