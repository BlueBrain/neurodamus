#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

from neurodamus import Cell
from neurodamus import StimuliSource
from neurodamus import Neuron

c = Cell.Builder.add_soma(60).create()
Cell.Mechanisms.mk_HH(gkbar=0.0, gnabar=0.0, el=-70).apply(c.soma)

clamp = StimuliSource.pulse(0.1, 50, delay=10).attach_to(c.soma)
Neuron.run_sim(100, c.soma, v_init=-70).plot()
clamp.detach()

StimuliSource.Constant(0.1, 50, 10).attach_to(c.soma)
Neuron.run_sim(100, c.soma, v_init=-70).plot()

from six.moves import input
input("Press enter to quit")
