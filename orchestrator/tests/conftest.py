"""Shared fixtures for orchestrator tests."""

import sys
import os
import pytest
from unittest.mock import MagicMock, patch

# Add orchestrator root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def mock_celery_app():
    """Mock the Celery app to avoid needing Redis."""
    with patch("celery_app.app") as mock_app:
        # Mock send_task to return a task with a fake ID
        mock_task = MagicMock()
        mock_task.id = "test-task-id-001"
        mock_app.send_task.return_value = mock_task

        # Mock signature for group operations
        mock_sig = MagicMock()
        mock_sig.id = "test-task-id-001"
        mock_app.signature.return_value = mock_sig

        yield mock_app


@pytest.fixture
def sample_rebound_result():
    """Sample REBOUND simulation result."""
    return {
        "tool": "rebound",
        "job_id": "job-rebound-001",
        "status": "SUCCESS",
        "data": {
            "n_particles": 5,
            "time_final": 6.28,
            "energy": {
                "kinetic": 1.5e30,
                "potential": -3.0e30,
                "total": -1.5e30,
            },
            "positions": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
        },
    }


@pytest.fixture
def sample_qutip_result():
    """Sample QuTiP simulation result."""
    return {
        "tool": "qutip",
        "job_id": "job-qutip-001",
        "status": "SUCCESS",
        "data": {
            "n_times": 100,
            "expectation_values": [0.5, 0.3, 0.1],
            "final_state": "ground",
        },
    }


@pytest.fixture
def sample_flat_results():
    """Pre-flattened results for export tests."""
    return [
        {
            "_job_id": "job-001",
            "tool": "rebound",
            "data.energy.kinetic": 1.5e30,
            "data.energy.potential": -3.0e30,
            "data.n_particles": 5,
        },
        {
            "_job_id": "job-002",
            "tool": "qutip",
            "data.energy.kinetic": 0.5,
            "data.energy.potential": -1.0,
            "data.n_particles": 2,
        },
    ]
