#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
from neurodamus import StimuliSource

__author__ = "Fernando Pereira"
__copyright__ = "Fernando Pereira"


class TestStimuli(object):
    def setup_method(self):
        self.stim = StimuliSource()

    def test_flat_segment(self):
        self.stim.add_segment(1.2, 10)
        assert list(self.stim.time_vec) == [0, 10]
        assert list(self.stim.stim_vec) == [1.2, 1.2]

    def test_pulse(self):
        self.stim.add_pulse(1.2, 10)
        assert list(self.stim.time_vec) == [0, 0, 10, 10]
        assert list(self.stim.stim_vec) == [0, 1.2, 1.2, 0]

    @pytest.mark.parametrize("base_amp", [-1, 0, 1.5])
    def test_pulse_diff_base(self, base_amp):
        self.stim.add_pulse(1.2, 10, base_amp=base_amp)
        assert list(self.stim.time_vec) == [0, 0, 10, 10]
        assert list(self.stim.stim_vec) == [base_amp, 1.2, 1.2, base_amp]

    def test_two_pulses(self):
        self.stim.add_pulse(1.2, 10)
        self.stim.delay(5)
        self.stim.add_pulse(0.8, 5)
        assert list(self.stim.time_vec) == [0, 0, 10, 10, 15, 15, 20, 20]
        assert list(self.stim.stim_vec) == [0, 1.2, 1.2, 0, 0, 0.8, 0.8, 0]

    def test_ramp(self):
        self.stim.add_ramp(5, 7.5, 10)
        assert list(self.stim.time_vec) == [0, 0, 10, 10]
        assert list(self.stim.stim_vec) == [0, 5, 7.5, 0]

    def test_train(self):
        self.stim.add_train(1.2, 10, 20, 350)
        # At 10Hz pulses have T=100ms
        # We end up with 4 pulses, the last one with reduced rest phase
        assert list(self.stim.time_vec) == [0, 0, 20, 20, 100, 100, 120, 120, 200, 200, 220, 220,
                                            300, 300, 320, 320, 350]
        assert list(self.stim.stim_vec) == [0, 1.2, 1.2, 0] * 4 + [0]

    def test_sin(self):
        self.stim.add_sin(1, 0.1, 10000)
        assert list(self.stim.time_vec) == pytest.approx([0, 0.025, 0.05, 0.075, 0.1])
        assert list(self.stim.stim_vec) == pytest.approx([0, 1, 0, -1, 0])

    def test_sin_long(self):
        self.stim.add_sin(1, 200, 10, 25)
        assert list(self.stim.time_vec) == pytest.approx([0, 25, 50, 75, 100, 125, 150, 175, 200])
        assert list(self.stim.stim_vec) == pytest.approx([0, 1, 0, -1] * 2 + [0])

    def test_add_pulses(self):
        self.stim.add_pulses(0.5, 1, 2, 3, 4, base_amp=0.1)
        assert list(self.stim.time_vec) == [0, 0, 0.5, 0.5, 1, 1, 1.5, 1.5, 2, 2]
        assert list(self.stim.stim_vec) == [0.1, 1, 1, 2, 2, 3, 3, 4, 4, 0.1]
