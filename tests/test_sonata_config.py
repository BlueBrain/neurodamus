import os
import pytest
import subprocess
from neurodamus.io.sonata_config import SonataConfig
from neurodamus.core.configuration import SimConfig

USECASE3 = os.path.abspath(os.path.join(os.path.dirname(__file__), "simulations", "usecase3"))
SONATA_CONF_FILE = os.path.join(USECASE3, "simulation_sonata.json")
V5 = os.path.abspath(os.path.join(os.path.dirname(__file__), "simulations", "v5_sonata"))


def fork_test_parse_base():
    raw_conf = SonataConfig(SONATA_CONF_FILE)
    assert raw_conf.run["random_seed"] == 1122
    assert raw_conf.parsedRun["BaseSeed"] == 1122


def fork_test_SimConfig_from_sonata():
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


# A pytest which executes fork_* tests in a new python interpreter
# For some reason pytest-forked crashes when loading libnrnmech
def test_run_forked_tests():
    for test_name in ("fork_test_parse_base", "fork_test_SimConfig_from_sonata"):
        print("[Forked] Running", test_name)
        subprocess.run(
            ["python", os.path.abspath(__file__), test_name],
            check=True
        )


if __name__ == "__main__":
    import sys
    # In case the test is specified
    if len(sys.argv) > 1:
        test_f = globals().get(sys.argv[1])
        sys.exit(test_f())

    fork_test_parse_base()
    fork_test_SimConfig_from_sonata()
    test_simulation_sonata_config()
    test_v5_sonata_config()
