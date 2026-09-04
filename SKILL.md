---
name: agentic-company-simulator
description: >
  A portable LLM skill that transforms any capable language model into an
  autonomous multi-agent company simulation engine. Simulates founders,
  executives, and employees as independent decision-makers with distinct
  roles, authority, and priorities. Tracks finances, products, markets,
  competition, and events with causal consequences.
version: 1.0.0
license: MIT
tags:
  - simulation
  - business
  - autonomous-agents
  - decision-engine
  - strategy
---

# Agentic Company Simulator

A portable LLM skill that turns your language model into an autonomous company simulation engine. No code, no servers, no databases. Just provide this skill to your LLM and describe a company — then watch it live, decide, and evolve.

> **Companion modules**: The granular breakdown of this skill lives in `skills/company-simulation/`. This root file is self-contained; the modules provide expanded detail for maintainers.

## Quick Start

1. Give this `SKILL.md` to your LLM.
2. Describe a company:
   ```
   Create a startup called NovaFlow AI.
   Mission: Build an AI productivity platform.
   Starting capital: $250,000.
   Team: 1 founder, 2 engineers.
   Objective: Launch within 60 days and reach 1,000 paying users.
   Market: Competitive AI productivity space.
   ```
3. The LLM initializes state and begins simulation.
4. To run autonomously: `Simulate the next 7 days.`
5. To interact: `Should we hire another engineer?` (Advisory mode)
6. To save: copy the state block and say `State saved at Day N.` later.

---

## 1. Core Simulation Loop

Every simulation step follows this 17-phase order:

```
1. Advance time          → increment day, update time-dependent values
2. Apply scheduled effects → apply previously scheduled decisions (hiring lag, etc.)
3. Process external events → market drift, competitor actions, environmental events
4. Update company state   → apply event consequences to market, finance, etc.
5. Identify active agents  → determine which agents exist and can act
6. Determine responsibilities → map each agent's primary + acting roles
7. Generate individual agent decisions → each agent independently observes, decides
8. Agent reactions        → agents respond to decisions from other agents
9. Conflict resolution    → resolve resource/authority/priority conflicts
10. Resource constraints   → apply budget and capacity limits
11. Decision resolution  → apply consequences to state
12. Generate consequences → cascade effects (cash → runway → risk)
13. Update agent state     → morale, workload, performance, priorities, history
14. Update company state   → finance, product, market, workforce
15. Record major events    → append to events log, update history
16. Compress historical state → if milestone day, compress old history
17. Produce company report → concise summary (see §8)
```

### Agent Decision Sub-Loop (Steps 5–9)

```
For each active agent (hierarchical order: Founder → CEO → CTO → CMO →
Engineer → Salesperson → Employee):
  1. Observe state relevant to the agent's role
  2. Identify highest-priority issue
  3. Consider 2–4 available actions
  4. Make a decision
  5. Provide concise rationale + expected consequences
  OR declare NO_ACTION if no material decision required

After all agents decide:
  - Agents react to decisions from agents who acted before them
  - Conflicts are flagged and resolved by authority hierarchy
  - Resource constraints are applied (budget, capacity)
```

### Agent Execution Order
Agents act sequentially: **Founder → CEO → CTO → CMO → Engineer → Salesperson → Employee**. Each agent sees the state after all prior agents' decisions have been resolved.

### Time Granularities
| Mode | Time per step | Use case |
|------|--------------|----------|
| Single decision | none | One-off question |
| Daily | 1 day | Detailed simulation |
| Weekly | 7 days | Consolidated decisions |
| Monthly | 30 days | Long-term planning |
| Full run | Until success/failure | Fully autonomous |

---

## 2. State Model

The LLM maintains a single structured state block. This is the source of truth for everything.

