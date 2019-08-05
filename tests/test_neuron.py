"""
Test checking hoc entities from neuron are accessible from the high level wrappers.
"""
from neurodamus.core import Neuron


def test_base_h():
    print(Neuron.dt)


# This test shall not be found by pytest since it is supposed to be run with "special -python"
def neurodamus():
    from neurodamus.core import NeuronDamus
    rng_conf = NeuronDamus.RNGSettings()
    assert rng_conf.RANDOM123 == 1


if __name__ == '__main__':
    test_base_h()
    neurodamus()
