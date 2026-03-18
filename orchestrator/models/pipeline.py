from typing import Any
from pydantic import BaseModel, Field


class PipelineStep(BaseModel):
    tool: str = Field(..., description="Tool key for this step")
    params: dict[str, Any] = Field(default_factory=dict, description="Tool-specific parameters")
    label: str | None = Field(default=None, description="Step label")
    param_map: dict[str, Any] | None = Field(
        default=None,
        description="Map param keys to previous step outputs, e.g. {'source_job_id': '$prev.job_id'}"
    )


class PipelineRequest(BaseModel):
    steps: list[PipelineStep] = Field(..., min_length=1, description="Ordered pipeline steps")
    project: str = Field(default="_default", description="Project for result grouping")
    label: str | None = Field(default=None, description="Pipeline label")


class PipelineStepStatus(BaseModel):
    step_index: int
    tool: str
    job_id: str | None = None
    status: str = "PENDING"
    progress: float = 0.0
    message: str | None = None
    result: dict[str, Any] | None = None


class PipelineStatus(BaseModel):
    pipeline_id: str
    status: str = "PENDING"  # PENDING, RUNNING, SUCCESS, FAILURE
    current_step: int = 0
    total_steps: int = 0
    steps: list[PipelineStepStatus] = Field(default_factory=list)
    label: str | None = None


# --- DAG Pipeline models (Phase 13) ---

class DAGStep(BaseModel):
    id: str = Field(..., description="Unique step identifier within pipeline")
    tool: str = Field(..., description="Tool key")
    params: dict[str, Any] = Field(default_factory=dict)
    label: str | None = None
    depends_on: list[str] = Field(default_factory=list, description="Step IDs that must complete first")
    param_map: dict[str, Any] | None = Field(
        default=None,
        description="Map param keys to step outputs: {'source_job_id': '$step_id.job_id'}"
    )
    condition: str | None = Field(
        default=None,
        description="Simple expression: \"$step_id.status == 'SUCCESS'\""
    )
    group: str | None = Field(default=None, description="Parallel group name")


class PipelineDAGRequest(BaseModel):
    steps: list[DAGStep] = Field(..., min_length=1)
    variables: dict[str, Any] = Field(default_factory=dict, description="Pipeline-level variables accessible as $var.name")
    project: str = Field(default="_default")
    label: str | None = None