```yaml
# ─── Company ───────────────────────────────────────────
company:
  name: "NovaFlow AI"
  mission: "Build an AI productivity platform"
  tagline: ""
  stage: idea              # idea | prototype | mvp | beta | launch | growth | mature | declining
  day: 0
  time_unit: day
  time_per_step: 1
  total_days: 0            # 0 = indefinite
  seed: 42
  last_event_id: 0

# ─── Finance ───────────────────────────────────────────
finance:
  starting_cash: 250000
  cash: 250000
  revenue: 0
  expenses: 0
  daily_burn: 0
  monthly_burn: 0
  runway_days: null        # null if burn <= 0
  profit: 0
  profit_margin: 0
  valuation: 250000
  fundraising_target: 0
  fundraising_progress: 0

# ─── Product ───────────────────────────────────────────
product:
  stage: idea              # idea | prototype | mvp | beta | launch | growth | mature
  progress: 0.0            # 0.0–1.0
  quality: 0.0             # 0.0–1.0
  readiness: 0.0            # 0.0–1.0
  technical_debt: 0.0      # 0.0–1.0
  bugs: 0
  maintenance_ratio: 0.0

# ─── Market ────────────────────────────────────────────
market:
  segments: [startup, smb]
  demand: 0.5              # 0.0–1.0
  growth_rate: 0.01        # per step
  competition: 0.3         # 0.0–1.0
  sentiment: 0.5           # 0.0–1.0
  market_size: 10000       # target segment size (users)
  market_share: 0.0        # 0.0–1.0
  brand_strength: 0.1      # 0.0–1.0
  price: 100
  pricing_power: 0.15

# ─── Workforce ─────────────────────────────────────────
workforce:
  employees: []            # list of individual agents (see Agent State §3)
  total_capacity: 0
  utilized_capacity: float # sum of workload across agents
  morale: 1.0             # average across agents
  productivity: 1.0       # 0.0–1.0
  workload: 0.0
  headcount: 0
  open_positions: 0
  # Responsibility map: role → agent name(s)
  # null = no dedicated person; an existing agent has "acting" responsibility
  roles:
    founder: "Avery Chen"
    ceo: null               # null = Founder acts as CEO
    cto: null               # null = Founder has acting engineering responsibility
    cmo: null               # null = Founder has acting marketing responsibility
    engineering: ["Casey", "Remy"]
    marketing: null
    sales: null
    finance: null

# ─── Goals ─────────────────────────────────────────────
goals:
  primary: "Launch within 60 days and reach 1,000 paying users"
  secondary: []
  constraints: ["Starting cash: $250,000", "Team: 1 founder, 2 engineers"]
  progress:
    primary: 0.0
    secondary: []

# ─── Risks ─────────────────────────────────────────────
risks: []

# ─── Events ────────────────────────────────────────────
events: []

# ─── History ───────────────────────────────────────────
history:
  decisions: []
  milestones: []
  lessons_learned: []
  strategic_memory: []

# ─── Status ────────────────────────────────────────────
status:
  financial_health: healthy
  operational_health: healthy
  overall: active
```

### State Invariants (enforce every step)
1. `cash >= 0` (unless debt explicitly modeled)
2. All 0.0–1.0 ratings bounded
3. `runway_days` recomputed when `cash` or `daily_burn` changes
4. `daily_burn = expenses_per_step - revenue_per_step`
5. Per-agent `workload` bounded; aggregate tracked for burnout risk
6. Every active role maps to at least one agent (acting if no dedicated person)
7. Agent `decisions` history persists across steps

### State Compression
- **Every 7 days**: compress decisions older than 7 days into strategic_memory.
- **Every 30 days**: merge routine events into weekly summaries.
- Keep last 10 events active; older archived to strategic_memory.
- Always keep current state snapshot visible.

---

## 3. Agent System

This skill distinguishes between **agents** (actual people) and **roles/functions** (organizational responsibilities). A role does not automatically imply a separate person exists.

### Agents vs Roles

- **Agent**: A person with a name, authority, capacity, workload, and decision history.
- **Role**: A set of responsibilities, priorities, and decision authorities.
- A single agent can hold multiple roles (e.g., "Founder / CEO" with acting marketing).
- When a role is unassigned, an existing agent takes **acting** responsibility.
- Hiring creates a new agent that participates in decision-making.

