import json
import numpy
import os
import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile

USECASE3 = Path(__file__).parent.absolute() / "usecase3"
SPONT_RATE = 100


@pytest.fixture
def sonata_config_file(sonata_config):
    sonata_config["run"]["tstop"] = 20
    sonata_config["connection_overrides"] = [
        {
            "name": "in-nodeA",
            "source": "nodesPopA",
            "target": "l4pc",
            "spont_minis": SPONT_RATE,
            "synapse_configure": "%s.verboseLevel=1"  # output when a spike is received
        },
    ]

    # create a tmp json file to read usecase3/no_edge_circuit_config.json
    with NamedTemporaryFile("w", suffix='.json', delete=False) as config_file:
        json.dump(sonata_config, config_file)

    yield config_file

    os.unlink(config_file.name)


def test_spont_minis(sonata_config_file):
    from neurodamus.connection_manager import Nd, SynapseRuleManager
    from neurodamus import Neurodamus
    from neurodamus.core.configuration import Feature

    nd = Neurodamus(
        sonata_config_file.name,
        restrict_node_populations=["NodeA"],
        restrict_features=[Feature.SpontMinis],  # Enable Feature.SynConfigure to see events
        restrict_connectivity=1,  # base restriction, no projections
        disable_reports=True,
        cleanup_atexit=False,
        # logging_level=3,
    )

    edges_a: SynapseRuleManager = nd.circuits.get_edge_manager("NodeA", "NodeA")
    assert len(list(edges_a.all_connections())) == 2
    conn_2_1 = next(edges_a.get_connections(1, 2))
    conn_1_2 = next(edges_a.get_connections(2, 1))
    assert conn_2_1._spont_minis.rate == SPONT_RATE
    assert conn_1_2._spont_minis is None

    c1 = edges_a.cell_manager.get_cellref(1)
    voltage_vec = Nd.Vector()
    voltage_vec.record(c1.soma[0](0.5)._ref_v)
    Nd.finitialize()  # reinit for the recordings to be registered

    nd.run()

    # When we get an event the voltage drops
    # We find that looking at the acceleration of the voltage drop
    # We do a convolution to weight in neighbor points and have a smoother line
    v_increase_rate = numpy.diff(voltage_vec, 2)
    window_sum = numpy.convolve(v_increase_rate, [1, 2, 4, 2, 1], 'valid')
    # print(numpy.array_str(window_sum, suppress_small=True))
    strong_reduction_pos = numpy.nonzero(window_sum < -0.01)[0]
    # At least one such point, at most 2% of all points
    assert 1 <= len(strong_reduction_pos) <= int(0.02 * len(window_sum))
