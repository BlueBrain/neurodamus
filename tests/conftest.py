import pytest
from pathlib import Path

SIM_DIR = Path(__file__).parent.absolute() / "simulations"
USECASE3 = SIM_DIR / "usecase3"


@pytest.fixture(scope="session")
def rootdir(request):
    return request.config.rootdir


@pytest.fixture(scope="session", name="SIM_DIR")
def sim_data_path():
    return SIM_DIR


@pytest.fixture(scope="session", name="USECASE3")
def usecase3_path():
    return USECASE3


@pytest.fixture
def sonata_config():
    return dict(
        manifest={"$CIRCUIT_DIR": str(USECASE3)},
        network="$CIRCUIT_DIR/circuit_config.json",
        node_sets_file="$CIRCUIT_DIR/nodesets.json",
        run={
            "random_seed": 12345,
            "dt": 0.05,
            "tstop": 10,
        }
    )
