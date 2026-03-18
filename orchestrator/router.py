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
from config import settings
from db.registry_service import (
    get_tool_registry, get_layers, get_presets, get_couplings,
    get_pipelines, get_pipeline_presets, get_coupling_presets,
)
from celery_app import app as celery_app
import results as results_store
import pipeline as pipeline_engine
import pipeline_dag
from validation import validate_params
from metrics import increment_simulation, increment_pipeline
from db.audit import write_audit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


# --- Layer / Tool discovery ---

@router.get("/layers")
def list_layers() -> list[LayerConfig]:
    LAYERS = get_layers()
    TOOL_REGISTRY = get_tool_registry()
    out = []
    for key, layer in LAYERS.items():
        if not layer.get("enabled", True):
            continue
        tools = []
        for tkey in layer["tools"]:
            t = TOOL_REGISTRY.get(tkey)
            if not t or not t.get("enabled", True):
                continue
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
def list_presets() -> list[PresetInfo]:
    PRESETS = get_presets()
    return [
        PresetInfo(key=k, **{kk: vv for kk, vv in v.items() if kk != "enabled"})
        for k, v in PRESETS.items()
        if v.get("enabled", True)
    ]


# Static sub-routes MUST come before the parameterized /presets/{key} route
@router.get("/presets/pipelines")
def list_pipeline_presets_endpoint() -> list[dict]:
    """Return list of all pipeline test presets."""
    PIPELINE_PRESETS = get_pipeline_presets()
    return [{"key": k, **v} for k, v in PIPELINE_PRESETS.items() if v.get("enabled", True)]


@router.get("/presets/pipelines/{key}")
def get_pipeline_preset(key: str) -> dict:
    """Return a pipeline test preset JSON."""
    PIPELINE_PRESETS = get_pipeline_presets()
    if key not in PIPELINE_PRESETS:
        raise HTTPException(404, f"Pipeline preset '{key}' not found")
    preset = PIPELINE_PRESETS[key]
    example_path = os.path.join("/app", "shared", "examples", preset["example_file"])
    if not os.path.exists(example_path):
        example_path = os.path.join(
            os.path.dirname(__file__), "..", "shared", "examples", preset["example_file"]
        )
    if not os.path.exists(example_path):
        raise HTTPException(404, "Example file not found")
    with open(example_path) as f:
        return json.load(f)


@router.get("/presets/couplings")
def list_coupling_presets_endpoint() -> list[dict]:
    """Return list of all coupling test presets."""
    COUPLING_PRESETS = get_coupling_presets()
    return [{"key": k, **v} for k, v in COUPLING_PRESETS.items() if v.get("enabled", True)]


@router.get("/presets/couplings/{key}")
def get_coupling_preset(key: str) -> dict:
    """Return a coupling test preset JSON."""
    COUPLING_PRESETS = get_coupling_presets()
    if key not in COUPLING_PRESETS:
        raise HTTPException(404, f"Coupling preset '{key}' not found")
    preset = COUPLING_PRESETS[key]
    example_path = os.path.join("/app", "shared", "examples", preset["example_file"])
    if not os.path.exists(example_path):
        example_path = os.path.join(
            os.path.dirname(__file__), "..", "shared", "examples", preset["example_file"]
        )
    if not os.path.exists(example_path):
        raise HTTPException(404, "Example file not found")
    with open(example_path) as f:
        return json.load(f)


@router.get("/presets/{key}")
def get_preset(key: str) -> dict:
    PRESETS = get_presets()
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
def list_couplings() -> dict:
    """Return available tool couplings/pipelines."""
    COUPLINGS = get_couplings()
    return {k: v for k, v in COUPLINGS.items() if v.get("enabled", True)}


@router.get("/pipelines")
def list_pipelines() -> dict:
    """Return all named pipeline definitions (summary)."""
    PIPELINES = get_pipelines()
    return {
        key: {
            "key": key,
            "label": p["label"],
            "description": p["description"],
            "n_steps": len(p["steps"]),
        }
        for key, p in PIPELINES.items()
        if p.get("enabled", True)
    }


@router.get("/pipelines/{key}")
def get_pipeline(key: str) -> dict:
    """Return a named pipeline with full step details."""
    PIPELINES = get_pipelines()
    if key not in PIPELINES:
        raise HTTPException(404, f"Pipeline not found: {key}")
    return {"key": key, **PIPELINES[key]}


# --- Simulation ---

