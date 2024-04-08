"""Tests load balance."""
# Since a good deal of load balance tests are e2e we put all of them together in this group
import logging
import os
import pytest
import shutil
import tempfile
from pathlib import Path

SIM_DIR = Path(__file__).parent.parent.absolute() / "simulations"


@pytest.fixture
def target_manager():
    from neurodamus.target_manager import NodesetTarget
    from neurodamus.core.nodeset import NodeSet
    nodes_t1 = NodeSet([1, 11, 21, 31, 41, 51, 61, 71, 81, 91, 101, 111]).register_global("All")
    nodes_t2 = NodeSet([1, 11, 21, 31, 41, 51]).register_global("All")
    t1 = NodesetTarget("Small", [nodes_t1], [nodes_t1])
    t2 = NodesetTarget("VerySmall", [nodes_t2], [nodes_t2])
    return MockedTargetManager(t1, t2)


def test_loadbal_no_cx(target_manager, caplog):
    from neurodamus.cell_distributor import LoadBalance, TargetSpec
    lbal = LoadBalance(1, "/gpfs/fake_path_to_nodes_1", "pop", target_manager, 4)
    assert not lbal._cx_targets
    assert not lbal._valid_loadbalance
    with caplog.at_level(logging.INFO):
        assert not lbal._cx_valid(TargetSpec("random_target"))
        assert " => No complexity files for current circuit yet" in caplog.records[-1].message


def test_loadbal_subtarget(target_manager, caplog):
    """Ensure given the right files are in the lbal dir, the correct situation is detected
    """
    from neurodamus.cell_distributor import LoadBalance, TargetSpec
    tmp_path = tempfile.TemporaryDirectory("test_loadbal_subtarget")
    os.chdir(tmp_path.name)
    nodes_file = "/gpfs/fake_node_path"
    lbdir, _ = LoadBalance._get_circuit_loadbal_dir(nodes_file, "pop")
    shutil.copyfile(SIM_DIR / "1k_v5_balance" / "cx_Small.dat", lbdir / "cx_Small#.dat")

    lbal = LoadBalance(1, nodes_file, "pop", target_manager, 4)
    assert "Small" in lbal._cx_targets
    assert not lbal._valid_loadbalance
    with caplog.at_level(logging.INFO):
        assert not lbal._cx_valid(TargetSpec("random_target"))
        assert " => No Cx files available for requested target" in caplog.records[-1].message
    assert lbal._cx_valid(TargetSpec("Small"))  # yes!
    assert not lbal._cx_valid(TargetSpec("VerySmall"))  # not yet, need to derive subtarget

    with caplog.at_level(logging.INFO):
        assert lbal._reuse_cell_complexity(TargetSpec("VerySmall"))
        assert len(caplog.records) >= 2
        assert "Attempt reusing cx files from other targets..." in caplog.records[-2].message
        assert "Target VerySmall is a subset of the target Small." in caplog.records[-1].message


@pytest.fixture
def circuit_conf():
    from neurodamus.core.configuration import CircuitConfig
    PROJ = "/gpfs/bbp.cscs.ch/project"
    return CircuitConfig(
        CircuitPath=PROJ + "/proj12/jenkins/cellular/circuit-2k",
        CellLibraryFile=PROJ + "/proj12/jenkins/cellular/circuit-2k/nodes_v2.h5",
        METypePath=PROJ + "/proj64/entities/emodels/2017.11.03/hoc",
        MorphologyPath=PROJ + "/proj12/jenkins/cellular/circuit-2k/morphologies/ascii",
        nrnPath="<NONE>",  # no connectivity
        CircuitTarget="All:Small"
    )


def test_load_balance_integrated(target_manager, circuit_conf):
    """Comprehensive test using real cells and deriving cx for a sub-target
    """
    from neurodamus.cell_distributor import CellDistributor, LoadBalance, TargetSpec
    tmp_path = tempfile.TemporaryDirectory("test_load_balance_integrated")
    os.chdir(tmp_path.name)
    cell_manager = CellDistributor(circuit_conf, target_manager)
    cell_manager.load_nodes()

    lbal = LoadBalance(1, circuit_conf.CircuitPath, "All", target_manager, 4)
    t1 = TargetSpec("All:Small")
    assert not lbal._cx_valid(t1)

    with lbal.generate_load_balance(t1, cell_manager):
        cell_manager.finalize()

    assert "All_Small" in lbal._cx_targets
    assert "All_Small" in lbal._valid_loadbalance
    assert lbal._cx_valid(t1)

    # Check subtarget
    assert "All_VerySmall" not in lbal._cx_targets
    assert "All_VerySmall" not in lbal._valid_loadbalance
    assert lbal._reuse_cell_complexity(TargetSpec("All:VerySmall"))

    # Check not super-targets
    assert not lbal._reuse_cell_complexity(TargetSpec(None))


