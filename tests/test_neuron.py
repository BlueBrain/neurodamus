"""
Test checking hoc entities from neuron are accessible from the high level wrappers.
"""
import pytest

pytestmark = pytest.mark.forked  # independent processes


def test_base_h():
    from neurodamus.core import Neuron
    print(Neuron.dt)


# This test shall not be found by pytest since it is supposed to be run with "special -python"
def neurodamus():
    from neurodamus.core import NeurodamusCore as Nd
    rng_conf = Nd.RNGSettings()
    assert rng_conf.RANDOM123 == 1
