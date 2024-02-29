from __future__ import absolute_import
import os
import sys
import logging
from time import strftime
from ._engine import EngineBase
from ..utils import classproperty
from ..utils.logging import setup_logging, log_stage, log_verbose
from .configuration import GlobalConfig, EXCEPTION_NODE_FILENAME
from ._neuron import _Neuron
from ._mpi import MPI

HOCLIB = "neurodamus"  # neurodamus.hoc should be in HOC_LIBRARY_PATH.
LOG_FILENAME = "pydamus_{}.log".format(strftime("%Y-%m-%d_%Hh%M"))


class _NeurodamusCore(_Neuron):
    """
    A wrapper class representing an instance of Neuron with the required
    neurodamus hoc and mod modules loaded
    """
    __slots__ = ()
    _pc = None

    @classproperty
    def h(cls):
        """The neuron hoc interpreter, initializing if needed
        """
        cls._pc or cls._init()
        return cls._h

    @classmethod
    def _init(cls, **kwargs):
        if cls._pc is not None:
            return
        # Neurodamus requires MPI. We still respect NEURON_INIT_MPI though
        _Neuron._init(int(os.environ.get("NEURON_INIT_MPI", 1)))  # if needed, sets cls._h

        # Init logging
        log_name = kwargs.get("log_filename") or LOG_FILENAME
        if MPI.rank == 0:
            open(log_name, "w").close()  # Truncate
        MPI.barrier()  # Sync so that all processes see the file
        setup_logging(GlobalConfig.verbosity, log_name, MPI.rank)
        log_stage("Initializing Neurodamus... Logfile: " + log_name)

        # Some previous executions may have left a bad exception node file
        # This is done now so it's a very early stage and we know the mpi rank
        if MPI.rank == 0 and os.path.exists(EXCEPTION_NODE_FILENAME):
            os.remove(EXCEPTION_NODE_FILENAME)

        # Load mods if not available
        cls._load_nrnmechlibs()
        log_verbose("Mechanisms (mod) library(s) successfully loaded")

        # Load main Hoc
        cls.load_hoc(HOCLIB)

        # Additional libraries introduced in saveUpdate
        sys.path.append(os.environ['HOC_LIBRARY_PATH'])

        # Attempt to instantiate BBSaveState to early detect errors
        cls._h.BBSaveState()
        cls._pc = MPI.pc
        logging.info(" => Neurodamus Mod & Hoc lib loaded.")

        logging.info("Checking for plugins...")
        EngineBase.find_plugins()

    @classmethod
    def _load_nrnmechlibs(cls):
        """Loads the required mods for neurodamus to work

        Two sets are required:
          1. neurodamus mechanisms: "Extensions" for reports, edges, etc
            (built-in or exclusively from NRNMECH_LIB_PATH)
          2. model mechanisms: synapse mechanisms, etc...
            (built-in or coming from BGLIBPY_MOD_LIBRARY_PATH)

        As so, the models may be combined in a library pointed by
        NRNMECH_LIB_PATH which is searched first. Nevertheless
        BGLIBPY_MOD_LIBRARY_PATH must exclusively contain model mechs

        Env vars can also point to several libs separated by ':'
        """

        def check_load_lib(mech, env_lib_path):
            if hasattr(cls._h, mech):
                return True
            mechlib = os.environ.get(env_lib_path)
            if mechlib is None:
                return False

            for libpath in mechlib.split(":"):
                libpath = libpath.strip()
                if os.path.isfile(libpath):
                    logging.info("Loading MECH lib: " + libpath)
                    cls.load_dll(libpath)
                else:
                    logging.warning("Invalid entry in %s: %s", env_lib_path, libpath)
            return hasattr(cls._h, mech)

        # DEV NOTE: model mods may together with core mods, so check for it first
        # Two independent env vars are required since we want to support "special -python"
        # which might not bring the model (support for split neurodamus) in which case
        # we should load only the model libs pointed by BGLIBPY_MOD_LIBRARY_PATH.

        if not check_load_lib("SonataReport", "NRNMECH_LIB_PATH"):
            logging.error("Could not load neurodamus core mechs from NRNMECH_LIB_PATH")
            sys.exit(1)
        if not check_load_lib("ProbAMPANMDA_EMS", "BGLIBPY_MOD_LIBRARY_PATH"):
            logging.error("Could not load mod library from BGLIBPY_MOD_LIBRARY_PATH")
            sys.exit(1)

    @property
    def pc(self):
        self._pc or self._init()
        return self._pc

    def init(self, **kwargs):
        self._pc or self._init(**kwargs)


# Singleton
NeurodamusCore = _NeurodamusCore()
