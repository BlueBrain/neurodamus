import os
import pytest
from pathlib import Path

USECASE3 = Path(__file__).parent.absolute() / "simulations" / "usecase3"
SONATA_CONF_FILE = str(USECASE3 / "simulation_sonata.json")
V5 = Path(__file__).parent.absolute() / "simulations" / "v5_sonata"


pytestmark = pytest.mark.forked


def test_parse_base():
    from neurodamus.io.sonata_config import SonataConfig
    raw_conf = SonataConfig(SONATA_CONF_FILE)
    assert raw_conf.run["random_seed"] == 1122
    assert raw_conf.parsedRun["BaseSeed"] == 1122


def test_SimConfig_from_sonata():
    from neurodamus.core.configuration import SimConfig
    SimConfig.init(SONATA_CONF_FILE, {})
    # RNGSettings in hoc correctly initialized from Sonata
    assert SimConfig.rng_info.getGlobalSeed() == 1122

    # run section
    assert SimConfig.run_conf['CircuitTarget'] == 'l4pc'
    assert SimConfig.run_conf['Simulator'] == 'NEURON'
    assert SimConfig.run_conf['Duration'] == 50.0
    assert SimConfig.run_conf['Dt'] == 0.1
    assert SimConfig.run_conf['Celsius'] == 35
    assert SimConfig.run_conf['V_Init'] == -75
    assert SimConfig.run_conf['MinisSingleVesicle'] is True

    # output section
    assert SimConfig.run_conf['SpikesFile'] == 'spikes.h5'
    assert SimConfig.run_conf['SpikesSortOrder'] == 'by_time'

    # reports section
    soma_report = SimConfig.reports['soma_report']
    assert soma_report['Target'] == 'l4pc'
    assert soma_report['Type'] == 'compartment'
    assert soma_report['ReportOn'] == 'v'
    assert soma_report['Compartments'] == 'center'
    assert soma_report['Sections'] == 'soma'
    assert soma_report['Scaling'] == 'area'
    assert soma_report['StartTime'] == 0.0
    assert soma_report['EndTime'] == 50.0
    assert soma_report['Dt'] == 0.1
    assert soma_report['Enabled']
    compartment_report = SimConfig.reports['compartment_report']
    assert compartment_report['Target'] == 'l4pc'
    assert compartment_report['Type'] == 'compartment'
    assert compartment_report['ReportOn'] == 'v'
    assert compartment_report['Compartments'] == 'all'
    assert compartment_report['Sections'] == 'all'
    assert compartment_report['Scaling'] == 'area'
    assert compartment_report['StartTime'] == 0.0
    assert compartment_report['EndTime'] == 10.0
    assert compartment_report['Dt'] == 0.1
    assert compartment_report['Enabled']

    # conditions section
    conditions = list(SimConfig._blueconfig.Conditions.values())[0]
    assert conditions['init_depleted_ProbAMPANMDA_EMS'] is False
    assert conditions['minis_single_vesicle_ProbAMPANMDA_EMS'] is True
    assert conditions['init_depleted_GluSynapse'] is True
    assert conditions['minis_single_vesicle_GluSynapse'] is False
    assert conditions['randomize_Gaba_risetime'] == 'False'


@pytest.mark.skipif(
    not os.environ.get("NEURODAMUS_NEOCORTEX_ROOT"),
    reason="Test requires loading a neocortex model to run")
def test_simulation_sonata_config():
    from neurodamus import Neurodamus
    nd = Neurodamus(str(USECASE3 / "simulation_sonata.json"), disable_reports=True)
    nd.run()
    # TODO: Check the sim status is ok. Sim has no spikes


@pytest.mark.skipif(
    not os.environ.get("NEURODAMUS_NEOCORTEX_ROOT"),
    reason="Test requires loading a neocortex model to run")
def test_v5_sonata_config():
    import numpy as np
    import numpy.testing as npt
    from neurodamus import Neurodamus

    nd = Neurodamus(str(V5 / "simulation_config.json"), disable_reports=True)
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
