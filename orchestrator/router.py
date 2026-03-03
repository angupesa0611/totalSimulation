import json
import logging
import os
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from celery.result import AsyncResult
from pydantic import BaseModel
from models.simulation import SimulationRequest, SimulationStatus
from models.layers import ToolConfig, LayerConfig, PresetInfo
from models.pipeline import PipelineRequest, PipelineDAGRequest
from config import TOOL_REGISTRY, LAYERS, PRESETS, COUPLINGS, PIPELINES, settings
from celery_app import app as celery_app
import results as results_store
import pipeline as pipeline_engine
import pipeline_dag
from validation import validate_params
from metrics import increment_simulation, increment_pipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


# --- Layer / Tool discovery ---

@router.get("/layers")
def get_layers() -> list[LayerConfig]:
    out = []
    for key, layer in LAYERS.items():
        tools = []
        for tkey in layer["tools"]:
            t = TOOL_REGISTRY[tkey]
            tools.append(ToolConfig(
                name=t["name"], key=tkey, description=t["description"],
                layer=t["layer"], queue=t["queue"],
            ))
        out.append(LayerConfig(
            name=layer["name"], key=key,
            description=layer["description"], tools=tools,
        ))
    return out


@router.get("/presets")
def get_presets() -> list[PresetInfo]:
    return [
        PresetInfo(key=k, **v) for k, v in PRESETS.items()
    ]


@router.get("/presets/{key}")
def get_preset(key: str) -> dict:
    if key not in PRESETS:
        raise HTTPException(404, f"Preset '{key}' not found")
    preset = PRESETS[key]
    # Try mounted volume path first, then relative path
    example_path = os.path.join("/app", "shared", "examples", preset["example_file"])
    if not os.path.exists(example_path):
        example_path = os.path.join(
            os.path.dirname(__file__), "..", "shared", "examples", preset["example_file"]
        )
    if not os.path.exists(example_path):
        raise HTTPException(404, f"Example file not found")
    with open(example_path) as f:
        return json.load(f)


@router.get("/couplings")
def get_couplings() -> dict:
    """Return available tool couplings/pipelines."""
    return COUPLINGS


@router.get("/pipelines")
def list_pipelines() -> dict:
    """Return all named pipeline definitions (summary)."""
    return {
        key: {
            "key": key,
            "label": p["label"],
            "description": p["description"],
            "n_steps": len(p["steps"]),
        }
        for key, p in PIPELINES.items()
    }


@router.get("/pipelines/{key}")
def get_pipeline(key: str) -> dict:
    """Return a named pipeline with full step details."""
    if key not in PIPELINES:
        raise HTTPException(404, f"Pipeline not found: {key}")
    return {"key": key, **PIPELINES[key]}


# --- Simulation ---

@router.post("/simulate")
def submit_simulation(req: SimulationRequest) -> SimulationStatus:
    if req.tool not in TOOL_REGISTRY:
        raise HTTPException(400, f"Unknown tool: {req.tool}")

    # Input validation
    errors = validate_params(req.tool, req.params)
    if errors:
        raise HTTPException(422, detail=errors)

    increment_simulation(req.tool)

    tool_meta = TOOL_REGISTRY[req.tool]
    task = celery_app.send_task(
        tool_meta["task"],
        kwargs={
            "params": req.params,
            "project": req.project,
            "label": req.label,
        },
        queue=tool_meta["queue"],
    )
    return SimulationStatus(
        job_id=task.id,
        tool=req.tool,
        status="PENDING",
    )


@router.post("/tools/{tool_key}/solo")
def run_solo(tool_key: str, req: SimulationRequest) -> SimulationStatus:
    """Submit a simulation for a specific tool."""
    if tool_key not in TOOL_REGISTRY:
        raise HTTPException(400, f"Unknown tool: {tool_key}")
    req.tool = tool_key
    return submit_simulation(req)


@router.get("/status/{job_id}")
def get_status(job_id: str) -> SimulationStatus:
    result = AsyncResult(job_id, app=celery_app)
    status = result.status
    data = None
    progress = None
    message = None

    if status == "PROGRESS":
        info = result.info or {}
        progress = info.get("progress", 0)
        message = info.get("message", "")
    elif status == "SUCCESS":
        data = result.result
    elif status == "FAILURE":
        message = str(result.result)

    return SimulationStatus(
        job_id=job_id,
        tool=result.result.get("tool", "") if isinstance(result.result, dict) else "",
        status=status,
        progress=progress,
        message=message,
        result=data,
    )


# --- Job cancel ---

@router.post("/simulate/{job_id}/cancel")
def cancel_job(job_id: str, project: str = "_default") -> dict:
    """Cancel a running job via Celery revoke."""
    celery_app.control.revoke(job_id, terminate=True)
    results_store.update_result_status(job_id, project, "CANCELLED")
    logger.info("Job cancelled", extra={"job_id": job_id})
    return {"job_id": job_id, "status": "CANCELLED"}


# --- Pipeline ---

# DAG routes must come before the catch-all {pipeline_id} to avoid path conflicts
@router.post("/pipeline/dag")
def submit_dag_pipeline(req: PipelineDAGRequest) -> dict:
    """Submit a DAG pipeline with parallel steps, conditionals, and variables."""
    try:
        increment_pipeline("dag")
        return pipeline_dag.start_dag_pipeline(req)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/pipeline/dag/{pipeline_id}")
