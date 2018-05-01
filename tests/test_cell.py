from os import path
from neurodamus import Neuron, Cell, StimuliSource
from pytest import approx


def test_load_cell():
    d = path.dirname(__file__)
    c = Cell(1, path.join(d, "morphology/C060114A7.asc"))
    assert len(c.all) == 325
    assert c.axons[4].name() == "Cell[0].axon[4]"
    assert c.soma.L == approx(26.11, abs=0.01)


def test_basic_system():
    c = Cell.Builder.add_soma(60).create()
    Cell.Mechanisms.mk_HH(gkbar=0.0, gnabar=0.0, el=-70).apply(c.soma)
    StimuliSource.pulse(0.1, 50, delay=10).attach_to(c.soma)
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
    from six.moves import input
    input("Press enter to quit")
