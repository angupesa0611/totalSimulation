"""Audit log helper — fire-and-forget write to results.audit_log table."""

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def write_audit(
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    username: str | None = None,
    details: dict | None = None,
) -> None:
    """Write an audit log entry. Never raises — logs errors silently."""
    try:
        from db.engine import sync_session_factory
        from db.models.results import AuditLog

        session = sync_session_factory()
        try:
            entry = AuditLog(
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                username=username,
                details=details,
                created_at=datetime.now(timezone.utc),
            )
            session.add(entry)
            session.commit()
        finally:
            session.close()
    except Exception:
        logger.debug("Failed to write audit log: %s %s %s", action, entity_type, entity_id)
