import os
import pytest
import subprocess
from pathlib import Path

SIM_DIR = Path(__file__).parent.absolute() / "simulations"

requires_mpi = pytest.mark.skipif(
    os.environ.get("SLURM_JOB_ID") is None and os.environ.get("RUN_MPI") is None,
    reason="Simulation tests require MPI")


@pytest.mark.slow
@requires_mpi
def test_quick_v6():
    """A quick v6 test

    We require launching with mpiexec, so we do it in a bash script
    """
    simdir = SIM_DIR / "mini_v6"
    subprocess.run(
        ["bash", "tests/test_simulation.bash", simdir, "BlueConfig", "mpiexec"],
        check=True
    )
