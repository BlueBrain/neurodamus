import os
from neurodamus.io.sonata_config import SonataConfig
from neurodamus.core.configuration import SimConfig

USECASE3 = os.path.abspath(os.path.join(os.path.dirname(__file__), "simulations", "usecase3"))
SONATA_CONF_FILE = os.path.join(USECASE3, "simulation_sonata.json")


def _test_parse_base():
    raw_conf = SonataConfig(SONATA_CONF_FILE)
    print(raw_conf)


def _test_SimConfig_from_sonata():
    SimConfig.init(SONATA_CONF_FILE, {})
    # RNGSettings in hoc correctly initialized from Sonata
    assert SimConfig.rng_info.getGlobalSeed() == 1122


def test_simulation_sonata_config():
    import subprocess
    os.environ['NEURODAMUS_PYTHON'] = "."
    subprocess.run(
        ["bash", "tests/test_simulation.bash", USECASE3, "simulation_sonata.json"],
        check=True
    )


if __name__ == "__main__":
    _test_parse_base()
    _test_SimConfig_from_sonata()
    test_simulation_sonata_config()
