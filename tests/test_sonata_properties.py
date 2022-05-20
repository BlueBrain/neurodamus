import logging
import os
import pytest
import subprocess
from tempfile import NamedTemporaryFile

from neurodamus.node import Node
from neurodamus.core import NeurodamusCore as Nd
from neurodamus.core.configuration import GlobalConfig, SimConfig, LogLevel
from neurodamus.utils import compat


alltests = ['test_input_resistance', 'test_input_resistance_2']

# BlueConfig string
BC_str = """
Run Default
{{
    CellLibraryFile \
/gpfs/bbp.cscs.ch/project/proj83/circuits/Bio_M/20200805/sonata/networks/nodes/All/nodes.h5
    nrnPath <NONE>
    CircuitPath .

    BioName /gpfs/bbp.cscs.ch/project/proj83/circuits/Bio_M/20200805/bioname
    Atlas /gpfs/bbp.cscs.ch/project/proj83/data/atlas/S1/MEAN/P14-MEAN

    METypePath /gpfs/bbp.cscs.ch/project/proj83/singlecell/release_2020-07-31/hoc
    MEComboInfoFile \
/gpfs/bbp.cscs.ch/project/proj83/singlecell/fixed_L6_allBPC_thresholds/mecombo_emodel.tsv
    MorphologyPath /gpfs/bbp.cscs.ch/project/proj83/morphologies/fixed_ais_L23PC_20201210/ascii
    MorphologyType asc

    CurrentDir .
    OutputRoot .

    TargetFile {target_file}
    CircuitTarget small
    Duration 300
    Dt 0.025

    RNGMode Random123
    BaseSeed 549821
    StimulusSeed 549821

    Simulator NEURON
    RunMode WholeCell
    ForwardSkip 0

    MinisSingleVesicle 1
    SpikeLocation AIS
    V_Init -80
}}
"""

# Target file string
TGT_str = """
Target Cell single
{
  a3899540
}

Target Compartment single_all
{
  single
}

Target Section single_soma
{
  single soma
}

Target Cell small
{
 a3425774
 a3868780
 a2886525
 a3099746
}

Target Compartment small_all
{
  small
}

Target Section small_soma
{
  small soma
}
"""

NODE = "/gpfs/bbp.cscs.ch/project/proj83/circuits/Bio_M/20200805/sonata/networks/nodes/All/nodes.h5"


@pytest.mark.slow
@pytest.mark.skipif(
    not os.path.isfile(NODE),
    reason="Circuit file not available")
@pytest.mark.skipif(
    not os.environ.get("NEURODAMUS_NEOCORTEX_ROOT"),
    reason="Test requires loading a neocortex model to run")
def unit_test():
    for test in alltests:
        subprocess.run(
            ["python", os.path.abspath(__file__), test],
            check=True
        )


def exec_test_input_resistance():
    """
    A test of getting input resistance values from SONATA nodes file. BBPBGLIB-806
    """
    # dump config to files
    with NamedTemporaryFile("w", prefix='test_input_resistance_tgt', delete=False) as tgt_file:
        tgt_file.write(TGT_str)
    with NamedTemporaryFile("w", prefix="test_input_resistance_bc", delete=False) as bc_file:
        bc_file.write(BC_str.format(target_file=tgt_file.name))

    # create Node from config
    GlobalConfig.verbosity = LogLevel.VERBOSE
    n = Node(bc_file.name)

    # append Stimulus and StimulusInject blocks programmatically
    # relativeOU
    STIM_relativeOU = compat.Map(Nd.Map())
    STIM_relativeOU["Mode"] = "Conductance"
    STIM_relativeOU["Pattern"] = "RelativeOrnsteinUhlenbeck"
    STIM_relativeOU["Delay"] = 50
    STIM_relativeOU["Duration"] = 200
    STIM_relativeOU["Reversal"] = 0
    STIM_relativeOU["Tau"] = 2.8
    STIM_relativeOU["MeanPercent"] = 20
    STIM_relativeOU["SDPercent"] = 20
    SimConfig.stimuli.hoc_map.put("relativeOU", STIM_relativeOU.hoc_map)
    SimConfig.stimuli._size = int(SimConfig.stimuli.hoc_map.count())
    # inject_relativeOU
    INJECT_relativeOU = compat.Map(Nd.Map())
    INJECT_relativeOU["Stimulus"] = "relativeOU"
    INJECT_relativeOU["Target"] = "small"
    SimConfig.injects.hoc_map.put("inject_relativeOU", INJECT_relativeOU.hoc_map)
    SimConfig.injects._size = int(SimConfig.injects.hoc_map.count())

    # check requirements again (NOTE: should be callable from SimConfig)
    logging.info("Checking simulation requirements")
    for requisitor in SimConfig._requisitors:
        requisitor(SimConfig, SimConfig._config_parser)

    # setup sim
    n.load_targets()
    n.create_cells()
    n.create_synapses()
    n.enable_stimulus()
    # manually finalize synapse managers (otherwise netcons are not created)
    for syn_manager in n._circuits.all_synapse_managers():
        syn_manager.finalize(n._run_conf.get("BaseSeed", 0), SimConfig.coreneuron)
    n.sim_init()
    n.solve()

    # check spikes
    nspike = sum(len(spikes) for spikes, _ in n._spike_vecs)
    assert(nspike == 9)

    # remove temporary files
    os.unlink(bc_file.name)
    os.unlink(tgt_file.name)


