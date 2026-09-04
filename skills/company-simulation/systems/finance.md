# Finance System

## Core Principles

1. **Cash is king** — cash balance drives all decisions. No spending that would make cash negative.
2. **Burn is real** — cash decreases daily by operating expenses.
3. **Runway dictates strategy** — when runway < 90 days, survival mode activates.

## Financial Model

### Cash Flow
```text
daily_burn = total_daily_expenses - daily_revenue
cash = cash - daily_burn (per step)
runway_days = cash / daily_burn   (null if burn <= 0)
```

### Expense Categories
| Category | Typical % of burn | Notes |
|----------|-------------------|-------|
| Payroll | 50-70% | Salaries, benefits |
| Infrastructure | 10-20% | Hosting, tools, software |
| Marketing | 10-30% | Campaigns, ads |
| Operations | 5-15% | Legal, accounting, misc |
| Product | 0-10% | Feature-specific costs |

### Revenue Model
Revenue comes from:
1. **Paying users** × monthly_value × conversion (daily step uses proportional allocation)
2. **Enterprise deals** closed by salesperson
3. **Partnerships** (one-time or recurring)

### Financial Health Tiers

| Tier | Cash adequacy | Runway | Score |
|------|--------------|--------|-------|
| Healthy | > 30 days expenses | > 180 days | ≥ 0.7 |
| At risk | 14-30 days | 90-180 days | 0.4-0.7 |
| Critical | 7-14 days | 30-90 days | 0.2-0.4 |
| Failed | < 7 days or cash ≤ 0 | < 30 days | < 0.2 |

## Financial Rules

- **No overdraft**: Spending that would make `cash < 0` is rejected unless debt is modeled.
- **Payroll is fixed**: Salaries are paid every step; cannot be skipped.
- **Marketing spend is variable**: Can be increased/decreased within budget authority.
- **Infrastructure scales**: Grows with user base but has a base cost.
- **Revenue lag**: New customers start paying next step; churned customers stop paying next step.

## Daily Financial Update

After each step, update:
1. Revenue from active paying customers.
2. Expenses (payroll, infrastructure, marketing, operations).
3. Cash balance.
4. Runway calculation.
5. Financial health status.
6. Profit/loss.

If `daily_burn > 0` and `cash` drops below runway threshold → trigger `risk_detected` event.
