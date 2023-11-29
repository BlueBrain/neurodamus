import json
import numpy
import os
import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile

USECASE3 = Path(__file__).parent.absolute() / "usecase3"

"""
Test multiple simulated populations, with/without interconnections
"""


@pytest.fixture
def sonata_config_file(sonata_config, extra_config):
    sonata_config["inputs"] = {
        "spikeReplay": {
            "module": "synapse_replay",
            "input_type": "spikes",
            "spike_file": str(USECASE3 / "input.dat"),
            "delay": 0,
            "duration": 1000,
            "node_set": "nodesPopA"
        }
    }

    if extra_config:
        sonata_config.update(extra_config)

    with NamedTemporaryFile("w", suffix='.json', delete=False) as config_file:
        json.dump(sonata_config, config_file)

    yield config_file
    os.unlink(config_file.name)


@pytest.mark.parametrize("extra_config", [{
    "connection_overrides": [
        {
            "name": "nodeB-nodeB",
            "source": "nodesPopB",
            "target": "nodesPopB",
            "synapse_configure": "%s.verboseLevel=1"  # output when a spike is received
        },
    ]
}])
def test_multipop_simple(sonata_config_file):
    """
    Test that two populations are correctly set for running in parallel, with offsetting
    """
    from neurodamus.connection_manager import SynapseRuleManager
    from neurodamus import Neurodamus
    from neurodamus.core.configuration import Feature

    nd = Neurodamus(
        sonata_config_file.name,
        restrict_features=[Feature.SynConfigure],  # use config verboseLevel as Flag
        restrict_connectivity=1,  # start off with two initial disconnected populations
        disable_reports=True,
        cleanup_atexit=False,
        logging_level=3,
    )

    assert set(nd.circuits.node_managers) == {None, "NodeA", "NodeB"}
    assert len(nd.circuits.edge_managers) == 2  # only intra connectivity
    edges_A: SynapseRuleManager = nd.circuits.get_edge_manager("NodeA", "NodeA")
    assert len(list(edges_A.all_connections())) == 2
    cell_man = edges_A.cell_manager
    assert cell_man.local_nodes.offset == 0
    assert set(cell_man.local_nodes.raw_gids()) == set(cell_man.gid2cell) == {1, 2, 3}

    edges_B: SynapseRuleManager = nd.circuits.get_edge_manager("NodeB", "NodeB")
    assert len(list(edges_B.all_connections())) == 2
    cell_man = edges_B.cell_manager
    assert cell_man.local_nodes.offset == 1000
    assert set(cell_man.local_nodes.raw_gids()) == {1, 2}
    assert set(cell_man.local_nodes.final_gids()) == set(cell_man.gid2cell) == {1001, 1002}

    for conn in edges_A.all_connections():
        assert conn.tgid <= 3
        assert conn.sgid <= 3
        assert conn.synapses[0].verboseLevel == 0

    for conn in edges_B.all_connections():
        assert 1000 < conn.tgid <= 1003
        assert 1000 < conn.sgid <= 1003
        assert conn.synapses[0].verboseLevel == 1


