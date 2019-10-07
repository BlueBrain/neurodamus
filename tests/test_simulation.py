import os
import pytest
import subprocess

sims = os.path.abspath(os.path.join(os.path.dirname(__file__), "simulations"))

requires_mpi = pytest.mark.skipif(
    os.environ.get("SLURM_JOB_ID") is None and os.environ.get("RUN_MPI") is None,
    reason="Simulation tests require MPI"
)


@pytest.mark.slow
@requires_mpi
def test_quick_v6():
    """A quick v6 test

    We require launching with mpiexec, so we do it in a bash script
    """
    simdir = os.path.join(sims, "mini_v6")

    ps = subprocess.run(["bash", "tests/test_simulation.bash", simdir])
    assert ps.returncode == 0


if __name__ == '__main__':
    test_quick_v6()
