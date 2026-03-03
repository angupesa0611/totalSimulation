from typing import Any
from pydantic import BaseModel, Field


class SweepAxis(BaseModel):
    param: str = Field(..., description="Dot-path into params dict, e.g. 'n_steps' or 'integrator.dt'")
    values: list[Any] | None = Field(default=None, description="Explicit list of values")
    range: dict | None = Field(default=None, description="Range spec: {min, max, steps}")
    log_scale: bool = Field(default=False, description="Use log spacing for range")


class SweepRequest(BaseModel):
    tool: str = Field(..., description="Tool key to sweep over")
    base_params: dict[str, Any] = Field(default_factory=dict, description="Base parameters (axes override specific keys)")
    axes: list[SweepAxis] = Field(..., min_length=1, max_length=3, description="1-3 sweep axes")
    method: str = Field(default="grid", description="Sampling method: grid, random, lhs")
    n_samples: int | None = Field(default=None, description="Number of samples for random/lhs")
    project: str = Field(default="_default")
    label: str | None = None


class SweepRunInfo(BaseModel):
    run_index: int
    params: dict[str, Any]
    job_id: str | None = None
    status: str = "PENDING"
    result_summary: dict[str, Any] | None = None


class SweepStatus(BaseModel):
    sweep_id: str
    status: str = "PENDING"  # PENDING, RUNNING, PARTIAL, SUCCESS, FAILURE
    total_runs: int = 0
    completed_runs: int = 0
    failed_runs: int = 0
    runs: list[SweepRunInfo] = Field(default_factory=list)
