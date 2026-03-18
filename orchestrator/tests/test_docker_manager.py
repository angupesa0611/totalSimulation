"""Tests for the on-demand worker container manager."""

import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

import pytest

from docker_manager import DockerManager, TOOL_CONTAINER_MAP, WorkerContainerNotFound


EMBEDDED_TOOLS = [
    "rebound", "qutip", "pyscf", "mdanalysis", "pybullet", "einsteinpy",
    "basico", "tellurium", "brian2", "msprime", "rdkit", "cantera",
    "sympy", "gmsh", "lcapy", "pennylane", "lammps", "lean4", "gap",
    "pyspice", "qiskit", "matplotlib", "control", "pyomo", "networkx",
    "phiflow", "nrpy", "comsol", "alphafold", "tskit", "simupop",
    "pyrosetta", "rayoptics", "lightpipes", "strawberryfields", "openbabel",
]


@pytest.fixture
def manager():
    return DockerManager()


def test_embedded_tools_return_none(manager):
    """Embedded tools (running inside orchestrator) should return None."""
    for tool in EMBEDDED_TOOLS:
        assert manager.get_service_for_tool(tool) is None, f"{tool} should be embedded"


def test_containerized_tools_return_service(manager):
    """Containerized tools should return their docker-compose service name."""
    assert manager.get_service_for_tool("openmm") == "openmm-worker"
    assert manager.get_service_for_tool("psi4") == "psi4-worker"
    assert manager.get_service_for_tool("manim") == "manim-worker"
    assert manager.get_service_for_tool("einstein_toolkit") == "einstein-toolkit-worker"
    assert manager.get_service_for_tool("meep") == "meep-worker"


def test_tool_container_map_completeness():
    """All 19 containerized worker services must be in the map."""
    assert len(TOOL_CONTAINER_MAP) == 19
    expected_services = {
        "openmm-worker", "psi4-worker", "gromacs-worker", "namd-worker",
        "qmmm-worker", "fenics-worker", "elmer-worker", "nest-worker",
        "qe-worker", "sagemath-worker", "manim-worker", "su2-worker",
        "firedrake-worker", "openfoam-worker", "dedalus-worker",
        "einstein-toolkit-worker", "slim-worker", "vtk-worker", "meep-worker",
    }
    assert set(TOOL_CONTAINER_MAP.values()) == expected_services


@pytest.mark.asyncio
async def test_ensure_worker_embedded_noop(manager):
    """Embedded tools should return {'needed': False} without touching Docker."""
    result = await manager.ensure_worker("rebound")
    assert result == {"needed": False}


@pytest.mark.asyncio
async def test_ensure_worker_already_running(manager):
    """If container is already running, should return started=False."""
    mock_container = MagicMock()
    mock_container.status = "running"

    with patch.object(manager, '_find_container', return_value=mock_container):
        result = await manager.ensure_worker("openmm")
        assert result["needed"] is True
        assert result["started"] is False
        mock_container.start.assert_not_called()


@pytest.mark.asyncio
async def test_ensure_worker_starts_stopped(manager):
    """If container is stopped, should start it."""
    mock_container = MagicMock()
    mock_container.status = "exited"
    mock_container.start = MagicMock()

    with patch.object(manager, '_find_container', return_value=mock_container), \
         patch.object(manager, '_wait_for_celery_ready', new_callable=AsyncMock):
        result = await manager.ensure_worker("openmm")
        assert result["needed"] is True
        assert result["started"] is True
        assert result["service"] == "openmm-worker"


@pytest.mark.asyncio
async def test_ensure_worker_not_found_raises(manager):
    """If container doesn't exist at all, should raise WorkerContainerNotFound."""
    with patch.object(manager, '_find_container', return_value=None):
        with pytest.raises(WorkerContainerNotFound):
            await manager.ensure_worker("openmm")


def test_record_activity(manager):
    """Recording activity should update the last_activity timestamp."""
    manager.record_activity("openmm")
    assert "openmm-worker" in manager._last_activity
    assert manager._last_activity["openmm-worker"] > 0

    # Embedded tools should not create activity entries
    manager.record_activity("rebound")
    assert "rebound" not in manager._last_activity
