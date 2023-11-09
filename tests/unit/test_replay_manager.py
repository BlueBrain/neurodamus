import pytest
import numpy.testing as npt
from pathlib import Path

SAMPLE_DATA_DIR = Path(__file__).parent.parent.absolute() / "sample_data"


@pytest.mark.forked
def test_replay_manager_sonata():
    from neurodamus.replay import SpikeManager, MissingSpikesPopulationError
    spikes_sonata = SAMPLE_DATA_DIR / "out.h5"

    timestamps, spike_gids = SpikeManager._read_spikes_sonata(spikes_sonata, "NodeA")
    npt.assert_allclose(timestamps[:8], [0.1, 0.15, 0.175, 2.275, 3.025, 3.45, 4.35, 5.7])
    npt.assert_equal(spike_gids[:8], [1, 3, 2, 1, 2, 3, 1, 2])

    # We do an internal assertion when the population doesnt exist. Verify it works as expected
    with pytest.raises(MissingSpikesPopulationError, match="Spikes population not found"):
        SpikeManager._read_spikes_sonata(spikes_sonata, "wont-exist")
