# Sales System

## Sales Pipeline

The salesperson manages opportunities through 5 stages:

```text
Lead → Qualified → Proposal → Negotiation → Closed-Won|Lost
```

### Pipeline Metrics
| Stage | Typical conversion | Sales effectiveness modifier |
|-------|-------------------|------------------------------|
| Lead → Qualified | 60% | × effectiveness |
| Qualified → Proposal | 70% | × effectiveness |
| Proposal → Negotiation | 50% | × effectiveness |
| Negotiation → Won | 60% | × effectiveness |

`sales_effectiveness` starts at 0.3 (new company) and improves with experience, process, and team.

## Deal Management

### Per Step
1. Review pipeline: identify deals at each stage.
2. Advance deals through stages based on effort and effectiveness.
3. Close deals at end of step (won or lost).
4. Record revenue for won deals.
5. Note reasons for lost deals (objections, price, competition).

### Deal Value Factors
- Customer segment (SMB < Mid-Market < Enterprise)
- Product price × expected users
- Salesperson relationship strength
- Competitor status
- Product quality

### Enterprise Deals
- Higher value, longer sales cycle (3-5 steps).
- Requires CEO approval for discounts > 10%.
- Multiple stakeholders to convince.
- Competitive evaluation process.

## Sales Activities

| Activity | Capacity cost | Effect |
|----------|--------------|--------|
| Prospecting | 0.5 | +1-3 new leads |
| Qualifying | 0.3 | +1 deal to Qualified |
| Demo | 0.5 | Moves deal forward |
| Proposal | 0.3 | Moves deal forward |
| Negotiation | 0.5 | Moves deal toward close |
| Relationship | 0.2 | +10% close rate for existing contacts |

## Sales Constraints

- Cannot advance more deals than capacity allows.
- Must balance new prospecting vs closing existing pipeline.
- Cannot offer discounts above authority level.
- Product must be ready for demos (beta or better).
