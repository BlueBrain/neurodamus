from __future__ import absolute_import
from os import path as Path
import logging
from ..utils import classproperty
from ..utils.logging import setup_logging
from .configuration import GlobalConfig
from ._neuron import _Neuron
from ._mpi import MPI

LIB_PATH = Path.realpath(Path.join(Path.dirname(__file__), "../../../lib"))
MOD_LIB = Path.join(LIB_PATH, "modlib", "libnrnmech.so")
HOC_LIB = "neurodamus"  # neurodamus.hoc should be in HOC_LIBRARY_PATH.
LOG_FILENAME = "pydamus.log"


class NeurodamusCore(_Neuron):
    """
    A wrapper class representing an instance of Neuron with the required neurodamus hoc and mod
    modules loaded
    """
    __name__ = "NeurodamusCore"
    __slots__ = ()
    _pc = None

    @classproperty
    def h(cls):
        """The neuron hoc interpreter, initializing if needed
        """
        cls._pc or cls._init()
        return cls._h

    @classmethod
    def _init(cls):
        _Neuron._init()  # if needed, sets cls._h
        if cls._pc is None:
            # logging.debug("Loading mods from: " + MOD_LIB)
            # cls.load_dll(MOD_LIB)  # While py neuron doesnt support mpi init use "special"
            logging.debug("Loading master Hoc: " + HOC_LIB)
            cls.load_hoc(HOC_LIB)
            # Additional libraries introduced in saveUpdate
            cls.load_hoc("CompartmentMapping")

            cls._pc = MPI.pc

            # default logging (if set previously this wont have any effect)
            if MPI.rank == 0:
                open(LOG_FILENAME, "w").close()  # Truncate
                MPI.barrier()
                setup_logging(GlobalConfig.verbosity, LOG_FILENAME, rank=0)
            else:
                MPI.barrier()
                setup_logging(0, LOG_FILENAME, MPI.rank)
            logging.info("Neurodamus Mod & Hoc lib loaded.")

            # Attempt to instantiate BBSaveState to early detect errors
            cls.h.BBSaveState()

    @property
    def pc(self):
        self._pc or self._init()
        return self._pc

    def init(self):
        self._pc or self._init()


# Singleton
NeurodamusCore = NeurodamusCore()
