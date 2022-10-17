import logging
import os
import pytest
import shutil
import tempfile
from pathlib import Path

SIM_DIR = Path(__file__).parent.absolute() / "simulations"

pytestmark = pytest.mark.forked


@pytest.fixture
def target_manager_hoc():
    from neurodamus.target_manager import _HocTarget
    t1 = _HocTarget("Small", None, _raw_gids=[1, 11, 21, 31, 41, 51, 61, 71, 81, 91, 101, 111])
    t2 = _HocTarget("VerySmall", None, _raw_gids=[1, 11, 21, 31, 41, 51])
    return MockedTargetManager(t1, t2)


def test_loadbal_no_cx(target_manager_hoc, caplog):
    from neurodamus.cell_distributor import LoadBalance, TargetSpec
    lbal = LoadBalance(1, "/gpfs/fake_path_to_nodes_1", target_manager_hoc, 4)
    assert not lbal._cx_targets
    assert not lbal._valid_loadbalance
    with caplog.at_level(logging.INFO):
        assert not lbal._cx_valid(TargetSpec("random_target"))
        assert caplog.records[-1].message == " => No complexity files for current circuit yet"


def test_loadbal_subtarget(target_manager_hoc, caplog):
    """Ensure given the right files are in the lbal dir, the correct situation is detected
    """
    from neurodamus.cell_distributor import LoadBalance, TargetSpec
    tmp_path = tempfile.TemporaryDirectory("test_loadbal_subtarget")
    os.chdir(tmp_path.name)
    nodes_file = "/gpfs/fake_node_path"
    lbdir, _ = LoadBalance._get_circuit_loadbal_dir(nodes_file)
    shutil.copyfile(SIM_DIR / "1k_v5_balance" / "cx_Small.dat", lbdir / "cx_Small#.dat")

    lbal = LoadBalance(1, nodes_file, target_manager_hoc, 4)
    assert "Small" in lbal._cx_targets
    assert not lbal._valid_loadbalance
    with caplog.at_level(logging.INFO):
        assert not lbal._cx_valid(TargetSpec("random_target"))
        assert caplog.records[-1].message == " => No Cx files available for requested target"
    assert lbal._cx_valid(TargetSpec("Small"))  # yes!
    assert not lbal._cx_valid(TargetSpec("VerySmall"))  # not yet, need to derive subtarget

    with caplog.at_level(logging.INFO):
        assert lbal._reuse_cell_complexity(TargetSpec("VerySmall"))
        assert len(caplog.records) >= 2
        assert caplog.records[-2].message == "Attempt reusing cx files from other targets..."
        assert caplog.records[-1].message.startswith(
            "Target VerySmall is a subset of the target Small."
        )


@pytest.fixture
def circuit_conf():
    from neurodamus.core.configuration import CircuitConfig
    PROJ = "/gpfs/bbp.cscs.ch/project"
    return CircuitConfig(
        CircuitPath=PROJ + "/proj12/jenkins/cellular/circuit-2k",
        CellLibraryFile="circuit.mvd3",
        MEComboInfoFile=PROJ + "/proj64/entities/emodels/2017.11.03/mecombo_emodel.tsv",
        METypePath=PROJ + "/proj64/entities/emodels/2017.11.03/hoc",
        MorphologyPath=PROJ + "/proj12/jenkins/cellular/circuit-2k/morphologies/ascii",
        nrnPath="<NONE>",  # no connectivity
        CircuitTarget="Small"
    )


@pytest.mark.skipif(
    not os.environ.get("NEURODAMUS_NEOCORTEX_ROOT"),
    reason="Test requires loading a neocortex model to run"
)
def test_load_balance_integrated(target_manager_hoc, circuit_conf):
    """Comprehensive test using real cells and deriving cx for a sub-target
    """
    from neurodamus.cell_distributor import CellDistributor, LoadBalance, TargetSpec
    tmp_path = tempfile.TemporaryDirectory("test_load_balance_integrated")
    os.chdir(tmp_path.name)
    cell_manager = CellDistributor(circuit_conf, target_manager_hoc)
    cell_manager.load_nodes()

    lbal = LoadBalance(1, circuit_conf.CircuitPath, target_manager_hoc, 4)
    t1 = TargetSpec("Small")
    assert not lbal._cx_valid(t1)

    with lbal.generate_load_balance(t1, cell_manager):
        cell_manager.finalize()

    assert "Small" in lbal._cx_targets
    assert "Small" in lbal._valid_loadbalance
    assert lbal._cx_valid(t1)

    # Check subtarget
    assert "VerySmall" not in lbal._cx_targets
    assert "VerySmall" not in lbal._valid_loadbalance
    assert lbal._reuse_cell_complexity(TargetSpec("VerySmall"))

    # Check not super-targets
    assert not lbal._reuse_cell_complexity(TargetSpec(None))


@pytest.mark.skipif(
    not os.environ.get("NEURODAMUS_NEOCORTEX_ROOT"),
    reason="Test requires loading a neocortex model to run"
)
def test_multisplit(target_manager_hoc, circuit_conf, capsys):
    """Comprehensive test using real cells, multi-split and complexity derivation
    """
    from neurodamus.cell_distributor import CellDistributor, LoadBalance, TargetSpec
    MULTI_SPLIT = 2
    tmp_path = tempfile.TemporaryDirectory("test_multisplit")
    os.chdir(tmp_path.name)

    cell_manager = CellDistributor(circuit_conf, target_manager_hoc)
    cell_manager.load_nodes()
    lbal = LoadBalance(MULTI_SPLIT, circuit_conf.CircuitPath, target_manager_hoc, 4)
    t1 = TargetSpec("Small")
    assert not lbal._cx_valid(t1)

    with lbal.generate_load_balance(t1, cell_manager):
        cell_manager.finalize()

    captured = capsys.readouterr()
    assert "13 pieces" in captured.out
    assert "at least one cell is broken into 2 pieces" in captured.out
    assert "Small" in lbal._cx_targets
    assert "Small" in lbal._valid_loadbalance
    assert lbal._cx_valid(t1)

    # Convert balance for 1 CPU so we can import
    lbal.target_cpu_count = 1
    lbal._cpu_assign("Small")
    binfo = lbal.load_balance_info(t1)
    assert binfo.npiece() == 13

    # Ensure load-bal is reused for smaller targets in multisplit too
    assert "VerySmall" not in lbal._cx_targets
    assert "VerySmall" not in lbal._valid_loadbalance
    assert lbal.valid_load_distribution(TargetSpec("VerySmall"))
    assert "VerySmall" in lbal._cx_targets
    assert "VerySmall" in lbal._valid_loadbalance
    captured = capsys.readouterr()
    assert "Target VerySmall is a subset of the target Small" in captured.out


class MockedTargetManager:
    """
    A mock target manager, for the single purpose of returning the provided targets
    """

    def __init__(self, *targets) -> None:
        self.targets = {t.name: t for t in targets}

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

    # Target manager has a hoc target parser which we need to mock too
    class Parser:
        def updateTargets(self, *_):
            pass

    parser = Parser()
