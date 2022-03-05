#!/usr/bin/env python
"""
Test suite for the new-gen Stimuli source (replacing TStim.hoc and parts of StimManager)
"""
import pytest
from neurodamus.core.stimuli import CurrentSource, ConductanceSource, RealElectrode, PointSourceElectrode
from neurodamus.core.random import Random123
from neuron import h
import numpy as np


class TestElectrodes(object):
    def setup_method(self):
        rng = Random123(1, 2, 3)
        self.stim = PointSourceElectrode('Extracellular', 1000, 'Pulse', [100],  [100], None, [100], 0, 0, 0, sigma=1)

    def test_attach(self):

        testSec = h.Section(name='testSec')
        testSec.L = 10
        testSec.diam = 10
        testSec.insert('hh')
        testSec.nseg = 1
        testSec.pt3dadd(.5,0,0,10)
        testSec.pt3dadd(1.5,0,0,10)

        self.stim.attach_to(testSec)

        vec = self.stim.extracellulars[0].to_python()
        assert vec == pytest.approx([0,0,100/(4*np.pi)*1e3,100/(4*np.pi)*1e3,0])
