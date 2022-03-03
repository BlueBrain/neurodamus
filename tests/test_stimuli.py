#!/usr/bin/env python
"""
Test suite for the new-gen Stimuli source (replacing TStim.hoc and parts of StimManager)
"""
import pytest
from neurodamus.core import CurrentSource, ConductanceSource
from neurodamus.core.random import Random123


class TestStimuli(object):
    def setup_method(self):
        rng = Random123(1, 2, 3)
        self.stim = CurrentSource(rng=rng)
        self.stim_g = ConductanceSource(rng=rng)

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
        assert list(self.stim.time_vec) == pytest.approx([0, 0.025, 0.05, 0.075, 0.1, 0.1])
        assert list(self.stim.stim_vec) == pytest.approx([0, 1, 0, -1, 0, 0])

    def test_sin_long(self):
        self.stim.add_sin(1, 200, 10, 25)
        assert list(self.stim.time_vec) == pytest.approx([0, 25, 50, 75, 100, 125, 150,
                                                          175, 200, 200])
        assert list(self.stim.stim_vec) == pytest.approx([0, 1, 0, -1] * 2 + [0, 0])

    def test_add_pulses(self):
        self.stim.add_pulses(0.5, 1, 2, 3, 4, base_amp=0.1)
        assert list(self.stim.time_vec) == [0, 0, 0.5, 0.5, 1, 1, 1.5, 1.5, 2, 2]
        assert list(self.stim.stim_vec) == [0.1, 1, 1, 2, 2, 3, 3, 4, 4, 0.1]

    def test_noise(self):
        self.stim.add_noise(0.5, 0.1, 5, init_zero=True, final_zero=True)
        assert list(self.stim.time_vec) == pytest.approx([0, 0.5, 1, 1.5, 2, 2.5,
                                                          3, 3.5, 4, 4.5, 5, 5])
        assert list(self.stim.stim_vec) == pytest.approx([0, 0.56316322, 0.5539058, 0.6810689,
                                                          0.20896532, 1.00691217, 0.78783759,
                                                          0.68817496, -6.4286609e-05, 0.21165959,
                                                          0, 0])

    def test_shot_noise(self):
        self.stim.add_shot_noise(4.0, 0.4, 2E3, 40E-3, 16E-4, 2)
        assert list(self.stim.time_vec) == pytest.approx([0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5,
                                                          1.75, 2.0, 2.0])
        assert list(self.stim.stim_vec) == pytest.approx([0.0, 0.0, 0.0, 0.0, 0.0, 0.0700357,
                                                          0.1032799, 0.1170881, 0.1207344, 0.0])

    def test_ornstein_uhlenbeck(self):
        self.stim_g.add_ornstein_uhlenbeck(2.8, 0.0042, 0.029, 2)
        assert list(self.stim_g.time_vec) == pytest.approx([0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5,
                                                            1.75, 2.0, 2.0])
        assert list(self.stim_g.stim_vec) == pytest.approx([0.029, 0.02933925, 0.02959980,
                                                            0.03052109, 0.02882802, 0.03156533,
                                                            0.03289219, 0.03357043, 0.03049419,
                                                            0.0])

    def test_pulses_arbitrary(self):
        self.stim.add_pulses_arbitrary([1],[1])
        assert list(self.stim.time_vec) == [0.0, 0.0, 0.0, 1.0, 1.0]
        assert list(self.stim.stim_vec) == [0.0, 0.0, 1.0, 1.0, 0.0]

    def test_pulses_arbitrary_complex(self):
        self.stim.add_pulses_arbitrary([1,2],[10,20],delay=100)
        assert list(self.stim.time_vec) == [0.0, 100.0, 100.0, 110.0, 110.0, 130, 130]
        assert list(self.stim.stim_vec) == [0.0, 0.0, 1.0, 1.0, 2.0, 2.0, 0]
