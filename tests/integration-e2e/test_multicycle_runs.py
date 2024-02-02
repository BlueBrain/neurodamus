import numpy as np
import os
import pytest
from pathlib import Path

SIM_DIR = Path(__file__).parent.parent.absolute() / "simulations"


@pytest.fixture(autouse=True)
def _change_test_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(str(SIM_DIR / "usecase3"))


def test_nodeset_target_generate_subtargets():
    from neurodamus.core.nodeset import NodeSet
    from neurodamus.target_manager import NodesetTarget

    N_PARTS = 3
    raw_gids_a = list(range(10))
    raw_gids_b = list(range(5))
    nodes_popA = NodeSet(raw_gids_a).register_global("pop_A")
    nodes_popB = NodeSet(raw_gids_b).register_global("pop_B")
    target = NodesetTarget("Column", [nodes_popA, nodes_popB])
    assert np.array_equal(target.get_gids(),
                          np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 1000, 1001, 1002, 1003, 1004]))

    subtargets = target.generate_subtargets(N_PARTS)
    assert len(subtargets) == N_PARTS
    assert len(subtargets[0]) == 2
    subtarget_popA = subtargets[0][0]
    subtarget_popB = subtargets[0][1]
    assert subtarget_popA.name == "pop_A__Column_0"
    assert subtarget_popA.population_names == {"pop_A"}
    assert np.array_equal(subtarget_popA.get_gids(), np.array([0, 3, 6, 9]))
    assert subtarget_popB.name == "pop_B__Column_0"
    assert subtarget_popB.population_names == {"pop_B"}
    assert np.array_equal(subtarget_popB.get_gids(), np.array([1000, 1003]))
    assert np.array_equal(subtargets[1][0].get_gids(), np.array([1, 4, 7]))
    assert np.array_equal(subtargets[2][0].get_gids(), np.array([2, 5, 8]))
    assert np.array_equal(subtargets[1][1].get_gids(), np.array([1001, 1004]))
    assert np.array_equal(subtargets[2][1].get_gids(), np.array([1002]))


def _create_tmpconfig_coreneuron(config_file):
    import fileinput
    import shutil
    from tempfile import NamedTemporaryFile

    suffix = ".json" if config_file.endswith(".json") else ".BC"
    tmp_file = NamedTemporaryFile(suffix=suffix, dir=os.path.dirname(config_file), delete=True)
    shutil.copy2(config_file, tmp_file.name)
    with fileinput.FileInput(tmp_file.name, inplace=True) as file:
        for line in file:
            if config_file.endswith(".json"):
                print(line.replace("\"target_simulator\": \"NEURON\"",
                                   "\"target_simulator\": \"CORENEURON\""), end='')
            else:
                print(line.replace("Simulator NEURON", "Simulator CORENEURON"), end='')
    return tmp_file


def _read_sonata_spike_file(spike_file):
    import libsonata
    spikes = libsonata.SpikeReader(spike_file)
    pop_name = spikes.get_population_names()[0]
    data = spikes[pop_name].get()
    timestamps = np.array([x[1] for x in data])
    spike_gids = np.array([x[0] for x in data])
    return timestamps, spike_gids


def test_v5_sonata_multisteps(capsys):
    import numpy.testing as npt
    from neurodamus import Neurodamus

    config_file = str(SIM_DIR / "v5_sonata" / "simulation_config.json")
    output_dir = str(SIM_DIR / "v5_sonata" / "output_coreneuron")
    tmp_file = _create_tmpconfig_coreneuron(config_file)

    nd = Neurodamus(tmp_file.name, output_path=output_dir, modelbuilding_steps=3)
    nd.run()

    # compare spikes with refs
    spike_gids = np.array([
        68855, 69877, 64935, 66068, 63698, 67666, 68223, 65915, 62945,
        63256, 69530, 64861, 68532, 66105, 64163, 68855, 62797, 65951,
        69877
    ])  # 0-based
    timestamps = np.array([
        9.15, 14.3, 15.425, 30.125, 33.175, 34.175, 35.075, 35.625,
        36.15, 36.85, 36.875, 37.075, 37.525, 37.6, 38.05, 38.3,
        38.45, 39.6, 39.85
    ])
    obtained_timestamps, obtained_spike_gids = _read_sonata_spike_file(os.path.join(output_dir,
                                                                                    "out.h5"))
    npt.assert_allclose(spike_gids, obtained_spike_gids)
    npt.assert_allclose(timestamps, obtained_timestamps)

    captured = capsys.readouterr()
    assert "MULTI-CYCLE RUN: 3 Cycles" in captured.out


def test_usecase3_sonata_multisteps():
    import numpy.testing as npt
    from neurodamus import Neurodamus

    config_file = str(SIM_DIR / "usecase3" / "simulation_sonata.json")
    output_dir = str(SIM_DIR / "usecase3" / "output_coreneuron")
    tmp_file = _create_tmpconfig_coreneuron(config_file)

    nd = Neurodamus(tmp_file.name, output_path=output_dir, modelbuilding_steps=2)
    nd.run()

    # compare spikes with refs
    spike_gids = np.array([
        0, 1, 2, 0, 1, 2, 0, 0, 1, 2, 2, 2, 2, 2, 0, 2, 1, 0, 2, 0, 1
    ])  # 0-based
    timestamps = np.array([
        0.2, 0.3, 0.3, 2.5, 3.4, 4.2, 5.5, 7., 7.4, 8.6, 13.8, 19.6, 25.7, 32., 36.4, 38.5,
        40.8, 42.6, 45.2, 48.3, 49.9
    ])
    obtained_timestamps, obtained_spike_gids = _read_sonata_spike_file(os.path.join(output_dir,
                                                                                    "spikes.h5"))
    npt.assert_allclose(spike_gids, obtained_spike_gids)
    npt.assert_allclose(timestamps, obtained_timestamps)
