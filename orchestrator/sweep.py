"""Parameter sweep engine — grid, random, and Latin Hypercube sampling with Celery group execution."""

import copy
import math
import random
import uuid
from itertools import product

from celery import group
from celery.result import AsyncResult
from celery_app import app as celery_app
from config import TOOL_REGISTRY, settings


# In-memory sweep state (same pattern as pipeline.py)
_sweep_state: dict[str, dict] = {}


def _expand_axis_values(axis) -> list:
    """Expand an axis spec into a concrete list of values."""
    if axis.values is not None:
        return list(axis.values)
    if axis.range is not None:
        r = axis.range
        mn, mx, steps = r["min"], r["max"], r.get("steps", 5)
        if axis.log_scale:
            log_min, log_max = math.log10(mn), math.log10(mx)
            return [10 ** (log_min + i * (log_max - log_min) / (steps - 1)) for i in range(steps)]
        else:
            return [mn + i * (mx - mn) / (steps - 1) for i in range(steps)]
    return []


def _apply_axis_value(base_params: dict, dot_path: str, value) -> dict:
    """Set a nested dict value by dot-path. Returns a new dict."""
    params = copy.deepcopy(base_params)
    parts = dot_path.split(".")
    target = params
    for part in parts[:-1]:
        if part not in target:
            target[part] = {}
        target = target[part]
    target[parts[-1]] = value
    return params


def generate_sweep_points(axes, method: str, n_samples: int | None,
                          base_params: dict) -> list[dict]:
    """Generate parameter combinations from sweep axes."""
    axis_values = [_expand_axis_values(a) for a in axes]
    axis_paths = [a.param for a in axes]

    if method == "grid":
        points = []
        for combo in product(*axis_values):
            p = copy.deepcopy(base_params)
            for path, val in zip(axis_paths, combo):
                p = _apply_axis_value(p, path, val)
            points.append(p)
        return points

    elif method == "random":
        n = n_samples or 10
        points = []
        for _ in range(n):
            p = copy.deepcopy(base_params)
            for path, vals in zip(axis_paths, axis_values):
                val = random.choice(vals) if vals else None
                if val is not None:
                    p = _apply_axis_value(p, path, val)
            points.append(p)
        return points

    elif method == "lhs":
        # Latin Hypercube Sampling — stratified random, no scipy dependency
        n = n_samples or 10
        n_axes = len(axes)
        # For each axis, create n equally spaced intervals and sample one from each
        intervals = []
        for ax_vals in axis_values:
            k = len(ax_vals)
            if k == 0:
                intervals.append([None] * n)
                continue
            # Map n samples to k values via stratified bins
            indices = list(range(n))
            random.shuffle(indices)
            sampled = [ax_vals[int(idx * k / n) % k] for idx in indices]
            intervals.append(sampled)

        points = []
        for i in range(n):
            p = copy.deepcopy(base_params)
            for j, path in enumerate(axis_paths):
                val = intervals[j][i]
                if val is not None:
                    p = _apply_axis_value(p, path, val)
            points.append(p)
        return points

    else:
        raise ValueError(f"Unknown sweep method: {method}")


def start_sweep(request) -> dict:
    """Generate sweep points, submit all as a Celery group, store state."""
    tool_key = request.tool
    if tool_key not in TOOL_REGISTRY:
        raise ValueError(f"Unknown tool: {tool_key}")

    tool_meta = TOOL_REGISTRY[tool_key]
    sweep_points = generate_sweep_points(
        request.axes, request.method, request.n_samples, request.base_params
    )

    if len(sweep_points) > settings.max_sweep_runs:
        raise ValueError(
            f"Sweep produces {len(sweep_points)} runs, exceeding max of {settings.max_sweep_runs}"
        )

    sweep_id = str(uuid.uuid4())
    label = request.label or f"Sweep {tool_key}"
    total = len(sweep_points)

    # Build Celery group
    tasks = []
    runs = []
    for i, point_params in enumerate(sweep_points):
        task_sig = celery_app.signature(
            tool_meta["task"],
            kwargs={
                "params": point_params,
                "project": request.project,
                "label": f"{label} [{i + 1}/{total}]",
            },
            queue=tool_meta["queue"],
        )
        tasks.append(task_sig)
        runs.append({
            "run_index": i,
            "params": point_params,
            "job_id": None,
            "status": "PENDING",
            "result_summary": None,
        })

    # Submit group
    group_result = group(tasks).apply_async()

    # Store task IDs from group children
    for i, child in enumerate(group_result.children or []):
        runs[i]["job_id"] = child.id

    state = {
        "sweep_id": sweep_id,
        "tool": tool_key,
        "status": "RUNNING",
        "total_runs": total,
        "completed_runs": 0,
        "failed_runs": 0,
        "runs": runs,
        "group_result_id": group_result.id,
        "project": request.project,
    }
    _sweep_state[sweep_id] = state

    return _format_status(state)


