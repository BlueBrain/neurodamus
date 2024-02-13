import json
import os
import pytest
from pathlib import Path

from neurodamus.core.configuration import ConfigurationError
from neurodamus.io.synapse_reader import SynapseParameters
from neurodamus.node import Node
from tempfile import NamedTemporaryFile

SIM_DIR = Path(__file__).parent.parent.absolute() / "simulations" / "v5_sonata"
CONFIG_FILE_MINI = SIM_DIR / "simulation_config_mini.json"


@pytest.fixture
def sonata_config_file_err(sonata_config):
    extra_config = {"connection_overrides": [
        {
            "name": "config_ERR",
            "source": "nodesPopB",
            "target": "nodesPopB",
            "synapse_configure": "%s.dummy=1"
        }
    ]}

    sonata_config.update(extra_config)

    with NamedTemporaryFile("w", suffix='.json', delete=False) as config_file:
        json.dump(sonata_config, config_file)

    yield config_file
    os.unlink(config_file.name)


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
def test_config_error(sonata_config_file_err):
    with pytest.raises(ConfigurationError):
        n = Node(str(sonata_config_file_err.name))
        n.load_targets()
        n.create_cells()
        n.create_synapses()
        for syn_manager in n._circuits.all_synapse_managers():
            syn_manager.finalize(0, False)