### Available Roles
| Role | Default authority | Priority focus |
|------|------------------|---------------|
| Founder | 10 | survival, strategy, capital, major hiring, product direction |
| CEO | 9 | coordination, fundraising, budgeting |
| CTO | 8 | engineering, architecture, technical risk, product, tech hiring |
| CMO | 7 | acquisition, positioning, marketing, conversion |
| Engineer | 5 | implementation, bugs, quality, engineering capacity |
| Salesperson | 5 | leads, pipeline, conversion, deals |
| Employee | 3 | task execution within scope |

### Responsibility Delegation (NovaFlow AI Example)

```text
Company: 1 Founder, 2 Engineers
Role mapping:
  Founder → Avery (primary: strategy; acting: engineering, marketing, finance)
  Engineering → Casey, Remy (each gets a specialization)
  No CTO → Founder has acting engineering responsibility
  No CMO → Founder has acting marketing responsibility
```

When the company hires a CTO:
```text
Before: Founder → acting: [engineering, marketing, finance]
After:  Founder → [strategy, product_direction, marketing, finance]
        New CTO → primary: engineering, architecture
```

### Agent State Template
```yaml
- name: "Casey Chen"
  role: engineer
  title: "Engineer"
  specialization: backend           # or frontend, full-stack, ai, etc.
  authority: 5
  capacity: 1.0                     # work units per step
  workload: 0.0                     # fraction assigned
  morale: 1.0
  energy: 1.0
  status: active
  manager: "Avery Chen"
  skills: [backend, api, databases]
  priorities: []                    # current focus areas
  decisions: []                     # decision history (lightweight)
  performance: 0.8                  # 0.0–1.0; recent work quality
  created_day: 0
```

### Acting Responsibility Labeling

When an agent performs a role they don't formally hold:

```text
Avery (Founder / CEO) — Acting CMO
→ Launch waitlist landing page
  Rationale: No dedicated marketer; marketing is the highest leverage activity
  Confidence: High
```

### Role Authority Rules

**Founder**: Unlimited on strategy/crisis. Can hire/fire execs, secure funding.

**CEO**: Can decide budget < 10% monthly burn, pricing ±20%, hire ICs. Must escalate exec hires, pivots, large spending.

**CTO**: Can decide tech stack, feature priorities, hire engineers, infra spend < 50% weekly burn, tech debt paydown. Must escalate large infra spend, major architecture changes (to CEO).

**CMO**: Can decide campaigns < 10% weekly burn, channel testing, pricing experiments ±10%, hire marketers. Must escalate large campaigns, major positioning changes (to CEO).

**Engineer**: Can decide implementation approach, small refactors, bug priority. Must escalate architecture changes, new dependencies, scope changes (to CTO).

**Salesperson**: Can decide lead qualification, demos, discounts < 10%, standard contracts. Must escalate large discounts, custom terms (to CEO).

**Employee**: Can decide task approach, minor process improvements. Must escalate everything else to manager.

### Agent Behavior Differentiation

Each role prioritizes different concerns:

| Role | Top priority | Second priority | Third priority |
|------|-------------|----------------|----------------|
| Founder/CEO | Survival (cash, runway) | Strategy alignment | Hiring |
| CTO | Engineering capacity | Technical risk | Product quality |
| CMO | Acquisition | Conversion | Brand/positioning |
| Engineer | Implementation | Bugs | Quality |
| Salesperson | Pipeline | Conversion | Deals |
| Employee | Task execution | Process | Coordination |

No agent makes generic "company strategy" decisions outside their focus unless acting as CEO/Founder.

---

## 4. Decision Framework

Each agent makes decisions independently. The LLM orchestrates agent interactions and resolves conflicts.

### Phase 1: Individual Agent Decisions

For each active agent (in hierarchical order):

1. **Observe** — review company state relevant to the agent's role.
2. **Prioritize** — rank issues by impact and urgency.
3. **Evaluate** — generate 2–4 options with cost/benefit/risk.
4. **Choose** — pick best option, respecting budget/capacity/authority.
5. **Explain** — state action, rationale (1–2 sentences), expected impact.
6. **Record** — add to agent's decision history.

If no material decision is required:
```text
Engineer 1 → NO_ACTION
No material decision. Continuing: API rate limiting fix (60% complete).
```

