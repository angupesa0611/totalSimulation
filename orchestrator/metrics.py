"""Redis-backed metrics for simulation tracking."""

import logging
from fastapi import APIRouter
from config import settings

logger = logging.getLogger(__name__)
metrics_router = APIRouter(prefix="/api")

_redis = None


def _get_redis():
    global _redis
    if _redis is None:
        import redis
        _redis = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    return _redis


def increment_simulation(tool: str):
    """Increment simulation counter for a tool."""
    try:
        r = _get_redis()
        r.hincrby("metrics:simulations_by_tool", tool, 1)
        r.incr("metrics:simulations_total")
    except Exception:
        logger.debug("Failed to update metrics", exc_info=True)


def increment_sweep():
    """Increment sweep counter."""
    try:
        _get_redis().incr("metrics:sweeps_total")
    except Exception:
        logger.debug("Failed to update metrics", exc_info=True)


def increment_pipeline(pipeline_type: str = "sequential"):
    """Increment pipeline counter."""
    try:
        r = _get_redis()
        r.hincrby("metrics:pipelines_by_type", pipeline_type, 1)
        r.incr("metrics:pipelines_total")
    except Exception:
        logger.debug("Failed to update metrics", exc_info=True)


def increment_export(format: str):
    """Increment export counter."""
    try:
        _get_redis().hincrby("metrics:exports_by_format", format, 1)
    except Exception:
        logger.debug("Failed to update metrics", exc_info=True)


@metrics_router.get("/metrics")
def get_metrics() -> dict:
    """Return current metrics."""
    try:
        r = _get_redis()
        return {
            "simulations_total": int(r.get("metrics:simulations_total") or 0),
            "simulations_by_tool": r.hgetall("metrics:simulations_by_tool"),
            "sweeps_total": int(r.get("metrics:sweeps_total") or 0),
            "pipelines_total": int(r.get("metrics:pipelines_total") or 0),
            "pipelines_by_type": r.hgetall("metrics:pipelines_by_type"),
            "exports_by_format": r.hgetall("metrics:exports_by_format"),
        }
    except Exception:
        return {"error": "Metrics unavailable — Redis connection failed"}