@router.post("/simulate")
async def submit_simulation(req: SimulationRequest) -> SimulationStatus:
    TOOL_REGISTRY = get_tool_registry()
    if req.tool not in TOOL_REGISTRY:
        raise HTTPException(400, f"Unknown tool: {req.tool}")

    # Input validation
    errors = validate_params(req.tool, req.params)
    if errors:
        raise HTTPException(422, detail=errors)

    increment_simulation(req.tool)

    # Ensure the worker container is running (no-op for embedded tools)
    from docker_manager import docker_mgr
    await docker_mgr.ensure_worker(req.tool)

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

    docker_mgr.record_activity(req.tool)

    write_audit("submit", "simulation", entity_id=task.id,
                details={"tool": req.tool, "project": req.project, "label": req.label})

    return SimulationStatus(
        job_id=task.id,
        tool=req.tool,
        status="PENDING",
    )


@router.post("/tools/{tool_key}/solo")
async def run_solo(tool_key: str, req: SimulationRequest) -> SimulationStatus:
    """Submit a simulation for a specific tool."""
    TOOL_REGISTRY = get_tool_registry()
    if tool_key not in TOOL_REGISTRY:
        raise HTTPException(400, f"Unknown tool: {tool_key}")
    req.tool = tool_key
    return await submit_simulation(req)


@router.get("/status/{job_id}")
def get_status(job_id: str) -> SimulationStatus:
    result = AsyncResult(job_id, app=celery_app)
    data = None
    progress = None
    message = None

    try:
        status = result.status
    except Exception:
        # Celery can't decode error metadata — treat as failed
        return SimulationStatus(
            job_id=job_id, tool="", status="FAILURE",
            message="Task failed (error details unavailable)",
        )

    if status == "PROGRESS":
        info = result.info or {}
        progress = info.get("progress", 0)
        message = info.get("message", "")
    elif status == "SUCCESS":
        data = result.result
    elif status == "FAILURE":
        try:
            message = str(result.result)
        except Exception:
            message = "Task failed"

    tool = ""
    try:
        if isinstance(result.result, dict):
            tool = result.result.get("tool", "")
    except Exception:
        pass

    return SimulationStatus(
        job_id=job_id,
        tool=tool,
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
async def submit_dag_pipeline(req: PipelineDAGRequest) -> dict:
    """Submit a DAG pipeline with parallel steps, conditionals, and variables."""
    try:
        increment_pipeline("dag")
        result = await pipeline_dag.start_dag_pipeline(req)
        write_audit("submit", "pipeline_dag", entity_id=result.get("pipeline_id"),
                    details={"label": req.label, "project": req.project})
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/pipeline/dag/{pipeline_id}")
async def get_dag_pipeline_status(pipeline_id: str) -> dict:
    """Get DAG pipeline execution status."""
    status = await pipeline_dag.get_dag_pipeline_status(pipeline_id)
    if status is None:
        raise HTTPException(404, "DAG pipeline not found")
    return status


@router.post("/pipeline")
async def submit_pipeline(req: PipelineRequest) -> dict:
    """Submit a multi-step sequential pipeline."""
    steps = [step.model_dump() for step in req.steps]

    # Validate all tools exist
    TOOL_REGISTRY = get_tool_registry()
    for step in steps:
        if step["tool"] not in TOOL_REGISTRY:
            raise HTTPException(400, f"Unknown tool in pipeline: {step['tool']}")

    increment_pipeline("sequential")
    result = await pipeline_engine.start_pipeline(steps, req.project, req.label)
    write_audit("submit", "pipeline", entity_id=result.get("pipeline_id"),
                details={"label": req.label, "project": req.project})
    return result


@router.get("/pipeline/{pipeline_id}")
async def get_pipeline_status(pipeline_id: str) -> dict:
    """Get pipeline execution status."""
    status = await pipeline_engine.get_pipeline_status(pipeline_id)
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
    write_audit("delete", "result", entity_id=job_id, details={"project": project})
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


# --- Layer activation (DB-backed) ---

@router.get("/layers/activation")
def get_layer_activation() -> dict:
    """Get layer activation state. Returns {layers: [...active layer keys]}."""
    LAYERS = get_layers()
    active = [k for k, v in LAYERS.items() if v.get("enabled", True)]
    return {"layers": sorted(active)}


class LayerActivationRequest(BaseModel):
    layers: list[str]


@router.post("/layers/activate")
def activate_layers(req: LayerActivationRequest) -> dict:
    """Activate layers (enable in DB)."""
    from db.registry_service import toggle_layer
    for layer_key in req.layers:
        toggle_layer(layer_key, True)
    LAYERS = get_layers()
    active = [k for k, v in LAYERS.items() if v.get("enabled", True)]
    return {"layers": sorted(active)}


@router.post("/layers/deactivate")
def deactivate_layers(req: LayerActivationRequest) -> dict:
    """Deactivate layers (disable in DB)."""
    from db.registry_service import toggle_layer
    for layer_key in req.layers:
        toggle_layer(layer_key, False)
    LAYERS = get_layers()
    active = [k for k, v in LAYERS.items() if v.get("enabled", True)]
    return {"layers": sorted(active)}
