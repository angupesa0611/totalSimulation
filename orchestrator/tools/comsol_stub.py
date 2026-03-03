"""COMSOL stub — deferred due to license unavailability.

FEniCS and Elmer provide full open-source coverage of COMSOL's capabilities.
When a commercial license is acquired, this stub will be replaced with the
actual COMSOL batch-mode integration (comsolbatch CLI + Java API).
"""

from celery_app import app
import results as results_store


COMSOL_ERROR = (
    "COMSOL is not yet licensed. Use FEniCS or Elmer for "
    "continuum/multiphysics simulation. COMSOL will be enabled "
    "when a commercial license is acquired.\n\n"
    "Equivalent open-source alternatives:\n"
    "  - FEniCS: custom PDE research (variational form)\n"
    "  - Elmer: built-in multiphysics (thermal-structural, EM)\n"
    "  - Firedrake: high-performance FEM with PETSc backend"
)


@app.task(name="tools.comsol_stub.run_comsol", bind=True, soft_time_limit=5)
def run_comsol(self, params=None, project="_default", label=None):
    """Stub task — always fails with a clear message."""
    raise NotImplementedError(COMSOL_ERROR)
