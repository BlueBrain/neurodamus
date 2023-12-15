import json
import numpy
import os
import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile

USECASE3 = Path(__file__).parent.absolute() / "usecase3"

"""
Test "Projections", which in Sonata are basically Edges where the source population
is virtual, i.e. cells were not instantiated.
By applying Replay to it we should see received events
"""


@pytest.fixture
def sonata_config_file(sonata_config, request):
    enable_synapse_delay = request.param
    connection_overrides = [
        {
            "name": "nodeB-nodeA",
            "source": "nodesPopB",
            "target": "nodesPopA",
            "synapse_configure": "%s.verboseLevel=1"  # output when a spike is received
        },
        {
            "name": "nodeA-nodeA",
            "source": "nodesPopA",
            "target": "nodesPopA",
        },
    ]
    # Add synapse_delay_override to both connection overrides
    if enable_synapse_delay:
        connection_overrides[0]["synapse_delay_override"] = 3.
        connection_overrides[1]["synapse_delay_override"] = 5.
    sonata_config["connection_overrides"] = connection_overrides
    sonata_config["inputs"] = {
        "spikeReplay": {
            "module": "synapse_replay",
            "input_type": "spikes",
            "spike_file": str(USECASE3 / "input.dat"),
            "delay": 0,
            "duration": 1000,
            "source": "nodesPopB",
            "node_set": "nodesPopA"
        }
    }

    # create a tmp json file to read usecase3/no_edge_circuit_config.json
    with NamedTemporaryFile("w", suffix='.json', delete=False) as config_file:
        json.dump(sonata_config, config_file)

    yield config_file

    os.unlink(config_file.name)


@pytest.mark.parametrize("sonata_config_file", [False], indirect=True)
def test_projections(sonata_config_file):
    """
    Test that projections are correctly set up
    """
    from neurodamus.connection_manager import Nd, SynapseRuleManager
    from neurodamus import Neurodamus
    from neurodamus.core.configuration import Feature

    nd = Neurodamus(
        sonata_config_file.name,
        restrict_node_populations=["NodeA"],
        restrict_features=[Feature.Replay, Feature.SynConfigure],  # use config verboseLevel as Flag
        restrict_connectivity=False,
        disable_reports=True,
        cleanup_atexit=False,
        logging_level=3,
    )

    edges_A: SynapseRuleManager = nd.circuits.get_edge_manager("NodeA", "NodeA")
    assert len(list(edges_A.all_connections())) == 2
    edges_B_A: SynapseRuleManager = nd.circuits.get_edge_manager("NodeB", "NodeA")
    assert len(list(edges_B_A.all_connections())) == 2

    for conn in edges_A.all_connections():
        assert conn.synapses[0].verboseLevel == 0
    for conn in edges_B_A.all_connections():
        assert conn.synapses[0].verboseLevel == 1

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
    assert numpy.array_equal(strong_reduction_pos, numpy.array([96, 97]))


@pytest.mark.parametrize("sonata_config_file", [True], indirect=True)
def test_synapse_delay_override(sonata_config_file):
    """
    Test that the 'synapse_delay_override' property works as expected
    """
    from neurodamus.connection_manager import Nd, SynapseRuleManager
    from neurodamus import Neurodamus
    from neurodamus.core.configuration import Feature

    nd = Neurodamus(
        sonata_config_file.name,
        restrict_node_populations=["NodeA"],
        restrict_features=[Feature.Replay, Feature.SynConfigure],  # use config verboseLevel as Flag
        restrict_connectivity=False,
        disable_reports=True,
        cleanup_atexit=False,
        logging_level=3,
    )

    edges_A: SynapseRuleManager = nd.circuits.get_edge_manager("NodeA", "NodeA")
    assert len(list(edges_A.all_connections())) == 2
    edges_B_A: SynapseRuleManager = nd.circuits.get_edge_manager("NodeB", "NodeA")
    assert len(list(edges_B_A.all_connections())) == 2

    # Verify that netcons are created and they have the correct delay
    assert any(len(conn._netcons) for conn in edges_A.all_connections())
    for conn in edges_A.all_connections():
        assert conn.synapses[0].verboseLevel == 0
        for netcon in conn._netcons:
            assert netcon.delay == 5.

    # Check if any connections in edges_B_A have replay netcons
    assert any(len(conn._replay.netcons) for conn in edges_B_A.all_connections())
    for conn in edges_B_A.all_connections():
        assert conn.synapses[0].verboseLevel == 1
        # Check if the connection has replay netcons
        assert len(conn._replay.netcons) != 0
        for netcon in conn._replay.netcons:
            assert netcon.delay == 3.
        assert conn.syndelay_override == 3.

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
    assert numpy.array_equal(strong_reduction_pos, numpy.array([119, 120]))
