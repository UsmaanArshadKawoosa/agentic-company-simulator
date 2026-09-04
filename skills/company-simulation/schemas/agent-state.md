# Agent State Schema

## Agents vs Roles

This skill distinguishes between **agents** (actual people in the simulated company) and **roles/functions** (organizational responsibilities).

- An **agent** is a person with a name, authority, capacity, and decision history.
- A **role** is a set of responsibilities, priorities, and decision authorities.
- A role does not automatically imply a separate person exists.
- When a role is unassigned, an existing agent may take on "acting" responsibility for that function.

A single agent can hold multiple roles (e.g., "Founder / CEO" with acting marketing responsibility).

## Agent Structure

```yaml
agent:
  name: string                    # unique identifier (e.g., "Avery Chen")
  role: string                    # e.g., "founder", "engineer", "cto"
  title: string                   # human-readable (e.g., "Founder / CEO")
  authority: integer              # 1–10; scope of unilateral decisions
  responsibilities:
    primary: list[string]         # e.g., ["strategy", "product_direction"]
    acting: list[string]          # temporarily held roles (e.g., ["marketing", "finance"])
  capacity: float                 # work capacity per step (0.0–1.0 for ICs, 0.0 for executives)
  workload: float                 # fraction assigned (0.0–1.0+; >1.0 = overload)
  morale: float                   # 0.0–1.0
  energy: float                   # 0.0–1.0 (depleted by overtime)
  priorities: list[string]        # ranked focus areas for current step
  decisions: list[object]         # decision history (see decision schema)
  performance: float              # 0.0–1.0; recent task quality
  created_day: integer
  status: active | onboarding | at_risk | resigned
  manager: string | null          # name of direct manager
  specialization: string | null   # e.g., "backend", "frontend", "growth"
  skills: list[string]
```

## Agent Behavior Differentiation

Each role has inherent priority focus. Agents of the same role share behavioral patterns but differ in specialization and personal traits.

### Founder / CEO
Priority focus: survival, strategy, company goals, capital, major hiring, product direction

### CTO
Priority focus: engineering capacity, architecture, technical risk, product development, technical hiring

### CMO
Priority focus: acquisition, positioning, marketing, conversion, customer growth

### Engineer
Priority focus: implementation, bugs, technical tasks, product quality, engineering capacity

### Salesperson
Priority focus: leads, pipeline, conversion, customer acquisition, deals

### Employee
Priority focus: task execution within assigned scope

## Acting Responsibilities

When a role is unassigned (e.g., no CTO hired), an existing agent may take "acting" responsibility:

```yaml
agent:
  name: "Avery Chen"
  role: "founder"
  title: "Founder / CEO"
  responsibilities:
    primary: [strategy, company_direction]
    acting: [engineering, product, marketing, finance]  # explicitly marked as acting
```

Acting responsibilities are always labeled with the `acting` prefix in output:
```
Acting CTO — Founder
→ Decision about architecture
```

## Decision Scheduling

Not every agent makes a decision every step. The LLM determines whether an agent has a meaningful decision by checking:
1. Are there open issues in the agent's responsibility area?
2. Does the agent have available capacity?
3. Is there a conflict or dependency requiring their input?

If no material decision is required:
```
Engineer 1 → No material decision required.
Continuing: API rate limiting fix (70% complete).
```

This is distinct from:
```
Engineer 1 → INVALID_RESPONSE
```
Which indicates the LLM failed to produce a valid decision.

## Agent History

Each agent maintains a lightweight decision history (last 5–10 decisions). This influences future behavior — agents know what they were previously working on and can detect patterns (e.g., recurring blockers, consistently missed deadlines).
