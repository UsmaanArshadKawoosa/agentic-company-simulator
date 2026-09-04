# Product System

## Product Lifecycle

Products progress through stages: `idea → prototype → mvp → beta → launch → growth → mature`.

See [Product Progression Model](../core/progression.md) for stage criteria.

## Features

Each product is composed of tracked features. Each feature has:
- `name`, `progress` (0.0–1.0), `quality` (0.0–1.0), `status`
- Associated tasks that drive progress

### Feature Progress
```text
feature.progress = avg(task.progress for tasks in feature)
product.progress = weighted_avg(feature.progress for all features)
```

### Feature Quality
```text
feature.quality = frac(completed_tasks) adjusted for rush
product.quality = avg(feature.quality) - technical_debt_penalty
```

## Engineering Capacity

- Each engineer contributes `capacity` per step.
- The CTO assigns engineers to features/tasks.
- Total capacity consumed per step ≤ total available capacity.
- Overloading (capacity > 1.0 per engineer) reduces quality.

## Technical Debt

- **Accumulates**: +0.01 per step per incomplete feature.
- **Penalty**: Each 0.1 technical debt reduces product quality by 0.02 and slows work by 5%.
- **Paydown**: 2 capacity-days per 0.05 debt reduction.
- **Rush penalty**: Completing a feature with < 80% quality adds +0.03 debt.

## Bugs

- Discovered during QA or by users.
- Severity: low, medium, high, critical.
- Critical bugs block launch.
- Bug fixes consume engineering capacity.
- High bug count reduces product quality.

## Product Rules

- Cannot launch until `product.progress >= 0.9`.
- Cannot launch with `product.quality < 0.3`.
- Cannot launch with unresolved critical bugs.
- Post-launch: new features follow the same model (smaller increments).
- Quality directly affects customer churn and acquisition rates.
