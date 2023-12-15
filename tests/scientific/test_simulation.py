import numpy as np
import numpy.testing as npt
import os
import pytest
from pathlib import Path

SIM_DIR = Path(__file__).parent.parent.absolute() / "simulations"


@pytest.mark.skipif(
    os.environ.get("SLURM_JOB_ID") is None or os.environ.get("RUN_MPI") is None,
    reason="Simulation tests require MPI")
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
        0.2, 0.3, 0.3, 2.5, 3.4, 4.2, 5.5, 7., 7.4, 8.6, 13.8, 19.6, 25.7, 32., 36.4, 38.5,
        40.8, 42.6, 45.2, 48.3, 49.9
    ])
    obtained_timestamps = nd._spike_vecs[0][0].as_numpy()
    obtained_spike_gids = nd._spike_vecs[0][1].as_numpy()
    npt.assert_allclose(spike_gids, obtained_spike_gids)
    npt.assert_allclose(timestamps, obtained_timestamps)


def test_v5_sonata_config():
    import numpy as np
    import numpy.testing as npt
    from neurodamus import Neurodamus

    config_file = str(SIM_DIR / "v5_sonata" / "simulation_config.json")
    nd = Neurodamus(config_file, disable_reports=True)
    nd.run()

    spike_gids = np.array([
        68855, 69877, 64935, 66068, 63698, 67666, 68223, 65915,
        62945, 63256, 69530, 64861, 68532, 66105, 64163, 68855,
        62797, 65951, 69877
    ]) + 1  # Conform to nd 1-based
    timestamps = np.array([
        9.15, 14.3, 15.425, 30.125, 33.175, 34.175, 35.075, 35.625,
        36.15, 36.85, 36.875, 37.075, 37.525, 37.6, 38.05, 38.3,
        38.45, 39.6, 39.85
    ])

    obtained_timestamps = nd._spike_vecs[0][0].as_numpy()
    obtained_spike_gids = nd._spike_vecs[0][1].as_numpy()
    npt.assert_allclose(spike_gids, obtained_spike_gids)
    npt.assert_allclose(timestamps, obtained_timestamps)


def test_v5_gap_junction():
    import numpy as np
    from neurodamus import Neurodamus
    from neurodamus.gap_junction import GapJunctionManager

    config_file = str(SIM_DIR / "v5_gapjunctions" / "simulation_config.json")
    nd = Neurodamus(config_file, disable_reports=True)

    cell_manager = nd.circuits.get_node_manager("default")
    gids = cell_manager.get_final_gids()
    assert 75779 in gids
    assert 80640 in gids

    syn_manager = cell_manager.connection_managers["default"]  # unnamed population
    syn_manager_2 = nd.circuits.get_edge_manager("default", "default")
    assert syn_manager is syn_manager_2
    del syn_manager_2

    assert syn_manager.connection_count == 509
    assert len(syn_manager._populations) == 1  # connectivity and projections get merged

    cell1_src_gids = np.array([c.sgid for c in syn_manager.get_connections(75779)], dtype="int")
    proj_syn_manager = nd.circuits.get_edge_manager("thalamus-proj32-blob_projections", "default")
    projections_src_gids = np.array([c.sgid for c in proj_syn_manager.get_connections(75779)],
                                    dtype="int")
    assert len(projections_src_gids) == 17
    assert len(cell1_src_gids) == 316

    gj_manager = nd.circuits.get_edge_manager("default", "default", GapJunctionManager)
    # Ensure we got our GJ instantiated and bi-directional
    gjs_1 = list(gj_manager.get_connections(75779))
    assert len(gjs_1) == 1
    assert gjs_1[0].sgid == 80640
    gjs_2 = list(gj_manager.get_connections(80640))
    assert len(gjs_2) == 1
    assert gjs_2[0].sgid == 75779

    # P2: Assert simulation went well
    # Check voltages
    from neuron import h
    c = cell_manager.get_cell(75779)
    voltage_vec = h.Vector()
    voltage_vec.record(c._cellref.soma[0](0.5)._ref_v, 0.125)
    h.finitialize()  # reinit for the recordings to be registered

    nd.run()

    # The second order derivate get us the v increase rate (happen after a spike)
    # On a plot we clearly see the peaks. scipy can find them for us
    from scipy.signal import find_peaks
    v = voltage_vec.as_numpy()
    v_increase_rate = np.diff(v, 2)
    v_peaks, _heights = find_peaks(v_increase_rate, 2)
    assert len(v_peaks) == 4

    # SPIKES
    # NOTE: Test assertions should ideally be against irrefutable values. However it is almost
    # impossible to predict when a spike will occur given the complexity of the simulations
    # and the use of random numbers.
    # Please avoid it and use it when the conditions (e.g. replay) are obvious enough for the event
    # to occur
    spikes = nd._spike_vecs[0]
    assert spikes[1].size() == 1
    assert spikes[1][0] == 75779
    assert spikes[0][0] == pytest.approx(23.075)
