# Product Progression Model

## Stages

```text
idea → prototype → mvp → beta → launch → growth → mature → declining
```

### Stage Criteria

| Stage | Readiness threshold | Key milestone |
|-------|-------------------|---------------|
| idea | 0% | Problem identified |
| prototype | 10% | Basic concept validated |
| mvp | 40% | Minimum viable product ready |
| beta | 70% | Beta released to early users |
| launch | 90% | Product ready for market |
| growth | 95% + revenue > 0 | Growing customer base |
| mature | stable metrics | Product-market fit achieved |
| declining | revenue declining 3+ steps | Market disruption |

## Progress Mechanics

- **Product progress** = weighted average of feature progress across all tracked features.
- **Feature progress** = proportion of that feature's tasks completed.
- **Work capacity** allocated per step determines how many features advance.
- Progress does NOT increase automatically — it requires engineering work.

## Quality Model

```text
product_quality = avg(feature_quality) - technical_debt_penalty
```

- **Feature quality** = fraction of tasks completed without rushing.
- **Technical debt penalty** grows when features are rushed (completed with incomplete tasks).
- Quality directly affects customer churn and acquisition.

## Technical Debt

- Accumulates at +0.01 per day per incomplete feature (rushed work).
- Reduces product quality and slows future development by 5% per 0.1 debt.
- Can be reduced by dedicating capacity to refactoring (2 capacity-days → -0.05 debt).

## Product Constraints

- Cannot launch before reaching 90% readiness.
- Cannot launch with quality below 0.3.
- Cannot launch with unresolved critical bugs.
- Post-launch features follow the same progression model (smaller increments).
