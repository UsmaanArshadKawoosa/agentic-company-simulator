# Example Company: SaaS Startup

## Definition

```
Create a SaaS company called SecureFlow.
Mission: Zero-trust data sharing for healthcare and finance.
Starting capital: $750,000
Team: 1 founder/CEO, 1 CTO, 2 engineers, 1 CMO
Objective: Reach $100K ARR within 8 months
Market: Regulated B2B SaaS (healthcare + finance)
Seed: 88
```

## Recommended Team Composition

| Role | Count | Authority |
|------|-------|-----------|
| Founder/CEO | 1 | 10 |
| CTO | 1 | 8 |
| Engineer | 2 | 5 |
| CMO | 1 | 7 |

## Initial State Template

```yaml
company:
  name: "SecureFlow"
  mission: "Zero-trust data sharing for regulated industries"
  stage: idea
  day: 0
  seed: 88

finance:
  starting_cash: 750000
  cash: 750000
  daily_burn: 694        # payroll: founder $8K + CTO $7K + 2 engineers $8K + CMO $7K = ~$20K/month
  runway_days: ~1080
  valuation: 750000

product:
  stage: idea
  progress: 0.0
  quality: 0.0
  readiness: 0.0
  technical_debt: 0.0

market:
  segments: [mid_market, enterprise]
  demand: 0.65           # regulated data sharing is growing
  competition: 0.55      # established players
  sentiment: 0.70        # positive toward security
  market_size: 500       # enterprises in target
  market_share: 0.0
  brand_strength: 0.10

workforce:
  employees: []          # fill with team
  headcount: 5
  morale: 1.0
  workload: 0.0

goals:
  primary: "Reach $100K ARR within 8 months"
  secondary: ["Achieve SOC 2 compliance by Day 45", "Land 3 pilot customers"]
  progress:
    primary: 0.0
```

## Key Differences from Startup Template

- Enterprise sales cycle is longer (3–5 steps vs 1–2 for SMB).
- Compliance work adds 15-20% to engineering time.
- Higher salary costs (CTO, CMO roles).
- Smaller market (500 vs 5000) but higher ACV ($5K–$50K vs $50–$500).
- Brand strength starts higher (CMO on day 1).
