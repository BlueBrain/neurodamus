"""
Module implementing entry functions
"""
from __future__ import absolute_import

import logging
import os
import sys
from docopt import docopt
from os.path import abspath
from pprint import pprint

from . import Neurodamus
from .core import MPI
from .core.configuration import ConfigurationError, LogLevel
from .hocify import Hocify
from .utils.pyutils import docopt_sanitize


def neurodamus(args=None):
    """neurodamus

    Usage:
        neurodamus <BlueConfig> [options]
        neurodamus --help

    Options:
        -v --verbose            Increase verbosity level
        --debug                 Extremely verbose mode for debugging
        --disable-reports       Disable all reports [default: False]
        --build-model=[AUTO, ON, OFF]
                                Shall it build and eventually overwrite? [default: AUTO]
                                AUTO: build model if doesn't exist and simulator is coreneuron
                                ON: always build and eventually overwrite the model
                                OFF: Don't build the model. Simulation may fail to start
        --simulate-model=[ON, OFF]     Shall the simulation start automatically? [default: ON]
        --output-path=PATH      Alternative output directory, overriding BlueConfigs
        --keep-build            Keep coreneuron intermediate data. Otherwise deleted at the end
        --modelbuilding-steps=<number> Set the number of ModelBuildingSteps for the CoreNeuron sim
        --experimental-stims=[ON, OFF] Shall use only Python stimuli? [default: OFF]

    """
    options = docopt_sanitize(docopt(neurodamus.__doc__, args))
    config_file = options.pop("BlueConfig")
    log_level = _pop_log_level(options)

    if not os.path.isfile(config_file):
        logging.error("Config file not found: %s", config_file)
        return 1

    # Shall replace process with special? Don't if is special or already replaced
    if not sys.argv[0].endswith("special") and not os.environ.get("neurodamus_special"):
        _attempt_launch_special(config_file)

    try:
        Neurodamus(config_file, True, log_level, **options).run()
    except ConfigurationError as e:  # Common, only show error in Rank 0
        if MPI._rank == 0:           # Use _rank so that we avoid init
            logging.error(str(e))
        return 1
    except Exception:
        logging.critical("Unhandled Exception. Terminating...", exc_info=(MPI._rank == 0))
        _mpi_abort()

    return 0


def hocify(args=None):
    """hocify

    Usage:
        hocify <MorphologyPath> [options]
        hocify --help

    Options:
        -v --verbose            Increase verbosity level.
        --nframe=<number>       NEURON_NFRAME value [default: 1000].
        --output-dir=<PATH>     Output directory for hoc files.
    """
    options = docopt_sanitize(docopt(hocify.__doc__, args))
    morph_dir = abspath(options.pop("MorphologyPath"))
    log_level = _pop_log_level(options)
    neuron_nframe = options.pop("nframe")
    options.pop("help")  # never pass to the library

    try:
        Hocify(morph_dir, neuron_nframe, log_level, **options).convert()
    except Exception as e:
        logging.critical(str(e), exc_info=True)
        return 1
    from neuron import version as nrn_version
    logging.info("Neuron version used for hocifying: " + nrn_version)
    return 0


def _pop_log_level(options):
    log_level = LogLevel.DEFAULT
    if options.pop("debug", False):
        log_level = LogLevel.DEBUG
    elif options.pop("verbose", False):
        log_level = LogLevel.VERBOSE
    if log_level >= 3:
        pprint(options)
    return log_level


def _attempt_launch_special(config_file):
    import shutil
    special = shutil.which("special")
    if os.path.isfile("x86_64/special"):  # prefer locally compiled special
        special = abspath("x86_64/special")
    if special is None:
        logging.warning("special not found. Running neurodamus from Python with libnrnmech. "
                        "-> DO NOT USE WITH PRODUCTION RUNS")
        return
    print("::INIT:: Special available. Replacing binary...")
    os.environ["neurodamus_special"] = "1"
    init_script = os.path.join(os.environ["NEURODAMUS_PYTHON"], "init.py")
    os.execl(special,
             "-mpi",
             "-python", init_script,
             "--configFile=" + config_file,
             *sys.argv[2:])


def _mpi_abort():
    import ctypes
    c_api = ctypes.CDLL(None)
    c_api.MPI_Abort(0)
