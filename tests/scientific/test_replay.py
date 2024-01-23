import json
import numpy
import numpy.testing as npt
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

USECASE3 = Path(__file__).parent.absolute() / "usecase3"
SAMPLE_DATA_DIR = Path(__file__).parent.parent.absolute() / "sample_data"


def replay_sim_config(sonata_config, replay_files):
    sonata_config["inputs"] = {}
    for i, replay_file in enumerate(replay_files):
        sonata_config["inputs"][f"spikeReplay{i}"] = {
            "module": "synapse_replay",
            "input_type": "spikes",
            "spike_file": replay_file,
            "delay": 0,
            "duration": 1000,
            "node_set": "Mosaic",  # no limits!
        }

    # create a tmp json file to read usecase3/no_edge_circuit_config.json
    with NamedTemporaryFile("w", suffix='.json', delete=False) as config_file:
        json.dump(sonata_config, config_file)

    return config_file


def test_replay_sim(sonata_config):
    from neurodamus import Neurodamus
    from neurodamus.core.configuration import Feature

    config_file = replay_sim_config(sonata_config, [str(USECASE3 / "input.dat")])
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


def test_many_replay_sim(sonata_config):
    from neurodamus import Neurodamus
    from neurodamus.core.configuration import Feature

    replay_files = [str(USECASE3 / file) for file in ["input.dat", "input1.dat", "input2.dat"]]
    config_file = replay_sim_config(sonata_config, replay_files)
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
    assert len(time_vec) == 14
    npt.assert_allclose(time_vec[:8], [0.175, 3., 3., 3.025, 5.7, 8., 8.975, 13.95])

    conn_1_2 = next(edges_a.get_connections(2, 1))
    time_vec = conn_1_2._replay.time_vec.as_numpy()
    assert len(time_vec) == 17
    npt.assert_allclose(time_vec[:8], [0.1, 2., 2.275, 4., 4.35, 7.725, 12.525, 16.825])

    nd.run()
    gids = nd._spike_vecs[0][1].as_numpy().astype(int)
    times = nd._spike_vecs[0][0].as_numpy()
    assert 1 == len(gids) == len(times)
    assert gids[0] == 3
    assert numpy.allclose(times, [0.75])

    os.unlink(config_file.name)


# A more comprehensive example, using Sonata replay with two populations
# ======================================================================
def test_replay_sonata_spikes(sonata_config):
    from neurodamus import Neurodamus
    from neurodamus.core.configuration import Feature

    config_file = replay_sim_config(sonata_config, [str(SAMPLE_DATA_DIR / "out.h5")])
    nd = Neurodamus(
        config_file.name,
        restrict_features=[Feature.Replay],
        disable_reports=True,
        cleanup_atexit=False,
        logging_level=2,
    )

    node_managers = nd.circuits.node_managers
    assert set(node_managers) == set([None, "NodeA", "NodeB"])

    edges_a = nd.circuits.get_edge_manager("NodeA", "NodeA")

    conn_2_1 = next(edges_a.get_connections(1, 2))
    time_vec = conn_2_1._replay.time_vec.as_numpy()
    assert len(time_vec) == 11
    npt.assert_allclose(time_vec[:8], [0.175, 3.025, 5.7, 8.975, 13.95, 20.15, 26.125, 31.725])

    conn_1_2 = next(edges_a.get_connections(2, 1))
    time_vec = conn_1_2._replay.time_vec.as_numpy()
    assert len(time_vec) == 13
    npt.assert_allclose(time_vec[:8], [0.1, 2.275, 4.35, 7.725, 12.525, 16.825, 21.4, 26.05])

    # projections get replay too
    edges_a = nd.circuits.get_edge_manager("NodeA", "NodeB")
    conn_2_1001 = next(edges_a.get_connections(1001, 2))
    time_vec = conn_2_1001._replay.time_vec.as_numpy()
    assert len(time_vec) == 11
    npt.assert_allclose(time_vec[:8], [0.175, 3.025, 5.7, 8.975, 13.95, 20.15, 26.125, 31.725])

    os.unlink(config_file.name)
