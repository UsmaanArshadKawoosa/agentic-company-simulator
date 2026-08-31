# Agent Company Simulator

An AI-powered company simulation where autonomous AI employees operate inside a
simulated company with goals, tasks, hierarchy, resources, decisions, and an
evolving environment.

This repository currently implements **Phase 1: Project Foundation** — a clean,
production-quality foundation that later phases build on. It includes a working
backend (FastAPI + SQLAlchemy + Pydantic), a minimal frontend shell
(React + TypeScript + Vite + Tailwind), and a test suite.

> **Phase 1 scope note:** No autonomous behavior or LLM calls are implemented
> yet. The agent lifecycle (`observe/think/decide/act/reflect`), the simulation
> engine, and the LLM service are present but return deterministic placeholder
> results. An extension point for WebSockets is intentionally left for later.

## Architecture

```
backend/                 FastAPI application
  app/
    main.py             App entrypoint, CORS, router registration
    config.py           Settings (pydantic-settings)
    enums.py            Domain enums (roles, statuses, event types)
    api/               REST routers (companies, agents, simulation)
    agents/            Agent abstraction + CEO/CTO/CMO/Engineer
    simulation/        Engine, state, events, scheduler
    services/          LLM service, decisions, memory
    models/            SQLAlchemy ORM models (8 tables)
    db/                Engine, session, Base, model registry
    schemas/           Pydantic v2 schemas
  tests/               pytest suite (backend)
frontend/              React + TypeScript + Vite + Tailwind shell
docker-compose.yml     PostgreSQL service
```

### Database tables

`companies`, `agents`, `goals`, `projects`, `tasks`, `events`, `decisions`,
`memories`. Relationships use foreign keys (`company_id`, `manager_id`,
`project_id`, `created_by`, `assigned_to`, `actor_id`, `agent_id`). JSON
fields (`personality`, `skills`, `meta`, `context`) are stored as JSON/JSONB.

## Prerequisites

- Python 3.11+
- Node.js 18+ (Node 20+ recommended)
- PostgreSQL (optional for local dev — SQLite works without it)

## 1. Backend setup

```bash
cd backend

# Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1      # Windows (PowerShell)
# source .venv/bin/activate       # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
```

Edit `.env` and set `DATABASE_URL`. The default expects PostgreSQL:

```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/agent_company
```

To develop without PostgreSQL, use SQLite instead:

```
DATABASE_URL=sqlite:///./agent_company.db
```

## 2. Start PostgreSQL

With Docker:

```bash
docker compose up -d          # starts PostgreSQL on :5432
```

Without Docker, install PostgreSQL locally and create a database named
`agent_company` with user/password `postgres`/`postgres` (or update `.env`).

Tables are created automatically on backend startup.

## 3. Start the backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

- API base: `http://localhost:8000/api`
- Interactive docs: `http://localhost:8000/docs`

## 4. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

The dev server runs on `http://localhost:5173` and proxies `/api` to the
backend on port `8000`.

To build for production:

```bash
npm run build      # outputs to frontend/dist
```

## 5. Run tests

```bash
cd backend
.\.venv\Scripts\Activate.ps1
pytest
```

The backend test suite runs against a temporary SQLite database, so PostgreSQL
is **not** required to run the tests. It covers company creation, automatic
agent seeding, the agent hierarchy, simulation start/pause/tick, event
persistence, API endpoints, and database relationships.

## API reference

### Companies

| Method | Path                              | Description                     |
| ------ | --------------------------------- | ------------------------------- |
| POST   | `/api/companies`                  | Create a company (+ 4 agents)   |
| GET    | `/api/companies/{company_id}`    | Get a company                   |
| GET    | `/api/companies/{company_id}/agents` | List the company's agents    |
| GET    | `/api/companies/{company_id}/events` | List the company's events   |

### Simulation

| Method | Path                                 | Description                |
| ------ | ------------------------------------ | -------------------------- |
| POST   | `/api/simulation/{company_id}/start` | Start the simulation       |
| POST   | `/api/simulation/{company_id}/pause` | Pause the simulation       |
| POST   | `/api/simulation/{company_id}/tick`  | Advance one deterministic day |
| GET    | `/api/simulation/{company_id}`       | Get current simulation state |

When a company is created, the initial organization is seeded automatically:

```
CEO
├── CTO
│    └── Engineer
└── CMO
```

represented via `manager_id` (not hardcoded UI logic). Default starting values:
`cash=100000`, `revenue=0`, `expenses=0`, `current_day=1`, `status=CREATED`.

## Implementation notes

- **Enums** (`AgentRole`, `AgentStatus`, `TaskStatus`, `CompanyStatus`, …) are
  strongly typed and used throughout the domain instead of raw strings.
- **`BaseAgent`** defines `observe/think/decide/act/reflect`. `CEOAgent`,
  `CTOAgent`, `CMOAgent`, and `EngineerAgent` subclass it.
- **`SimulationEngine`** exposes `start/pause/tick/get_state` and supports a
  single deterministic tick without an LLM.
- **`LLMService`** is an abstraction (`generate` / `structured_generate`); the
  current `NoOpLLMService` returns placeholders so no provider is called yet.
- The reserved SQL Alchemy attribute name `metadata` is avoided; the events
  table column is `metadata` but the ORM/schema attribute is named `meta`.

## Next phases

Phase 2+ will introduce real LLM-driven agent behavior, autonomous task
execution, decision-making, memory/learning, and (optionally) WebSocket-based
real-time updates.
