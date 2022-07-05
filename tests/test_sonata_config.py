import os
import pytest
from neurodamus.io.sonata_config import SonataConfig
from neurodamus.core.configuration import SimConfig

USECASE3 = os.path.abspath(os.path.join(os.path.dirname(__file__), "simulations", "usecase3"))
SONATA_CONF_FILE = os.path.join(USECASE3, "simulation_sonata.json")
V5 = os.path.abspath(os.path.join(os.path.dirname(__file__), "simulations", "v5_sonata"))


def _test_parse_base():
    raw_conf = SonataConfig(SONATA_CONF_FILE)
    print(raw_conf)


def _test_SimConfig_from_sonata():
    SimConfig.init(SONATA_CONF_FILE, {})
    # RNGSettings in hoc correctly initialized from Sonata
    assert SimConfig.rng_info.getGlobalSeed() == 1122

    # run section
    assert SimConfig.run_conf['CircuitTarget'] == 'l4pc'
    assert SimConfig.run_conf['Simulator'] == 'NEURON'
    assert SimConfig.run_conf['Duration'] == 50.0
    assert SimConfig.run_conf['Dt'] == 0.1

    # output section
    assert SimConfig.run_conf['SpikesFile'] == 'spikes.h5'
    assert SimConfig.run_conf['SpikesSortOrder'] == 'by_time'

    # reports section
    soma_report = SimConfig.reports['soma_report']
    assert soma_report['Target'] == 'l4pc'
    assert soma_report['Type'] == 'Compartment'
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
    assert compartment_report['Type'] == 'Compartment'
    assert compartment_report['ReportOn'] == 'v'
    assert compartment_report['Compartments'] == 'all'
    assert compartment_report['Sections'] == 'all'
    assert compartment_report['Scaling'] == 'area'
    assert compartment_report['StartTime'] == 0.0
    assert compartment_report['EndTime'] == 10.0
    assert compartment_report['Dt'] == 0.1
    assert compartment_report['Enabled']


@pytest.mark.skipif(
    not os.environ.get("NEURODAMUS_NEOCORTEX_ROOT"),
    reason="Test requires loading a neocortex model to run")
def test_simulation_sonata_config():
    import subprocess
    os.environ['NEURODAMUS_PYTHON'] = "."
    subprocess.run(
        ["bash", "tests/test_simulation.bash", USECASE3, "simulation_sonata.json"],
        check=True
    )


@pytest.mark.skipif(
    not os.environ.get("NEURODAMUS_NEOCORTEX_ROOT"),
    reason="Test requires loading a neocortex model to run")
def test_v5_sonata_config():
    import subprocess
    os.environ['NEURODAMUS_PYTHON'] = "."
    subprocess.run(
        ["bash", "tests/test_simulation.bash", V5, "simulation_config.json"],
        check=True
    )


if __name__ == "__main__":
    _test_parse_base()
    _test_SimConfig_from_sonata()
    test_simulation_sonata_config()
    test_v5_sonata_config()
