import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from router import router
from render_router import render_router
from sweep_router import sweep_router
from export_router import export_router
from auth_router import auth_router
from websocket.manager import ws_router
from logging_config import setup_logging
from metrics import metrics_router
from config import settings
from auth import get_current_user

setup_logging()
logger = logging.getLogger(__name__)


def _recover_stale_jobs():
    """Scan all projects for results stuck in RUNNING/PENDING and mark INTERRUPTED."""
    import results as results_store
    from celery.result import AsyncResult
    from celery_app import app as celery_app

    recovered = 0
    for project in results_store.list_projects():
        for entry in results_store.list_results(project):
            status = entry.get("status")
            if status not in ("RUNNING", "PENDING"):
                continue

            job_id = entry.get("job_id")
            if not job_id:
                continue

            # Check Celery for actual state
            try:
                ar = AsyncResult(job_id, app=celery_app)
                celery_status = ar.status
            except Exception:
                celery_status = "UNKNOWN"

            if celery_status in ("SUCCESS", "FAILURE", "REVOKED"):
                continue

            # Mark as interrupted
            results_store.update_result_status(
                job_id, project, "INTERRUPTED",
                error="Server restarted while job was in progress",
            )
            recovered += 1
            logger.info(
                "Recovered stale job",
                extra={"job_id": job_id, "tool": entry.get("tool", "unknown")},
            )

    if recovered:
        logger.info("Startup recovery: marked %d stale jobs as INTERRUPTED", recovered)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    _recover_stale_jobs()
    logger.info("totalSimulation API started")
    yield
    # Shutdown
    logger.info("totalSimulation API shutting down")


app = FastAPI(title="totalSimulation", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AuthMiddleware(BaseHTTPMiddleware):
    """Protect /api/ routes with JWT when AUTH_ENABLED=true."""

    SKIP_PREFIXES = ("/health", "/api/auth/", "/results-files/", "/ws/")

    async def dispatch(self, request: Request, call_next):
        if not settings.auth_enabled:
            return await call_next(request)

        path = request.url.path

        if request.method == "OPTIONS":
            return await call_next(request)

        if any(path.startswith(p) for p in self.SKIP_PREFIXES):
            return await call_next(request)

        if not path.startswith("/api/"):
            return await call_next(request)

        auth_header = request.headers.get("authorization")
        try:
            get_current_user(auth_header)
        except ValueError as e:
            return JSONResponse(
                status_code=401,
                content={"detail": str(e)},
            )

        return await call_next(request)


app.add_middleware(AuthMiddleware)

# Auth router registered before AuthMiddleware so /api/auth/* is always accessible
app.include_router(auth_router)
app.include_router(router)
app.include_router(render_router)
app.include_router(sweep_router)
app.include_router(export_router)
app.include_router(metrics_router)
app.include_router(ws_router)
app.mount("/results-files", StaticFiles(directory="/data/results"), name="results-files")


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0"}
