# Example Company: Consumer Brand

## Definition

```
Create a consumer brand called Bloom & Co.
Mission: Sustainable home goods delivered monthly.
Starting capital: $100,000
Team: 1 founder, 1 marketer, 1 operations person
Objective: Reach 5,000 subscribers within 6 months
Market: Eco-conscious consumers
Seed: 21
```

## Recommended Team Composition

| Role | Count | Authority |
|------|-------|-----------|
| Founder/CEO | 1 | 10 |
| Marketer (CMO-type) | 1 | 7 |
| Operations (Employee) | 1 | 3 |

## Initial State Template

```yaml
company:
  name: "Bloom & Co"
  mission: "Sustainable home goods delivered monthly"
  stage: idea
  day: 0
  seed: 21

finance:
  starting_cash: 100000
  cash: 100000
  daily_burn: 208         # payroll: founder $4K + marketer $3K + ops $2K = ~$9K/month
  runway_days: ~480
  valuation: 100000

product:
  stage: idea
  progress: 0.0
  quality: 0.0
  readiness: 0.0
  technical_debt: 0.0

market:
  segments: [consumer]
  demand: 0.45            # niche market
  competition: 0.35       # moderate
  sentiment: 0.60         # positive toward sustainability
  market_size: 50000      # eco-conscious households
  market_share: 0.0
  brand_strength: 0.05
  price: 39               # $39/month subscription
  pricing_power: 0.30

workforce:
  employees: []
  headcount: 3
  morale: 1.0
  workload: 0.0

goals:
  primary: "Reach 5,000 subscribers within 6 months"
  secondary: ["Achieve 85% monthly retention by Day 30", "Source 10 sustainable products"]
  progress:
    primary: 0.0
```

## Key Differences from Startup Template

- Subscription revenue (predictable MRR).
- Physical goods inventory costs.
- Shipping/logistics overhead.
- Lower ACV ($39/month) but higher volume potential.
- Inventory risk (unsold goods).
- Supply chain dependencies.
- Customer retention is critical (85%+ monthly target).
