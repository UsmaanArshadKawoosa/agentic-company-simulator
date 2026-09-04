# Usage Guide

## What You Need

- A chat interface to a capable LLM (Claude, GPT-4, Gemini, etc.)
- This skill file (`SKILL.md`)
- ~10–30 minutes for a meaningful simulation

No Python. No Node.js. No database. No API keys. No servers.

## Installation

1. Download `SKILL.md` from this repository.
2. Open your LLM chat interface (Claude Code, ChatGPT, Claude.ai, etc.).
3. Provide `SKILL.md` as context (upload/file attach or paste).
4. Describe your company (see examples below).
5. Start the simulation.

## Starting a Simulation

### Basic
```
Create a startup called NovaFlow AI.
Mission: Build an AI productivity platform.
Starting capital: $250,000
Team: 1 founder, 2 engineers
Objective: Launch within 60 days and reach 1,000 paying users
Market: Competitive AI productivity market
```

The LLM will initialize the state and begin day 1 automatically.

### Running Autonomously
```
Simulate the next 7 days.
```
or
```
Run the company until launch.
```
or
```
Simulate 12 months.
```

### Interacting with the Simulation

**Founder Mode** (you control the founder):
```
What should I do today?
```
The LLM presents options. You choose.

**Advisory Mode** (ask for advice):
```
Should we raise funding now?
```
The LLM analyzes state and advises.

**Scenario Mode** (what-if):
```
What if we double marketing spend?
```
The LLM runs a counterfactual (doesn't modify primary state).

**Comparison Mode**:
```
Compare hiring engineers vs outsourcing development.
```
The LLM evaluates both paths.

## Saving and Resuming

The LLM outputs a state block at the end of each session. To save:

1. Copy the state block (YAML format).
2. Save to a file: `company-state.yaml`
3. Paste back and say: "Continue from this state."

```
Continue from this state:

company:
  name: "NovaFlow AI"
  day: 10
  ...
```

## Tips

- Use daily granularity for the first 10 days, then switch to weekly.
- The 60-day launch objective is aggressive; manage scope tightly.
- Competitor responses happen automatically — don't ignore them.
- Cash is the ultimate constraint — watch runway daily.
- Beta test before public launch to catch critical bugs.
