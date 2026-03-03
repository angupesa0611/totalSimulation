import uuid
import json
from celery_app import app as celery_app
from config import TOOL_REGISTRY
from results import get_result


# In-memory pipeline state (lightweight — Redis-backed Celery handles the real state)
_pipeline_state: dict[str, dict] = {}


def resolve_param_map(param_map: dict[str, str], prev_result: dict) -> dict:
    """Resolve $prev references in param_map against previous step result."""
    resolved = {}
    for param_key, ref in param_map.items():
        if ref.startswith("$prev."):
            path = ref[6:]  # strip "$prev."
            value = prev_result
            for part in path.split("."):
                if isinstance(value, dict):
                    value = value.get(part)
                elif isinstance(value, list) and part.isdigit():
                    value = value[int(part)]
                else:
                    value = None
                    break
            resolved[param_key] = value
        else:
            resolved[param_key] = ref
    return resolved


def start_pipeline(steps: list[dict], project: str = "_default",
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

    # Submit the first step
    _submit_step(pipeline_id, 0)

    return {
        "pipeline_id": pipeline_id,
        "status": "RUNNING",
        "current_step": 0,
        "total_steps": len(steps),
        "steps": step_statuses,
        "label": label,
    }


def _submit_step(pipeline_id: str, step_index: int):
    """Submit a single pipeline step as a Celery task."""
    state = _pipeline_state.get(pipeline_id)
    if not state:
        return

    step_config = state["step_configs"][step_index]
    tool_key = step_config["tool"]

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
        prev_result = prev_step.get("result", {})
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


def get_pipeline_status(pipeline_id: str) -> dict | None:
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
            _submit_step(pipeline_id, next_step)
        else:
            state["status"] = "SUCCESS"
    elif celery_status == "FAILURE":
        step["status"] = "FAILURE"
        step["message"] = str(result.result)
        state["status"] = "FAILURE"

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
