#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

from neurodamus import Cell
from neurodamus import StimuliSource
from neurodamus import Neuron

c = Cell.Builder.add_soma(60).create()
soma = c.soma
soma.insert("hh")
soma.gkbar_hh = 0.0 # S/cm^2
soma.gnabar_hh = 0.0 # S/cm^2
soma.el_hh = -70 # mV
print("Soma:\n", c.section_info(soma))

StimuliSource.pulse(0.1, 50, delay=10).attach_to(soma)
Neuron.run_sim(100, c.soma, v_init=-70).plot()
