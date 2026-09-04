# Decision Framework

## Overview

Each agent makes decisions independently. Decisions must be grounded in company state, aligned with the agent's role authority, and produce traceable consequences. The LLM orchestrates agent interactions and resolves conflicts.

## The Multi-Agent Decision Process

### Phase 1: Individual Agent Decisions

For each active agent (in hierarchical order):

1. **Observe** — review company state relevant to the agent's role.
2. **Prioritize** — rank issues by impact and urgency (critical → high → medium → low).
3. **Evaluate** — generate 2–4 options with cost/benefit/risk for the top issue.
4. **Choose** — pick the best option, respecting budget/capacity/authority.
5. **Explain** — state action, rationale (1–2 sentences), expected impact.
6. **Record** — add to agent's decision history.

### Phase 2: Agent Interactions

After all agents decide, agents react to each other:

- Agents who acted later can respond to earlier decisions.
- Dependencies and conflicts are flagged.
- Resource or authority conflicts escalate to the next level in the hierarchy.

### Phase 3: Conflict Resolution

The LLM checks for conflicts:

| Conflict type | Resolution |
|---------------|------------|
| Resource conflict (over-budget, over-capacity) | Higher authority wins; lower-priority items deferred |
| Authority conflict (agent exceeds authority) | Escalate to manager agent |
| Priority conflict (two agents want same resource) | Higher-priority agent gets it; other re-prioritized |
| Dependency conflict (A needs B's work) | B's decision takes precedence; A adjusts timeline |

### Phase 4: Decision Resolution

The LLM applies all resolved decisions and their consequences to state.

## Decision Output Format

```text
[Agent Name] ([Role]) [acting: Role(s) if applicable]
→ [Action / NO_ACTION / INVALID_RESPONSE]

Situation: [brief description]
Options considered:
  A) [action] — cost: [X], benefit: [Y], risk: [Z]
  B) [alternative] — cost: [X], benefit: [Y], risk: [Z]
Chosen: [A or B, or "none"]
Rationale: [1-2 sentences]
Expected: [estimate with confidence: low|medium|high]
Confidence: [low|medium|high]

Consequences:
- [state change 1]
- [state change 2]
```

### NO_ACTION
Used when an agent consciously decides no action is required — continuing the current plan is optimal. Must include a brief rationale.

```text
Engineer 2 → NO_ACTION
Continuing: Onboarding UI improvements (60% complete).
```

### INVALID_RESPONSE
Used only when the LLM fails to produce a valid decision for an agent. Never presents as a legitimate agent decision. The LLM should retry resolution.

## Decision Constraints

- An agent cannot spend more than available cash or its approved budget.
- An agent cannot assign more work than total available capacity.
- Spending that would make `cash < 0` is forbidden (unless debt modeled).
- An agent acting outside its authority must escalate to its manager.

## Decision Scheduling

Not every agent makes a decision every step. The LLM determines whether an agent has a material decision by checking:
1. Are there open issues in the agent's responsibility area?
2. Does the agent have available capacity?
3. Is there a conflict or dependency requiring their input?

If no material decision is required, the agent declares `NO_ACTION` with a rationale.
