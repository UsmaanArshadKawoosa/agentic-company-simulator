# Outcomes and Termination

## Success Conditions

The company achieves success when any of these conditions are met:

| Outcome | Trigger |
|---------|---------|
| **Survival** | Cash > 0 at day 180+ |
| **Product launch** | Product reaches `launch` stage |
| **Product-market fit** | `paying_users > 0` AND `market_share > 0.05` for 5+ consecutive days |
| **Revenue growth** | Monthly revenue > 10x starting revenue |
| **Profitability** | `daily_burn <= 0` and `revenue > 0` for 3+ consecutive days |
| **Fundraising** | `fundraising_target` reached |
| **Rapid expansion** | 5+ new employees and 3+ new features in 10 days |
| **Acquisition** | External acquisition event (external trigger) |
| **IPO** | Revenue > $1M/day and 50+ employees (external trigger) |

## Failure Conditions

The company fails when any of these occur:

| Failure | Trigger |
|---------|---------|
| **Cash exhaustion** | `cash <= 0` |
| **Runway exhaustion** | `runway_days < 7` |
| **Failed launch** | `product.stage >= launch` but `paying_users == 0` for 10+ days |
| **Persistent churn** | Churn rate > 15% for 5+ consecutive days |
| **Product-market failure** | `market_share < 0.01` and `paying_users < 1` for 14+ days |
| **Operational collapse** | 3+ employees resign in 5 days OR `morale < 0.2` |
| **Quality crisis** | `product.quality < 0.2` with active paying customers |
| **Team collapse** | CEO or Founder resigns (or is the only employee and resigns) |

## Failure Analysis

When the company fails, the LLM must produce:

1. **Root cause**: The primary reason for failure.
2. **Key decisions**: 2-3 decisions that contributed to the downfall, including which agent made each decision, whether any agent declared NO_ACTION when it would have mattered, and whether conflict resolution failed.
3. **Warning signs**: Earlier indicators that were (or weren't) acted upon — including agent reactions that were ignored or conflicts that escalated unresolved.
4. **What could have changed it**: One counterfactual action that might have saved the company.

## Success Analysis

When the company succeeds, the LLM must produce:

1. **Key achievements**: What made success possible.
2. **Pivotal decisions**: 2-3 decisions that turned the trajectory, including which agent made each decision and how acting responsibility delegation (e.g., founder acting as CTO/CMO) enabled or constrained the outcome.
3. **Critical advantages**: What differentiated the company.
4. **Ongoing risks**: Challenges that remain even after success.

## Termination

When a success or failure condition is met:
1. Stop the simulation loop.
2. Record the outcome and analysis.
3. Offer the user options: restart, counterfactual analysis, or save and exit.
