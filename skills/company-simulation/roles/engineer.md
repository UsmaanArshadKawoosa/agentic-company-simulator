# Engineer Role

## Authority Level: 5

Implements product features, fixes bugs, and maintains technical quality.

## Responsibilities

- Write code for assigned features and tasks
- Fix bugs and address technical debt
- Participate in code reviews
- Communicate blockers to CTO
- Estimate task effort

## Decision Authority

| Area | Can decide alone | Must escalate |
|------|-----------------|---------------|
| Task implementation approach | ✓ | — |
| Bug priority (non-critical) | ✓ | — |
| Refactoring small modules | ✓ (up to 1 day) | — |
| Architecture changes | — | Acting CTO (Founder) |
| New dependencies | — | Acting CTO (Founder) |
| Feature scope changes | — | Acting CTO (Founder) |

## Work Model

- Each engineer has `capacity` per step (default: 1.0).
- Tasks consume capacity based on complexity.
- Complex tasks (3+ capacity) are split across multiple steps.
- Engineers report blockers to the acting CTO (typically the Founder) — unresolved blockers create risk.

## Task Lifecycle

```text
todo → in_progress → blocked | completed | cancelled
```

- Engineers pull tasks from the assigned backlog.
- `workload > 1.0` for 2+ steps triggers burnout risk.
- Morale drops when tasks are frequently blocked or cancelled.

## Quality Standards

- Each task has a quality target (0.0–1.0).
- Rushed tasks (capacity < required) lower quality.
- Bugs discovered during QA send tasks back.
- Engineers flag quality concerns to the acting CTO (Founder).
