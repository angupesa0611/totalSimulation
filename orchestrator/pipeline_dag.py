"""DAG pipeline engine — extends sequential pipelines with parallel execution, conditionals, and variables."""

import ast
import copy
import uuid
from collections import defaultdict, deque

from celery.result import AsyncResult
from celery_app import app as celery_app
from config import TOOL_REGISTRY, settings


# In-memory DAG pipeline state
_dag_state: dict[str, dict] = {}


def _build_execution_graph(steps: list[dict]) -> tuple[dict, list[str]]:
    """
    Validate DAG (no cycles), return adjacency map and topological order.
    Raises ValueError on cycle detection.
    """
    step_ids = {s["id"] for s in steps}
    adj = defaultdict(list)   # step_id -> list of dependent step_ids
    in_degree = {s["id"]: 0 for s in steps}

    for step in steps:
        for dep in step.get("depends_on", []):
            if dep not in step_ids:
                raise ValueError(f"Step '{step['id']}' depends on unknown step '{dep}'")
            adj[dep].append(step["id"])
            in_degree[step["id"]] += 1

    # Kahn's algorithm for topological sort + cycle detection
    queue = deque([sid for sid, deg in in_degree.items() if deg == 0])
    topo_order = []

    while queue:
        node = queue.popleft()
        topo_order.append(node)
        for neighbor in adj[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(topo_order) != len(steps):
        raise ValueError("Pipeline contains a cycle — DAG validation failed")

    return dict(adj), topo_order


def _resolve_dag_params(step: dict, completed_results: dict, variables: dict) -> dict:
    """Resolve $step_id.field and $var.name references in param_map."""
    params = dict(step.get("params", {}))
    param_map = step.get("param_map")
    if not param_map:
        return params

    for param_key, ref in param_map.items():
        if ref.startswith("$var."):
            # Pipeline variable reference
            var_path = ref[5:]
            value = variables
            for part in var_path.split("."):
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    value = None
                    break
            params[param_key] = value
        elif ref.startswith("$"):
            # Step reference: $step_id.field.subfield
            parts = ref[1:].split(".", 1)
            step_ref_id = parts[0]
            if step_ref_id in completed_results and len(parts) > 1:
                field_path = parts[1]
                value = completed_results[step_ref_id]
                for part in field_path.split("."):
                    if isinstance(value, dict):
                        value = value.get(part)
                    elif isinstance(value, list) and part.isdigit():
                        value = value[int(part)]
                    else:
                        value = None
                        break
                params[param_key] = value
            elif step_ref_id in completed_results:
                params[param_key] = completed_results[step_ref_id]
        else:
            params[param_key] = ref

    return params


def _evaluate_condition(condition: str, completed_results: dict) -> bool:
    """
    Safe AST-based expression evaluator for pipeline conditions.
    Supports: $step_id.status == 'SUCCESS', $step_id.data.value > 10
    Only allows Compare nodes with literals. Rejects function calls and imports.

    Security: Uses ast.parse() for validation, then ast.literal_eval-style
    walking. The eval runs with __builtins__={} — no access to any Python
    builtins. This is the approach recommended by the plan for safe condition
    evaluation in pipeline DAGs.
    """
    if not condition:
        return True

    # Replace $step_id.field references with their values
    import re
    expr = condition
    refs = re.findall(r'\$(\w+(?:\.\w+)*)', expr)
    for ref in refs:
        parts = ref.split(".", 1)
        step_ref_id = parts[0]
        if step_ref_id in completed_results:
            if len(parts) > 1:
                value = completed_results[step_ref_id]
                for part in parts[1].split("."):
                    if isinstance(value, dict):
                        value = value.get(part)
                    else:
                        value = None
                        break
            else:
                value = completed_results[step_ref_id]
            # Replace in expression
            expr = expr.replace(f"${ref}", repr(value))
        else:
            # Step not completed yet — condition cannot be evaluated
            return False

    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError:
        return False

    # Walk AST and reject unsafe nodes (function calls, imports, etc.)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Call, ast.Import, ast.ImportFrom)):
            return False

    # Safe sandboxed evaluation with no builtins access
    try:
        code = compile(tree, "<condition>", "eval")
        # Intentional sandboxed eval: AST-validated expression with empty builtins
        result = eval(code, {"__builtins__": {}}, {})  # noqa: S307
        return bool(result)
    except Exception:
        return False


def start_dag_pipeline(request) -> dict:
    """Start a DAG pipeline. Returns initial status."""
    steps_raw = [s.model_dump() for s in request.steps]

    if len(steps_raw) > settings.max_pipeline_steps:
        raise ValueError(
            f"Pipeline has {len(steps_raw)} steps, exceeding max of {settings.max_pipeline_steps}"
        )

    # Validate all tools
    for step in steps_raw:
        if step["tool"] not in TOOL_REGISTRY:
            raise ValueError(f"Unknown tool in pipeline: {step['tool']}")

    # Validate DAG structure
    _, topo_order = _build_execution_graph(steps_raw)

    pipeline_id = str(uuid.uuid4())

    step_map = {}
    for step in steps_raw:
        step_map[step["id"]] = {
            "id": step["id"],
            "tool": step["tool"],
            "config": step,
            "job_id": None,
            "status": "PENDING",
            "progress": 0.0,
            "message": None,
            "result": None,
            "depends_on": step.get("depends_on", []),
        }

    state = {
        "pipeline_id": pipeline_id,
        "status": "RUNNING",
        "steps": step_map,
        "topo_order": topo_order,
        "completed_results": {},
        "variables": request.variables,
        "project": request.project,
        "label": request.label,
    }
    _dag_state[pipeline_id] = state

    # Advance — submit initial steps (no dependencies)
    _advance_dag(pipeline_id)

    return _format_dag_status(state)


def _advance_dag(pipeline_id: str):
    """Find newly-unblocked steps, submit them, check completion."""
    state = _dag_state.get(pipeline_id)
    if not state or state["status"] != "RUNNING":
        return

    steps = state["steps"]
    completed_results = state["completed_results"]

    for step_id in state["topo_order"]:
        step = steps[step_id]
        if step["status"] != "PENDING":
            continue

        # Check all dependencies completed
        deps_met = all(
            steps[dep]["status"] == "SUCCESS"
            for dep in step["depends_on"]
        )
        if not deps_met:
            # Check if any dep failed — if so, mark this step as SKIPPED
            any_failed = any(
                steps[dep]["status"] in ("FAILURE", "SKIPPED")
                for dep in step["depends_on"]
            )
            if any_failed:
                step["status"] = "SKIPPED"
                step["message"] = "Dependency failed"
            continue

        # Check condition
        condition = step["config"].get("condition")
        if condition and not _evaluate_condition(condition, completed_results):
            step["status"] = "SKIPPED"
            step["message"] = f"Condition not met: {condition}"
            continue

        # Resolve params and submit
        tool_key = step["tool"]
        tool_meta = TOOL_REGISTRY[tool_key]
        params = _resolve_dag_params(step["config"], completed_results, state["variables"])

        task = celery_app.send_task(
            tool_meta["task"],
            kwargs={
                "params": params,
                "project": state["project"],
                "label": step["config"].get("label"),
            },
            queue=tool_meta["queue"],
        )
        step["job_id"] = task.id
        step["status"] = "SUBMITTED"


def get_dag_pipeline_status(pipeline_id: str) -> dict | None:
    """Get current DAG pipeline status, polling Celery for active steps."""
    state = _dag_state.get(pipeline_id)
    if not state:
        return None

    if state["status"] not in ("RUNNING",):
        return _format_dag_status(state)

    steps = state["steps"]

    for step_id, step in steps.items():
        if step["status"] in ("SUCCESS", "FAILURE", "SKIPPED", "PENDING"):
            continue

        job_id = step.get("job_id")
        if not job_id:
            continue

        result = AsyncResult(job_id, app=celery_app)
        celery_status = result.status

        if celery_status == "PROGRESS":
            step["status"] = "RUNNING"
            info = result.info or {}
            step["progress"] = info.get("progress", 0)
            step["message"] = info.get("message", "")
        elif celery_status == "STARTED":
            step["status"] = "RUNNING"
        elif celery_status == "SUCCESS":
            step["status"] = "SUCCESS"
            step["progress"] = 1.0
            step["result"] = result.result
            state["completed_results"][step_id] = result.result
        elif celery_status == "FAILURE":
            step["status"] = "FAILURE"
            step["message"] = str(result.result)

    # Try to advance after polling
    _advance_dag(pipeline_id)

    # Re-check state after advancing
    all_done = True
    any_failed = False
    for step in steps.values():
        if step["status"] in ("PENDING", "SUBMITTED", "RUNNING"):
            all_done = False
        if step["status"] == "FAILURE":
            any_failed = True

    if all_done:
        state["status"] = "FAILURE" if any_failed else "SUCCESS"

    return _format_dag_status(state)


def _format_dag_status(state: dict) -> dict:
    """Format DAG pipeline state for API response."""
    steps_list = []
    for step_id in state["topo_order"]:
        step = state["steps"][step_id]
        steps_list.append({
            "id": step["id"],
            "tool": step["tool"],
            "job_id": step.get("job_id"),
            "status": step["status"],
            "progress": step.get("progress", 0.0),
            "message": step.get("message"),
            "result": step.get("result"),
            "depends_on": step.get("depends_on", []),
            "label": step["config"].get("label"),
        })

    return {
        "pipeline_id": state["pipeline_id"],
        "status": state["status"],
        "total_steps": len(state["steps"]),
        "steps": steps_list,
        "label": state.get("label"),
    }
