# Market System

## Market Variables

The market is an external force that influences the company. It evolves over time:

| Variable | Range | Description |
|----------|-------|-------------|
| `demand` | 0.0–1.0 | Current market demand for your product category |
| `growth_rate` | -0.1 to +0.1 | Daily/weekly growth rate of demand |
| `competition` | 0.0–1.0 | Competitive intensity |
| `sentiment` | 0.0–1.0 | Market sentiment toward your category |
| `market_size` | numeric | Total addressable market (users or revenue) |

## Market Segments

Standard segments:
- **Startup**: 500M TAM, price sensitivity high, early adopters
- **SMB**: 2B TAM, price sensitivity high, practical needs
- **Mid-Market**: 5B TAM, price sensitivity medium, scaling needs
- **Enterprise**: 10B TAM, price sensitivity low, security compliance

The company selects a primary target segment. Market share is calculated against that segment.

## Market Evolution

### Daily/Weekly Drift
Each step, market variables drift within bounds:
- `demand`: ±0.03 per step (±0.05 for weekly)
- `competition`: ±0.02 per step
- `sentiment`: ±0.03 per step

### Demand Factors
Demand is influenced by:
1. **Category growth** (baseline trend)
2. **Technology cycles** (waves of interest)
3. **Economic conditions** (slower growth in downturns)
4. **Customer sentiment** (feedback loops)

### Sentiment
Sentiment reflects how the market feels about your product category:
- High sentiment → easier acquisition, higher willingness to pay
- Low sentiment → harder acquisition, price pressure
- Sentiment shifts slowly and sticks

## Market Impact on Company

### Customer Acquisition
```text
acquisition_pressure = demand × sentiment × (1 - competition)
```

### Churn
```text
churn_pressure = competition × (1 - sentiment) + (1 - product_quality)
```

### Pricing Power
```text
pricing_power = sentiment × brand_strength × (1 - competition)
```

## Market Rules

- Market does not respond to single company actions (too small to move market alone).
- Market shifts affect ALL companies in the category.
- Market data is observed, not controlled.
- Companies can choose segments with different demand/competition profiles.
