"""PyRosetta stub — deferred due to academic license requirement.

PyRosetta is a Python interface to the Rosetta macromolecular modeling suite.
It requires an academic license obtained from PyRosetta.org. Capabilities include
ab initio protein folding, homology modeling, ligand docking, and protein design.

OpenMM provides energy minimization and MD refinement as an alternative for
basic structural refinement tasks.

When a PyRosetta license is acquired, this stub will be replaced with the
actual PyRosetta integration.
"""

from celery_app import app
import results as results_store


PYROSETTA_ERROR = (
    "PyRosetta is deferred — requires an academic license from PyRosetta.org.\n\n"
    "Capabilities (when enabled):\n"
    "  - Ab initio protein folding (fragment assembly)\n"
    "  - Homology modeling (comparative modeling)\n"
    "  - Ligand docking (small molecule + protein)\n"
    "  - Protein design (sequence optimization)\n\n"
    "Current alternatives:\n"
    "  - OpenMM: energy minimization and MD refinement of protein structures\n"
    "  - AlphaFold: deep learning structure prediction (also deferred — storage)"
)


@app.task(name="tools.pyrosetta_stub.run_pyrosetta", bind=True, soft_time_limit=5)
def run_pyrosetta(self, params=None, project="_default", label=None):
    """Stub task — always fails with a clear message."""
    raise NotImplementedError(PYROSETTA_ERROR)
