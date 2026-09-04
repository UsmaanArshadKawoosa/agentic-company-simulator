# Event System

## Event Types

Events are categorized by source and impact:

### Internal Events (agent-initiated)
| Event | Triggers |
|-------|----------|
| `agent_decision` | Agent makes a decision |
| `hiring` | New employee joins |
| `product_launch` | Product reaches launch stage |
| `feature_completed` | A product feature ships |
| `goal_achieved` | Primary or secondary objective reached |
| `risk_detected` | New risk identified |
| `incident_created` | Risk escalates to incident |
| `funding_raised` | Capital raised |
| `budget_approved` | Spending authorized |

### External Events (market/system-initiated)
| Event | Triggers |
|-------|----------|
| `market_update` | Daily market drift |
| `competitor_action` | Competitor launches, prices, hires |
| `environmental_event` | Market boom/downturn, regulatory pressure, tech shift |
| `customer_acquired` | New customer signs up |
| `customer_churned` | Customer leaves |
| `financial_summary` | Periodic financial update |

## Event Generation

Events are **context-sensitive**, not random:

1. **Market events** derive from current `market.demand`, `competition`, and `sentiment`.
2. **Competitor events** derive from competitor profiles and relative performance.
3. **Customer events** derive from product quality, marketing spend, and pricing.
4. **Internal events** derive from agent decisions and state changes.

### Event Probabilities

| Event type | Base probability | Scales with |
|------------|-----------------|-------------|
| Market boom | 2% | High sentiment |
| Market downturn | 2% | Low sentiment |
| Competitor launch | 3% | Your product readiness |
| Competitor price drop | 2% | You losing market share |
| Customer surge | 3% | High demand + marketing |
| Customer decline | 3% | Low demand + competition |
| Infrastructure cost increase | 2% | Company age |
| Regulatory pressure | 1% | Market size |
| Technology shift | 2% | Product stage |

Multiple events can occur in a single step. Each event's effect is applied immediately and cascaded.

## Event Consequences

Every event must list 1-3 concrete consequences that modify state:

```text
Event: Competitor price drop
Consequences:
- market.competition +0.08
- market.market_share -0.03
- risk: "Price competition eroding margins (severity: medium)"
```

## Event History

- Keep the last 10 events in the active `events` list.
- Older events are compressed into `history.strategic_memory`.
- Each event must reference `day`, `actor`, `severity`, and `consequences`.
