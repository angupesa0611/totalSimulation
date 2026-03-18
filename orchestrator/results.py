"""Simulation results storage — dual-write: metadata to PostgreSQL + files to disk.

Large result payloads (result.json) stay on the filesystem. Metadata and
search indexes live in the results.simulation_runs table.
"""

import json
import logging
import os
import shutil
from datetime import datetime, timezone

from sqlalchemy import select, func, desc, asc

from config import settings
from db.engine import sync_session_factory
from db.models.results import Project, SimulationRun

logger = logging.getLogger(__name__)


def _get_or_create_project(session, project_name: str) -> Project:
    """Get existing project or create it."""
    project = session.execute(
        select(Project).where(Project.name == project_name)
    ).scalar_one_or_none()
    if not project:
        project = Project(name=project_name, created_at=datetime.now(timezone.utc))
        session.add(project)
        session.flush()
    return project


def get_results_dir(project: str = "_default") -> str:
    path = os.path.join(settings.results_dir, project)
    os.makedirs(path, exist_ok=True)
    return path


def save_result(job_id: str, tool: str, data: dict, project: str = "_default",
                label: str | None = None, duration: float | None = None,
                params: dict | None = None, status: str = "SUCCESS",
                error: str | None = None) -> str:
    """Save simulation result to disk AND DB. Returns the result directory path."""
    results_dir = get_results_dir(project)
    run_dir = os.path.join(results_dir, f"{job_id}")
    os.makedirs(run_dir, exist_ok=True)

    data_str = json.dumps(data)
    params_summary = json.dumps(params)[:200] if params else None
    now = datetime.now(timezone.utc)

    metadata = {
        "job_id": job_id,
        "tool": tool,
        "project": project,
        "label": label,
        "timestamp": now.isoformat(),
        "status": status,
        "duration_s": duration,
        "params_summary": params_summary,
        "result_size_bytes": len(data_str),
        "error": error,
    }
    with open(os.path.join(run_dir, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    with open(os.path.join(run_dir, "result.json"), "w") as f:
        f.write(data_str)

    # Also update legacy _index.json for backward compat
    _update_index(project, metadata)

    # Write to DB
    try:
        session = sync_session_factory()
        try:
            proj = _get_or_create_project(session, project)

            existing = session.execute(
                select(SimulationRun).where(SimulationRun.job_id == job_id)
            ).scalar_one_or_none()

            if existing:
                existing.status = status
                existing.duration_s = duration
                existing.error = error
                existing.result_size_bytes = len(data_str)
                existing.result_path = run_dir
                if status in ("SUCCESS", "FAILURE", "CANCELLED", "INTERRUPTED"):
                    existing.completed_at = now
            else:
                run = SimulationRun(
                    job_id=job_id,
                    project_id=proj.id,
                    tool_key=tool,
                    label=label,
                    status=status,
                    params_summary=params_summary,
                    duration_s=duration,
                    error=error,
                    result_path=run_dir,
                    result_size_bytes=len(data_str),
                    created_at=now,
                    completed_at=now if status in ("SUCCESS", "FAILURE") else None,
                )
                session.add(run)
            session.commit()
        finally:
            session.close()
    except Exception:
        logger.exception("Failed to write result metadata to DB (file write succeeded)")

    return run_dir


def _update_index(project: str, entry: dict) -> None:
    """Append or update entry in project's _index.json (legacy)."""
    results_dir = get_results_dir(project)
    index_path = os.path.join(results_dir, "_index.json")

    index = []
    if os.path.exists(index_path):
        with open(index_path) as f:
            index = json.load(f)

    existing = next((i for i, e in enumerate(index) if e.get("job_id") == entry["job_id"]), None)
    if existing is not None:
        index[existing] = entry
    else:
        index.append(entry)

    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)


def delete_result(job_id: str, project: str = "_default") -> bool:
    """Delete a result directory, remove from _index.json, and delete from DB."""
    results_dir = get_results_dir(project)
    run_dir = os.path.join(results_dir, job_id)

    found = False
    if os.path.exists(run_dir):
        shutil.rmtree(run_dir)
        found = True

    # Remove from legacy index
    index_path = os.path.join(results_dir, "_index.json")
    if os.path.exists(index_path):
        with open(index_path) as f:
            index = json.load(f)
        index = [e for e in index if e.get("job_id") != job_id]
        with open(index_path, "w") as f:
            json.dump(index, f, indent=2)

    # Remove from DB
    try:
        session = sync_session_factory()
        try:
            run = session.execute(
                select(SimulationRun).where(SimulationRun.job_id == job_id)
            ).scalar_one_or_none()
            if run:
                session.delete(run)
                session.commit()
                found = True
        finally:
            session.close()
    except Exception:
        logger.exception("Failed to delete result from DB")

    return found


def update_result_status(job_id: str, project: str = "_default",
                         status: str = "SUCCESS", error: str | None = None) -> bool:
    """Update the status of an existing result (file + DB)."""
    results_dir = get_results_dir(project)
    meta_path = os.path.join(results_dir, job_id, "metadata.json")

    found = False
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            metadata = json.load(f)
        metadata["status"] = status
        if error is not None:
            metadata["error"] = error
        with open(meta_path, "w") as f:
            json.dump(metadata, f, indent=2)
        _update_index(project, metadata)
        found = True

    # Update DB
    try:
        session = sync_session_factory()
        try:
            run = session.execute(
                select(SimulationRun).where(SimulationRun.job_id == job_id)
            ).scalar_one_or_none()
            if run:
                run.status = status
                if error is not None:
                    run.error = error
                if status in ("SUCCESS", "FAILURE", "CANCELLED", "INTERRUPTED"):
                    run.completed_at = datetime.now(timezone.utc)
                session.commit()
                found = True
        finally:
            session.close()
    except Exception:
        logger.exception("Failed to update result status in DB")

    return found


def search_results(project: str = "_default", query: str | None = None,
                   tool_filter: str | None = None, status_filter: str | None = None,
                   sort: str = "newest", offset: int = 0,
                   limit: int = 20) -> dict:
    """Search and filter results from DB with pagination."""
    session = sync_session_factory()
    try:
        proj = session.execute(
            select(Project).where(Project.name == project)
        ).scalar_one_or_none()
        if not proj:
            return {"results": [], "total": 0, "offset": offset, "limit": limit}

        stmt = select(SimulationRun).where(SimulationRun.project_id == proj.id)

        if tool_filter:
            stmt = stmt.where(SimulationRun.tool_key == tool_filter)
        if status_filter:
            stmt = stmt.where(SimulationRun.status == status_filter)
        if query:
            q = f"%{query}%"
            stmt = stmt.where(
                SimulationRun.label.ilike(q) |
                SimulationRun.tool_key.ilike(q) |
                SimulationRun.job_id.ilike(q) |
                SimulationRun.params_summary.ilike(q)
            )

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = session.execute(count_stmt).scalar()

        # Sort
        if sort == "newest":
            stmt = stmt.order_by(desc(SimulationRun.created_at))
        elif sort == "oldest":
            stmt = stmt.order_by(asc(SimulationRun.created_at))
        elif sort == "tool":
            stmt = stmt.order_by(asc(SimulationRun.tool_key))

        stmt = stmt.offset(offset).limit(limit)
        rows = session.execute(stmt).scalars().all()

        results = []
        for run in rows:
            results.append({
                "job_id": run.job_id,
                "tool": run.tool_key,
                "project": project,
                "label": run.label,
                "timestamp": run.created_at.isoformat() if run.created_at else None,
                "status": run.status,
                "duration_s": run.duration_s,
                "params_summary": run.params_summary,
                "result_size_bytes": run.result_size_bytes,
                "error": run.error,
            })

        return {"results": results, "total": total, "offset": offset, "limit": limit}
    finally:
        session.close()


def get_result_files(job_id: str, project: str = "_default") -> list[dict] | None:
    """List files in a result directory."""
    results_dir = get_results_dir(project)
    run_dir = os.path.join(results_dir, job_id)

    if not os.path.exists(run_dir):
        return None

    files = []
    for name in sorted(os.listdir(run_dir)):
        filepath = os.path.join(run_dir, name)
        if os.path.isfile(filepath):
            files.append({
                "name": name,
                "size_bytes": os.path.getsize(filepath),
            })
    return files


def get_result_file_path(job_id: str, filename: str,
                         project: str = "_default") -> str | None:
    """Get absolute path of a file in a result directory."""
    results_dir = get_results_dir(project)
    filepath = os.path.join(results_dir, job_id, filename)

    # Prevent path traversal
    real_path = os.path.realpath(filepath)
    real_base = os.path.realpath(os.path.join(results_dir, job_id))
    if not real_path.startswith(real_base):
        return None

    if not os.path.isfile(filepath):
        return None
    return filepath


def list_projects() -> list[str]:
    """List all projects from DB (with filesystem fallback)."""
    session = sync_session_factory()
    try:
        rows = session.execute(
            select(Project.name).order_by(Project.name)
        ).scalars().all()
        if rows:
            return list(rows)
    except Exception:
        pass
    finally:
        session.close()

    # Fallback to filesystem
    base = settings.results_dir
    if not os.path.exists(base):
        return ["_default"]
    projects = []
    for name in sorted(os.listdir(base)):
        if os.path.isdir(os.path.join(base, name)) and not name.startswith("."):
            projects.append(name)
    if not projects:
        projects = ["_default"]
    return projects


def create_project(name: str) -> bool:
    """Create a new project (DB + directory)."""
    results_dir = get_results_dir(name)
    index_path = os.path.join(results_dir, "_index.json")
    if not os.path.exists(index_path):
        with open(index_path, "w") as f:
            json.dump([], f)

    session = sync_session_factory()
    try:
        existing = session.execute(
            select(Project).where(Project.name == name)
        ).scalar_one_or_none()
        if existing:
            return False
        project = Project(name=name, created_at=datetime.now(timezone.utc))
        session.add(project)
        session.commit()
        return True
    except Exception:
        session.rollback()
        return False
    finally:
        session.close()


def delete_project(name: str) -> bool:
    """Delete a project and all its results (DB + disk)."""
    if name == "_default":
        return False

    # Delete from disk
    project_dir = os.path.join(settings.results_dir, name)
    if os.path.exists(project_dir):
        shutil.rmtree(project_dir)

    # Delete from DB
    session = sync_session_factory()
    try:
        project = session.execute(
            select(Project).where(Project.name == name)
        ).scalar_one_or_none()
        if not project:
            return os.path.exists(project_dir)  # Was on disk but not in DB
        # Delete associated runs first
        session.execute(
            SimulationRun.__table__.delete().where(SimulationRun.project_id == project.id)
        )
        session.delete(project)
        session.commit()
        return True
    except Exception:
        session.rollback()
        return False
    finally:
        session.close()


def get_result_metadata(job_id: str, project: str = "_default") -> dict | None:
    """Get metadata for a specific result (DB first, file fallback)."""
    session = sync_session_factory()
    try:
        run = session.execute(
            select(SimulationRun).where(SimulationRun.job_id == job_id)
        ).scalar_one_or_none()
        if run:
            return {
                "job_id": run.job_id,
                "tool": run.tool_key,
                "project": project,
                "label": run.label,
                "timestamp": run.created_at.isoformat() if run.created_at else None,
                "status": run.status,
                "duration_s": run.duration_s,
                "params_summary": run.params_summary,
                "result_size_bytes": run.result_size_bytes,
                "error": run.error,
            }
    except Exception:
        pass
    finally:
        session.close()

    # Fallback to file
    results_dir = get_results_dir(project)
    meta_path = os.path.join(results_dir, job_id, "metadata.json")
    if not os.path.exists(meta_path):
        return None
    with open(meta_path) as f:
        return json.load(f)


def list_results(project: str = "_default") -> list[dict]:
    """List all results for a project from DB."""
    result = search_results(project=project, limit=10000)
    return result["results"]


def get_result(job_id: str, project: str = "_default") -> dict | None:
    """Get a specific result by job_id (reads result.json from disk)."""
    results_dir = get_results_dir(project)
    result_path = os.path.join(results_dir, job_id, "result.json")
    if not os.path.exists(result_path):
        return None
    with open(result_path) as f:
        return json.load(f)


def get_result_data(job_id: str, project: str = "_default") -> dict | None:
    """Get result data for pipeline chaining. Tries saved file first, then Celery backend."""
    result = get_result(job_id, project)
    if result is not None:
        return result

    from celery.result import AsyncResult
    from celery_app import app as celery_app
    ar = AsyncResult(job_id, app=celery_app)
    if ar.status == "SUCCESS":
        return ar.result
    return None


def migrate_index_files() -> int:
    """One-time migration: scan _index.json files and import to DB.

    Returns number of entries migrated.
    """
    base = settings.results_dir
    if not os.path.exists(base):
        return 0

    migrated = 0
    session = sync_session_factory()
    try:
        for project_name in os.listdir(base):
            project_dir = os.path.join(base, project_name)
            if not os.path.isdir(project_dir) or project_name.startswith("."):
                continue

            index_path = os.path.join(project_dir, "_index.json")
            if not os.path.exists(index_path):
                continue

            try:
                with open(index_path) as f:
                    entries = json.load(f)
            except (json.JSONDecodeError, OSError):
                continue

            if not entries:
                continue

            proj = _get_or_create_project(session, project_name)

            for entry in entries:
                job_id = entry.get("job_id")
                if not job_id:
                    continue

                # Skip if already in DB
                existing = session.execute(
                    select(SimulationRun).where(SimulationRun.job_id == job_id)
                ).scalar_one_or_none()
                if existing:
                    continue

                timestamp_str = entry.get("timestamp")
                created_at = datetime.now(timezone.utc)
                if timestamp_str:
                    try:
                        created_at = datetime.fromisoformat(timestamp_str)
                    except (ValueError, TypeError):
                        pass

                run = SimulationRun(
                    job_id=job_id,
                    project_id=proj.id,
                    tool_key=entry.get("tool", "unknown"),
                    label=entry.get("label"),
                    status=entry.get("status", "SUCCESS"),
                    params_summary=entry.get("params_summary"),
                    duration_s=entry.get("duration_s"),
                    error=entry.get("error"),
                    result_path=os.path.join(project_dir, job_id),
                    result_size_bytes=entry.get("result_size_bytes"),
                    created_at=created_at,
                )
                session.add(run)
                migrated += 1

        session.commit()
        logger.info("Migrated %d result entries from _index.json files to DB", migrated)

        # Rename migrated files so we don't re-scan next startup
        for project_name in os.listdir(base):
            project_dir = os.path.join(base, project_name)
            index_path = os.path.join(project_dir, "_index.json")
            if os.path.exists(index_path):
                try:
                    os.rename(index_path, index_path + ".migrated")
                except OSError:
                    pass
    except Exception:
        session.rollback()
        logger.exception("Failed to migrate _index.json files")
    finally:
        session.close()

    return migrated
