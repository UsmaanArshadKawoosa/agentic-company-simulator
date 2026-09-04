# Agentic Company Simulator

A portable LLM skill that turns any capable language model into an **autonomous company simulation engine**. Simulate startups, SaaS companies, consumer brands, and more — no code, no servers, no databases.

[![Skill](https://img.shields.io/badge/Skill-portable-blue)](SKILL.md)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## What Is It?

Agentic Company Simulator is a single downloadable `SKILL.md` file that you provide to your LLM. Once loaded, the LLM becomes a company operating system — capable of:

- **Initializing a company** from a natural-language description
- **Simulating autonomous agents** (Founder, CEO, CTO, CMO, Engineer, Salesperson)
- **Running the simulation loop** day by day with realistic decisions
- **Tracking finances, product, market, and workforce** in structured state
- **Responding to competitor actions and market events**
- **Simulating success or failure** based on real causal chains

No Python. No Node.js. No Docker. No PostgreSQL. No API keys.

Just your LLM + this skill.

---

## Quick Start

```text
1. Download SKILL.md
2. Give it to your LLM (Claude, GPT-4, Gemini, etc.)
3. Describe your company
4. Start simulation
```

### Example

```
Create a startup called NovaFlow AI.
Mission: Build an AI productivity platform.
Starting capital: $250,000
Team: 1 founder, 2 engineers
Objective: Launch within 60 days and reach 1,000 paying users
Market: Competitive AI productivity market
```

Then:

```
Simulate the next 7 days.
```

The LLM outputs a concise daily report showing company health, agent decisions, consequences, risks, and next priorities.

See [`examples/prompts/nova-flow-ai.md`](examples/prompts/nova-flow-ai.md) for a ready-to-use prompt.

---

## How It Works

```
SKILL.md                  ← You download this
   ↓
Your LLM                 ← Claude, GPT-4, Gemini, etc.
   ↓
Company State (YAML)     ← Maintained in conversation
   ↓
Agents (roles)           ← Founder, CEO, CTO, CMO, Engineer, ...
   ↓
Decisions              ← Structured: observe → evaluate → choose → resolve
   ↓
Consequences           ← Applied to state with causal chains
   ↓
Evolving Company       ← Finance, product, market, workforce change over time
```

Each simulation step follows a 15-phase loop: market evolution → agent decisions → work execution → financial processing → risk detection → goal evaluation → outcome assessment.

---

## Interaction Modes

| Mode | How to use | What it does |
|------|-----------|--------------|
| **Autonomous** | `Simulate the next 7 days.` | LLM runs the company independently |
| **Founder** | `What should I do today?` | LLM presents options; you choose |
| **Advisory** | `Should we raise funding?` | LLM analyzes state and advises |
| **Scenario** | `What if we double marketing?` | LLM simulates counterfactuals |
| **Comparison** | `Compare hiring vs outsourcing.` | LLM evaluates both paths |

---

## State & Persistence

The LLM maintains company state as YAML in the conversation. At any point you can:

```text
Save state.
```

The LLM outputs a state block. Copy it, then later:

```text
Continue from this state:
<state block>
```

The LLM resumes the simulation from the saved point.

---

## Repository Structure

```text
agentic-company-simulator/
├── SKILL.md                          ← THE PRODUCT (download this)
├── skills/company-simulation/        ← Modular reference for maintainers
│   ├── SKILL.md                      ← Modular entry point
│   ├── core/                         ← Simulation loop, state, decisions
│   ├── roles/                        ← Agent role definitions
│   ├── systems/                      ← Finance, product, market, etc.
│   ├── schemas/                      ← State schemas
│   └── examples/                     ← Example company definitions
├── examples/
│   ├── prompts/                      ← Ready-to-use prompts
│   └── simulations/                  ← Worked simulation examples
│       ├── nova-flow-ai.md           ← 10-day startup simulation
│       └── secureflow-saas.md        ← 30-day SaaS simulation
├── docs/
│   ├── usage.md                      ← User guide
│   ├── architecture.md               ← Design principles
│   └── skill-development.md          ← Maintainer guide
├── tests/
│   └── test_skill.py                 ← Skill validation
└── README.md
```

---

## Full Example: NovaFlow AI (10-Day Simulation)

See [`examples/simulations/nova-flow-ai.md`](examples/simulations/nova-flow-ai.md) for a complete 10-day worked simulation showing:

- Agent decisions with rationale
- Product development (idea → beta → launch-ready features)
- Competitor response (SwiftTask AI launch)
- Customer acquisition (waitlist → beta → paying users)
- Financial tracking (cash burn, runway, first revenue)
- Risk detection and mitigation
- State compression and continuation

---

## What the Skill Simulates

| Domain | What's tracked |
|--------|---------------|
| **Founders & Executives** | CEO, CTO, CMO authority, decisions, priorities |
| **Engineering** | Capacity, tasks, features, technical debt, bugs |
| **Marketing** | Campaigns, brand strength, acquisition funnel |
| **Sales** | Pipeline, conversion, CAC, LTV |
| **Finance** | Cash, burn, runway, revenue, valuation |
| **Product** | Stages, progress, quality, readiness |
| **Workforce** | Hiring, onboarding, morale, turnover |
| **Market** | Demand, competition, sentiment, segments |
| **Competition** | Competitor actions, market share |
| **Fundraising** | Investor pipeline, valuation, dilution |
| **Risk & Incidents** | Detection, escalation, resolution |
| **Events** | Contextual, consequential market events |

---

## Validation

```bash
python tests/test_skill.py
```

Tests verify:
- `SKILL.md` exists and contains required sections
- All referenced supporting files exist
- No broken cross-references
- State schema covers all required domains
- All 7 agent roles are defined
- All 9 systems are documented
- Example simulations demonstrate key mechanics

---

## License

MIT
