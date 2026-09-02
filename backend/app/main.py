import logging
import time
import uuid
from contextvars import ContextVar
from contextlib import asynccontextmanager

import asyncio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.api import agents, companies, scenarios, simulation, websocket as ws_router, workforce, operations
from app.config import settings
from app.db.database import create_db_and_tables

# ---------------------------------------------------------------------------
# Structured logging
# ---------------------------------------------------------------------------
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = getattr(record, "request_id", request_id_ctx.get() or "-")
        return True


logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s [%(request_id)s] %(name)s: %(message)s",
)
logger = logging.getLogger("agent_company_simulator")
logger.addFilter(RequestIdFilter())

# ---------------------------------------------------------------------------
# Store the main event loop so background tasks (e.g. WebSocket broadcasts)
# can be scheduled from synchronous endpoint handlers running in threadpool.
# ---------------------------------------------------------------------------
_main_loop: asyncio.AbstractEventLoop | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _main_loop
    _main_loop = asyncio.get_running_loop()
    try:
        create_db_and_tables()
        logger.info("Database tables ensured.")
    except Exception as exc:
        logger.warning("Could not create database tables on startup: %s", exc)
    yield


app = FastAPI(title=settings.PROJECT_NAME, version="0.1.0", lifespan=lifespan)


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request ID + duration middleware
# ---------------------------------------------------------------------------
class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        token = request_id_ctx.set(req_id)
        request.state.request_id = req_id
        start = time.perf_counter()
        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start) * 1000
            logger.info(
                "%s %s -> %s (%.1fms)",
                request.method,
                request.url.path,
                response.status_code,
                duration_ms,
            )
            response.headers["X-Request-ID"] = req_id
            return response
        except Exception as exc:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.error(
                "%s %s -> 500 (%.1fms) error=%s",
                request.method,
                request.url.path,
                duration_ms,
                exc,
            )
            raise


app.add_middleware(RequestIdMiddleware)


# ---------------------------------------------------------------------------
# Health / Readiness
# ---------------------------------------------------------------------------


@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "ok", "service": settings.PROJECT_NAME}


@app.get("/ready", tags=["health"])
def readiness(request: Request) -> dict:
    from sqlalchemy import text
    from app.db.database import engine
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as exc:
        logger.error("Readiness DB check failed: %s", exc)
        db_status = "error"

    status = "ok" if db_status == "ok" else "error"
    return {
        "status": status,
        "service": settings.PROJECT_NAME,
        "request_id": request.state.request_id,
        "database": db_status,
    }


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(companies.router, prefix=settings.API_PREFIX)
app.include_router(agents.router, prefix=settings.API_PREFIX)
app.include_router(scenarios.router, prefix=settings.API_PREFIX)
app.include_router(simulation.router, prefix=settings.API_PREFIX)
app.include_router(workforce.router, prefix=settings.API_PREFIX)
app.include_router(operations.router, prefix=settings.API_PREFIX)
app.include_router(ws_router.router, prefix=settings.API_PREFIX)