def test_multisplit(target_manager, circuit_conf, capsys):
    """Comprehensive test using real cells, multi-split and complexity derivation
    """
    from neurodamus.cell_distributor import CellDistributor, LoadBalance, TargetSpec
    MULTI_SPLIT = 2
    tmp_path = tempfile.TemporaryDirectory("test_multisplit")
    os.chdir(tmp_path.name)

    cell_manager = CellDistributor(circuit_conf, target_manager)
    cell_manager.load_nodes()
    lbal = LoadBalance(MULTI_SPLIT, circuit_conf.CircuitPath, "All", target_manager, 4)
    t1 = TargetSpec("All:Small")
    assert not lbal._cx_valid(t1)

    with lbal.generate_load_balance(t1, cell_manager):
        cell_manager.finalize()

    captured = capsys.readouterr()
    assert "13 pieces" in captured.out
    assert "at least one cell is broken into 2 pieces" in captured.out
    assert "All_Small" in lbal._cx_targets
    assert "All_Small" in lbal._valid_loadbalance
    assert lbal._cx_valid(t1)

    # Convert balance for 1 CPU so we can import
    lbal.target_cpu_count = 1
    lbal._cpu_assign("All_Small")
    binfo = lbal.load_balance_info(t1)
    assert binfo.npiece() == 13

    # Ensure load-bal is reused for smaller targets in multisplit too
    assert "All_VerySmall" not in lbal._cx_targets
    assert "All_VerySmall" not in lbal._valid_loadbalance
    assert lbal.valid_load_distribution(TargetSpec("All:VerySmall"))
    assert "All_VerySmall" in lbal._cx_targets
    assert "All_VerySmall" in lbal._valid_loadbalance
    captured = capsys.readouterr()
    assert "Target VerySmall is a subset of the target All_Small" in captured.out


def _create_tmpconfig_lbal(config_file):
    import json
    import shutil
    from tempfile import NamedTemporaryFile

    with open(config_file, "r") as f:
        sim_config_data = json.load(f)
        sim_config_data["connection_overrides"] = [
            {
                "name": "virtual_proj",
                "source": "virtual_target",
                "target": "l4pc",
                "weight": 0.0
            },
            {
                "name": "disconnect",
                "source": "l4pc",
                "target": "virtual_target",
                "delay": 0.025,
                "weight": 0.0
            }
        ]
    tmp_file = NamedTemporaryFile(suffix=".json", dir=os.path.dirname(config_file), delete=True)
    shutil.copy2(config_file, tmp_file.name)

    with open(tmp_file.name, "w") as f:
        json.dump(sim_config_data, f, indent=2)
    return tmp_file


def _read_complexity_file(base_dir, pattern, cx_pattern):
    import glob
    # Construct the full pattern path
    full_pattern = os.path.join(base_dir, pattern, cx_pattern)

    # Use glob to find files that match the pattern
    matching_files = glob.glob(full_pattern)

    # Read each matching file
    for file_path in matching_files:
        try:
            with open(file_path, 'r') as file:
                content = file.read()
                return content
        except FileNotFoundError:
            print(f"File not found: {file_path}")


def test_loadbal_integration():
    """Ensure given the right files are in the lbal dir, the correct situation is detected
    """
    from neurodamus import Node
    from neurodamus.core.configuration import GlobalConfig, SimConfig
    GlobalConfig.verbosity = 2

    # Add connection_overrides for the virtual population so the offsets are calculated before LB
    tmp_file = _create_tmpconfig_lbal(SIM_DIR / "usecase3" / "simulation_sonata.json")
    nd = Node(tmp_file.name, {"lb_mode": "WholeCell"})
    nd.load_targets()
    SimConfig.check_connections_configure(nd._target_manager)
    lb = nd.compute_load_balance()
    nd.create_cells(lb)

    # Check the complexity file
    base_dir = "sim_conf"
    pattern = "_loadbal_*.*"  # Matches any hash and population
    cx_pattern = "cx_*#.dat"  # Matches any cx file with the pattern
    assert Path(base_dir).is_dir(), "Directory 'sim_conf' not found."
    cx_file = _read_complexity_file(base_dir, pattern, cx_pattern)
    lines = cx_file.splitlines()
    assert int(lines[1]) == 3, "Number of gids different than 3."
    # Gid should be without offset (2 instead of 1002)
    assert int(lines[3].split()[0]) == 2, "gid 2 not found."


class MockedTargetManager:
    """
    A mock target manager, for the single purpose of returning the provided targets
    """

    def __init__(self, *targets) -> None:
        self.targets = {t.name.split(":")[-1]: t for t in targets}

    def get_target(self, target_spec, target_pop=None):
        from neurodamus.target_manager import TargetSpec
        if not isinstance(target_spec, TargetSpec):
            target_spec = TargetSpec(target_spec)
        if target_pop:
            target_spec.population = target_pop
        target_name = target_spec.name or TargetSpec.GLOBAL_TARGET_NAME
        target_pop = target_spec.population
        target = self.targets[target_name]
        return target if target_pop is None else target.make_subtarget(target_pop)

    def register_local_nodes(*_):
        pass
