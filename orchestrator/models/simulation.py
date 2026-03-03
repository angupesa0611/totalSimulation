from typing import Any
from pydantic import BaseModel, Field


class SimulationRequest(BaseModel):
    tool: str = Field(..., description="Tool name: rebound, qutip, openmm, pyscf, mdanalysis, psi4, gromacs, namd, qmmm")
    params: dict[str, Any] = Field(..., description="Tool-specific parameters")
    project: str = Field(default="_default", description="Project for result grouping")
    label: str | None = Field(default=None, description="Human-readable run label")
    input_from: str | None = Field(default=None, description="Job ID to use as input (for pipeline chaining)")


class SimulationStatus(BaseModel):
    job_id: str
    tool: str
    status: str  # PENDING, STARTED, PROGRESS, SUCCESS, FAILURE
    progress: float | None = None  # 0.0 to 1.0
    message: str | None = None
    result: dict[str, Any] | None = None


class SimulationResult(BaseModel):
    job_id: str
    tool: str
    label: str | None = None
    project: str = "_default"
    status: str = "SUCCESS"
    data: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
