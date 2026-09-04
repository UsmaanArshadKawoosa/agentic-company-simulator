# Architecture

## Overview

The Agentic Company Simulator is a **portable LLM skill** — a single markdown file that transforms any capable LLM into an autonomous company simulation engine.

```
SKILL.md
   ↓
Your LLM (Claude, GPT-4, Gemini, etc.)
   ↓
Company State (YAML, maintained in conversation)
   ↓
Agents (simulated roles: Founder, CEO, CTO, CMO, Engineer, ...)
   ↓
Decisions (structured)
   ↓
Consequences (applied to state)
   ↓
Evolving Company
```

## Design Principles

### 1. No Infrastructure
The skill runs entirely in the LLM. No database, no server, no runtime. State is maintained as structured text in the conversation.

### 2. Deterministic Where Possible
Given the same initial state and seed, the LLM should produce the same market evolution and event probabilities. Agent decisions may vary between runs (no two CEOs decide identically), but the framework is consistent.

### 3. Causal Chains
Every decision has traceable consequences. Market changes affect acquisition. Acquisition affects revenue. Revenue affects cash. Cash affects runway. Runway affects strategy. The LLM must trace these chains.

### 4. Role Authority
Agents cannot act outside their authority. A CMO cannot launch a product. An engineer cannot approve a budget. This prevents the "god agent" problem where any role can do anything.

### 5. Resource Constraints
Companies cannot do everything simultaneously:
- Cash limits spending.
- Engineering capacity limits speed.
- Employee bandwidth limits simultaneous initiatives.
- Time limits ambitious goals.

### 6. State Compression
For long simulations, old history is compressed into strategic memory. Current state + key decisions + major events are retained; daily minutiae is summarized.

## State Model

The complete state is defined in Section 2 of `SKILL.md` (root) and `schemas/company-state.md`. Key domains:

- **company**: identity, stage, time
- **finance**: cash, burn, runway, valuation
- **product**: stage, progress, quality, technical debt
- **market**: demand, competition, sentiment, segments
- **workforce**: employees, capacity, morale
- **goals**: primary, secondary, progress
- **risks**: active risks with severity
- **events**: recent event log
- **history**: decisions, milestones, strategic memory

## Skill Structure

```
SKILL.md                                    ← Self-contained product (THE DOWNLOAD)
skills/company-simulation/                  ← Modular reference for maintainers
├── SKILL.md                               ← Modular entry point
├── core/                                  ← Simulation logic
│   ├── simulation.md                     ← Loop, time granularities
│   ├── state.md                          ← State lifecycle, invariants
│   ├── decision-making.md                ← Decision process
│   ├── events.md                         ← Event system
│   ├── progression.md                    ← Product stages
│   └── outcomes.md                       ← Success/failure conditions
├── roles/                                 ← Agent role definitions
│   ├── founder.md, ceo.md, cto.md, cmo.md, engineer.md, salesperson.md, employee.md
├── systems/                               ← Domain systems
│   ├── finance.md, product.md, engineering.md, marketing.md,
│   │   sales.md, workforce.md, market.md, competition.md, fundraising.md
├── schemas/                               ← Data schemas
│   ├── company-state.md, agent-state.md, decision.md, event.md
└── examples/                              ← Example company definitions
    ├── startup.md, saas.md, consumer-company.md
examples/                                  ← End-user examples
├── prompts/                               ← Ready-to-use prompts
│   ├── nova-flow-ai.md
tests/                                     ← Validation tests
└── test_skill.py
```

## Why This Architecture?

The old architecture (FastAPI + React + PostgreSQL + Docker) required:
- Python runtime, Node.js, PostgreSQL
- Docker compose orchestration
- API keys for deployment
- Server management

The new architecture requires only:
- A chat interface to a capable LLM
- This single skill file

All simulation logic that was previously in ~226 Python files is now encoded as structured instructions in the skill. The LLM performs the computation that SQLAlchemy queries and Python functions once did.
