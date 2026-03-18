"""Worker container management API."""

from fastapi import APIRouter, HTTPException
from docker_manager import docker_mgr, TOOL_CONTAINER_MAP, WorkerContainerNotFound

workers_router = APIRouter(prefix="/api/workers", tags=["workers"])


@workers_router.get("/")
def list_workers():
    """List all worker container statuses."""
    return docker_mgr.get_worker_status()


@workers_router.get("/{service_name}")
def get_worker(service_name: str):
    """Get a single worker's status."""
    if service_name not in TOOL_CONTAINER_MAP.values():
        raise HTTPException(404, f"Unknown worker service: {service_name}")
    statuses = docker_mgr.get_worker_status()
    for s in statuses:
        if s["service"] == service_name:
            return s
    raise HTTPException(404, "Worker not found")


@workers_router.post("/start/{tool_key}")
async def start_worker_endpoint(tool_key: str):
    """Start the worker container for a tool. Builds if container doesn't exist."""
    if tool_key not in TOOL_CONTAINER_MAP:
        # Embedded tool — no container needed, always ready
        return {"tool_key": tool_key, "status": "embedded"}
    try:
        result = await docker_mgr.ensure_worker(tool_key)
        return {"tool_key": tool_key, "status": "running", **result}
    except WorkerContainerNotFound:
        # Container doesn't exist — build it, then start
        try:
            await docker_mgr.build_worker(tool_key)
            result = await docker_mgr.ensure_worker(tool_key)
            return {"tool_key": tool_key, "status": "running", "built": True, **result}
        except RuntimeError as e:
            raise HTTPException(500, str(e))
        except WorkerContainerNotFound as e:
            raise HTTPException(503, str(e))


@workers_router.post("/{service_name}/stop")
async def stop_worker(service_name: str):
    """Manually stop a worker container."""
    if service_name not in TOOL_CONTAINER_MAP.values():
        raise HTTPException(404, f"Unknown worker service: {service_name}")
    stopped = await docker_mgr.stop_worker(service_name)
    if not stopped:
        raise HTTPException(400, "Worker is not running")
    return {"service": service_name, "status": "stopped"}
