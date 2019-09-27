"""
Internal module which defines an MPI object based on Neuron's ParallelContext
"""
import logging
import sys
import time
from ._neuron import Neuron


class MPI(object):
    """A singleton of MPI runtime information
    """
    __name__ = "MPI"
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

        # When using MPI (and more than 1 rank) we need to MPIAbort on exception to avoid deadlocks
        def excepthook(etype, value, tb):
            time.sleep(0.1 * cls._rank)  # Order errors
            logging.critical(str(value))
            pc.allreduce(1, 1)  # Share error state
            # Print and cleanup exception
            sys.__excepthook__(etype, value, tb)
            Neuron.quit()  # With 'special' terminates right here
            sys.exit(1)
        sys.excepthook = excepthook

    @classmethod
    def check_no_errors(cls):
        # All processes send their status. If one is problematic then quit
        res = cls._pc.allreduce(0, 1)
        if res > 0:
            if MPI.rank == 0:
                logging.critical("Another rank raised an irrecoverable error. Check log file.")
            Neuron.quit()
            sys.exit(1)

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


MPI = MPI()
"""A singleton of MPI runtime information"""
