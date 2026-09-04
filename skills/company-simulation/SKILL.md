---
name: company-simulation
description: >
  Modular breakdown of the Agentic Company Simulator skill. See root SKILL.md
  for the self-contained version.
version: 1.0.0
parent: ../SKILL.md
---

# Company Simulation Skill (Modular Reference)

This directory contains the granular breakdown of the [Agentic Company Simulator](/) skill. The root `SKILL.md` is the self-contained version; this modular structure is for maintainers who want to edit individual components.

## Structure

| Directory | Contents |
|-----------|----------|
| `core/` | Simulation loop, state model, decision framework, events, progression, outcomes |
| `roles/` | Role definitions: Founder, CEO, CTO, CMO, Engineer, Salesperson, Employee |
| `systems/` | Domain systems: Finance, Product, Engineering, Marketing, Sales, Workforce, Market, Competition, Fundraising |
| `schemas/` | Data schemas: Company State, Agent State, Decision, Event |
| `examples/` | Example company definitions |

## How It Maps to the Root SKILL.md

| Section | Root SKILL.md | This module |
|---------|--------------|-------------|
| Simulation Loop | §1 | `core/simulation.md` |
| State Model | §2 | `schemas/company-state.md` |
| Agent System | §3 | `roles/*.md` |
| Decision Framework | §4 | `core/decision-making.md` |
| Finance System | §5.1 | `systems/finance.md` |
| Product System | §5.2 | `systems/product.md` |
| Engineering | §5.3 | `systems/engineering.md` |
| Marketing | §5.4 | `systems/marketing.md` |
| Sales | §5.5 | `systems/sales.md` |
| Workforce | §5.6 | `systems/workforce.md` |
| Market | §5.7 | `systems/market.md` |
| Competition | §5.8 | `systems/competition.md` |
| Fundraising | §5.9 | `systems/fundraising.md` |
| Events | §6 | `core/events.md` |
| Interaction Modes | §7 | (covered in root) |
| Output Format | §8 | (covered in root) |
| Outcomes | §10 | `core/outcomes.md` |
| Progression | — | `core/progression.md` |

## Usage

- **End users**: Use the root `SKILL.md` only.
- **Maintainers**: Edit files in this directory, then sync changes to the root `SKILL.md`.
- **Validation**: Run `tests/test_skill.py` to check integrity.

See `docs/skill-development.md` for contribution guidelines.
