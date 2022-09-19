import os
import pytest
import shutil
import subprocess
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

from neurodamus.node import Node
from neurodamus.core.configuration import GlobalConfig, LogLevel

SIMS = Path(__file__).parent.absolute() / "simulations"


# NOTE: These tests are currently disabled since they require some work
# Namely launch it via python directly, and use a separate random dir

# BlueConfig string
BC_str = """
Run Default
{{
    CircuitPath {SIMS}/usecase3
    MorphologyPath {SIMS}/usecase3/CircuitA/morphologies/asc
    MorphologyType asc
    METypePath {SIMS}/usecase3/CircuitA/hoc
    CellLibraryFile {SIMS}/usecase3/nodes_A.h5
    nrnPath <NONE>
    CircuitTarget Mosaic_A

    Simulator NEURON
    BaseSeed 1
    RNGMode Random123

    CurrentDir .
    OutputRoot output
    TargetFile {target_file}

    RunMode RR
    Duration 50
    Dt 0.025
}}

Circuit PointNeurons
{{
    Engine PointNeuron
    CircuitPath /gpfs/bbp.cscs.ch/project/proj12/jenkins/cellular/circuit-point/nodes
    CellLibraryFile /gpfs/bbp.cscs.ch/project/proj12/jenkins/cellular/circuit-point/\
nodes/whole_brain_model_SONATA.h5
    nrnPath <NONE>
    CircuitTarget Single
}}

Projection projDetailedToPoint
{{
    Path {SIMS}/point_detailed/edges_A_point.h5
    Type Point
}}

Projection projPointToDetailed
{{
    Path {SIMS}/point_detailed/edges_point_A.h5
}}

Connection AtoPoint
{{
    Source NodeA:Mosaic_A
    Destination default:Single
    Weight 1
}}

Connection PointToA
{{
    Source default:Single
    Destination NodeA:Mosaic_A
    Weight 1
}}
"""

# Target file string
TGT_str = """
Target Cell Mosaic_A
{
  a1 a2 a3
}

Target Cell Single
{
a71709499
}
"""


def _build_special(test_dir, repo_dir, mod_files_dir):
    subprocess.run(
        ["git", "clone", "--recursive", "-b", "adex_mod",
            "git@bbpgitlab.epfl.ch:hpc/sim/models/hippocampus.git", repo_dir],
        check=True
    )
    os.mkdir(mod_files_dir)
    shutil.copyfile(os.path.join(repo_dir, "mod", "adex.mod"),
                    os.path.join(mod_files_dir, "adex.mod"))
    with open(os.path.join(mod_files_dir, "neuron_only_mods.txt"), 'w') as f:
        print('adex.mod', file=f)
    subprocess.run(
        ["build_neurodamus.sh", mod_files_dir],
        check=True,
        cwd=test_dir
    )


@pytest.fixture(scope="module")
def _setup():
    test_dir = TemporaryDirectory("hip_point_test")
    hippocampus_repo_dir = test_dir / "hippocampus"
    mod_files_dir = test_dir / "mod"
    x86_dir = test_dir / "x86_64"

    if not os.path.isfile(os.path.join(x86_dir, "special")):
        _build_special(test_dir, hippocampus_repo_dir, mod_files_dir)

    os.environ["NRNMECH_LIB_PATH"] = str(x86_dir / "libnrnmech.so")
    os.environ["LD_LIBRARY_PATH"] = str(x86_dir) + ":" + os.environ.get("LD_LIBRARY_PATH", "")

    yield  # Run tests now! Keep test_dir alive
    pass   # done


@pytest.mark.slow
@pytest.mark.forked
@pytest.mark.skipif(
    not os.path.isdir("/gpfs/bbp.cscs.ch/project/proj12/jenkins/cellular/circuit-point"),
    reason="Circuit file not available")
@pytest.mark.skipif(
    not os.environ.get("NEURODAMUS_NEOCORTEX_ROOT"),
    reason="Test requires loading a neocortex model to run")
def _test_point_detailed_conn(_setup):
    """
    A test of the impact of eager caching of synaptic parameters. BBPBGLIB-813
    """
    # dump config to files
    with NamedTemporaryFile("w", prefix='test_point_detailed_conn_tgt', delete=False) as tgt_file:
        tgt_file.write(TGT_str)
    with NamedTemporaryFile("w", prefix="test_point_detailed_conn_bc", delete=False) as bc_file:
        bc_file.write(BC_str.format(target_file=tgt_file.name, SIMS=SIMS))

    # create Node from config
    GlobalConfig.verbosity = LogLevel.DEBUG
    n = Node(bc_file.name)

    # setup sim
    n.load_targets()
    n.create_cells()
    n.create_synapses()
    # init
    base_seed = n._run_conf.get("BaseSeed", 0)  # base seed for synapse RNG
    for syn_manager in n._circuits.all_synapse_managers():
        syn_manager.finalize(base_seed, False)
    n.sim_init()

    # Get gids for the detailed and point neurons that connect with each other
    # after calculating their offsets
    detailed_neuron_final_gid = n.circuits.get_node_manager("NodeA").get_final_gids()[0]
    point_neuron_final_gid = n.circuits.get_node_manager("default").get_final_gids()[0]

    # Check that the Detailed -> Point Neuron synapse is created and has the
    # correct sgid and tgid
    conn_list_det_pnt = [conn for conn in n.circuits.get_edge_managers("NodeA",
                         "default")[0].get_target_connections("NodeA:Mosaic_A", "default:Single")]
    assert conn_list_det_pnt[0].synapses[0].srcgid() == detailed_neuron_final_gid
    assert conn_list_det_pnt[0].tgid == point_neuron_final_gid

    # Check that the Point -> Detailed Neuron synapse is created and has the
    # correct sgid and tgid as well as the correct type
    conn_list_pnt_det = [conn for conn in n.circuits.get_edge_managers("default",
                         "NodeA")[0].get_target_connections("default:Single", "NodeA:Mosaic_A")]
    assert len(conn_list_pnt_det[0].synapses) == 2
    assert conn_list_pnt_det[0].synapses[0].hname() == "ProbGABAAB_EMS[0]"
    assert conn_list_pnt_det[0].synapses[1].hname() == "ProbGABAAB_EMS[1]"
    assert conn_list_pnt_det[0].sgid == point_neuron_final_gid
    assert conn_list_pnt_det[0].tgid == detailed_neuron_final_gid

    # remove temp files
    os.unlink(bc_file.name)
    os.unlink(tgt_file.name)
