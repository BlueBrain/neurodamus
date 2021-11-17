import os
import pytest
import subprocess
from tempfile import NamedTemporaryFile

from neurodamus.node import Node
from neurodamus.core import NeurodamusCore as Nd
from neurodamus.core.configuration import GlobalConfig, SimConfig, LogLevel
from neurodamus.utils import compat
from neurodamus.utils.logging import log_verbose


alltests = ['test_TTX_modification', 'test_ConfigureAllSections_modification']

# BlueConfig string
BC_str = """
Run Default
{{
    CellLibraryFile /gpfs/bbp.cscs.ch/project/proj83/circuits/Bio_M/20200805/circuit.mvd3
    nrnPath <NONE>
    CircuitPath .
    TargetFile {target_file}

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
    Duration 200
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
}}

Stimulus stimTest
{{
    Mode Current
    Pattern RelativeLinear
    Delay 0
    Duration 200
    PercentStart 120
}}

StimulusInject stimTestInject
{{
    Stimulus stimTest
    Target single
}}

Stimulus hypamp
{{
        Mode Current
     Pattern Hyperpolarizing
       Delay 0.0
    Duration 200
}}

StimulusInject hypampInject
{{
    Stimulus hypamp
      Target single
}}
"""

# Target file string
TGT_str = """
Target Cell single
{
    a3899539
}
"""


@pytest.mark.slow
@pytest.mark.skipif(
    not os.path.isfile("/gpfs/bbp.cscs.ch/project/proj83/circuits/Bio_M/20200805/circuit.mvd3"),
    reason="Circuit file not available")
@pytest.mark.skipif(
    not os.environ.get("NEURODAMUS_NEOCORTEX_ROOT"),
    reason="Test requires loading a neocortex model to run")
def test_modifications():
    for test in alltests:
        subprocess.run(
            ["python", os.path.abspath(__file__), test],
            check=True
        )


def exec_test_TTX_modification():
    """
    A test of enabling TTX with a short simulation.
    Expected outcome is non-zero spike count without TTX, zero with TTX.

    We require launching with mpiexec (numprocs=1).
    """
    # dump config to files
    with NamedTemporaryFile("w", prefix='test_ttx_mod_tgt', delete=False) as tgt_file:
        tgt_file.write(TGT_str)
    with NamedTemporaryFile("w", prefix="test_ttx_mod_bc", delete=False) as bc_file:
        bc_file.write(BC_str.format(target_file=tgt_file.name))

    # create Node from config
    GlobalConfig.verbosity = LogLevel.VERBOSE
    n = Node(bc_file.name)

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

    log_verbose("spikes without TTX = %s, with TTX = %s", nspike_noTTX, nspike_TTX)
    assert(nspike_noTTX > 0 and nspike_TTX == 0)
    os.unlink(bc_file.name)
    os.unlink(tgt_file.name)


def exec_test_ConfigureAllSections_modification():
    """
    A test of performing ConfigureAllSections with a short simulation.
    Expected outcome is higher spike count when enabled.

    We require launching with mpiexec (numprocs=1).
    """
    with NamedTemporaryFile("w", prefix='test_allsec_mod_tgt', delete=False) as tgt_file:
        tgt_file.write(TGT_str)
    with NamedTemporaryFile("w", prefix="test_allsec_mod_bc", delete=False) as bc_file:
        bc_file.write(BC_str.format(target_file=tgt_file.name))

    # create Node from config
    GlobalConfig.verbosity = LogLevel.VERBOSE
    n = Node(bc_file.name)

    # setup sim
    n.load_targets()
    n.create_cells()
    n.create_synapses()
    n.enable_stimulus()
    n.sim_init()
    n.solve()
    nspike_noConfigureAllSections = sum(len(spikes) for spikes, _ in n._spike_vecs)

    # append modification to config directly
    ConfigureAllSections_mod = compat.Map(Nd.Map())
    ConfigureAllSections_mod["Type"] = "ConfigureAllSections"
    ConfigureAllSections_mod["Target"] = "single"
    ConfigureAllSections_mod["SectionConfigure"] = "%s.gSK_E2bar_SK_E2 = 0"
    # set HOC map as value of key "no_SK_E2"
    SimConfig.modifications.hoc_map.put("no_SK_E2", ConfigureAllSections_mod.hoc_map)
    # manually update item count in compat.Map
    SimConfig.modifications._size = int(SimConfig.modifications.hoc_map.count())

    # setup sim again
    Nd.t = 0.0
    n._sim_ready = False
    n.enable_modifications()
    n.sim_init()
    n.solve()
    nspike_ConfigureAllSections = sum(len(spikes) for spikes, _ in n._spike_vecs)

    log_verbose("spikes without ConfigureAllSections = %s, with ConfigureAllSections = %s",
                nspike_ConfigureAllSections, nspike_noConfigureAllSections)
    assert(nspike_ConfigureAllSections > nspike_noConfigureAllSections)
    os.unlink(bc_file.name)
    os.unlink(tgt_file.name)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        exec('exec_{}()'.format(sys.argv[1]))
    else:
        test_modifications()
