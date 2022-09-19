import os
import pytest
from tempfile import NamedTemporaryFile

from neurodamus.node import Node
from neurodamus.core.configuration import GlobalConfig, SimConfig, LogLevel
from neurodamus.utils import compat


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

    CircuitTarget L5_5cells
    Duration 200
    Dt 0.025

    RNGMode Random123
    BaseSeed 549821

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
Target Cell L5_5cells
{
    pre_L5_BCs pre_L5_PCs post_L5_PC
}

Target Cell pre_L5_BCs
{
    a3473955
    a3587718
}

Target Cell pre_L5_PCs
{
    a3644853
    a4148946
}

Target Cell post_L5_PC
{
    a3424037
}
"""


@pytest.mark.slow
@pytest.mark.forked
@pytest.mark.skipif(
    not os.path.isfile("/gpfs/bbp.cscs.ch/project/proj83/circuits/Bio_M/20200805/circuit.mvd3"),
    reason="Circuit file not available")
@pytest.mark.skipif(
    not os.environ.get("NEURODAMUS_NEOCORTEX_ROOT"),
    reason="Test requires loading a neocortex model to run")
def test_eager_caching():
    """
    A test of the impact of eager caching of synaptic parameters. BBPBGLIB-813
    """
    from neurodamus.core import NeurodamusCore as Nd

    # dump config to files
    with NamedTemporaryFile("w", prefix='test_eager_caching_tgt', delete=False) as tgt_file:
        tgt_file.write(TGT_str)
    with NamedTemporaryFile("w", prefix="test_eager_caching_bc", delete=False) as bc_file:
        bc_file.write(BC_str.format(target_file=tgt_file.name))

    # create Node from config
    GlobalConfig.verbosity = LogLevel.VERBOSE
    n = Node(bc_file.name)

    # set nrnPath (w/plasticity)
    SimConfig.base_circuit['nrnPath'] = \
        "/gpfs/bbp.cscs.ch/project/proj83/circuits/sscx-v7-plasticity/edges.sonata"

    # append Connection blocks programmatically
    # plasticity
    CONN_plast = compat.Map(Nd.Map())
    CONN_plast["Source"] = "pre_L5_PCs"
    CONN_plast["Destination"] = "post_L5_PC"
    CONN_plast["ModOverride"] = "GluSynapse"
    CONN_plast["Weight"] = 1.0
    SimConfig.connections.hoc_map.put("plasticity", CONN_plast.hoc_map)
    # init_I_E
    CONN_i2e = compat.Map(Nd.Map())
    CONN_i2e["Source"] = "pre_L5_BCs"
    CONN_i2e["Destination"] = "post_L5_PC"
    CONN_i2e["Weight"] = 1.0
    SimConfig.connections.hoc_map.put("init_I_E", CONN_i2e.hoc_map)
    # manually update item count in compat.Map
    SimConfig.connections._size = int(SimConfig.connections.hoc_map.count())

    # setup sim
    n.load_targets()
    n.create_cells()
    n.create_synapses()
    # manually finalize synapse managers (otherwise netcons are not created)
    for syn_manager in n._circuits.all_synapse_managers():
        syn_manager.finalize(n._run_conf.get("BaseSeed", 0), SimConfig.coreneuron)
    n.sim_init()  # not really necessary

    # here we get the HOC object for the post cell
    tgt = n._target_manager.get_target('post_L5_PC')
    post_gid = tgt.get_raw_gids()[0]
    post_cell = n._target_manager.hoc.cellDistributor.getCell(post_gid)
    # here we check that all synaptic delays are rounded to timestep
    # we skip minis netcons (having precell == None)
    delays = [nc.delay for nc in Nd.h.cvode.netconlist('', post_cell, '')
              if nc.precell() is not None]
    patch_delays = [int(x / Nd.dt + 1E-5) * Nd.dt for x in delays]
    assert (delays == patch_delays)

    os.unlink(bc_file.name)
    os.unlink(tgt_file.name)
