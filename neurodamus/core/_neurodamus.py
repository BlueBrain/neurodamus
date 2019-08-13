from __future__ import absolute_import
import os
import logging
from ..utils import classproperty
from ..utils.logging import setup_logging, log_verbose
from .configuration import GlobalConfig
from ._neuron import _Neuron
from ._mpi import MPI

HOCLIB = "neurodamus"  # neurodamus.hoc should be in HOC_LIBRARY_PATH.
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
        _Neuron._init(mpi=True)  # if needed, sets cls._h
        if cls._pc is not None:
            return

        # Load mods if not available
        if not hasattr(cls._h, "SpikeWriter"):
            cls._load_nrnmechlib()

        # Load main Hoc
        cls.load_hoc(HOCLIB)

        # Additional libraries introduced in saveUpdate
        cls.load_hoc("CompartmentMapping")
        # Attempt to instantiate BBSaveState to early detect errors
        cls._h.BBSaveState()

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

    @classmethod
    def _load_nrnmechlib(cls):
        mechlib = os.environ.get("NRNMECH_LIB_PATH")
        assert mechlib is not None, "NRNMECH_LIB_PATH not found. Please load neurodamus-xxx."
        modlib = os.path.join(os.path.dirname(mechlib),
                              "libnrnmech_nd" + os.path.splitext(mechlib)[1])
        log_verbose("Loading mods from: " + modlib)
        cls.load_dll(modlib)

    @property
    def pc(self):
        self._pc or self._init()
        return self._pc

    def init(self):
        self._pc or self._init()


# Singleton
NeurodamusCore = NeurodamusCore()
