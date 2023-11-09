import pytest


class MockParallelExec:
    """We need to create a replacement since a magic-mock will return garbage"""

    def allreduce(self, number, _op):
        return number


@pytest.fixture(autouse=True, scope="module")
def _mock_neuron():
    # We want to inhibit Neuron altogether. Unfortunately stims use h.Vector which
    # would be weird to mock
    # import sys
    # sys.modules['neuron'] = unnittest.mock.MagicMock()
    from neurodamus.core import _mpi
    _mpi.MPI._pc = MockParallelExec()
