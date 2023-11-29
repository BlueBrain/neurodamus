## Neurodamus Unit Tests

This folder contains the unit tests for Neurodamus.

By definition a unit test shoult test a small functionality in isolation, which might require
the use of mocks or even monkey-patching.

In particular tests here should not rely on processing done by dependencies, especially NEURON,
since it will not be fully configured. Those tests should instead be in the 'integration' test
folder. Nevertheless, to ease life a bit, essential libraries like numpy and scipy can be relied on.