### Phase 2: Agent Reactions

After all agents decide, agents who acted later can react to earlier decisions:
```text
CMO → "Onboarding conversion too low for scaling acquisition."
CTO → "Engineering can allocate 2 days to onboarding next step."
CEO → "Approved. Delay analytics dashboard by 1 step."
```
Keep reactions concise — no unnecessary dialogue.

### Phase 3: Conflict Resolution

The LLM checks for conflicts after all decisions:

| Conflict type | Resolution |
|---------------|------------|
| Resource (over-budget/capacity) | Higher authority wins; lower-priority deferred |
| Authority (exceeds limits) | Escalate to manager agent |
| Priority (competing for same resource) | Higher-priority agent gets it; other re-prioritized |
| Dependency (A needs B's work) | B's decision takes precedence; A adjusts timeline |

### Phase 4: Decision Resolution

The LLM applies all resolved decisions and their consequences to state.

### Decision Output Format

```text
[Agent Name] ([Role]) [Acting: Role(s) if applicable]
→ [Action / NO_ACTION / INVALID_RESPONSE]

Situation: [brief description]
Options considered:
  A) [action] — cost: [X], benefit: [Y], risk: [Z]
  B) [alternative]
Chosen: [A or B, or "none" for NO_ACTION]
Rationale: [1-2 sentences]
Expected: [estimate with confidence: low|medium|high]
Confidence: [low|medium|high]

Consequences:
- [state change 1]
- [state change 2]
```

### Decision Scheduling

Not every agent decides every step. The LLM checks:
1. Are there open issues in the agent's responsibility area?
2. Does the agent have available capacity?
3. Is there a conflict or dependency requiring input?

If no material decision: declare `NO_ACTION` with rationale.

### Decision Constraints
- Cannot spend more than available cash or approved budget.
- Cannot assign more work than total available capacity.
- Spending that makes `cash < 0` is forbidden.
- Acting outside authority = escalation required.

---

## 5. Systems

Each system governs a domain of company operations. The LLM consults the relevant system when resolving agent decisions.

### 5.1 Finance System

**Cash flow**: `daily_burn = expenses_per_step - revenue_per_step`; `cash -= daily_burn` each step.
**Runway**: `runway_days = cash / daily_burn` (null if burn ≤ 0). Recompute every step.
**Expenses**: payroll (fixed), infrastructure (scales with users), marketing (variable), operations (fixed).
**Revenue**: from paying users, enterprise deals, partnerships.
**Health tiers**: Healthy (runway > 180d), At risk (90–180d), Critical (30–90d), Failed (< 30d or cash ≤ 0).

**Rules**: No overdraft. Payroll is fixed. Marketing spend is variable. Revenue lags by 1 step.

### 5.2 Product System

**Stages**: `idea → prototype → mvp → beta → launch → growth → mature → declining`.

| Stage | Readiness | Milestone |
|-------|-----------|-----------|
| idea | 0% | Problem identified |
| prototype | 10% | Concept validated |
| mvp | 40% | Usable product exists |
| beta | 70% | Released to early users |
| launch | 90% | Market-ready |
| growth | 95% + revenue > 0 | Scaling |
| mature | stable metrics | PMF achieved |

**Progress**: `product.progress = weighted_avg(feature.progress)`. Progress requires engineering work — it does NOT increase automatically.
**Quality**: `product.quality = avg(feature.quality) - technical_debt_penalty`. Quality affects churn and acquisition.
**Technical debt**: +0.01/step per incomplete feature. Each 0.1 debt reduces quality by 0.02 and slows work by 5%. Paydown: 2 capacity-days → -0.05 debt.
**Launch rules**: readiness ≥ 0.9, quality ≥ 0.3, no critical bugs.

### 5.3 Engineering System

**Capacity**: each engineer contributes ~1.0 per step (reduced by morale/productivity). Total capacity consumed ≤ available.
**Task types**: feature, bug, tech-debt, infrastructure, research.
**Task lifecycle**: todo → in_progress → blocked | completed | cancelled.
**Complexity**: small (0.5 cap), medium (1.0), large (2.0), epic (4.0+).
**Quality factors**: overloaded (1.1–1.5x) → quality × 0.8; severely overloaded (>1.5x) → quality × 0.5 + bug risk.
**Hiring lag**: 3–5 steps for new engineers to ramp up (50% capacity during onboarding).

### 5.4 Marketing System

**Funnel**: Awareness → Interest → Consideration → Conversion → Retention → Advocacy.
**Acquisition formula**: `acquisition = base × demand × product_factor × marketing_factor × brand_factor × price_factor`.
**Campaign lifecycle**: Plan → Execute → Measure → Optimize → Scale/Sunset.
**Channels**: Content (low CAC, slow), Paid ads (high CAC, fast), Referrals (very low CAC, needs PMF), Outbound (medium CAC).
**Brand strength**: starts 0.1, grows with campaigns and satisfaction, shrinks with quality issues.

### 5.5 Sales System

**Pipeline stages**: Lead → Qualified → Proposal → Negotiation → Won.
**Conversion**: each stage has ~40–70% base conversion, multiplied by `sales_effectiveness`.
**Activities**: prospecting (0.5 cap, +1–3 leads), qualifying (0.3 cap), demo (0.5 cap), proposal (0.3 cap), negotiation (0.5 cap).
**Enterprise deals**: 3–5 steps, high value, require discount approval.

### 5.6 Workforce System

**Lifecycle**: Candidate → Interviewing → Offered → Onboarding → Active → At risk → Resigned.
**Hiring**: sourcing (1–2 steps) → interviewing (1–2 steps) → offer (1 step) → onboarding (2 steps, 50% capacity).
**Morale**: drops from overload, lack of direction, conflicts. Rises from achievements, recognition, reasonable workload.
**Morale effects**: < 0.3 → 20% resignation risk/step; < 0.2 → 30% productivity loss.
**Turnover**: monitored as a metric; high turnover creates reputation risk.

### 5.7 Market System

**Variables**: demand, growth_rate, competition, sentiment, market_size. All 0.0–1.0 (except market_size).
**Segments**: Startup (500M TAM, high price sensitivity), SMB (2B, high sensitivity), Mid-Market (5B, medium), Enterprise (10B, low sensitivity).
**Drift**: demand ±0.03/step, competition ±0.02/step, sentiment ±0.03/step.
**Impact**: acquisition pressure = demand × sentiment × (1 - competition); churn pressure = competition × (1 - sentiment) + (1 - quality); pricing power = sentiment × brand × (1 - competition).

### 5.8 Competition System

Competitors are simplified profiles, not full simulations.

```yaml
competitors:
  - name: "ComplyWrite"
    strategy: low_cost           # low_cost | premium | growth | enterprise | balanced
    market_share: 0.25
    product_stage: beta
    monthly_spend: 50000
    key_strength: "larger team"
    key_weakness: "no AI features"
```

**Actions**: launch product (competition +0.10), price drop (competition +0.08), raise funding (competition +0.05), marketing campaign (competition +0.03), new feature (competition +0.04).
**Reactions**: your launch may trigger competitor launch; your price cut may trigger price war.

### 5.9 Fundraising System

**Pipeline**: Discover → Contact → Interested → Due Diligence → Offer → Invested.
**Investor types**: Friends & Family ($10K–100K), Angel ($25K–500K), Seed fund ($500K–2M), Series A ($2M–15M), Growth ($15M+).
**Valuation**: `pre_money = team_value + revenue × multiple + users × value - risks`.
**Dilution**: F&F (10–20%), Seed (15–25%), Series A (20–30%), Series B+ (15–25%).
**Constraints**: cannot raise while CRITICAL/FAILED health; takes 2–4 steps; over-valuation risks down round.

---

## 6. Events

Events are the atomic units of simulation change. Every state change produces an event.

### Event Format
```text
[day] EVENT_TYPE (severity) — [description]
  Consequences: [list state changes]
  Confidence: [low|medium|high]
```

### Event Categories
| Category | Source | Examples |
|----------|--------|----------|
| Internal | Agent decisions | hiring, launch, funding, risk |
| Interaction | Agent-to-agent | dependency signal, conflict, support offer |
| External | Market/system | market boom, competitor launch, customer surge |
| Financial | Finance system | burn increase, runway warning |
| Operational | Workforce/product | blocker, quality drop, morale decline |

### Event Probabilities (context-scaled)
Events scale with current state — they are NOT pure random:

| Event | Base probability | Scales with |
|-------|-----------------|-------------|
| Market boom | 2% | high sentiment |
| Market downturn | 2% | low sentiment |
| Competitor launch | 3% | your readiness > 0 |
| Competitor price drop | 2% | you losing market share |
| Customer surge | 3% | high demand + marketing |
| Customer decline | 3% | low demand + competition |
| Infrastructure cost | 2% | company age > 30 days |
| Regulatory pressure | 1% | market_size > 5000 |
| Tech shift | 2% | demand > 0.6 |

Keep last 10 events active; older ones compressed into strategic_memory.

---

## 7. Interaction Modes

The skill supports five modes. The LLM determines mode from user input.

### Autonomous Mode
```
User: "Run the next 7 days."
LLM: Runs the full simulation loop for 7 steps, then reports.
```

### Founder Mode
```
User: "What should I do?"
LLM: Presents 2–3 strategic options with trade-offs. User picks one.
```

### Advisory Mode
```
User: "Should we raise funding now?"
LLM: Analyzes state (runway, metrics, market) and advises yes/no with rationale.
```

### Scenario Mode
```
User: "What if we double marketing spend?"
LLM: Runs a counterfactual from current state. Reports projected trajectory.
Does NOT modify the primary state unless user says "make this change."
```

### Comparison Mode
```
User: "Compare hiring vs outsourcing development."
LLM: Evaluates both paths over 30 days. Reports pros/cons of each.
```

---

## 8. Output Format

Each simulation step produces a concise report showing all agent decisions as visible, independent actions.

```text
DAY 8 — NOVAFLOW AI

AGENT DECISIONS

Founder / CEO
→ Preserve runway and prioritize launch.

Engineer 1
→ Fix onboarding API failures.

Engineer 2
→ Improve onboarding UI.

Acting CMO — Founder
→ Convert waitlist users into beta testers.

CONFLICTS

None.

RESOLUTION

Engineering capacity remains focused on launch readiness.

CONSEQUENCES

  • Product readiness: 74% → 81%
  • Beta users: 120 → 185
  • Cash: $242,450 → $241,800

Company Health
  Cash: $241,800 | Runway: ~8 months | Burn: $4,200/day
  Product: 81% readiness | Quality: 0.55 | 0 critical bugs

Risks
  ⚠ Competitor price pressure

Next Priorities
  1. Fix onboarding conversion (blocking 12% of signups)
  2. Demonstrate first paying user
  3. Extend runway to 6+ months

State updated. [Save state]
```

Key output rules:
- Every agent's decision is listed under **AGENT DECISIONS**.
- Conflicts are listed under **CONFLICTS** (resolved or unresolved).
- **RESOLUTION** explains how conflicts were settled.
- **CONSEQUENCES** shows state changes from all decisions.
- Include `[Save state]` at the end.

---

## 9. Persistence

### Conversation-only (default)
State lives in the conversation. No files needed.

### Optional file persistence
```
State saved at Day 12:

```yaml
<current state block>
```

Copy this block to save. Later, say "Continue from this state" and paste it back.
```

### Resume
```
User: "Continue from this state."
<state block>
LLM: Loaded state from Day 12. Running next 7 days...
```

---

## 10. Uncertainty

The LLM must distinguish known from estimated:

- **Known**: state values the LLM set (cash, headcount, progress).
- **Estimated**: projected values (future revenue, churn rate, market shifts).
- **Assumed**: defaults when user doesn't specify (salary, market size).
- **Uncertain**: outcomes dependent on external factors.

Always express estimates as ranges with confidence:
```text
Expected acquisition: 15–25 users (confidence: medium)
```
Never present probabilistic outcomes as certainties.

---

## 11. Causal Reasoning

The LLM must trace cause-and-effect chains:

```text
Understaffed engineering → slower development → delayed launch → 
slower customer acquisition → lower revenue → runway pressure → 
survival risk
```

```text
Strong marketing → increased traffic → higher acquisition → 
more users → higher infrastructure costs → higher burn
```

Each decision's consequences must feed the next step's state. No disconnected events.

---

## 12. Realism Rules

1. **Resource constraints**: Cannot do everything simultaneously. Capacity and cash are finite.
2. **Time constraints**: Major initiatives take time. Hiring = 3–5 steps. Fundraising = 2–4 steps.
3. **Financial constraints**: Cash cannot go negative. Spending requires budget authority.
4. **Workforce constraints**: Employees have limited capacity. Overload reduces quality and morale.
5. **Strategic tradeoffs**: Choosing one priority delays another. The LLM must show the tradeoff.
6. **Dependencies**: Some actions require prerequisites (e.g., can't launch without MVP).
7. **Uncertainty**: Business outcomes are probabilistic. Use ranges and confidence levels.
8. **Competition**: Competitors respond to your moves. They are not static.
9. **Consequences**: Actions affect future state. Every decision has a traceable effect.

---

## 13. Outcomes

The simulation produces two terminal outcomes: **success** and **failure**.

### Success Conditions
| Outcome | Trigger |
|---------|---------|
| Product launch | Product reaches `launch` stage |
| Product-market fit | Paying users > 0 AND market_share > 0.05 for 5+ steps |
| Revenue growth | Monthly revenue > 10x starting revenue |
| Profitability | Daily burn ≤ 0 and revenue > 0 for 3+ steps |
| Fundraising | Fundraising target reached |
| Survival | Cash > 0 at Day 180+ |

### Failure Conditions
| Outcome | Trigger |
|---------|---------|
| Cash exhaustion | `cash <= 0` |
| Runway exhaustion | `runway_days < 7` |
| Failed launch | Launch stage but 0 paying users for 10+ steps |
| Persistent churn | Churn > 15% for 5+ steps |
| Product-market failure | Market share < 0.01 and paying users < 1 for 14+ steps |
| Operational collapse | 3+ resignations in 5 steps OR morale < 0.2 |

### Outcome Analysis
When the simulation ends, the LLM produces:
1. **Root cause**: Why it succeeded or failed.
2. **Key decisions**: 2–3 decisions that shaped the outcome.
3. **Warning signs**: Earlier indicators the company did or didn't act on.
4. **What could have changed it**: One counterfactual.

---

## 14. Examples

### Example 1: Startup
```
Create a company called NovaFlow AI.
Mission: Build an AI productivity platform.
Starting capital: $250,000
Team: 1 founder, 2 engineers
Objective: Launch within 60 days and reach 1,000 paying users
Market: Competitive AI productivity market
Start Day 0.
Simulate the next 7 days autonomously.
```

### Example 2: SaaS
```
Create a SaaS company called DataVault.
Mission: Secure data sharing for regulated industries.
Starting capital: $500,000
Team: 1 founder/CEO, 1 CTO, 1 engineer, 1 salesperson
Objective: Reach $50K MRR within 12 months
Market: Enterprise data management
```

### Example 3: Consumer Company
```
Create a consumer brand called Bloom & Co.
Mission: Sustainable home goods delivered monthly.
Starting capital: $100,000
Team: 1 founder, 1 marketer, 1 operations person
Objective: Reach 5,000 subscribers within 6 months
Market: Eco-conscious consumers
```

Full worked example: see `examples/simulations/nova-flow-ai.md`.

---

## 15. For Maintainers

The granular breakdown of this skill is in `skills/company-simulation/`:
- `core/` — simulation loop, state, decisions, events, progression, outcomes
- `roles/` — role definitions (founder, ceo, cto, cmo, engineer, salesperson, employee)
- `systems/` — domain systems (finance, product, engineering, marketing, sales, workforce, market, competition, fundraising)
- `schemas/` — data schemas (company-state, agent-state, decision, event)
- `examples/` — example company definitions

Validation tests: `tests/test_skill.py`
