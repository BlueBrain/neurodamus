#!/usr/bin/env python
# -*- coding: utf-8 -*-
from neurodamus import Cell
from neurodamus import StimuliSource
from neurodamus import Neuron

# Change v_init globally
# Alternatively v_init can be configured per simulation in run_sim(**kw)
Neuron.Simulation.v_init = -70


def test_tut1(quick=True):
    c = Cell.Builder.add_soma(60).create()
    hh = Cell.Mechanisms.mk_HH(gkbar=0.0, gnabar=0.0, el=-70)
    hh.apply(c.soma)

    # clamp = StimuliSource.pulse(0.1, 50, delay=10).attach_to(c.soma)  # eqv. to Constant()
    StimuliSource.Constant(0.1, 50, 10).attach_to(c.soma)
    Neuron.run_sim(100, c.soma).plot()
    if quick:
        return

    # Execution with Active channels
    hh.gkbar = 0.01
    hh.gnabar = 0.2
    hh.apply(c.soma)
    sim = Neuron.run_sim(50, c.soma)
    sim.plot()
    # Continue run until 100 ms
    sim.run_continue(100)
    sim.plot()

    # Extending the model with dendrites
    c.builder.add("dend", 400, 9, diam=2).add("dend2", 400, 9, diam=2).create()
    Cell.show_topology()

    Cell.Mechanisms.mk_HH(el=-70, gl=1e-4, gkbar=.0, gnabar=.0).apply(c.dendrites)


if __name__ == "__main__":
    from six.moves import input
    test_tut1(False)
    input("Press enter to quit")
