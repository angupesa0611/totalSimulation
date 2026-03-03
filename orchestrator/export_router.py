"""API routes for academic export operations."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from models.export import ExportRequest, ExportResponse
import export_engine

export_router = APIRouter(prefix="/api/export")

# Track exports for download
_export_files: dict[str, dict] = {}


@export_router.post("/")
def submit_export(req: ExportRequest) -> ExportResponse:
    """Generate export file, returns export_id + download_url."""
    try:
        export_id, filepath, filename = export_engine.export_results(
            job_ids=req.job_ids,
            format=req.format,
            columns=req.columns,
            title=req.title,
            project=req.project,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

    _export_files[export_id] = {"filepath": filepath, "filename": filename}

    return ExportResponse(
        export_id=export_id,
        format=req.format,
        download_url=f"/api/export/download/{export_id}",
        filename=filename,
    )


@export_router.get("/download/{export_id}")
def download_export(export_id: str):
    """Download an exported file."""
    info = _export_files.get(export_id)
    if not info:
        raise HTTPException(404, "Export not found")

    import os
    if not os.path.exists(info["filepath"]):
        raise HTTPException(404, "Export file not found on disk")

    media_types = {
        ".csv": "text/csv",
        ".json": "application/json",
        ".tex": "text/plain",
        ".pdf": "application/pdf",
    }
    ext = os.path.splitext(info["filename"])[1]
    media_type = media_types.get(ext, "application/octet-stream")

    return FileResponse(
        info["filepath"],
        filename=info["filename"],
        media_type=media_type,
    )


@export_router.get("/formats")
def list_formats() -> list[dict]:
    """List available export formats."""
    return [
        {"key": "csv", "name": "CSV", "description": "Comma-separated values, compatible with Excel/R/pandas"},
        {"key": "json", "name": "JSON", "description": "Structured JSON array with filtered columns"},
        {"key": "latex", "name": "LaTeX", "description": "LaTeX tabular with booktabs formatting"},
        {"key": "pdf", "name": "PDF", "description": "PDF report with title page and data table"},
    ]
