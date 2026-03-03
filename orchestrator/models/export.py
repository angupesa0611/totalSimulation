from pydantic import BaseModel, Field


class ExportRequest(BaseModel):
    job_ids: list[str] = Field(..., min_length=1, description="One or more result job_ids")
    format: str = Field(default="csv", description="Export format: csv, json, latex, pdf")
    columns: list[str] | None = Field(default=None, description="Specific result keys to include (None = all)")
    title: str | None = Field(default=None, description="Title for PDF/LaTeX header")
    project: str = Field(default="_default")


class ExportResponse(BaseModel):
    export_id: str
    format: str
    download_url: str
    filename: str