def get_dag_pipeline_status(pipeline_id: str) -> dict:
    """Get DAG pipeline execution status."""
    status = pipeline_dag.get_dag_pipeline_status(pipeline_id)
    if status is None:
        raise HTTPException(404, "DAG pipeline not found")
    return status


@router.post("/pipeline")
def submit_pipeline(req: PipelineRequest) -> dict:
    """Submit a multi-step sequential pipeline."""
    steps = [step.model_dump() for step in req.steps]

    # Validate all tools exist
    for step in steps:
        if step["tool"] not in TOOL_REGISTRY:
            raise HTTPException(400, f"Unknown tool in pipeline: {step['tool']}")

    increment_pipeline("sequential")
    return pipeline_engine.start_pipeline(steps, req.project, req.label)


@router.get("/pipeline/{pipeline_id}")
def get_pipeline_status(pipeline_id: str) -> dict:
    """Get pipeline execution status."""
    status = pipeline_engine.get_pipeline_status(pipeline_id)
    if status is None:
        raise HTTPException(404, "Pipeline not found")
    return status


# --- Results ---

@router.get("/results")
def list_results(
    project: str = "_default",
    tool: str | None = None,
    status: str | None = None,
    q: str | None = None,
    sort: str = "newest",
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> dict:
    """List results with optional filtering, search, and pagination."""
    return results_store.search_results(
        project=project,
        query=q,
        tool_filter=tool,
        status_filter=status,
        sort=sort,
        offset=offset,
        limit=limit,
    )


@router.get("/results/{job_id}")
def get_result(job_id: str, project: str = "_default") -> dict:
    result = results_store.get_result(job_id, project)
    if result is None:
        raise HTTPException(404, "Result not found")
    return result


@router.get("/results/{job_id}/metadata")
def get_result_metadata(job_id: str, project: str = "_default") -> dict:
    """Get metadata for a specific result."""
    metadata = results_store.get_result_metadata(job_id, project)
    if metadata is None:
        raise HTTPException(404, "Result not found")
    return metadata


@router.delete("/results/{job_id}")
def delete_result(job_id: str, project: str = "_default") -> dict:
    """Delete a result and its files."""
    if not results_store.delete_result(job_id, project):
        raise HTTPException(404, "Result not found")
    logger.info("Result deleted", extra={"job_id": job_id})
    return {"deleted": True, "job_id": job_id}


@router.get("/results/{job_id}/files")
def list_result_files(job_id: str, project: str = "_default") -> list[dict]:
    """List files in a result directory."""
    files = results_store.get_result_files(job_id, project)
    if files is None:
        raise HTTPException(404, "Result not found")
    return files


@router.get("/results/{job_id}/files/{filename:path}")
def download_result_file(job_id: str, filename: str, project: str = "_default"):
    """Download a specific file from a result directory."""
    filepath = results_store.get_result_file_path(job_id, filename, project)
    if filepath is None:
        raise HTTPException(404, "File not found")
    return FileResponse(filepath, filename=filename)


# --- Projects ---

@router.get("/projects")
def list_projects() -> list[str]:
    """List all projects."""
    return results_store.list_projects()


class ProjectCreate(BaseModel):
    name: str


@router.post("/projects")
def create_project(req: ProjectCreate) -> dict:
    """Create a new project."""
    if not req.name or req.name.startswith("."):
        raise HTTPException(400, "Invalid project name")
    if not results_store.create_project(req.name):
        raise HTTPException(409, "Project already exists")
    logger.info("Project created: %s", req.name)
    return {"created": True, "name": req.name}


@router.delete("/projects/{name}")
def delete_project(name: str) -> dict:
    """Delete a project and all its results."""
    if name == "_default":
        raise HTTPException(400, "Cannot delete the default project")
    if not results_store.delete_project(name):
        raise HTTPException(404, "Project not found")
    logger.info("Project deleted: %s", name)
    return {"deleted": True, "name": name}


# --- Layer activation ---

def _get_redis():
    """Get a Redis connection from the Celery broker URL."""
    import redis
    return redis.Redis.from_url(settings.redis_url, decode_responses=True)


LAYER_ACTIVATION_KEY = "layer_activation"


@router.get("/layers/activation")
def get_layer_activation() -> dict:
    """Get layer activation state. Returns {layers: [...active layer keys]}."""
    r = _get_redis()
    raw = r.get(LAYER_ACTIVATION_KEY)
    if raw is None:
        # Default: all layers active
        return {"layers": list(LAYERS.keys())}
    return {"layers": json.loads(raw)}


class LayerActivationRequest(BaseModel):
    layers: list[str]


@router.post("/layers/activate")
def activate_layers(req: LayerActivationRequest) -> dict:
    """Activate layers (add to active set)."""
    r = _get_redis()
    raw = r.get(LAYER_ACTIVATION_KEY)
    active = set(json.loads(raw)) if raw else set(LAYERS.keys())
    active.update(req.layers)
    r.set(LAYER_ACTIVATION_KEY, json.dumps(sorted(active)))
    return {"layers": sorted(active)}


@router.post("/layers/deactivate")
def deactivate_layers(req: LayerActivationRequest) -> dict:
    """Deactivate layers (remove from active set)."""
    r = _get_redis()
    raw = r.get(LAYER_ACTIVATION_KEY)
    active = set(json.loads(raw)) if raw else set(LAYERS.keys())
    active -= set(req.layers)
    r.set(LAYER_ACTIVATION_KEY, json.dumps(sorted(active)))
    return {"layers": sorted(active)}
