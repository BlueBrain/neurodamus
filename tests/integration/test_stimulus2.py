"""
A collection of tests for advanced stimulus generated with the help of Neuron
"""

import pytest
from neurodamus.core import CurrentSource, ConductanceSource
from neurodamus.core.random import Random123


class TestStimuli:
    def setup_method(self):
        rng = Random123(1, 2, 3)
        self.stim = CurrentSource(rng=rng)

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
        self.stim.add_noise(0.5, 0.1, 5)
        assert list(self.stim.time_vec) == pytest.approx([0, 0, 0.5, 1, 1.5, 2, 2.5,
                                                          3, 3.5, 4, 4.5, 5, 5])
        assert list(self.stim.stim_vec) == pytest.approx([0, 0.70681968, 0.56316322, 0.5539058,
                                                          0.6810689, 0.20896532, 1.00691217,
                                                          0.78783759, 0.68817496, -6.4286609e-05,
                                                          0.21165959, 0.03874813, 0])

    def test_shot_noise(self):
        self.stim.add_shot_noise(4.0, 0.4, 2E3, 40E-3, 16E-4, 2)
        assert list(self.stim.time_vec) == pytest.approx([0, 0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5,
                                                          1.75, 2.0, 2.0])
        assert list(self.stim.stim_vec) == pytest.approx([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0700357,
                                                          0.1032799, 0.1170881, 0.1207344, 0.0])

    def test_ornstein_uhlenbeck(self):
        stim_g = ConductanceSource(rng=Random123(1, 2, 3))
        stim_g.add_ornstein_uhlenbeck(2.8, 0.0042, 0.029, 2)
        assert list(stim_g.time_vec) == pytest.approx([0, 0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5,
                                                       1.75, 2.0, 2.0])
        assert list(stim_g.stim_vec) == pytest.approx([0.0, 0.029, 0.02933925, 0.02959980,
                                                       0.03052109, 0.02882802, 0.03156533,
                                                       0.03289219, 0.03357043, 0.03049419, 0.0])

    def test_stacked(self):
        """
        Assert each individual stim, namely noise, starts and returns to zero
        """
        stim = self.stim
        stim.add_noise(0.5, 0.1, 2)  # dt is 0.5
        STIM1_SAMPLES = 7  # 4+1+2
        assert stim.time_vec.size() == stim.stim_vec.size() == STIM1_SAMPLES
        assert stim.time_vec[0] == 0.0
        assert stim.stim_vec[0] == 0.0
        assert stim.time_vec[-1] == 2.0
        assert stim.stim_vec[-1] == 0.0

        stim.delay(2)
        stim.add_shot_noise(4.0, 0.4, 2E3, 0.5, 0.1, 2)  # dt is 0.025
        STIM2_SAMPLES = 11  # 8+1+2
        assert stim.time_vec.size() == stim.stim_vec.size() == STIM1_SAMPLES + STIM2_SAMPLES
        assert stim.time_vec[STIM1_SAMPLES + 1] == 4.0
        assert stim.stim_vec[STIM1_SAMPLES + 1] == 0.0
        assert stim.time_vec[-1] == 6.0
        assert stim.stim_vec[-1] == 0.0
