#!/usr/bin/env python
# -*- coding: utf-8 -*-
from neurodamus import Cell
from neurodamus import StimuliSource
from neurodamus import Neuron
from os import path

MORPHO = path.join(path.dirname(__file__), "..", "tests/morphology/C060114A7.asc")


def test_tut2():
    c = Cell(0, MORPHO)
    print("The morphology {} basal, {} apical, {} axonal sections.".format(
        len(c.dendrites), len(c.apical_dendrites), len(c.axons)))

    hh = Cell.Mechanisms.mk_HH(gkbar=.0, gnabar=.0, el=-70)
    hh.apply(c.all)
    hh.gkbar = 0.01
    hh.gnabar = 0.2
    hh.apply(c.soma)
    hh.gnabar = 0.25
    hh.apply(c.axons)

    StimuliSource.Constant(0.5, 200, 10).attach_to(c.soma)
    Neuron.run_sim(300, c.soma, v_init=-70).plot()


if __name__ == "__main__":
    test_tut2()
