import numpy as np
import os
import pytest
from pathlib import Path

SIM_DIR = Path(__file__).parent.absolute() / "simulations"


@pytest.mark.forked
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


@pytest.mark.forked
def test_hoc_target_generate_subtargets():
    from neurodamus.target_manager import _HocTarget

    N_PARTS = 3
    gids = list(range(10))
    target = _HocTarget("Column", None, pop_name=None)
    target._raw_gids = np.array(gids, dtype="uint32")

    subtargets = target.generate_subtargets(N_PARTS)
    assert len(subtargets) == N_PARTS
    assert subtargets[0].name == "Column_0"
    assert subtargets[0].population_names == {None}
    assert np.array_equal(subtargets[0].get_gids(), np.array([0, 3, 6, 9]))
    assert np.array_equal(subtargets[1].get_gids(), np.array([1, 4, 7]))
    assert np.array_equal(subtargets[2].get_gids(), np.array([2, 5, 8]))


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


@pytest.mark.forked
@pytest.mark.skipif(
    not os.environ.get("NEURODAMUS_NEOCORTEX_ROOT"),
    reason="Test requires loading a neocortex model to run")
def test_v5_sonata_multisteps():
    import numpy.testing as npt
    from neurodamus import Neurodamus

    config_file = str(SIM_DIR / "v5_sonata" / "simulation_config.json")
    output_dir = str(SIM_DIR / "v5_sonata" / "output_coreneuron")
    tmp_file = _create_tmpconfig_coreneuron(config_file)

    nd = Neurodamus(tmp_file.name, output_path=output_dir, modelbuilding_steps=3)
    nd.run()

    # compare spikes with refs
    spike_gids = np.array([
        68855, 69877, 64935, 66068, 62945, 63698, 67666, 68223,
        65915, 69530, 63256, 64861, 66105, 68532, 65951, 64163,
        68855, 62797, 69877
    ])  # 0-based
    timestamps = np.array([
        9.125, 14.3, 15.425, 29.075, 31.025, 33.2, 34.175, 35.075,
        35.625, 36.875, 36.95, 37.1, 37.6, 37.6, 38.05, 38.075,
        38.175, 38.45, 39.875
    ])
    obtained_timestamps, obtained_spike_gids = _read_sonata_spike_file(os.path.join(output_dir,
                                                                                    "out.h5"))
    npt.assert_allclose(spike_gids, obtained_spike_gids)
    npt.assert_allclose(timestamps, obtained_timestamps)


@pytest.mark.forked
@pytest.mark.skipif(
    not os.environ.get("NEURODAMUS_NEOCORTEX_ROOT"),
    reason="Test requires loading a neocortex model to run")
def test_usecase3_BlueConfig_multisteps():
    import numpy.testing as npt
    from neurodamus import Neurodamus

    config_file = str(SIM_DIR / "usecase3" / "BlueConfig")
    output_dir = str(SIM_DIR / "usecase3" / "output_coreneuron")
    tmp_file = _create_tmpconfig_coreneuron(config_file)

    nd = Neurodamus(tmp_file.name, output_path=output_dir, modelbuilding_steps=2)
    nd.run()

    # compare spikes with refs
    spike_gids = np.array([
        0, 2, 1, 0, 1, 2, 0, 1, 2, 0, 1, 2, 0, 1, 2, 0, 1, 2, 0, 2, 0, 1, 2,
        0, 1, 0, 2, 1, 0, 2, 1, 0, 2, 1, 0
    ])  # 0-based
    timestamps = np.array([
        0.1, 0.15, 0.175, 2.275, 3.025, 3.45, 4.35, 5.7, 6.975, 7.7, 8.975,
        11.05, 12.525, 13.95, 15.5, 16.8, 20.15, 20.225, 21.4, 25.175,
        26.05, 26.1, 30.3, 30.6, 31.725, 35.1, 35.55, 37.125, 39.525,
        40.925, 42.45, 43.95, 46.4, 47.75, 48.375
    ])
    obtained_timestamps, obtained_spike_gids = _read_sonata_spike_file(os.path.join(output_dir,
                                                                                    "out.h5"))
    npt.assert_allclose(spike_gids, obtained_spike_gids)
    npt.assert_allclose(timestamps, obtained_timestamps)
