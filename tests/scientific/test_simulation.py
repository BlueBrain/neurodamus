import numpy as np
import numpy.testing as npt
import os
import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile

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

    config_file = str(SIM_DIR / "v5_sonata" / "simulation_config_mini.json")
    nd = Neurodamus(config_file, disable_reports=True)
    nd.run()

    spike_gids = np.array([
        4, 2, 0
    ]) + 1  # Conform to nd 1-based
    timestamps = np.array([
        33.425, 37.35, 39.725
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
    assert 1 in gids
    assert 2 in gids

    syn_manager = cell_manager.connection_managers["external_default"]  # unnamed population
    syn_manager_2 = nd.circuits.get_edge_manager("external_default", "default")
    assert syn_manager is syn_manager_2
    del syn_manager_2

    assert syn_manager.connection_count == 509
    assert len(syn_manager._populations) == 1  # connectivity and projections get merged

    cell1_src_gids = np.array([c.sgid for c in syn_manager.get_connections(1)], dtype="int")
    proj_syn_manager = nd.circuits.get_edge_manager("thalamus-proj32-blob_projections", "default")
    projections_src_gids = np.array([c.sgid for c in proj_syn_manager.get_connections(1)],
                                    dtype="int")
    assert len(projections_src_gids) == 17
    assert len(cell1_src_gids) == 316

    gj_manager = nd.circuits.get_edge_manager("default", "default", GapJunctionManager)
    # Ensure we got our GJ instantiated and bi-directional
    gjs_1 = list(gj_manager.get_connections(1))
    assert len(gjs_1) == 1
    assert gjs_1[0].sgid == 2
    gjs_2 = list(gj_manager.get_connections(2))
    assert len(gjs_2) == 1
    assert gjs_2[0].sgid == 1

    # P2: Assert simulation went well
    # Check voltages
    from neuron import h
    c = cell_manager.get_cell(1)
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
    assert len(v_peaks) == 7

    # SPIKES
    # NOTE: Test assertions should ideally be against irrefutable values. However it is almost
    # impossible to predict when a spike will occur given the complexity of the simulations
    # and the use of random numbers.
    # Please avoid it and use it when the conditions (e.g. replay) are obvious enough for the event
    # to occur
    spikes = nd._spike_vecs[0]
    assert spikes[1].size() == 2
    assert spikes[1][0] == 1
    assert spikes[0][0] == pytest.approx(21.025)


def test_v5_gap_junction_corrections(capsys):
    import json
    from neurodamus import Neurodamus
    from neurodamus.core.configuration import SimConfig

    # Add beta_features section for gj user corrections
    config_file = str(SIM_DIR / "v5_gapjunctions" / "simulation_config.json")
    with open(config_file) as f:
        sim_config_data = json.load(f)
    sim_config_data["output"]["output_dir"] = "$CURRENT_DIR/output_gj_corrections"
    sim_config_data["beta_features"] = {
        "gapjunction_target_population": "default",
        "deterministic_stoch": True,
        "procedure_type": "validation_sim",
        "gjc": 0.2,
        "load_g_pas_file": "$CURRENT_DIR/test_g_pas_passive.hdf5",
        "manual_MEComboInfo_file": "$CURRENT_DIR/test_holding_per_gid.hdf5"
    }
    with NamedTemporaryFile("w", dir=str(SIM_DIR / "v5_gapjunctions"),
                            suffix='.json', delete=False) as tmp_config:
        json.dump(sim_config_data, tmp_config, indent=2)

    Neurodamus(tmp_config.name, disable_reports=True)
    captured = capsys.readouterr()
    assert SimConfig.beta_features.get("gapjunction_target_population") == "default"
    assert "Load user modification" in captured.out
    assert SimConfig.beta_features.get("deterministic_stoch")
    assert "Set deterministic = 1 for StochKv" in captured.out
    assert SimConfig.beta_features.get("gjc") == 0.2
    assert "Set GJc = 0.2 for 2 gap synapses" in captured.out
    assert SimConfig.beta_features.get("load_g_pas_file")
    assert "Update g_pas to fit 0.2 - file" in captured.out
    assert SimConfig.beta_features.get("manual_MEComboInfo_file")
    assert "Load holding_ic from manual_MEComboInfoFile" in captured.out

    os.unlink(tmp_config.name)
