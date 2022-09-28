import os
import pytest
import subprocess
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


@pytest.mark.skipif(
    os.environ.get("SLURM_JOB_ID") is None and os.environ.get("RUN_MPI") is None,
    reason="Simulation tests require MPI")
def test_quick_v6():
    """ A full-execution quick v6 test
        We require launching with mpiexec, so we do it in a bash script
    """
    simdir = SIM_DIR / "mini_v6"
    subprocess.run(
        ["bash", "tests/test_simulation.bash", simdir, "BlueConfig", "mpiexec"],
        check=True
    )


def test_simulation_sonata_config():
    from neurodamus import Neurodamus
    config_file = str(SIM_DIR / "usecase3" / "simulation_sonata.json")
    nd = Neurodamus(config_file, disable_reports=True)
    nd.run()
    # TODO: Check the sim status is ok. Sim has no spikes


def test_v5_sonata_config():
    import numpy as np
    import numpy.testing as npt
    from neurodamus import Neurodamus

    config_file = str(SIM_DIR / "v5_sonata" / "simulation_config.json")
    nd = Neurodamus(config_file, disable_reports=True)
    nd.run()

    spike_gids = np.array([
        68855, 69877, 64935, 66068, 62945, 63698, 67666, 68223,
        65915, 69530, 63256, 64861, 66105, 68532, 65951, 64163,
        68855, 62797, 69877
    ]) + 1  # Conform to nd 1-based
    timestamps = np.array([
        9.125, 14.3, 15.425, 29.075, 31.025, 33.2, 34.175, 35.075,
        35.625, 36.875, 36.95, 37.1, 37.6, 37.6, 38.05, 38.075,
        38.175, 38.45, 39.875
    ])

    obtained_timestamps = nd._spike_vecs[0][0].as_numpy()
    obtained_spike_gids = nd._spike_vecs[0][1].as_numpy()
    npt.assert_allclose(spike_gids, obtained_spike_gids)
    npt.assert_allclose(timestamps, obtained_timestamps)


def test_v5_gap_junction():
    import numpy as np
    from neurodamus import Neurodamus
    from neurodamus.gap_junction import GapJunctionManager

    config_file = str(SIM_DIR / "v5_gapjunctions" / "BlueConfig")
    nd = Neurodamus(config_file, disable_reports=True)

    cell_manager = nd.circuits.base_cell_manager
    gids = cell_manager.get_final_gids()
    assert 74188 in gids
    assert 74051 in gids

    syn_mananer = cell_manager.connection_managers[""]  # unnamed population
    syn_manager_2 = nd.circuits.get_edge_manager("", "")
    assert syn_mananer is syn_manager_2
    del syn_manager_2

    assert syn_mananer.connection_count == 677
    assert len(syn_mananer._populations) == 1  # connectivity and projections get merged

    cell1_src_gids = np.array([c.sgid for c in syn_mananer.get_connections(74188)], dtype="int")
    PROJ_GID0 = 220422  # first gid in proj_Thalamocortical_VPM_Source
    projections_src_gids = cell1_src_gids[cell1_src_gids >= PROJ_GID0]
    assert len(projections_src_gids) == 18
    assert len(cell1_src_gids[cell1_src_gids < PROJ_GID0]) == 192

    gj_manager = nd.circuits.get_edge_manager("", "", GapJunctionManager)
    # Ensure we got our GJ instantiated and bi-directional
    gjs_1 = list(gj_manager.get_connections(74188))
    assert len(gjs_1) == 1
    assert gjs_1[0].sgid == 74051
    gjs_2 = list(gj_manager.get_connections(74051))
    assert len(gjs_2) == 1
    assert gjs_2[0].sgid == 74188

    # P2: Assert simulation went well
    # Check voltages
    from neuron import h
    c = cell_manager.gid2cell[74188]
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
    assert spikes[1][0] == 74188
    assert spikes[0][0] == pytest.approx(28.425)
