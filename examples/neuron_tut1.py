#!/usr/bin/env python
"""
Neuron tutorial I using the new HighLevel API. Original tutorial at
https://github.com/BlueBrain/SimulationTutorials/blob/master/CNS2017/NEURON/NEURON_intro.ipynb
"""
from neurodamus.core import Cell
from neurodamus.core import CurrentSource
from neurodamus.core import Neuron
from neurodamus.core import mechanisms


# Change v_init globally
# Alternatively v_init can be configured per simulation in run_sim(**kw)
Neuron.Simulation.v_init = -70


def test_tut1(quick=True):
    c = Cell.Builder.add_soma(60).create()
    hh = Cell.Mechanisms.HH(gkbar=0.0, gnabar=0.0, el=-70)
    hh.apply(c.soma)

    # clamp = StimuliSource.pulse(0.1, 50, delay=10).attach_to(c.soma)  # eqv. to Constant()
    CurrentSource.Constant(0.1, 50, 10).attach_to(c.soma)
    Neuron.run_sim(100, c.soma).plot()
    if quick:
        return

    # Execution with Active channels
    hh.gkbar = 0.01
    hh.gnabar = 0.2
    hh.apply(c.soma)
    sim = Neuron.run_sim(100, c.soma)
    # sim.run_continue(100)
    sim.plot()

    # Extending the model with dendrites
    c = (c.builder
         .add_dendrite("dend", 400, 9, diam=2, Ra=100)
         .add_dendrite("dend2", 400, 9, diam=2, Ra=100)
         .create())

    mechanisms.HH(el=-70, gl=5e-4, gkbar=.0, gnabar=.0).apply(c.dendrites)
    Neuron.run_sim(50, c.dendrites[0]).plot()

    Cell.show_topology()
    Neuron.h.psection(sec=c.dendrites[0])


if __name__ == "__main__":
    test_tut1(False)
    from six.moves import input
    input("Press enter to quit")
