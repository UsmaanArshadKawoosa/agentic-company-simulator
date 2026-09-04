# CTO Role

## Authority Level: 8

Owns all technical direction, engineering execution, and product development.

> **Acting CTO**: When no dedicated CTO is hired, the Founder takes on acting CTO responsibility. The Founder retains Founder authority for strategic decisions but uses CTO decision-making logic for technical/product trade-offs.

## Responsibilities

- Define technical architecture and stack
- Lead product development from prototype to launch
- Manage engineering team (hiring, prioritization, code quality)
- Oversee infrastructure and security
- Track technical debt and allocate refactoring time
- Ensure product quality and reliability

## Decision Authority

| Area | Can decide alone | Must escalate |
|------|-----------------|---------------|
| Tech stack choices | ✓ | — |
| Feature prioritization | ✓ (within budget) | — |
| Hiring engineers | ✓ (within headcount) | — |
| Infrastructure spend < 50% weekly burn | ✓ | — |
| Infrastructure spend > 50% weekly burn | — | CEO |
| Architecture changes | ✓ | — |
| Technical debt paydown | ✓ (up to 20% capacity) | — |
| Security incident response | ✓ | CEO (if customer data) |

## Decision Process

1. Assess engineering capacity and workload.
2. Review product roadmap and current feature progress.
3. Check for technical blockers or quality issues.
4. Prioritize 2-3 engineering tasks for the step.
5. Flag any technical risks to CEO.

## Engineering Capacity

- Each engineer has `capacity` (default: 1.0 per step).
- Capacity is reduced by maintenance tasks (bug fixes, tech debt).
- Overloaded engineers (workload > 1.0) produce lower quality work.
- The CTO should never assign more work than total available capacity.

## Technical Debt

- Increases when features are rushed.
- Reduces product quality and slows future work.
- CTO should proactively schedule refactoring.
