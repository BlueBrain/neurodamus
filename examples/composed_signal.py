#!/usr/bin/env python
"""
An example on how to use CurrentSource to create a stimulus composed of different signals
"""
from neurodamus.core import CurrentSource


def test_composed_signal():
    s = CurrentSource.train(0.5, 100, 4, 100)
    s.add_noise(0, 0.1, 100)
    s.plot(ylims=(-1, 1))


if __name__ == "__main__":
    from six.moves import input
    test_composed_signal()
    input("Press enter to quit")
