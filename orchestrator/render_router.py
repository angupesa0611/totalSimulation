"""Render API — convert simulation results into Manim animations."""

from fastapi import APIRouter, HTTPException
from celery_app import app as celery_app
import results as results_store
from manim_converters import get_converter, get_available_scenes, CONVERTER_REGISTRY

render_router = APIRouter(prefix="/api/render")


@render_router.get("/scenes/{tool_key}")
def list_scenes_for_tool(tool_key: str):
    """Return available Manim scene types for a tool."""
    scenes = get_available_scenes(tool_key)
    if not scenes:
        raise HTTPException(404, f"No Manim scenes for tool: {tool_key}")
    return {"tool": tool_key, "scenes": scenes}


@render_router.post("/from-result/{job_id}")
def render_from_result(job_id: str, body: dict = {}):
    """Render a Manim animation from an existing simulation result.

    Body (optional): {scene_type, quality, format, project, options}
    """
    project = body.get("project", "_default")
    result = results_store.get_result(job_id, project)
    if not result:
        raise HTTPException(404, f"Result not found: {job_id}")

    tool_key = result.get("tool")
    if not tool_key:
        raise HTTPException(400, "Result has no tool field")

    converter = get_converter(tool_key)
    if not converter:
        raise HTTPException(400, f"No Manim converter for tool: {tool_key}")

    scene_type = body.get("scene_type") or converter.default_scene(result)
    quality = body.get("quality", "medium_quality")
    fmt = body.get("format", "mp4")

    # Convert result -> Manim params
    manim_params = converter.convert(result, scene_type, body.get("options"))
    manim_params["quality"] = quality
    manim_params["format"] = fmt

    # Submit to Manim queue
    task = celery_app.send_task(
        "tools.manim_tool.run_manim",
        kwargs={"params": manim_params, "project": project,
                "label": f"Render: {tool_key}/{scene_type}"},
        queue="render-manim",
    )
    return {"render_job_id": task.id, "scene_type": scene_type, "status": "PENDING"}


@render_router.get("/tools")
def list_renderable_tools():
    """Return all tools that have Manim converters."""
    return {
        tool_key: conv.supported_scenes()
        for tool_key, conv in CONVERTER_REGISTRY.items()
    }


@render_router.post("/pipeline/{pipeline_id}")
def render_pipeline(pipeline_id: str, body: dict = {}):
    """Render a composite animation from a completed pipeline.

    Renders each step's result that has a converter, then returns render job IDs.
    Composite stitching via ffmpeg is deferred to client-side or a follow-up task.
    """
    project = body.get("project", "_default")
    quality = body.get("quality", "medium_quality")
    fmt = body.get("format", "mp4")

    # Load pipeline results from index
    all_results = results_store.list_results(project)
    pipeline_results = [r for r in all_results
                        if r.get("label", "").startswith(f"Pipeline {pipeline_id}")]

    if not pipeline_results:
        raise HTTPException(404, f"No results found for pipeline: {pipeline_id}")

    render_jobs = []
    for meta in pipeline_results:
        result = results_store.get_result(meta["job_id"], project)
        if not result:
            continue

        tool_key = result.get("tool") or meta.get("tool")
        if not tool_key:
            continue

        converter = get_converter(tool_key)
        if not converter:
            continue

        scene_type = converter.default_scene(result)
        manim_params = converter.convert(result, scene_type)
        manim_params["quality"] = quality
        manim_params["format"] = fmt

        task = celery_app.send_task(
            "tools.manim_tool.run_manim",
            kwargs={"params": manim_params, "project": project,
                    "label": f"Pipeline render: {tool_key}/{scene_type}"},
            queue="render-manim",
        )
        render_jobs.append({
            "render_job_id": task.id,
            "tool": tool_key,
            "scene_type": scene_type,
            "source_job_id": meta["job_id"],
        })

    if not render_jobs:
        raise HTTPException(400, "No renderable steps found in pipeline")

    return {"pipeline_id": pipeline_id, "render_jobs": render_jobs, "status": "PENDING"}
