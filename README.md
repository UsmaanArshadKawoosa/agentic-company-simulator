# Agent Company Simulator

An AI-powered company simulation platform where autonomous AI agents operate inside a simulated company — complete with organizational hierarchy, goals, tasks, resources, decision-making, and an evolving market environment.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Node.js](https://img.shields.io/badge/Node.js-18+-green.svg)](https://nodejs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Overview

Agent Company Simulator is a full-stack application that models a company as a multi-agent system. Each company is staffed with AI agents — a CEO, CTO, CMO, and Engineer — who observe their environment, make decisions, execute actions, and learn from outcomes. The simulation advances through discrete time steps ("days"), during which market conditions evolve, customers are acquired and churn, products are developed, and the financial state of the company changes in response to agent actions.

The project is designed as a platform for exploring autonomous agent behavior in a business context. Researchers, developers, and strategists can use it to test decision-making frameworks, observe emergent organizational dynamics, or prototype AI-driven management systems. The deterministic simulation engine ensures reproducible runs, while the pluggable LLM abstraction allows swapping between placeholder logic and real language model providers (Anthropic, OpenAI).

The backend is built on FastAPI with SQLAlchemy ORM, exposing a comprehensive REST API and WebSocket endpoint for real-time updates. The frontend is a React + TypeScript application with Tailwind CSS, providing a command-center dashboard to monitor and control simulations. The entire system is containerized with Docker and includes a comprehensive test suite with 364 tests.

## Key Features

### Autonomous Agent Lifecycle
Each agent follows a complete observe → think → decide → act → reflect cycle. Agents perceive their environment through structured context, formulate decisions via LLM (or deterministic fallback), execute validated actions against company state, and persist memories for future reference.

### Hierarchical Organization
Companies are seeded with a realistic org chart: CEO → CTO → Engineer, and CEO → CMO. Each agent has defined authority levels, budgets, salaries, personality traits, and skill sets that influence their decision-making.

### Deterministic Simulation Engine
The simulation advances day-by-day with fully deterministic behavior given the same seed. Market evolution, customer acquisition/churn, financial calculations, and agent decisions all derive from a seeded RNG, enabling reproducible experiments.

### Real-Time WebSocket Updates
A WebSocket endpoint streams simulation events to connected clients in real-time — including agent decisions, market changes, risk detections, and financial summaries — enabling live dashboards without polling.

### Comprehensive Domain Model
The system models 34 database entities including companies, agents, goals, projects, tasks, events, decisions, memories, customers, competitors, campaigns, sales opportunities, employees, funding rounds, investors, risks, incidents, and objectives.

### Financial Intelligence
Full financial modeling with revenue, expenses, cash flow, runway calculations, burn rate tracking, valuation estimation, fundraising pipeline management, cap table tracking, and budget request workflows.

### Market Simulation
Dynamic market segments (SMB, Mid-Market, Enterprise, Startup) with evolving demand, competition, and sentiment. Competitor agents with distinct strategies (Low-Cost, Premium, Growth, Enterprise) compete for market share.

### Risk & Incident Management
Automatic risk detection based on company state (low cash runway, quality crises, customer churn spikes), with escalation paths and incident resolution workflows.

### Workforce Management
Employee lifecycle from candidate generation through hiring, onboarding, performance evaluation, and termination. Morale, productivity, and capacity tracking by role.

### LLM Provider Abstraction
Pluggable LLM service interface with implementations for NoOp (deterministic placeholders), Mock (scripted test behavior), and Real (Anthropic/OpenAI with retry logic and JSON parsing).

## How It Works

```
User creates company via Frontend
         ↓
Frontend calls POST /api/companies
         ↓
Backend seeds organization (CEO, CTO, CMO, Engineer)
         ↓
User starts simulation
         ↓
SimulationEngine.tick() advances day:
    1. Market evolution (demand, competition, sentiment)
    2. Environmental events (market boom/downturn, competitor actions)
    3. Task execution (engineer capacity consumed)
    4. Product progress (features, milestones, quality)
    5. Customer acquisition/churn
    6. Financial processing (revenue, expenses, cash)
    7. Risk detection and incident creation
    8. Agent cycles (observe/think/decide/act/reflect)
    9. Goal evaluation
    10. Company success/failure assessment
         ↓
Events broadcast via WebSocket
         ↓
Frontend updates dashboard in real-time
```

### Simulation Tick Detail

Each tick represents one simulated day. The engine processes systems in a fixed order to ensure determinism:

1. **Market System** — evolves demand, competition, sentiment using seeded RNG
2. **Segment System** — updates market segment dynamics
3. **Competitor System** — evolves competitor strategies and market positions
4. **Environmental Events** — generates random events (market boom, competitor launch, etc.)
5. **Task Blocking** — updates task dependency state
6. **Workforce** — updates onboarding, morale, productivity, performance
7. **Work Execution** — engineers complete assigned tasks
8. **Milestones & Projects** — updates progress, calculates product readiness
9. **Product** — updates features, quality, technical debt
10. **Marketing** — processes campaign spend and completion
11. **Sales** — advances opportunities through pipeline stages
12. **Market Share** — recalculates based on competitive position
13. **Customers** — acquisition and churn based on product quality/marketing
14. **Economy** — processes revenue, expenses, updates cash
15. **Financial Health** — calculates runway, burn rate, financial health score
16. **Fundraising** — updates investor pipeline
17. **Risk Detection** — identifies new risks from company state
18. **Incident Detection** — creates incidents from critical risks
19. **Expectations** — evaluates previous decision expectations
20. **Plans** — advances active plans based on step completion
21. **Objectives** — updates objective progress
22. **Attention** — computes management attention metrics
23. **Decision Quality** — evaluates pending decisions
24. **Agent Cycles** — each agent runs observe/think/decide/act/reflect
25. **Goals** — evaluates goal progress
26. **Outcomes** — assesses company success/failure conditions

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ CommandCenter│  │ CreateCompany│  │    Simulation Page     │  │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘  │
│         │                │                      │                │
│  ┌──────┴────────────────┴──────────────────────┴─────────────┐  │
│  │                    Custom Hooks                             │  │
│  │  ┌──────────────────┐  ┌────────────────────────────────┐  │  │
│  │  │ useSimulation()  │  │      useWebSocket()            │  │  │
│  │  └──────────────────┘  └────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                              │                                   │
│  ┌───────────────────────────┴────────────────────────────────┐  │
│  │                      API Client                             │  │
│  └───────────────────────────┬────────────────────────────────┘  │
└──────────────────────────────┼───────────────────────────────────┘
                               │ HTTP / WebSocket
┌──────────────────────────────┼───────────────────────────────────┐
│                        Backend (FastAPI)                         │
│  ┌───────────────────────────┴────────────────────────────────┐  │
│  │                      API Routers                            │  │
│  │  ┌──────────┐ ┌────────────┐ ┌───────────┐ ┌───────────┐  │  │
│  │  │companies │ │ simulation │ │operations │ │ workforce │  │  │
│  │  └──────────┘ └────────────┘ └───────────┘ └───────────┘  │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │                   websocket                          │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                              │                                   │
│  ┌───────────────────────────┴────────────────────────────────┐  │
│  │                   Core Services                             │  │
│  │  ┌──────────────────┐  ┌────────────────────────────────┐  │  │
│  │  │ SimulationEngine │  │     LLMService (Abstract)      │  │  │
│  │  └──────────────────┘  └────────────────────────────────┘  │  │
│  │  ┌──────────────────┐  ┌────────────────────────────────┐  │  │
│  │  │  Agent Base      │  │     DecisionValidator          │  │  │
│  │  └──────────────────┘  └────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                              │                                   │
│  ┌───────────────────────────┴────────────────────────────────┐  │
│  │              Simulation Systems (40+ modules)               │  │
│  │  economy  market  customers  product  sales  marketing     │  │
│  │  workforce  strategy  pricing  competitors  risks          │  │
│  │  incidents  objectives  resources  priority  attention     │  │
│  │  financial_health  fundraising  capital  valuation         │  │
│  │  plans  expectations  communication  memory  adaptation    │  │
│  └────────────────────────────────────────────────────────────┘  │
│                              │                                   │
│  ┌───────────────────────────┴────────────────────────────────┐  │
│  │                   Data Layer                                │  │
│  │  ┌──────────────────┐  ┌────────────────────────────────┐  │  │
│  │  │   SQLAlchemy     │  │       Pydantic Schemas         │  │  │
│  │  │   ORM Models     │  │       (Validation)             │  │  │
│  │  └──────────────────┘  └────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────┼───────────────────────────────────┘
                               │
┌──────────────────────────────┼───────────────────────────────────┐
│                        Database                                  │
│  ┌───────────────────────────┴────────────────────────────────┐  │
│  │              PostgreSQL (production)                        │  │
│  │              SQLite (development/testing)                   │  │
│  └────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Backend Structure

| Module | Purpose |
|--------|---------|
| `app/api/` | REST routers for companies, agents, simulation, operations, workforce, WebSocket |
| `app/agents/` | Agent abstraction, role implementations (CEO/CTO/CMO/Engineer), context building, decision validation |
| `app/simulation/` | 40+ simulation systems handling economy, market, customers, product, sales, etc. |
| `app/services/` | LLM service abstraction, decision service, memory service, real-time broadcaster |
| `app/models/` | 34 SQLAlchemy ORM models with relationships |
| `app/schemas/` | Pydantic v2 schemas for request/response validation |
| `app/db/` | Database engine, session management, base model |
| `app/enums/` | 50+ domain enums for type safety |

### Frontend Structure

| Module | Purpose |
|--------|---------|
| `src/pages/` | CommandCenter (dashboard), CreateCompany, Simulation pages |
| `src/components/` | AgentCard, CompanyDashboard, Metrics, OrgChart, ActivityFeed |
| `src/hooks/` | useSimulation (API polling), useWebSocket (real-time updates) |
| `src/api/` | Typed API client for all backend endpoints |
| `src/types/` | TypeScript type definitions matching backend schemas |

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | React 18 + TypeScript | UI framework with type safety |
| Frontend | Vite 5 | Build tool and dev server |
| Frontend | Tailwind CSS 3 | Utility-first styling |
| Backend | FastAPI 0.110+ | Async Python web framework |
| Backend | SQLAlchemy 2.0+ | ORM with async support |
| Backend | Pydantic 2.5+ | Data validation and serialization |
| Backend | Uvicorn | ASGI server |
| Database | PostgreSQL 16 | Production database |
| Database | SQLite | Development and testing |
| AI/ML | Anthropic Claude | LLM provider (optional) |
| AI/ML | OpenAI GPT | LLM provider (optional) |
| Testing | pytest 8.0+ | Backend test suite |
| Testing | httpx | Async HTTP client for testing |
| Infrastructure | Docker | Containerization |
| Infrastructure | docker-compose | Multi-service orchestration |

## Getting Started

### Prerequisites

- **Python 3.11+** — required for modern type hints and performance
- **Node.js 18+** (20+ recommended) — frontend runtime
- **PostgreSQL 16** — optional; SQLite works without it
- **Docker** — optional; for running PostgreSQL container

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd agent-company-simulator
```

#### Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1      # Windows (PowerShell)
# source .venv/bin/activate       # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
```

Edit `.env` to configure your database:

```env
# For PostgreSQL (recommended for production)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/agent_company

# For SQLite (zero-config development)
DATABASE_URL=sqlite:///./agent_company.db
```

#### Frontend Setup

```bash
cd frontend
npm install
```

### Running the Application

#### Start PostgreSQL (if using)

```bash
# From the project root
docker compose up -d
```

Tables are created automatically on backend startup.

#### Start the Backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

- API base: `http://localhost:8000/api`
- Interactive docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

#### Start the Frontend

```bash
cd frontend
npm run dev
```

The dev server runs on `http://localhost:5173` and proxies `/api` to the backend.

### Running Tests

```bash
cd backend
pytest
```

The test suite runs against SQLite by default — no PostgreSQL required. It covers:
- Company creation and organization seeding
- Agent hierarchy and lifecycle
- Simulation engine (start/pause/tick/resume)
- All simulation systems (economy, market, customers, product, etc.)
- API endpoints and WebSocket
- Database relationships and constraints
- Determinism verification

## API Reference

### Companies

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/companies` | Create a company (+ seed 4 agents) |
| GET | `/api/companies/{company_id}` | Get company details |
| GET | `/api/companies/{company_id}/agents` | List company agents |
| GET | `/api/companies/{company_id}/events` | List company events |
| GET | `/api/companies/{company_id}/customers` | List company customers |
| GET | `/api/companies/{company_id}/metrics` | Get financial/market/product metrics |

### Simulation

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/simulation/{company_id}/start` | Start simulation |
| POST | `/api/simulation/{company_id}/pause` | Pause simulation |
| POST | `/api/simulation/{company_id}/tick` | Advance one day |
| POST | `/api/simulation/{company_id}/resume` | Resume continuous simulation |
| POST | `/api/simulation/{company_id}/speed` | Set simulation speed |
| GET | `/api/simulation/{company_id}` | Get current state |
| GET | `/api/simulation/{company_id}/dashboard` | Get comprehensive dashboard |
| GET | `/api/simulation/{company_id}/timeline` | Get event timeline |
| GET | `/api/simulation/{company_id}/plans` | List plans |
| GET | `/api/simulation/{company_id}/messages` | List messages |
| GET | `/api/simulation/{company_id}/expectations` | List expectations |
| GET | `/api/simulation/{company_id}/agent-metrics` | Get agent performance |
| GET | `/api/simulation/{company_id}/market` | Get market segments |
| GET | `/api/simulation/{company_id}/competitors` | Get competitors |
| GET | `/api/simulation/{company_id}/strategy` | Get strategy state |
| GET | `/api/simulation/{company_id}/campaigns` | Get campaigns |
| GET | `/api/simulation/{company_id}/sales` | Get sales pipeline |
| GET | `/api/simulation/{company_id}/financials` | Get financial metrics |
| GET | `/api/simulation/{company_id}/valuation` | Get company valuation |
| GET | `/api/simulation/{company_id}/investors` | Get investors |
| GET | `/api/simulation/{company_id}/funding-rounds` | Get funding rounds |
| GET | `/api/simulation/{company_id}/pipeline` | Get fundraising pipeline |
| GET | `/api/simulation/{company_id}/cap-table` | Get cap table |
| GET | `/api/simulation/{company_id}/budget-requests` | Get budget requests |

### Operations (Phase 11)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/operations/companies/{company_id}/objectives` | List objectives |
| POST | `/api/operations/companies/{company_id}/objectives` | Create objective |
| PATCH | `/api/operations/companies/{company_id}/objectives/{id}` | Update objective |
| GET | `/api/operations/companies/{company_id}/risks` | List risks |
| POST | `/api/operations/companies/{company_id}/risks` | Create risk |
| PATCH | `/api/operations/companies/{company_id}/risks/{id}` | Update risk |
| GET | `/api/operations/companies/{company_id}/incidents` | List incidents |
| POST | `/api/operations/companies/{company_id}/incidents` | Create incident |
| PATCH | `/api/operations/companies/{company_id}/incidents/{id}` | Update incident |
| GET | `/api/operations/companies/{company_id}/resources` | List resource allocations |
| POST | `/api/operations/companies/{company_id}/resources` | Allocate resource |

### Workforce (Phase 9)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/workforce/companies/{company_id}/employees` | List employees |
| POST | `/api/workforce/companies/{company_id}/employees` | Hire employee |
| GET | `/api/workforce/companies/{company_id}/jobs` | List job openings |
| POST | `/api/workforce/companies/{company_id}/jobs` | Create job opening |
| GET | `/api/workforce/companies/{company_id}/candidates` | List candidates |
| GET | `/api/workforce/companies/{company_id}/workforce` | Get workforce summary |

### WebSocket

Connect to `ws://localhost:8000/api/ws/companies/{company_id}` for real-time events:

- `connection.established` — sent on connect
- `simulation.started` / `simulation.paused` — simulation state changes
- `simulation.tick` — day advanced with summary
- `agent.decision` — agent action taken
- `risk.detected` — new risk identified
- `incident.created` — new incident
- `objective.created` — new objective
- `resource.allocated` — resource allocated
- `priority.changed` — management attention update
- `pong` — response to ping

## Configuration

All configuration is via environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | PostgreSQL | Database connection string |
| `LLM_PROVIDER` | `noop` | LLM provider: `noop`, `mock`, `anthropic`, `openai` |
| `LLM_MODEL` | Provider default | Model identifier |
| `LLM_API_KEY` | — | Provider API key |
| `LLM_MAX_TOKENS` | 1024 | Max response tokens |
| `LLM_TEMPERATURE` | 0.0 | Sampling temperature |
| `LLM_TIMEOUT` | 30 | Request timeout (seconds) |
| `CORS_ORIGINS` | localhost:5173 | Allowed CORS origins |

## Example Usage

### Create and Run a Simulation

```bash
# Create a company
curl -X POST http://localhost:8000/api/companies \
  -H "Content-Type: application/json" \
  -d '{"name": "Acme Corp", "mission": "Build AI-powered tools"}'

# Start the simulation
curl -X POST http://localhost:8000/api/simulation/1/start

# Advance one day
curl -X POST http://localhost:8000/api/simulation/1/tick

# Get current state
curl http://localhost:8000/api/simulation/1

# Get dashboard
curl http://localhost:8000/api/simulation/1/dashboard
```

### WebSocket Client (JavaScript)

```javascript
const ws = new WebSocket('ws://localhost:8000/api/ws/companies/1');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data.type, data);
};

ws.onopen = () => {
  // Send ping
  ws.send(JSON.stringify({ type: 'ping', timestamp: Date.now() }));
};
```

## Current Capabilities

- **Phase 1**: Project foundation, database schema, basic API
- **Phase 2**: Agent hierarchy, organization seeding, event system
- **Phase 3**: Market simulation, customer acquisition/churn, financial processing
- **Phase 4**: Task execution, milestones, product features, work capacity
- **Phase 5**: Agent autonomy, plans, expectations, communication, memory, adaptation
- **Phase 6**: Market segments, competitors, campaigns, sales pipeline, pricing, PMF
- **Phase 7**: LLM integration, structured decisions, prompt engineering, observability
- **Phase 8**: Dashboard, command center, real-time updates
- **Phase 9**: Workforce management, hiring, performance, candidates
- **Phase 10**: Financial intelligence, fundraising, investors, cap table, valuation
- **Phase 11**: Objectives, resources, risks, incidents, priority, attention

## Limitations

- **Default LLM is NoOp**: Without configuring a real LLM provider, agents take deterministic placeholder actions. Set `LLM_PROVIDER=anthropic` or `LLM_PROVIDER=openai` with a valid API key for autonomous behavior.
- **Single-company focus**: The engine is optimized for simulating one company at a time. Multi-company scenarios require running separate instances.
- **Simplified physics**: Market dynamics, customer behavior, and financial models are simplified abstractions — not intended for real business planning.
- **No persistence of learned state**: Agent memories are stored in the database but sophisticated learning/retrieval is limited to importance-based filtering.

## Future Enhancements

- **Enhanced LLM Integration**: Richer prompts, multi-turn reasoning, tool use
- **Multi-Company Simulation**: Cross-company competition and market dynamics
- **Advanced Learning**: Agent skill improvement, strategy adaptation over time
- **Scenario Library**: Pre-built scenarios (startup growth, turnaround, market entry)
- **Export/Import**: Save and share simulation configurations and results
- **Analytics**: Post-simulation analysis, decision quality metrics, outcome attribution
- **Custom Agent Roles**: User-defined roles with custom behaviors and authority
- **Visualization**: Charts for financial trends, market share, org dynamics

## License

MIT
