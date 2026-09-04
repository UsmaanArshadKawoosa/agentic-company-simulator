# Competition System

## Competitor Model

Competitors are simplified — they are profiles with strategies, not full simulations.

### Competitor Profile
```yaml
- name: string
  strategy: low_cost | premium | growth | enterprise | balanced
  market_share: float
  funding_stage: pre_seed | seed | series_a | series_b | public
  product_stage: idea | prototype | mvp | beta | launch | growth
  monthly_spend: float
  key_strength: string
  key_weakness: string
```

## Competitor Actions

Competitors act autonomously (driven by the LLM based on their profile):

| Action | Triggers | Market effect |
|--------|----------|---------------|
| **Launch product** | Competitor reaches launch stage | competition +0.10, sentiment -0.05 |
| **Price drop** | Low-cost competitor loses market share | competition +0.08, sentiment -0.03 |
| **Raise funding** | Funding stage upgrade | competition +0.05 |
| **Marketing campaign** | Competitor has budget | competition +0.03 |
| **New feature** | Product improvements | competition +0.04 |
| **Hire talent** | Team expansion | competition +0.02, hiring difficulty + |

## Competitor Strategy Templates

### Low-Cost
- Competes on price
- Thin margins, high volume
- Actions: price drops, efficiency improvements
- Weakness: low quality perception

### Premium
- Competes on quality/price-insensitive
- High margins, strong brand
- Actions: quality improvements, premium features
- Weakness: smaller market

### Growth
- Competes on speed and scale
- High spending, fast iteration
- Actions: rapid launches, aggressive marketing
- Weakness: unsustainable burn

### Enterprise
- Competes on enterprise features
- Long sales cycles, high ACV
- Actions: enterprise features, sales hires
- Weakness: slow to adapt

### Balanced
- Competes across multiple dimensions
- Stable, well-rounded
- Actions: measured improvements
- Weakness: no clear advantage

## Competitive Response

Your company's actions can trigger competitor reactions:
- Your launch → competitor launches competing product
- Your price cut → competitor matches or undercuts
- Your funding → competitor races to fundraise
- Your feature → competitor adds similar feature

## Market Share Dynamics

```text
your_market_share_change = 
    (your_acquisition - competitor_acquisition) 
    × (1 - competition)
    × product_quality_factor
```

Market share is recalculated each step and affects:
- Revenue (more share = more customers)
- Brand strength (growing share = stronger brand)
- Investor interest (market position matters for fundraising)
