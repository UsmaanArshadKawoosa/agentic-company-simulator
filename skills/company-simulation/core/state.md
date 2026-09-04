# State Management

## State Representation

The LLM maintains two types of state: **company state** (global) and **agent state** (per-person). Both are structured blocks kept in the conversation.

## Company State Lifecycle

### 1. Initialization
```text
User provides company definition
          ↓
LLM constructs initial state
          ↓
Seeds organization (agents), finances, product, market
          ↓
Records initial state in conversation
```

### 2. Daily Maintenance
Every step:
- After market evolution: update market variables.
- After agent decisions: update affected fields.
- After financial processing: update cash, runway, burn.
- After product update: update progress, quality, readiness.
- After goal evaluation: update progress metrics.

### 3. Agent State Updates
Every step:
- After agent decisions: update `priorities`, append to `decisions` history.
- After work execution: update `workload`, `morale`, `performance`.
- After conflict resolution: update `authority` usage (if budget exceeded, etc.).

### 4. Invariants
The LLM must enforce these invariants after every step:
- `cash >= 0` (unless debt explicitly modeled).
- All 0.0–1.0 ratings bounded.
- `runway_days` recomputed when `cash` or `daily_burn` changes.
- `daily_burn = expenses_per_step - revenue_per_step`.
- Every active role maps to at least one agent (acting if no dedicated person).
- Agent `decisions` history persists (last 5–10 decisions).

### 5. Compression
- **Every 7 days**: compress decisions older than 7 days into `strategic_memory`.
- **Every 30 days**: merge routine events into weekly digests.
- Keep last 10 events active; older archived.
- Keep current state snapshot visible.

## Persistence

### Conversation-only (default)
State lives in the conversation. No files needed.

### Optional file persistence
```
State saved at Day N:

```yaml
company:
  name: "NovaFlow AI"
  day: 8
  ...
workforce:
  employees:
    - name: "Avery Chen"
      ...
```

Copy this block to save. Later, say "Continue from this state:" and paste it back.
```

## Agent State Lifecycle

1. **Onhire**: Agent added with `created_day`, initial `capacity`, `morale`, `priorities`.
2. **Onboarding**: First 2 steps — `capacity` at 50%, `status: onboarding`.
3. **Active**: Full capacity, participating in decisions.
4. **At risk**: Low morale or performance triggers risk.
5. **Resigned/Terminated**: Removed from active roster, kept in history.

## Responsibility Delegation

When initializing a company, the LLM maps roles to agents:

```text
Company: 1 Founder, 2 Engineers
Role mapping:
  Founder → Avery (primary: strategy, acting: engineering, marketing, finance)
  Engineering → Casey, Remy (each gets specialization)
  No CTO → Founder has acting engineering responsibility
  No CMO → Founder has acting marketing responsibility
```

When the company hires a CTO:
```text
Before: Founder → acting: [engineering, marketing, finance]
After:  Founder → [strategy, marketing, finance]  (engineering removed from acting)
        New CTO → primary: engineering, architecture
```

The LLM must explicitly update the responsibility map after hiring.
