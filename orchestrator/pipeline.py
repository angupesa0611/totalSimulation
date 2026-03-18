import asyncio
import logging
import uuid
import json
from datetime import datetime, timezone

from celery_app import app as celery_app
from db.registry_service import get_tool_registry
from results import get_result

logger = logging.getLogger(__name__)

# In-memory pipeline state (DB-backed for persistence across restarts)
_pipeline_state: dict[str, dict] = {}


def _resolve_value(ref, prev_result: dict):
    """Resolve a single param_map value, which may be a $prev ref, literal, or nested dict."""
    if isinstance(ref, str) and ref.startswith("$prev."):
        path = ref[6:]  # strip "$prev."
        value = prev_result
        for part in path.split("."):
            if isinstance(value, dict):
                value = value.get(part)
            elif isinstance(value, list) and part.isdigit():
                value = value[int(part)]
            else:
                return None  # path not found
        return value
    elif isinstance(ref, dict):
        # Recursively resolve nested dicts (e.g. {"expression": "$prev.result.expr"})
        # If ANY $prev ref inside is unresolved, skip the entire dict to preserve fallback
        out = {}
        for k, v in ref.items():
            resolved_v = _resolve_value(v, prev_result)
            if resolved_v is None:
                return None  # unresolved ref → skip entire nested param
            out[k] = resolved_v
        return out
    else:
        return ref  # literal string, number, bool, list, etc.


def resolve_param_map(param_map: dict, prev_result: dict) -> dict:
    """Resolve $prev references in param_map against previous step result.

    Unresolved $prev references (None) are skipped so that fallback params
    in the step config are preserved.
    """
    resolved = {}
    for param_key, ref in param_map.items():
        value = _resolve_value(ref, prev_result)
        if value is not None:
            resolved[param_key] = value
    return resolved


async def start_pipeline(steps: list[dict], project: str = "_default",
                         label: str | None = None) -> dict:
    """Start a sequential pipeline. Returns pipeline status dict."""
    pipeline_id = str(uuid.uuid4())

    step_statuses = []
    for i, step in enumerate(steps):
        step_statuses.append({
            "step_index": i,
            "tool": step["tool"],
            "job_id": None,
            "status": "PENDING",
            "progress": 0.0,
            "message": None,
            "result": None,
        })

    state = {
        "pipeline_id": pipeline_id,
        "status": "RUNNING",
        "current_step": 0,
        "total_steps": len(steps),
        "steps": step_statuses,
        "step_configs": steps,
        "project": project,
        "label": label,
    }
    _pipeline_state[pipeline_id] = state
    _persist_pipeline(state)

    # Ensure worker is running and submit the first step
    await _submit_step_async(pipeline_id, 0)

    return {
        "pipeline_id": pipeline_id,
        "status": "RUNNING",
        "current_step": 0,
        "total_steps": len(steps),
        "steps": step_statuses,
        "label": label,
    }


async def _submit_step_async(pipeline_id: str, step_index: int):
    """Ensure worker is running, then submit the step."""
    from docker_manager import docker_mgr

    state = _pipeline_state.get(pipeline_id)
    if not state:
        return

    tool_key = state["step_configs"][step_index]["tool"]
    try:
        await docker_mgr.ensure_worker(tool_key)
    except Exception as e:
        state["status"] = "FAILURE"
        state["steps"][step_index]["status"] = "FAILURE"
        state["steps"][step_index]["message"] = f"Worker startup failed: {e}"
        return

    _submit_step(pipeline_id, step_index)
    docker_mgr.record_activity(tool_key)


def _submit_step(pipeline_id: str, step_index: int):
    """Submit a single pipeline step as a Celery task."""
    state = _pipeline_state.get(pipeline_id)
    if not state:
        return

    step_config = state["step_configs"][step_index]
    tool_key = step_config["tool"]

    TOOL_REGISTRY = get_tool_registry()
    if tool_key not in TOOL_REGISTRY:
        state["status"] = "FAILURE"
        state["steps"][step_index]["status"] = "FAILURE"
        state["steps"][step_index]["message"] = f"Unknown tool: {tool_key}"
        return

    tool_meta = TOOL_REGISTRY[tool_key]
    params = dict(step_config.get("params", {}))

    # Resolve param_map from previous step
    param_map = step_config.get("param_map")
    if param_map and step_index > 0:
        prev_step = state["steps"][step_index - 1]
        prev_result = dict(prev_step.get("result") or {})
        # Inject job_id so $prev.job_id resolves (it's step metadata, not in result)
        if "job_id" not in prev_result:
            prev_result["job_id"] = prev_step.get("job_id", "")
        if prev_result:
            resolved = resolve_param_map(param_map, prev_result)
            params.update(resolved)

    task = celery_app.send_task(
        tool_meta["task"],
        kwargs={
            "params": params,
            "project": state["project"],
            "label": step_config.get("label"),
        },
        queue=tool_meta["queue"],
    )

    state["steps"][step_index]["job_id"] = task.id
    state["steps"][step_index]["status"] = "PENDING"
    state["current_step"] = step_index


