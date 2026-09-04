# Decision Schema

Every agent decision follows a compact, structured format.

```yaml
- day: integer
  agent: string              # agent name
  role: string               # agent role
  priority: low | medium | high | critical
  situation: string          # brief description of the problem
  options:
    - action: string
      cost: string           # resource cost (time, money, capacity)
      benefit: string        # expected benefit
      risk: string           # risk level / downside
  chosen_action: string
  rationale: string          # 1-2 sentences; why this option
  confidence: low | medium | high
  expected_outcome: string
  estimated_impact: string   # e.g. "+12% acquisition, -5% runway"
  dependencies: list[string] # what must happen first
  constraints_considered: list[string]
  consequences: list[string] # recorded after resolution
```

## Decision Process

1. **Observe** — read relevant state (finance, market, product, workforce).
2. **Prioritize** — rank issues by urgency and impact.
3. **Evaluate** — score 2-4 options against mission, budget, capacity, risk.
4. **Choose** — pick the option with best risk-adjusted return.
5. **Explain** — state the action, rationale, and expected impact in 1-2 sentences.
6. **Resolve** — the LLM applies consequences to state (not the agent itself).
7. **Record** — log the decision and its outcome in `history.decisions`.
