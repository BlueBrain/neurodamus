import json
import numpy
import os
import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile

USECASE3 = Path(__file__).parent.absolute() / "usecase3"


@pytest.mark.skipif(
    not os.environ.get("NEURODAMUS_NEOCORTEX_ROOT"),
    reason="Test requires loading a neocortex model to run"
)
def test_replay(sonata_config):
    from neurodamus import Neurodamus
    from neurodamus.core.configuration import Feature
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

    # create a tmp json file to read usecase3/no_edge_circuit_config.json
    with NamedTemporaryFile("w", suffix='.json', delete=False) as config_file:
        json.dump(sonata_config, config_file)

    nd = Neurodamus(
        config_file.name,
        restrict_node_populations=["NodeA"],
        restrict_features=[Feature.Replay],
        restrict_connectivity=1,  # base restriction, no projections
        disable_reports=True,
        cleanup_atexit=False,
    )

    node_managers = nd.circuits.node_managers
    assert set(node_managers) == set([None, "NodeA"])

    edges_a = nd.circuits.get_edge_manager("NodeA", "NodeA")

    conn_2_1 = next(edges_a.get_connections(1, 2))
    time_vec = conn_2_1._replay.time_vec.as_numpy()
    assert len(time_vec) == 1
    assert time_vec[0] == 3

    conn_1_2 = next(edges_a.get_connections(2, 1))
    time_vec = conn_1_2._replay.time_vec.as_numpy()
    assert len(time_vec) == 1
    assert time_vec[0] == 2

    nd.run()
    gids = nd._spike_vecs[0][1].as_numpy().astype(int)
    times = nd._spike_vecs[0][0].as_numpy()
    assert 1 == len(gids) == len(times)
    assert gids[0] == 3
    assert numpy.allclose(times, [0.75])

    os.unlink(config_file.name)
