import os
import pytest
import subprocess

from neurodamus.node import Node
from neurodamus.core import NeurodamusCore as Nd
from neurodamus.core.configuration import SimConfig
from neurodamus.utils import compat

requires_mpi = pytest.mark.skipif(
    os.environ.get("SLURM_JOB_ID") is None and os.environ.get("RUN_MPI") is None,
    reason="Modification tests require MPI"
)

# BlueConfig string
BC_str = """
Run Default
{
    CellLibraryFile /gpfs/bbp.cscs.ch/project/proj83/circuits/Bio_M/20200805/circuit.mvd3
    nrnPath <NONE>
    CircuitPath .
    TargetFile /tmp/test_modification_tgt.tmp

    BioName /gpfs/bbp.cscs.ch/project/proj83/circuits/Bio_M/20200805/bioname
    Atlas /gpfs/bbp.cscs.ch/project/proj83/data/atlas/S1/MEAN/P14-MEAN

    METypePath /gpfs/bbp.cscs.ch/project/proj83/singlecell/release_2020-07-31/hoc
    MEComboInfoFile /gpfs/bbp.cscs.ch/project/proj83/singlecell/fixed_L6_allBPC_thresholds/\
mecombo_emodel.tsv
    MorphologyPath /gpfs/bbp.cscs.ch/project/proj83/morphologies/fixed_ais_L23PC_20201210/ascii
    MorphologyType asc

    CurrentDir .
    OutputRoot .

    CircuitTarget single
    Duration 100
    Dt 0.025

    RNGMode Random123
    BaseSeed 549821

    Simulator NEURON
    RunMode WholeCell
    ForwardSkip 0

    ExtracellularCalcium 1.20
    MinisSingleVesicle 1
    SpikeLocation AIS
    V_Init -80
}

Stimulus stimTest
{
    Mode Current
    Pattern RelativeLinear
    Delay 0
    Duration 500
    PercentStart 120
}

StimulusInject stimTestInject
{
    Stimulus stimTest
    Target single
}

Stimulus hypamp
{
        Mode Current
     Pattern Hyperpolarizing
       Delay 0.0
    Duration 500
}

StimulusInject hypampInject
{
    Stimulus hypamp
      Target single
}
"""

# Target file string
TGT_str = """
Target Cell single
{
    a3899539
}
"""


@pytest.mark.slow
@requires_mpi
def test_modifications():
    ps = subprocess.run(["mpiexec", "-np", "1",
                         "python", os.path.abspath(__file__), "run"])
    assert ps.returncode == 0


def exec_test_ttx_modification():
    """
    A test of enabling TTX with a short simulation.
    Expected outcome is non-zero spike count without TTX, zero with TTX.

    We require launching with mpiexec (numprocs=1).
    """
    # dump config to file
    with open('/tmp/test_modification_bc.tmp', 'w') as f:
        print(BC_str, file=f)

    # dump target to file
    with open('/tmp/test_modification_tgt.tmp', 'w') as f:
        print(TGT_str, file=f)

    # create Node from config
    n = Node('/tmp/test_modification_bc.tmp')

    # setup sim
    n.load_targets()
    n.create_cells()
    n.create_synapses()
    n.enable_stimulus()
    n.sim_init()
    n.solve()
    # _spike_vecs is a list of (spikes, ids)
    nspike_noTTX = sum(len(spikes) for spikes, _ in n._spike_vecs)

    # append modification to config directly
    TTX_mod = compat.Map(Nd.Map())
    TTX_mod["Type"] = "TTX"
    TTX_mod["Target"] = "single"
    # set HOC map as value of key "applyTTX"
    SimConfig.modifications.hoc_map.put("applyTTX", TTX_mod.hoc_map)
    # manually update item count in compat.Map
    SimConfig.modifications._size = int(SimConfig.modifications.hoc_map.count())

    # setup sim again
    Nd.t = 0.0
    n._sim_ready = False
    n.enable_modifications()
    n.sim_init()
    n.solve()
    nspike_TTX = sum(len(spikes) for spikes, _ in n._spike_vecs)

    assert(nspike_noTTX > 0 and nspike_TTX == 0)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'run':
        exec_test_ttx_modification()
        # tests for other Modifications go here
    else:
        test_modifications()