def exec_test_input_resistance_2():
    """
    A test of getting input resistance values from SONATA nodes file. BBPBGLIB-806
    """
    # dump config to files
    with NamedTemporaryFile("w", prefix='test_input_resistance_2_tgt', delete=False) as tgt_file:
        tgt_file.write(TGT_str)
    with NamedTemporaryFile("w", prefix="test_input_resistance_2_bc", delete=False) as bc_file:
        bc_file.write(BC_str.format(target_file=tgt_file.name))

    # create Node from config
    GlobalConfig.verbosity = LogLevel.VERBOSE
    n = Node(bc_file.name)

    # append Stimulus and StimulusInject blocks programmatically
    # relativeSN
    STIM_relativeSN = compat.Map(Nd.Map())
    STIM_relativeSN["Mode"] = "Conductance"
    STIM_relativeSN["Pattern"] = "RelativeShotNoise"
    STIM_relativeSN["Delay"] = 50
    STIM_relativeSN["Duration"] = 200
    STIM_relativeSN["Reversal"] = 0
    STIM_relativeSN["RiseTime"] = 2.8
    STIM_relativeSN["DecayTime"] = 28
    STIM_relativeSN["AmpCV"] = 0.5
    STIM_relativeSN["MeanPercent"] = 20
    STIM_relativeSN["SDPercent"] = 20
    SimConfig.stimuli.hoc_map.put("relativeSN", STIM_relativeSN.hoc_map)
    SimConfig.stimuli._size = int(SimConfig.stimuli.hoc_map.count())
    # inject_relativeSN
    INJECT_relativeSN = compat.Map(Nd.Map())
    INJECT_relativeSN["Stimulus"] = "relativeSN"
    INJECT_relativeSN["Target"] = "small"
    SimConfig.injects.hoc_map.put("inject_relativeSN", INJECT_relativeSN.hoc_map)
    SimConfig.injects._size = int(SimConfig.injects.hoc_map.count())

    # check requirements again (NOTE: should be callable from SimConfig)
    logging.info("Checking simulation requirements")
    for requisitor in SimConfig._requisitors:
        requisitor(SimConfig, SimConfig._config_parser)

    # setup sim
    n.load_targets()
    n.create_cells()
    n.create_synapses()
    n.enable_stimulus()
    # manually finalize synapse managers (otherwise netcons are not created)
    for syn_manager in n._circuits.all_synapse_managers():
        syn_manager.finalize(n._run_conf.get("BaseSeed", 0), SimConfig.coreneuron)
    n.sim_init()
    n.solve()

    # check spikes
    nspike = sum(len(spikes) for spikes, _ in n._spike_vecs)
    assert(nspike == 12)

    # remove temporary files
    os.unlink(bc_file.name)
    os.unlink(tgt_file.name)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        exec('exec_{}()'.format(sys.argv[1]))
    else:
        unit_test()
