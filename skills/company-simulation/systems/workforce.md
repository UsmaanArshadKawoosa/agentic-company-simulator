# Workforce System

## Employee Lifecycle

```text
Candidate → Interviewing → Offered → Onboarding → Active → At Risk → Resigned/Terminated
```

## Hiring Process

1. **Identify need**: CTO/CEO/CMO requests headcount.
2. **Create job opening**: Define role, requirements, budget.
3. **Generate candidates**: 3-5 candidates per opening (simulated).
4. **Evaluate**: Score candidates on fit, skills, culture match.
5. **Offer**: Negotiate salary, equity, terms.
6. **Onboard**: 1-2 steps ramp-up period (reduced capacity).

### Hiring Timeline
- **Sourcing**: 1-2 steps
- **Interviewing**: 1-2 steps
- **Offer negotiation**: 1 step
- **Onboarding**: 2 steps (50% capacity during ramp-up)

### Hiring Cost
- 2-3 months of role's salary for recruitment overhead.
- New hire salary added to payroll.
- Onboarding time reduces team capacity temporarily.

## Performance & Morale

### Morale Factors
- Positive: achievements, recognition, reasonable workload, growth opportunities.
- Negative: excessive workload, lack of recognition, conflicts, unclear direction.

### Morale Effects
- `morale < 0.3`: Resignation risk (20% chance per step).
- `morale < 0.2`: Productivity drops by 30%.
- `workload > 1.0` for 2+ steps: Morale drops, burnout risk.

### Performance Ratings
| Rating | Description | Effect |
|--------|------------|--------|
| Strong | Exceeds expectations | +10% capacity, morale boost |
| Healthy | Meets expectations | Normal |
| At risk | Below expectations | -10% capacity, morale drop |
| Underperforming | Consistently poor | At risk of termination |

## Workforce Metrics

- **Total capacity**: sum of all employee capacity × morale × productivity.
- **Workload**: assigned_capacity / total_capacity (1.0 = fully loaded).
- **Turnover rate**: resignations per step.
- **Team velocity**: capacity × productivity.

## Workforce Rules

- Cannot hire without budget approval.
- Cannot fire without CEO/founder approval (for ICs) or founder (for execs).
- Onboarding employees contribute partial capacity.
- Team building improves morale but costs budget.
