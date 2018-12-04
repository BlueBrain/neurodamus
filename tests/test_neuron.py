"""
Test checking hoc entities from neuron are accessible from the high level wrappers.
"""
from neurodamus.core import Neuron
from neurodamus.core import NeuronDamus


def test_base_h():
    print(Neuron.dt)


def test_neurodamus():
    print(NeuronDamus.timeit_verbose)


if __name__ == '__main__':
    test_base_h()
    test_neurodamus()
