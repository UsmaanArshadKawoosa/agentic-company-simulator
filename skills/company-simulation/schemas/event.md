# Event Schema

Events are the atomic units of simulation change. Every event modifies state or records a significant occurrence.

```yaml
- id: integer              # sequential, unique
  day: integer
  type: company_created | simulation_started | tick | market_update |
       competitor_action | customer_acquired | customer_churned |
       product_progress | financial_summary | product_launch |
       hiring | funding_raised | risk_detected | incident_created |
       environmental_event | agent_decision | goal_achieved |
       company_failed | company_completed | custom
  description: string
  actor: string            # agent name or "market" or "system"
  severity: info | warning | alert | critical
  category: internal | external | financial | operational | market
  consequences: list[string]  # state changes resulting from this event
  confidence: low | medium | high   # how certain the outcome is
```

## Event Sourcing Principles

- Every state change produces an event.
- Events are append-only — never edited, only superseded.
- Events reference the agent (actor) that triggered them.
- External events (market shifts, competitor actions) come from the market/competition system.
- Internal events (decisions, hires, launches) come from agent actions.
- Each event includes 1-3 consequence strings that describe the state change.
