"""AlphaFold stub — deferred due to storage requirements (~500GB minimum).

PyRosetta + OpenMM cover the protein structure layer in the interim.
PyRosetta handles ab initio structure prediction (fragment assembly),
homology modeling, docking, and protein design. OpenMM provides
energy minimization and dynamics refinement.

When storage becomes available, this stub will be replaced with the
actual AlphaFold/ColabFold integration.
"""

from celery_app import app
import results as results_store


ALPHAFOLD_ERROR = (
    "AlphaFold is deferred — requires ~500 GB storage for the reduced "
    "database (2.2 TB for full database). ColabFold MMseqs2 (~100 GB) "
    "is a lighter alternative to evaluate when storage is available.\n\n"
    "Current alternatives:\n"
    "  - PyRosetta: ab initio folding, homology modeling, docking (Phase 10)\n"
    "  - OpenMM: energy minimization and MD refinement of structures"
)


@app.task(name="tools.alphafold_stub.run_alphafold", bind=True, soft_time_limit=5)
def run_alphafold(self, params=None, project="_default", label=None):
    """Stub task — always fails with a clear message."""
    raise NotImplementedError(ALPHAFOLD_ERROR)
