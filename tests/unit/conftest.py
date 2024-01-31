import pytest
import sys
import unittest.mock


class MockParallelExec:
    """We need to create a replacement since a magic-mock will return garbage"""

    def allreduce(self, number, _op):
        return number


@pytest.fixture(autouse=True, scope="module")
def _mock_neuron():
    from neurodamus.core import _mpi
    from neurodamus.utils import compat
    _mpi._MPI._pc = MockParallelExec()

    # Dont convert
    compat.hoc_vector = lambda x: x

    class VectorMock(compat.Vector):

        def __new__(cls, len=0):
            init = [0] * len
            return compat.Vector.__new__(cls, "d", init)

    neuron_mock = unittest.mock.Mock()
    neuron_mock.h.Vector = VectorMock
    sys.modules['neuron'] = neuron_mock