async def get_pipeline_status(pipeline_id: str) -> dict | None:
    """Get current pipeline status, polling Celery for active step."""
    state = _pipeline_state.get(pipeline_id)
    if not state:
        return None

    if state["status"] not in ("RUNNING",):
        return _format_status(state)

    # Poll current step
    current = state["current_step"]
    step = state["steps"][current]
    job_id = step.get("job_id")

    if not job_id:
        return _format_status(state)

    from celery.result import AsyncResult
    result = AsyncResult(job_id, app=celery_app)
    celery_status = result.status

    if celery_status == "PROGRESS":
        info = result.info or {}
        step["status"] = "RUNNING"
        step["progress"] = info.get("progress", 0)
        step["message"] = info.get("message", "")
    elif celery_status == "STARTED":
        step["status"] = "RUNNING"
    elif celery_status == "SUCCESS":
        step["status"] = "SUCCESS"
        step["progress"] = 1.0
        step["result"] = result.result

        # Advance to next step or complete
        next_step = current + 1
        if next_step < state["total_steps"]:
            await _submit_step_async(pipeline_id, next_step)
        else:
            state["status"] = "SUCCESS"
    elif celery_status == "FAILURE":
        step["status"] = "FAILURE"
        step["message"] = str(result.result)
        state["status"] = "FAILURE"

    _persist_pipeline(state)
    return _format_status(state)


def _format_status(state: dict) -> dict:
    """Format pipeline state for API response."""
    return {
        "pipeline_id": state["pipeline_id"],
        "status": state["status"],
        "current_step": state["current_step"],
        "total_steps": state["total_steps"],
        "steps": state["steps"],
        "label": state.get("label"),
    }


def _persist_pipeline(state: dict) -> None:
    """Save pipeline state to DB for restart recovery."""
    try:
        from sqlalchemy import select
        from db.engine import sync_session_factory
        from db.models.results import PipelineRun

        session = sync_session_factory()
        try:
            run = session.execute(
                select(PipelineRun).where(PipelineRun.pipeline_id == state["pipeline_id"])
            ).scalar_one_or_none()

            now = datetime.now(timezone.utc)
            # Serialize steps without large result data
            steps_snap = []
            for s in state["steps"]:
                steps_snap.append({
                    k: v for k, v in s.items() if k != "result"
                })

            if run:
                run.status = state["status"]
                run.current_step = state["current_step"]
                run.steps_snapshot = {"steps": steps_snap, "step_configs": state.get("step_configs")}
                if state["status"] in ("SUCCESS", "FAILURE"):
                    run.completed_at = now
            else:
                run = PipelineRun(
                    pipeline_id=state["pipeline_id"],
                    pipeline_type="sequential",
                    project_name=state.get("project", "_default"),
                    label=state.get("label"),
                    status=state["status"],
                    total_steps=state["total_steps"],
                    current_step=state["current_step"],
                    steps_snapshot={"steps": steps_snap, "step_configs": state.get("step_configs")},
                    created_at=now,
                )
                session.add(run)
            session.commit()
        finally:
            session.close()
    except Exception:
        logger.exception("Failed to persist pipeline state to DB")


def load_pipelines_from_db() -> int:
    """Load in-progress pipelines from DB on startup. Returns count loaded."""
    try:
        from sqlalchemy import select
        from db.engine import sync_session_factory
        from db.models.results import PipelineRun

        session = sync_session_factory()
        try:
            rows = session.execute(
                select(PipelineRun).where(
                    PipelineRun.pipeline_type == "sequential",
                    PipelineRun.status == "RUNNING",
                )
            ).scalars().all()

            loaded = 0
            for run in rows:
                snap = run.steps_snapshot or {}
                state = {
                    "pipeline_id": run.pipeline_id,
                    "status": run.status,
                    "current_step": run.current_step,
                    "total_steps": run.total_steps,
                    "steps": snap.get("steps", []),
                    "step_configs": snap.get("step_configs", []),
                    "project": run.project_name,
                    "label": run.label,
                }
                _pipeline_state[run.pipeline_id] = state
                loaded += 1

            if loaded:
                logger.info("Loaded %d in-progress sequential pipelines from DB", loaded)
            return loaded
        finally:
            session.close()
    except Exception:
        logger.exception("Failed to load pipelines from DB")
        return 0
