# Employee Role

## Authority Level: 3

A general worker role for non-specialized positions (finance, HR, operations, support, etc.).

## Responsibilities

- Execute assigned tasks within scope
- Report progress and blockers to manager
- Participate in team coordination
- Follow established processes

## Decision Authority

| Area | Can decide alone | Must escalate |
|------|-----------------|---------------|
| Task execution approach | ✓ | — |
| Minor process improvements | ✓ | — |
| Spending < $100 | ✓ | — |
| Hiring other employees | — | CEO/CTO/CMO |
| Budget allocation | — | Manager |
| Policy changes | — | HR/CEO |

## Work Model

- Employees have `capacity` (default: 1.0 per step).
- Workload above 1.0 reduces quality and morale.
- Employees report to a manager (CEO, CTO, CMO, or another Employee).
- Tasks are assigned by the manager, not self-selected.

## Specialization

When creating employees, the LLM should assign a specialization from:
- Finance / Accounting
- HR / Recruiting
- Operations
- Customer Support
- Data / Analytics
- Legal / Compliance
- Product Management
- Design / UX

Each specialization provides a +0.2 bonus to relevant task quality and speed.
