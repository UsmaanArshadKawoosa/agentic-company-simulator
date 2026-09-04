# Company State Schema

The LLM maintains company state as a structured block. This is the single source of truth for the simulation.

## Format

```yaml
company:
  name: string
  mission: string
  tagline: string           # optional
  stage: idea | prototype | mvp | beta | launch | growth | mature | declining
  day: integer              # current simulation day (starts at 0)
  time_unit: day | week | month
  time_per_step: integer    # days advanced per step
  total_days: integer       # target simulation length (0 = indefinite)
  seed: integer             # deterministic seed for reproducibility
  last_event_id: integer

finance:
  starting_cash: float
  cash: float               # MUST be tracked; must not go negative unless debt modeled
  revenue: float            # cumulative revenue
  expenses: float           # cumulative expenses
  daily_burn: float         # expenses minus revenue per step
  monthly_burn: float
  runway_days: float        # cash / daily_burn; null if burn <= 0
  profit: float             # revenue - expenses (cumulative)
  profit_margin: float      # profit / revenue
  valuation: float          # current estimated valuation
  fundraising_target: float # active fundraising goal (0 if none)
  fundraising_progress: float

product:
  stage: idea | prototype | mvp | beta | launch | growth | mature
  progress: float           # 0.0 to 1.0
  quality: float            # 0.0 to 1.0
  readiness: float          # 0.0 to 1.0
  technical_debt: float     # 0.0 to 1.0
  features: list            # tracked features
  bugs: integer
  maintenance_ratio: float

market:
  segments: list
  demand: float             # 0.0 to 1.0
  growth_rate: float
  competition: float        # 0.0 to 1.0
  sentiment: float          # 0.0 to 1.0
  market_size: float
  market_share: float       # 0.0 to 1.0
  brand_strength: float     # 0.0 to 1.0
  price: float
  pricing_power: float

workforce:
  employees: list[agent]    # see Agent State schema — individual agents
  total_capacity: float
  utilized_capacity: float  # sum of workload across agents
  morale: float             # 0.0 to 1.0 (average across agents)
  productivity: float       # 0.0 to 1.0
  headcount: integer
  open_positions: integer
  # Responsibility map: role → agent name(s)
  # When a role is unassigned, the responsible agent is marked as "acting"
  roles:
    founder: "Avery Chen"
    ceo: null               # null = no dedicated CEO (Founder acts as CEO)
    cto: null               # null = Founder has acting engineering responsibility
    cmo: null               # null = Founder has acting marketing responsibility
    engineering: ["Casey", "Remy"]
    marketing: null         # null = acting marketing owner
    sales: null
    finance: null

goals:
  primary: string
  secondary: list
  constraints: list
  progress:
    primary: float
    secondary: list[{name, progress}]

risks:
  - { id, severity: low|medium|high|critical, description, status, owner, created_day }

events:
  - { id, day, type, description, severity, category, consequences, actor }

history:
  decisions: list           # significant decisions with rationale
  milestones: list
  lessons_learned: list
  strategic_memory: list    # compressed summaries

status:
  financial_health: healthy | at_risk | critical | failed
  operational_health: healthy | at_risk | critical
  overall: active | paused | completed | failed
```

## State Invariants

1. `cash >= 0` (unless debt explicitly modeled).
2. All 0.0–1.0 ratings bounded.
3. `runway_days` recomputed when `cash` or `daily_burn` changes.
4. `daily_burn = expenses_per_step - revenue_per_step`.
5. `workload` per agent bounded; aggregate tracked for burnout risk.
6. `market_share ∈ [0.0, 1.0]`.
7. `stage` follows canonical progression.
8. Every active role maps to at least one agent (acting if no dedicated person).
9. Agent `decisions` history persists across steps.
