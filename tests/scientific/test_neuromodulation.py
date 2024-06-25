import numpy as np
import numpy.testing as npt
import os
from pathlib import Path

SIM_DIR = Path(__file__).parent.parent.absolute() / "simulations" / "neuromodulation"


def test_neuromodulation_sims_neuron():
    import numpy.testing as npt
    from neurodamus import Neurodamus

    config_file = str(SIM_DIR / "simulation_config.json")
    os.chdir(SIM_DIR)
    nd = Neurodamus(config_file, disable_reports=True)
    nd.run()

    # compare spikes with refs
    spike_gids = np.array([1, 2, 2])  # 1-based
    timestamps = np.array([1.55, 2.025, 13.525])
    obtained_timestamps = nd._spike_vecs[0][0].as_numpy()
    obtained_spike_gids = nd._spike_vecs[0][1].as_numpy()
    npt.assert_allclose(spike_gids, obtained_spike_gids)
    npt.assert_allclose(timestamps, obtained_timestamps)


def test_neuromodulation_sims_coreneuron():
    from neurodamus import Neurodamus
    from neurodamus.replay import SpikeManager

    config_file = str(SIM_DIR / "simulation_config.json")
    os.chdir(SIM_DIR)
    nd = Neurodamus(config_file, disable_reports=True, simulator="CORENEURON",
                    output_path="output_coreneuron")
    nd.run()

    # compare spikes with refs
    spike_dat = Path(nd._run_conf.get("OutputRoot"))/nd._run_conf.get("SpikesFile")
    obtained_timestamps, obtained_spike_gids = SpikeManager._read_spikes_sonata(spike_dat, "All")
    spike_gids = np.array([1, 2, 2])  # 1-based
    timestamps = np.array([1.55, 2.025, 13.525])
    npt.assert_allclose(spike_gids, obtained_spike_gids)
    npt.assert_allclose(timestamps, obtained_timestamps)
