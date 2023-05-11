import numpy as np
import numpy.testing as npt
import os
import pytest
from pathlib import Path

SIM_DIR = Path(__file__).parent.absolute() / "simulations"

pytestmark = [
    pytest.mark.forked,
    pytest.mark.slow,
    pytest.mark.skipif(
        not os.environ.get("NEURODAMUS_NEOCORTEX_ROOT"),
        reason="Test requires loading a neocortex model to run"
    )
]


def test_simulation_sonata_config():
    from neurodamus import Neurodamus
    config_file = str(SIM_DIR / "usecase3" / "simulation_sonata.json")
    nd = Neurodamus(config_file, disable_reports=True)
    nd.run()

    # compare spikes with refs
    spike_gids = np.array([
        1., 2., 3., 1., 2., 3., 1., 1., 2., 3., 3., 3., 3., 3., 1., 3., 2., 1., 3., 1., 2.
    ])  # 1-based
    timestamps = np.array([
        0.2, 0.3, 0.3, 2.5, 3.4, 4.2, 5.6, 7., 7.4, 8.6, 13.9, 19.6, 25.7, 32., 36.4, 38.5,
        40.8, 42.6, 45.2, 48.3, 49.9
    ])
    obtained_timestamps = nd._spike_vecs[0][0].as_numpy()
    obtained_spike_gids = nd._spike_vecs[0][1].as_numpy()
    npt.assert_allclose(spike_gids, obtained_spike_gids)
    npt.assert_allclose(timestamps, obtained_timestamps)