def get_sweep_status(sweep_id: str) -> dict | None:
    """Poll all AsyncResults for a sweep, return aggregated status."""
    state = _sweep_state.get(sweep_id)
    if not state:
        return None

    if state["status"] in ("SUCCESS", "FAILURE"):
        return _format_status(state)

    completed = 0
    failed = 0
    for run in state["runs"]:
        job_id = run.get("job_id")
        if not job_id:
            continue
        if run["status"] in ("SUCCESS", "FAILURE"):
            if run["status"] == "SUCCESS":
                completed += 1
            else:
                failed += 1
            continue

        result = AsyncResult(job_id, app=celery_app)
        celery_status = result.status

        if celery_status == "SUCCESS":
            run["status"] = "SUCCESS"
            run["result_summary"] = _summarize_result(result.result)
            completed += 1
        elif celery_status == "FAILURE":
            run["status"] = "FAILURE"
            run["result_summary"] = {"error": str(result.result)}
            failed += 1
        elif celery_status in ("PROGRESS", "STARTED"):
            run["status"] = "RUNNING"

    state["completed_runs"] = completed
    state["failed_runs"] = failed

    total = state["total_runs"]
    if completed + failed >= total:
        state["status"] = "SUCCESS" if failed == 0 else "PARTIAL"
    elif completed > 0 or failed > 0:
        state["status"] = "RUNNING"

    return _format_status(state)


def get_sweep_results(sweep_id: str) -> list[dict] | None:
    """Get all completed results for a sweep."""
    state = _sweep_state.get(sweep_id)
    if not state:
        return None

    results = []
    for run in state["runs"]:
        job_id = run.get("job_id")
        if not job_id:
            continue
        ar = AsyncResult(job_id, app=celery_app)
        if ar.status == "SUCCESS":
            results.append({
                "run_index": run["run_index"],
                "params": run["params"],
                "job_id": job_id,
                "result": ar.result,
            })
    return results


def cancel_sweep(sweep_id: str) -> dict | None:
    """Cancel remaining runs in a sweep."""
    state = _sweep_state.get(sweep_id)
    if not state:
        return None

    for run in state["runs"]:
        if run["status"] in ("PENDING", "RUNNING"):
            job_id = run.get("job_id")
            if job_id:
                celery_app.control.revoke(job_id, terminate=True)
            run["status"] = "CANCELLED"

    state["status"] = "CANCELLED"
    return _format_status(state)


def _summarize_result(result: dict) -> dict:
    """Extract a brief summary from a full result for the sweep status view."""
    if not isinstance(result, dict):
        return {}
    summary = {}
    # Include tool and top-level scalar values
    for key in ("tool", "job_id", "status"):
        if key in result:
            summary[key] = result[key]
    # Include numeric summary fields from data
    data = result.get("data", result)
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, (int, float, str, bool)):
                summary[k] = v
    return summary


def _format_status(state: dict) -> dict:
    """Format sweep state for API response."""
    return {
        "sweep_id": state["sweep_id"],
        "tool": state["tool"],
        "status": state["status"],
        "total_runs": state["total_runs"],
        "completed_runs": state["completed_runs"],
        "failed_runs": state["failed_runs"],
        "runs": state["runs"],
    }
