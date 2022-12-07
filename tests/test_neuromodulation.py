import numpy as np
import os
import pytest
from pathlib import Path


@pytest.mark.forked
@pytest.mark.skipif(
    not os.environ.get("NEURODAMUS_NEOCORTEX_ROOT"),
    reason="Test requires loading a neocortex model to run")
def test_neuromodulation_sims():
    import numpy.testing as npt
    from neurodamus import Neurodamus

    SIM_DIR = Path(__file__).parent.absolute() / "simulations" / "neuromodulation"
    config_file = str(SIM_DIR / "BlueConfig")
    os.chdir(SIM_DIR)
    nd = Neurodamus(config_file, disable_reports=True)
    nd.run()

    # compare spikes with refs
    spike_gids = np.array([1])  # 1-based
    timestamps = np.array([2.875])
    obtained_timestamps = nd._spike_vecs[0][0].as_numpy()
    obtained_spike_gids = nd._spike_vecs[0][1].as_numpy()
    npt.assert_allclose(spike_gids, obtained_spike_gids)
    npt.assert_allclose(timestamps, obtained_timestamps)
