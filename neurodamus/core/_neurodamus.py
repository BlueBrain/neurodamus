"""
Neurodamus execution main class
"""
from __future__ import absolute_import
from os import path
from ..utils import setup_logging, classproperty
from ._neuron import _Neuron
from .configuration import MPInfo

LIB_PATH = path.realpath(path.join(path.dirname(__file__), "../../../lib"))
MOD_LIB = path.join(LIB_PATH, "modlib", "libnrnmech.so")
HOC_LIB = path.join(LIB_PATH, "hoclib", "neurodamus")


class NeuronDamus(_Neuron):
    """
    A wrapper class representing an instance of Neuron with the required neurodamus hoc and mod
    modules loaded
    """
    __slots__ = ()
    _pnm = None  # ParallelNetManager (used as well to verify init)

    @classproperty
    def h(cls):
        """The neuron hoc interpreter, initializing if needed
        """
        if cls._pnm is None:
            return cls._init()
        return cls._h

    @classmethod
    def _init(cls):
        h = _Neuron._init()  # if needed, sets cls._h
        if cls._pnm is None:
            cls.load_dll(MOD_LIB)
            cls.load_hoc(HOC_LIB)
            cls._pnm = h.ParallelNetManager(0)

            # default logging (if set previously this wont have any effect)
            if MPInfo.rank == 0:
                h.timeit_setVerbose(1)
                setup_logging(1)
            else:
                setup_logging(0)
        return h

    @property
    def pnm(self):
        self._pnm or self._init()
        return self._pnm


# Singleton
NeuronDamus = NeuronDamus()
