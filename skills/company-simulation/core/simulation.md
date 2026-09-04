# Simulation Core

## Overview

The simulation engine operates as a deterministic loop. The LLM is the engine — there is no code to run. Each step represents a fixed period of simulated time (default: 1 day).

## The Multi-Agent Simulation Loop

Every step follows this fixed order:

```
1. Advance time          → increment day, update time-dependent values.
2. Apply scheduled effects → apply previously scheduled decisions (hiring lag, campaign ramp-up, etc.).
3. Process external events → market drift, competitor actions, environmental events.
4. Update company state   → apply event consequences to market, finance, etc.
5. Identify active agents  → determine which agents exist and are eligible to act.
6. Determine responsibilities → map each agent's primary + acting roles.
7. Generate individual agent decisions → each agent independently observes, prioritizes, decides.
8. Agent reactions          → agents react to decisions from other agents (dependency/conflict signals).
9. Conflict resolution       → resolve conflicting decisions (resource, authority, priority).
10. Resource constraints      → apply budget/capacity limits to resolved decisions.
11. Decision resolution       → apply consequences to state.
12. Generate consequences     → cascade effects (cash → runway → risk, etc.).
13. Update agent state        → morale, workload, performance, priorities.
14. Update company state       → finance, product, market, workforce.
15. Record major events        → append to events log, update history.
16. Compress historical state  → if milestone day, compress old history.
17. Produce company report     → concise summary (see Output Format).
```

### Agent Decision Sub-Loop (Steps 5–9)

```
For each active agent (in hierarchical order: Founder → CEO → CTO → CMO → Engineer → Salesperson → Employee):
  1. Observe state relevant to the agent's role
  2. Identify highest-priority issue
  3. Consider available actions (respecting authority + constraints)
  4. Make a decision (or declare NO_ACTION if none warranted)
  5. Provide concise rationale + expected consequences

After all agents decide:
  - Agents can react to decisions from agents who acted before them
  - Conflicts are flagged and resolved by authority hierarchy
  - Resource constraints are applied (budget, capacity)
```

### Agent Execution Order
Agents act sequentially in hierarchical order. Each agent sees the state after previous agents' decisions have been resolved. This prevents contradictions and allows dependencies.

### Time Granularities
| Mode | Time per step | Notes |
|------|--------------|-------|
| Single decision | — | One agent makes one decision |
| Daily | 1 day per step | Default; finest granularity |
| Weekly | 7 days per step | Consolidates 7 daily cycles |
| Monthly | 30 days per step | High-level; multi-year runs |
| Full run | Until success/failure | Fully autonomous |

### Determinism
- `seed` value guides market drift and event probabilities.
- Same seed + initial state → same market evolution (agent decisions may vary).
- State changes flow solely from agent decisions and system rules.

### State Compression
After every 7 steps (daily) or 4 steps (weekly/monthly):
- Compress `history.decisions` older than 7 days into `history.strategic_memory`.
- Merge routine events into daily summaries.
- Keep last 10 events active; older archived.
- Maintain current state snapshot visible.
