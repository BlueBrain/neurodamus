"""
Neurodamus execution main class
"""
from __future__ import absolute_import
from os import path
from ..utils import setup_logging, classproperty
from ._neuron import Neuron
from .configuration import MPInfo

LIB_PATH = path.realpath(path.join(path.dirname(__file__), "../../../lib"))
MOD_LIB = path.join(LIB_PATH, "modlib", "libnrnmech.so")
HOC_LIB = path.join(LIB_PATH, "hoclib", "neurodamus")


class NeuronDamus(Neuron):
    """
    A wrapper class representing an instance of Neuron with the required neurodamus hoc and mod
    modules loaded
    """
    _h = None
    _pnm = None

    @classmethod
    def _init(cls):
        if cls._h is None:
            cls._h = h = Neuron._init()
            cls.load_dll(MOD_LIB)
            cls.load_hoc(HOC_LIB)

            cls._pnm = pnm = h.ParallelNetManager(0)
            MPInfo.cpu_count = int(pnm.nhost)
            MPInfo.rank = int(pnm.myid)

            # default logging (if set previously this wont have any effect)
            if MPInfo.rank == 0:
                h.timeit_setVerbose(1)
                setup_logging(1)
            else:
                setup_logging(0)
        return cls._h

    @classproperty
    def h(cls):
        return cls._h or cls._init()

    @classproperty
    def pnm(cls):
        cls._init()
        return cls._pnm
