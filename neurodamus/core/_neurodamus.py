from __future__ import absolute_import
from os import path as Path
import logging
import time
from ..utils import classproperty
from ..utils.logging import setup_logging
from .configuration import GlobalConfig
from ._neuron import _Neuron, MPI

LIB_PATH = Path.realpath(Path.join(Path.dirname(__file__), "../../../lib"))
MOD_LIB = Path.join(LIB_PATH, "modlib", "libnrnmech.so")
HOC_LIB = Path.join(LIB_PATH, "hoclib", "neurodamus")
LOG_FILENAME = "pydamus.log"


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
        cls._pnm or cls._init()
        return cls._h

    @classmethod
    def _init(cls):
        _Neuron._init()  # if needed, sets cls._h
        if cls._pnm is None:
            # logging.debug("Loading mods from: " + MOD_LIB)
            # cls.load_dll(MOD_LIB)  # While py neuron doesnt support mpi init use "special"
            logging.debug("Loading master Hoc: " + HOC_LIB)
            cls.load_hoc(HOC_LIB)
            cls._pnm = MPI.pnm

            # default logging (if set previously this wont have any effect)
            if MPI.rank == 0:
                open(LOG_FILENAME, "w").close()  # Truncate
                MPI.barrier()
                setup_logging(GlobalConfig.verbosity, LOG_FILENAME, rank=0)
            else:
                MPI.barrier()
                setup_logging(0, LOG_FILENAME, MPI.rank)
            logging.info("Neurodamus Mod & Hoc lib loaded.")

    @property
    def pnm(self):
        self._pnm or self._init()
        return self._pnm

    def init(self):
        self._pnm or self._init()


# Singleton
NeuronDamus = NeuronDamus()
