"""Admin endpoints — toggle tools/layers/couplings/pipelines, reload cache, audit log."""

import logging
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, desc

from db.registry_service import (
    toggle_tool, toggle_layer, toggle_coupling, toggle_pipeline,
    invalidate_cache,
)
from db.engine import sync_session_factory
from db.models.results import AuditLog
from db.audit import write_audit

logger = logging.getLogger(__name__)

admin_router = APIRouter(prefix="/api/admin", tags=["admin"])


@admin_router.post("/tools/{key}/toggle")
def toggle_tool_endpoint(key: str, enabled: bool = True) -> dict:
    """Enable or disable a tool."""
    if not toggle_tool(key, enabled):
        raise HTTPException(404, f"Tool '{key}' not found")
    logger.info("Tool %s toggled: enabled=%s", key, enabled)
    write_audit("toggle", "tool", entity_id=key, details={"enabled": enabled})
    return {"key": key, "enabled": enabled}


@admin_router.post("/layers/{key}/toggle")
def toggle_layer_endpoint(key: str, enabled: bool = True) -> dict:
    """Enable or disable a layer."""
    if not toggle_layer(key, enabled):
        raise HTTPException(404, f"Layer '{key}' not found")
    logger.info("Layer %s toggled: enabled=%s", key, enabled)
    write_audit("toggle", "layer", entity_id=key, details={"enabled": enabled})
    return {"key": key, "enabled": enabled}


@admin_router.post("/couplings/{key}/toggle")
def toggle_coupling_endpoint(key: str, enabled: bool = True) -> dict:
    """Enable or disable a coupling."""
    if not toggle_coupling(key, enabled):
        raise HTTPException(404, f"Coupling '{key}' not found")
    logger.info("Coupling %s toggled: enabled=%s", key, enabled)
    write_audit("toggle", "coupling", entity_id=key, details={"enabled": enabled})
    return {"key": key, "enabled": enabled}


@admin_router.post("/pipelines/{key}/toggle")
def toggle_pipeline_endpoint(key: str, enabled: bool = True) -> dict:
    """Enable or disable a pipeline."""
    if not toggle_pipeline(key, enabled):
        raise HTTPException(404, f"Pipeline '{key}' not found")
    logger.info("Pipeline %s toggled: enabled=%s", key, enabled)
    write_audit("toggle", "pipeline", entity_id=key, details={"enabled": enabled})
    return {"key": key, "enabled": enabled}


@admin_router.get("/registry/reload")
def reload_registry() -> dict:
    """Force reload the registry cache from DB."""
    invalidate_cache()
    return {"status": "reloaded"}


@admin_router.get("/audit-log")
def get_audit_log(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    action: str | None = None,
    entity_type: str | None = None,
) -> dict:
    """Retrieve recent audit log entries."""
    session = sync_session_factory()
    try:
        stmt = select(AuditLog)
        if action:
            stmt = stmt.where(AuditLog.action == action)
        if entity_type:
            stmt = stmt.where(AuditLog.entity_type == entity_type)
        stmt = stmt.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit)

        rows = session.execute(stmt).scalars().all()
        entries = []
        for row in rows:
            entries.append({
                "id": row.id,
                "action": row.action,
                "entity_type": row.entity_type,
                "entity_id": row.entity_id,
                "username": row.username,
                "details": row.details,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            })
        return {"entries": entries, "offset": offset, "limit": limit}
    finally:
        session.close()
