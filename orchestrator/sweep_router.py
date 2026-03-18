"""API routes for parameter sweep operations."""

from fastapi import APIRouter, HTTPException
from models.sweep import SweepRequest
import sweep as sweep_engine
from db.audit import write_audit

sweep_router = APIRouter(prefix="/api/sweep")


@sweep_router.post("/")
async def submit_sweep(req: SweepRequest) -> dict:
    """Submit a parameter sweep, returns sweep_id + initial status."""
    try:
        result = await sweep_engine.start_sweep(req)
        write_audit("submit", "sweep", entity_id=result.get("sweep_id"),
                    details={"tool": req.tool, "method": req.method, "project": req.project})
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))


@sweep_router.get("/{sweep_id}")
def get_sweep_status(sweep_id: str) -> dict:
    """Get sweep status with all run statuses."""
    status = sweep_engine.get_sweep_status(sweep_id)
    if status is None:
        raise HTTPException(404, "Sweep not found")
    return status


@sweep_router.get("/{sweep_id}/results")
def get_sweep_results(sweep_id: str) -> list[dict]:
    """Get all completed results for comparison."""
    results = sweep_engine.get_sweep_results(sweep_id)
    if results is None:
        raise HTTPException(404, "Sweep not found")
    return results


@sweep_router.delete("/{sweep_id}")
def cancel_sweep(sweep_id: str) -> dict:
    """Cancel remaining runs in a sweep."""
    status = sweep_engine.cancel_sweep(sweep_id)
    if status is None:
        raise HTTPException(404, "Sweep not found")
    return status