@pytest.mark.parametrize("extra_config", [{
    "connection_overrides": [
        {
            "name": "nodeB-nodeB",
            "source": "nodesPopB",
            "target": "nodesPopB",
            "synapse_configure": "%s.verboseLevel=1"  # use as a flag for tests
        },
        {
            "name": "nodeB-nodeA",
            "source": "nodesPopB",
            "target": "nodesPopA",
            "synapse_configure": "%s.verboseLevel=2"
        },
        {
            "name": "nodeA-nodeB",
            "source": "nodesPopA",
            "target": "nodesPopB",
            "synapse_configure": "%s.verboseLevel=3"
        },
    ]
}])
def test_multipop_full_conn(sonata_config_file):
    """
    Test that two populations are correctly set for running in parallel, with offsetting
    """
    from neurodamus.connection_manager import Nd, SynapseRuleManager
    from neurodamus import Neurodamus
    from neurodamus.core.configuration import Feature

    nd = Neurodamus(
        sonata_config_file.name,
        restrict_features=[Feature.Replay, Feature.SynConfigure],  # use config verboseLevel as Flag
        restrict_connectivity=False,
        disable_reports=True,
        cleanup_atexit=False,
        logging_level=3,
    )

    assert set(nd.circuits.node_managers) == {None, "NodeA", "NodeB"}
    assert len(nd.circuits.edge_managers) == 4  # all-to-all connectivity
    edges_A: SynapseRuleManager = nd.circuits.get_edge_manager("NodeA", "NodeA")
    assert len(list(edges_A.all_connections())) == 2
    cell_man_A = edges_A.cell_manager
    assert cell_man_A.local_nodes.offset == 0
    assert set(cell_man_A.local_nodes.raw_gids()) == set(cell_man_A.gid2cell) == {1, 2, 3}

    edges_B: SynapseRuleManager = nd.circuits.get_edge_manager("NodeB", "NodeB")
    assert len(list(edges_B.all_connections())) == 2
    cell_man_B = edges_B.cell_manager
    assert cell_man_B.local_nodes.offset == 1000
    assert set(cell_man_B.local_nodes.raw_gids()) == {1, 2}
    assert set(cell_man_B.local_nodes.final_gids()) == set(cell_man_B.gid2cell) == {1001, 1002}

    edges_AB: SynapseRuleManager = nd.circuits.get_edge_manager("NodeA", "NodeB")
    assert len(list(edges_AB.all_connections())) == 3
    assert edges_AB.cell_manager == cell_man_B
    assert edges_AB.src_cell_manager == cell_man_A

    edges_BA: SynapseRuleManager = nd.circuits.get_edge_manager("NodeB", "NodeA")
    assert len(list(edges_AB.all_connections())) == 3
    assert edges_BA.cell_manager == cell_man_A
    assert edges_BA.src_cell_manager == cell_man_B

    for conn in edges_A.all_connections():
        assert conn.tgid <= 3
        assert conn.sgid <= 3
        assert conn.synapses[0].verboseLevel == 0

    for conn in edges_B.all_connections():
        assert 1000 < conn.tgid <= 1003
        assert 1000 < conn.sgid <= 1003
        assert conn.synapses[0].verboseLevel == 1

    for conn in edges_BA.all_connections():
        assert 0 < conn.tgid <= 3
        assert 1000 < conn.sgid <= 1003
        assert conn.synapses[0].verboseLevel == 2

    for conn in edges_AB.all_connections():
        assert 1000 < conn.tgid <= 1003
        assert 0 < conn.sgid <= 3
        assert conn.synapses[0].verboseLevel == 3

    # Replay will create spikes for all instantiated cells targeting popA
    # That means popA->popA and popB->popA
    conn_2_1 = next(edges_A.get_connections(1, 2))
    assert len(conn_2_1._replay.time_vec) == 1
    conn_1001_1 = next(edges_BA.get_connections(1, 1001))
    assert len(conn_1001_1._replay.time_vec) == 1
    for c in edges_B.all_connections():
        assert c._replay is None
    for c in edges_AB.all_connections():
        assert c._replay is None

    # Prepare run
    c1 = edges_A.cell_manager.get_cellref(1)
    voltage_vec = Nd.Vector()
    voltage_vec.record(c1.soma[0](0.5)._ref_v)
    Nd.finitialize()  # reinit for the recordings to be registered

    nd.run()

    # Find impact on voltage. See test_spont_minis for an explanation
    v_increase_rate = numpy.diff(voltage_vec, 2)
    window_sum = numpy.convolve(v_increase_rate, [1, 2, 4, 2, 1], 'valid')
    strong_reduction_pos = numpy.nonzero(window_sum < -0.03)[0]
    assert 1 <= len(strong_reduction_pos) <= int(0.02 * len(window_sum))
