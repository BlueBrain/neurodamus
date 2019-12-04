from __future__ import absolute_import
import os
import sys
import logging
from time import strftime
from ..utils import classproperty
from ..utils.logging import setup_logging, log_stage, log_verbose
from .configuration import GlobalConfig
from ._neuron import _Neuron
from ._mpi import MPI

HOCLIB = "neurodamus"  # neurodamus.hoc should be in HOC_LIBRARY_PATH.
LOG_FILENAME = "pydamus_{}.log".format(strftime("%Y-%m-%d_%Hh%M"))


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
        if cls._pc is not None:
            return
        # Neurodamus will generally require MPI
        # However if launched without, attempt
        within_mpi = (os.environ.get("PMI_RANK") is not None
                      or os.environ.get("OMPI_COMM_WORLD_RANK") is not None)
        _Neuron._init(mpi=within_mpi)  # if needed, sets cls._h

        # Init logging
        if MPI.rank == 0:
            open(LOG_FILENAME, "w").close()  # Truncate
        MPI.barrier()  # Sync so that all processes see the file
        setup_logging(GlobalConfig.verbosity, LOG_FILENAME, MPI.rank)
        log_stage("Initializing Neurodamus... Logfile: " + LOG_FILENAME)

        # Load mods if not available
        cls._load_nrnmechlibs()
        log_verbose("Mechanisms (mod) library(s) successfully loaded")

        # Load main Hoc
        cls.load_hoc(HOCLIB)

        # Additional libraries introduced in saveUpdate
        sys.path.append(os.environ['HOC_LIBRARY_PATH'])
        cls.load_hoc("CompartmentMapping")

        # Attempt to instantiate BBSaveState to early detect errors
        cls._h.BBSaveState()
        cls._pc = MPI.pc
        logging.info(" => Neurodamus Mod & Hoc lib loaded.")

    @classmethod
    def _load_nrnmechlibs(cls):
        """Loads the required mods for neurodamus to work

        Two sets are required (which eventually came from the same lib):
          1. model mechanisms: synapse mechanisms, etc...
          2. neurodamus mechanisms: "Extensions" for reports, edges, etc
        """
        mech_avail = (hasattr(cls._h, "ProbAMPANMDA_EMS"), hasattr(cls._h, "SpikeWriter"))
        if all(mech_avail):
            return
        elif any(mech_avail):
            logging.warning("Loaded partial mech sets (Model / Neurodamus): %s", str(mech_avail))

        mechlib = os.environ.get("NRNMECH_LIB_PATH")
        if mechlib is None:
            logging.error("No required mechanisms found and no NRNMECH_LIB_PATH set. "
                          "Please load the desired model-x module or neurodamus-x")
            sys.exit(1)

        if ':' not in mechlib:
            # This is the previous logic to find a combined mechlib
            modlib = os.path.join(os.path.dirname(mechlib),
                                  "libnrnmech_nd" + os.path.splitext(mechlib)[1])
            if os.path.isfile(modlib):
                logging.info("Loading MECH lib: " + modlib)
                cls.load_dll(modlib)
                return

        for libpath in mechlib.split(":"):
            libpath = libpath.strip()
            if os.path.isfile(libpath):
                logging.info("Loading MECH lib: " + libpath)
                cls.load_dll(libpath)
            else:
                logging.warning("Invalid entry in NRNMECH_LIB_PATH: %s", libpath)

        if any(not hasattr(cls._h, mech) for mech in ("ProbAMPANMDA_EMS", "SpikeWriter")):
            logging.error("Neurodamus could not load all required mechanisms")
            sys.exit(1)

    @property
    def pc(self):
        self._pc or self._init()
        return self._pc

    def init(self):
        self._pc or self._init()


# Singleton
NeurodamusCore = NeurodamusCore()
