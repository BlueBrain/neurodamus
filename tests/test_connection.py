import os
import pytest
from pathlib import Path
from neurodamus.io.synapse_reader import SynapseParameters
from neurodamus.node import Node


SIM_DIR = Path(__file__).parent.absolute() / "simulations" / "v5_sonata"
CONFIG_FILE_MINI = SIM_DIR / "simulation_config_mini.json"


@pytest.mark.slow
@pytest.mark.skipif(
    not os.environ.get("NEURODAMUS_NEOCORTEX_ROOT"),
    reason="Test requires loading a neocortex model to run")
# This test is to mimic the error reported in HPCTM-1687 during connection.add_syanpses()
# when detecting conn._synapse_params with more than one element is not None
def test_add_synapses():
    n = Node(str(CONFIG_FILE_MINI))
    n.load_targets()
    n.create_cells()
    n.create_synapses()
    syn_manager = n.circuits.get_edge_manager("default", "default")
    conn = list(syn_manager.get_connections(62798))[0]
    new_params = SynapseParameters.create_array(1)
    n_syns = len(conn._synapse_params)
    assert n_syns > 1
    new_params[0].sgid = conn.sgid
    conn.add_synapses(n._target_manager, new_params)
    assert len(conn._synapse_params) == n_syns + 1
    for syn_manager in n._circuits.all_synapse_managers():
        syn_manager.finalize(0, False)
