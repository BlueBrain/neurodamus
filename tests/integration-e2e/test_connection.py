import pytest
from pathlib import Path
from neurodamus.io.synapse_reader import SynapseParameters
from neurodamus.node import Node


SIM_DIR = Path(__file__).parent.parent.absolute() / "simulations" / "v5_sonata"
CONFIG_FILE_MINI = SIM_DIR / "simulation_config_mini.json"
CONFIG_FILE_ERR = SIM_DIR / "simulation_config_err.json"


@pytest.mark.slow
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


@pytest.mark.slow
def test_hoc_config_error():
    with pytest.raises(ValueError):
        n = Node(str(CONFIG_FILE_ERR))
        n.load_targets()
        n.create_cells()
        n.create_synapses()
        syn_manager = n.circuits.get_edge_manager("default", "default")
        conn = list(syn_manager.get_connections(62798))[0]
        new_params = SynapseParameters.create_array(1)
        new_params[0].sgid = conn.sgid
        conn.add_synapses(n._target_manager, new_params)
        for syn_manager in n._circuits.all_synapse_managers():
            syn_manager.finalize(0, False)
