import logging
from contextlib import asynccontextmanager

import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import agents, companies, simulation, websocket as ws_router, workforce, operations
from app.config import settings
from app.db.database import create_db_and_tables

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent_company_simulator")

# Store the main event loop so background tasks (e.g. WebSocket broadcasts)
# can be scheduled from synchronous endpoint handlers running in threadpool.
_main_loop: asyncio.AbstractEventLoop | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _main_loop
    _main_loop = asyncio.get_running_loop()
    try:
        create_db_and_tables()
        logger.info("Database tables ensured.")
    except Exception as exc:  # pragma: no cover - depends on live DB
        logger.warning("Could not create database tables on startup: %s", exc)
    yield


app = FastAPI(title=settings.PROJECT_NAME, version="0.1.0", lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(companies.router, prefix=settings.API_PREFIX)
app.include_router(agents.router, prefix=settings.API_PREFIX)
app.include_router(simulation.router, prefix=settings.API_PREFIX)
app.include_router(workforce.router, prefix=settings.API_PREFIX)
app.include_router(operations.router, prefix=settings.API_PREFIX)
app.include_router(ws_router.router, prefix=settings.API_PREFIX)


@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "ok", "service": settings.PROJECT_NAME}
