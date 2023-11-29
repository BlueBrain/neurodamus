"""
Basic tests to HL neuron for creating cells and setup a simple simulation
"""
import os
import pytest
from pathlib import Path
# !! NOTE: Please don't import neron/neurodamus at module level
# pytest weird discovery system will trigger Neuron init and open can of worms


@pytest.fixture(scope="session")
def morphologies_root(rootdir):
    return Path(rootdir) / "tests/sample_data/morphology"


@pytest.fixture
def Cell(rootdir):
    os.environ["HOC_LIBRARY_PATH"] = str(rootdir) + "/core/hoc"
    from neurodamus.core import Cell
    return Cell


@pytest.mark.parametrize(
    "morphology_path",
    ["C060114A7.asc", "C060114A7.h5", "merged_container.h5/C060114A7.h5"]
)
def test_load_cell(morphologies_root, morphology_path, Cell):
    c = Cell(1, str(morphologies_root / morphology_path))
    assert len(c.all) == 325
    assert c.axons[4].name().endswith(".axon[4]")
    assert c.soma.L == pytest.approx(26.11, abs=0.01)


def test_morphio_read(morphologies_root, Cell):
    c = Cell(1, str(morphologies_root / "simple.h5"))
    Cell.show_topology()
    assert len(c.all) == 7
    assert len(list(c.h.basal)) == 3
    assert len(list(c.h.axonal)) == 3


def test_create_cell(Cell):
    builder = Cell.Builder
    c = (builder
         .add_soma(1)
         .add_dendrite("dend1", 2, 5)
         .attach(builder.DendriteSection("dend2", 3, 2).add("sub2_dend", 4, 2))
         .add_axon("axon1", 2, 3)
         .create())

    Cell.show_topology()
    assert len(c.all) == 5
    assert len(list(c.h.basal)) == 3
    assert len(c._dend) == 3
    assert len(c._axon) == 1


def test_create_cell_2(Cell):
    c = (Cell.Builder
         .add_soma(1)
         .add_dendrite("dend1", 2, 5)
         .append_axon("ax1", 3, 2).append("ax1_2", 4, 2).append("ax1_3", 3, 3)
         .create())

    Cell.show_topology()
    assert len(c.all) == 5
    assert len(list(c.h.basal)) == 1
    assert len(c._dend) == 1
    assert len(c._axon) == 3


def test_create_cell_3(Cell):
    Dend = Cell.Builder.DendriteSection
    c = (Cell.Builder
         .add_soma(1)
         .add_dendrite("dend1", 2, 5)
         .attach(Dend("dend2", 3, 2)
                 .append("sub2_dend", 4, 2)
                 .get_root())
         .create())

    Cell.show_topology()
    assert len(c.all) == 4
    assert len(list(c.h.basal)) == 3
    assert len(c._dend) == 3
    assert c._axon is None
    assert len(c.axons) == 0


def test_basic_system():
    from neurodamus.core import Neuron, Cell, CurrentSource
    c = Cell.Builder.add_soma(60).create()
    Cell.Mechanisms.HH(gkbar=0.0, gnabar=0.0, el=-70).apply(c.soma)
    CurrentSource.pulse(0.1, 50, delay=10).attach_to(c.soma)
    # Start sim with specific dt. Default is dt=0.025 Requires setting steps as well
    sim = Neuron.run_sim(100, c.soma, v_init=-70, dt=0.1, steps_per_ms=10)
    rec = sim.get_voltages_at(c.soma)
    assert len(rec) == 1001
    assert rec[0] == -70
    assert -67.1 < rec[500] < -67
    assert rec[1000] < -69.9
    return sim


if __name__ == "__main__":
    sim = test_basic_system()
    sim.plot()
