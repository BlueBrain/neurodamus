import pytest

from neurodamus.node import Node
from neurodamus.core.configuration import GlobalConfig, SimConfig, LogLevel
from pathlib import Path


SIM_DIR = Path(__file__).parent.parent.absolute() / "simulations" / "sscx-v7-plasticity"
CONFIG_FILE = SIM_DIR / "simulation_config_base.json"


@pytest.mark.slow
def test_eager_caching():
    """
    A test of the impact of eager caching of synaptic parameters. BBPBGLIB-813
    """
    from neurodamus.core import NeurodamusCore as Nd

    # create Node from config
    GlobalConfig.verbosity = LogLevel.VERBOSE
    n = Node(str(CONFIG_FILE))

    # append Connection blocks programmatically
    # plasticity
    CONN_plast = {"Source": "pre_L5_PCs",
                  "Destination": "post_L5_PC",
                  "ModOverride": "GluSynapse",
                  "Weight": 1.0}
    SimConfig.connections["plasticity"] = CONN_plast
    # init_I_E
    CONN_i2e = {"Source": "pre_L5_BCs",
                "Destination": "post_L5_PC",
                "Weight": 1.0
                }
    SimConfig.connections["init_I_E"] = CONN_i2e
    assert len(SimConfig.connections) == 2

    # setup sim
    n.load_targets()
    n.create_cells()
    n.create_synapses()
    # manually finalize synapse managers (otherwise netcons are not created)
    for syn_manager in n._circuits.all_synapse_managers():
        syn_manager.finalize(n._run_conf.get("BaseSeed", 0), SimConfig.use_coreneuron)
    n.sim_init()  # not really necessary

    # here we get the HOC object for the post cell
    tgt = n._target_manager.get_target('post_L5_PC')
    post_gid = tgt.get_raw_gids()[0]
    post_cell = n.circuits.global_manager.get_cellref(post_gid)
    # here we check that all synaptic delays are rounded to timestep
    # we skip minis netcons (having precell == None)
    delays = [nc.delay for nc in Nd.h.cvode.netconlist('', post_cell, '')
              if nc.precell() is not None]
    patch_delays = [int(x / Nd.dt + 1E-5) * Nd.dt for x in delays]
    assert (delays == patch_delays)
