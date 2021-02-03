"""
Internal module which defines an MPI object based on Neuron's ParallelContext
"""
import logging
import sys
import time
from ._neuron import Neuron


class OtherRankError(RuntimeError):
    pass


class _MPI(object):
    """A singleton of MPI runtime information
    """
    _size = 1
    _rank = 0
    _pc = None

    SUM = 1
    MAX = 2
    MIN = 3

    @classmethod
    def _init_pc(cls):
        if cls._pc is not None:
            return

        Neuron.load_hoc("netparmpi")
        cls._pc = pc = Neuron.ParallelContext()
        cls._rank = int(pc.id())
        cls._size = int(pc.nhost())

        if cls._size <= 1:
            return  # done

        # In case neurodmus is not being used as a program, but rather imported by another
        # program (API mode) we must handle exceptions instead of just killing the process
        def excepthook(etype, value, tb):
            if etype == OtherRankError:
                # Do nothing because the exception only exists because of other ranks, not locally
                return

            # Print exceptions local to this rank
            time.sleep(0.01 * cls._rank)  # Order errors
            logging.critical(str(value), exc_info=True)
            if cls._rank == 0:
                import traceback
                traceback.print_tb(tb)

            # Participate in check_no_errors allreduce, letting it know there was exception
            pc.allreduce(1, 1)  # Share error state

        sys.excepthook = excepthook

    @classmethod
    def check_no_errors(cls):
        # All processes send their status. If one is problematic it will either call MPI_Abort
        # or, in API mode, participate in the allreduce
        res = cls._pc.allreduce(0, 1)
        if res > 0:
            raise OtherRankError("Another rank raised an irrecoverable error")

    @property
    def size(self):
        self._init_pc()
        return self._size

    @property
    def rank(self):
        self._init_pc()
        return self._rank

    @property
    def pc(self):
        self._init_pc()
        return self._pc

    def __getattr__(self, name):
        if name.startswith("__"):
            return object.__getattribute__(self, name)
        self._init_pc()
        return getattr(self._pc, name)


MPI = _MPI()
"""A singleton of MPI runtime information"""
