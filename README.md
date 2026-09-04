# Agentic Company Simulator

### Portable LLM skill for multi-agent company simulation

Simulate companies, agents, finances, markets, and consequences — with any capable LLM. No backend, no database, no API keys.

[About](#about) · [Current Status](#current-status) · [Getting Started](#getting-started) · [Usage](#usage) · [Testing](#testing) · [Client-Neutral Integration](#client-neutral-integration) · [Repository Layout](#repository-layout) · [Contributing](#contributing) · [License](#license) · [Contact](#contact)

---

## About

Agentic Company Simulator is a portable [`SKILL.md`](SKILL.md) that, when loaded by a sufficiently capable LLM, transforms that model into an autonomous **multi-agent company operating system**.

The LLM acts as the simulation engine — initializing a company, orchestrating multiple independent agents, executing a day-by-day simulation loop, and advancing the company through time with causal consequences.

```
User task
  → Company initialization
  → Agent orchestration
  → Individual agent decisions
  → Agent interaction
  → Conflict resolution
  → State update
  → Next simulation period
```

This is **not** an AI chatbot that gives business advice. It is an LLM-powered company simulator where the LLM operates simulated employees, makes organizational decisions, resolves conflicts between agents, updates structured company state, and advances the company through time.

**Why this exists:**

- Traditional business simulators use simplistic fixed rules that don't capture organizational dynamics
- Most require a backend, database, or server infrastructure
- Generic business advice tools don't actually simulate a company's evolution over time
- Multi-agent decision-making, conflict resolution, and role delegation are not modelled
- Existing solutions conflate roles and people — this skill separates them

The LLM itself is the engine. The skill defines the rules, roles, systems, and structure. You provide the task.

---

## Current Status

| Component              | Status        |
| ---------------------- | ------------- |
| Core simulation skill  | Complete      |
| Multi-agent system     | Complete      |
| Company state model    | Complete      |
| Agent state model      | Complete      |
| Decision framework     | Complete      |
| Simulation systems     | 9             |
| Agent roles            | 7             |
| Validation tests       | 37 passing    |
| Runtime                | LLM-native    |
| Backend                | None          |
| Database               | None          |
| Client dependency      | Client-neutral |

---

## Built With

`Markdown` · `YAML` · `LLMs` · `Structured State` · `Multi-Agent Simulation`

---

# Getting Started

## Prerequisites

- **A capable LLM** — Claude 3.5+, GPT-4, Gemini 1.5+, or any model that can follow structured instructions and maintain state
- **A client** — Claude Code, Kilo Code, ChatGPT, Claude.ai, or any AI interface that accepts instructions
- **The `SKILL.md` file** — the single-file skill that defines the simulation

No Python, Node.js, Docker, or database setup is required. No API keys. No server to run.

## Installation

```bash
git clone https://github.com/UsmaanArshadKawoosa/agentic-company-simulator.git
```

Then open [`SKILL.md`](SKILL.md) and provide it to a compatible LLM.

The root `SKILL.md` is intentionally self-contained — you can load it into any LLM conversation and start simulating immediately, with no other files required.

---

# Usage

## Supported Simulation Modes

| Mode            | Purpose                                                  |
| --------------- | -------------------------------------------------------- |
| **Autonomous**  | LLM operates the company with minimal user intervention  |
| **Founder**     | User makes major company decisions; LLM simulates outcomes |
| **Advisory**    | User asks the simulated company for advice               |
| **Scenario**    | Explore hypothetical / counterfactual situations         |
| **Comparison**  | Compare strategic alternatives side-by-side              |

## Multi-Agent Simulation

The company is composed of simulated **agents** — each an independent decision-maker with role, authority, capacity, priorities, and decision history.

### Agents

Actual people inside the company. Each agent has a distinct role, specialization, and decision focus.

| Agent      | Role      | Focus                         |
| ---------- | --------- | ----------------------------- |
| Founder    | founder   | Survival, strategy, finance   |
| CEO        | ceo       | High-level direction          |
| CTO        | cto       | Engineering, architecture     |
| CMO        | cmo       | Marketing, growth, acquisition |
| Engineer 1 | engineer  | Implementation, frontend      |
| Engineer 2 | engineer  | Implementation, backend       |
| Salesperson| sales     | Leads, pipeline, conversion   |
| Employee   | employee  | Task execution                |

Each agent has: `role`, `authority` (1–10), `responsibilities` (primary + acting), `capacity`, `workload`, `priorities`, `decisions` (history), `morale`, `energy`, `specialization`, and `skills`.

### Roles / Functions

Organizational responsibilities — **a role does not automatically create a person**.

| Function       | Responsibility                        |
| -------------- | ------------------------------------- |
| Strategy       | Vision, mission, long-term direction  |
| Engineering    | Product development, architecture     |
| Marketing      | Brand, campaigns, growth              |
| Sales          | Pipeline, conversion, customer acquisition |
| Finance        | Cash, burn, runway, valuation         |
| Product        | Feature scope, quality, readiness     |

When a role is unassigned (e.g., no CTO hired), an existing agent can hold **acting** responsibility for that function:

```text
Avery (Founder / CEO) — Acting CTO
→ Decision about architecture trade-off

Avery (Founder / CEO) — Acting CMO
→ Decision about marketing channel allocation
```

When a dedicated CTO is hired later, the acting responsibility transfers to the new agent and the Founder returns to full-time strategy.

### Agent Behavior

Agents make independent decisions within their responsibility areas, then:

- **React** to decisions from other agents (dependency signals, shared-resource conflicts)
- **Disagree** on priorities, scope, or approach
- **Compete** for limited resources (budget, capacity, attention)
- **Escalate** issues beyond their authority
- **Resolve conflicts** through organizational hierarchy (acting authority, Founder override)

### NO_ACTION vs INVALID_RESPONSE

Not every agent makes a decision every step. Two distinct outcomes are encoded:

```text
Engineer 1 → NO_ACTION
  Rationale: No material decision required; continuing current task

Engineer 2 → INVALID_RESPONSE
  Rationale: LLM failed to produce a valid structured decision
```

`NO_ACTION` is a valid state — the agent assessed its situation and concluded no material decision is required. `INVALID_RESPONSE` indicates the LLM broke the decision contract and must be caught.

## Simulation Loop

Each simulation step follows a 17-phase loop. The LLM performs every step:

```
Observe → Market evolution → External events → Risk assessment
  → Individual agent decisions → Agent reactions → Conflict resolution
  → Decision resolution → Apply consequences → Work execution
  → Update product → Update customers → Financial processing → Metrics update
  → Outcome → State compression → Goal evaluation → Advance time
```

## Key Files

| File | Purpose |
| ---- | ------- |
| [`SKILL.md`](SKILL.md) | Root skill file — self-contained, load into any LLM |
| [`skills/company-simulation/SKILL.md`](skills/company-simulation/SKILL.md) | Modular skill entry point for maintainers |
| [`skills/company-simulation/core/`](skills/company-simulation/core/) | Simulation loop, state model, decision framework, events, outcomes, progression |
| [`skills/company-simulation/roles/`](skills/company-simulation/roles/) | 7 role definitions (Founder, CEO, CTO, CMO, Engineer, Salesperson, Employee) |
| [`skills/company-simulation/systems/`](skills/company-simulation/systems/) | 9 subsystems (Finance, Product, Engineering, Marketing, Sales, Workforce, Market, Competition, Fundraising) |
| [`skills/company-simulation/schemas/`](skills/company-simulation/schemas/) | State schemas (company state, agent state, decision, event) |
| [`skills/company-simulation/examples/`](skills/company-simulation/examples/) | Example company definitions (startup, SaaS, consumer) |
| [`examples/simulations/`](examples/simulations/) | Worked multi-agent simulations |
| [`examples/prompts/`](examples/prompts/) | Ready-to-use prompts |
| [`tests/test_skill.py`](tests/test_skill.py) | 37 validation tests |
| [`docs/`](docs/) | Usage, architecture, and development guides |

## State and Persistence

The LLM maintains company state as YAML in conversation. At any point:

```text
Save state.
```

The LLM outputs a state block. Copy it, then later:

```text
Continue from this state:
<YAML state block>
```

The LLM resumes from the exact saved point. State includes company finances, product metrics, market variables, agent attributes, and decision history.

## Example

```text
Create a startup called NovaFlow AI.
Starting capital: $250,000.
Team: 1 founder (Avery), 2 engineers (Casey, Remy).
Market: Competitive AI productivity space.
Objective: Launch within 30 days and reach 1,000 paying users.
Simulate the next 7 days autonomously.
```

**Day 1 — Independent decisions:**

```text
Avery (Founder / Acting CMO) → Launch no-code landing page
  Rationale: Validate demand before spending on engineering

Casey (Engineer 1, frontend) → Build landing page in plain HTML/CSS
  Rationale: Ship fast, no framework overhead

Remy (Engineer 2, backend) → Set up Railway free-tier backend + waitlist API
  Rationale: Free infrastructure covers MVP
```

**Day 3 — Agent reaction + conflict:**

Avery (Acting CTO) resolves a conflict between Casey and Remy over feature priority:

```text
Conflict: Casey wants UI polish; Remy wants auth API robustness.
Acting CTO (Avery) → Remy, prioritize auth API (correct call). Casey, polish can wait.
```

**Day 5 — NO_ACTION:**

```text
Avery (Founder) → NO_ACTION on hiring
  Rationale: Product not shipped; adding payroll without proven demand is wasteful
```

See [`examples/simulations/nova-flow-ai.md`](examples/simulations/nova-flow-ai.md) for the full 7-day simulation demonstrating consequence chains, acting responsibilities, and conflict resolution.

---

# Testing

```bash
python tests/test_skill.py
```

**37 tests, 37 passing.**

Tests validate:

| Category | What is checked |
| -------- | --------------- |
| Structure  | All required files exist, YAML frontmatter present |
| Sections   | Root `SKILL.md` and modular skill cover all required sections |
| Systems    | All 9 subsystems documented |
| Roles      | All 7 agent roles defined with authority levels |
| Simulation | 17-step loop, all phases present |
| State      | Company state schema covers all domains + invariants |
| Agents     | Agent state schema distinguishes agents vs roles, covers acting responsibilities |
| Decisions  | NO_ACTION / INVALID_RESPONSE distinction, decision scheduling |
| Multi-agent behavior | Independent decisions, agent reactions, conflict resolution, consequence chains |
| Examples   | Simulations demonstrate failure risk, multi-agent dynamics |
| Cleanup    | No obsolete infrastructure references (no FastAPI, PostgreSQL, React, Docker, etc.) |

---

# Client-Neutral Integration

The skill is designed to be client-neutral. It works with:

- **Claude** / Claude Code
- **ChatGPT** / GPT-4
- **Gemini** 1.5+
- **Kilo Code**
- **other compatible AI coding/agent clients**

The core simulation instructions in `SKILL.md` are independent of any specific AI client. No client-specific plugins or adapters are required — only a capable LLM that can follow structured instructions and maintain state.

The repository does not require a specific provider, runtime, or API key. It contains no backend, database, or server components.

---

# Repository Layout

```
.
├── SKILL.md                          ← THE PRODUCT (single-file, self-contained)
├── skills/company-simulation/
│   ├── SKILL.md                      ← Modular skill entry point
│   ├── core/                         ← 6 files (simulation, state, decisions, events, outcomes, progression)
│   ├── roles/                        ← 7 role definitions (founder, ceo, cto, cmo, engineer, salesperson, employee)
│   ├── systems/                      ← 9 subsystems (finance, product, engineering, marketing, sales, workforce, market, competition, fundraising)
│   ├── schemas/                      ← 4 state schemas (company, agent, decision, event)
│   └── examples/                     ← 3 example company definitions (startup, SaaS, consumer)
├── examples/
│   ├── prompts/                      ← 1 ready-to-use prompt (nova-flow-ai)
│   └── simulations/                  ← 2 worked simulations (nova-flow-ai, secureflow-saas)
├── docs/                             ← usage.md, architecture.md, skill-development.md
├── tests/
│   └── test_skill.py                 ← 37 validation tests
├── README.md
└── LICENSE
```

---

# Contributing

Contributions are welcome. Fork the repo, create a feature branch, and open a PR.

1. Fork the Project
2. `git checkout -b feature/YourFeature`
3. Make changes to skill content
4. Run tests: `python tests/test_skill.py`
5. Commit: `git commit -m 'Add some feature'`
6. Push: `git push origin feature/YourFeature`
7. Open a Pull Request

---

# License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

---

## Acknowledgments

Thanks to the open-source LLM ecosystem and simulation / game theory / business simulation concepts that informed this design.

---

## Contact

- **Issues:** [GitHub Issues](https://github.com/UsmaanArshadKawoosa/agentic-company-simulator/issues)
- **Repository:** [GitHub](https://github.com/UsmaanArshadKawoosa/agentic-company-simulator)