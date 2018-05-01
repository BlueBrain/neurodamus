#!/usr/bin/env python
# -*- coding: utf-8 -*-
from neurodamus import Cell
from neurodamus import StimuliSource
from neurodamus import Neuron


def test_tut1():
    c = Cell.Builder.add_soma(60).create()
    Cell.Mechanisms.mk_HH(gkbar=0.0, gnabar=0.0, el=-70).apply(c.soma)

    clamp = StimuliSource.pulse(0.1, 50, delay=10).attach_to(c.soma)
    Neuron.run_sim(100, c.soma, v_init=-70).plot()
    clamp.detach()

    StimuliSource.Constant(0.1, 50, 10).attach_to(c.soma)
    Neuron.run_sim(100, c.soma, v_init=-70).plot()


if __name__ == "__main__":
    from six.moves import input
    test_tut1()
    input("Press enter to quit")
