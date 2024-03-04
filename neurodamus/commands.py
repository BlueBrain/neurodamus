"""
Module implementing entry functions
"""
from __future__ import absolute_import

import logging
import os
import sys
import time
from docopt import docopt
from os.path import abspath
from pathlib import Path

from . import Neurodamus
from .core import MPI, OtherRankError
from .core.configuration import ConfigurationError, LogLevel, EXCEPTION_NODE_FILENAME
from .hocify import Hocify, process_file as hocify_process_file
from .utils.pyutils import docopt_sanitize


def neurodamus(args=None):
    """neurodamus

    Usage:
        neurodamus <ConfigFile> [options]
        neurodamus --help

    Options:
        -v --verbose            Increase verbosity level
        --debug                 Extremely verbose mode for debugging
        --disable-reports       Disable all reports [default: False]
        --build-model=[AUTO, ON, OFF]
                                Shall it build and eventually overwrite? [default: AUTO]
                                - AUTO: build model if doesn't exist and simulator is coreneuron
                                - ON: always build and eventually overwrite the model
                                - OFF: Don't build the model. Simulation may fail to start
        --simulate-model=[ON, OFF]
                                Shall the simulation start automatically? [default: ON]
        --output-path=PATH      Alternative output directory, overriding the config file's
        --keep-build            Keep coreneuron intermediate data. Otherwise deleted at the end
        --modelbuilding-steps=<number>
                                Set the number of ModelBuildingSteps for the CoreNeuron sim
        --experimental-stims    Shall use only Python stimuli? [default: False]
        --lb-mode=[RoundRobin, WholeCell, MultiSplit, Memory]
                                The Load Balance mode.
                                - RoundRobin: Disable load balancing. Good for quick simulations
                                - WholeCell: Does a first pass to compute load balancing and
                                    redistributes cells so that CPU load is similar among ranks
                                - MultiSplit: Allows splitting cells into pieces for distribution.
                                    WARNING: This mode is incompatible with CoreNeuron
                                - Memory: Load balance based on memory usage. By default, it uses
                                    the "allocation.pkl.gz" file to load a pre-computed load balance
        --save=<PATH>           Path to create a save point to enable resume.
        --save-time=<TIME>      The simulation time [ms] to save the state. (Default: At the end)
        --restore=<PATH>        Restore and resume simulation from a save point on disk
        --dump-cell-state=<GID> Dump cell state debug files on start, save-restore and at the end
        --enable-shm=[ON, OFF]  Enables the use of /dev/shm for coreneuron_input [default: ON]
        --model-stats           Show model stats in CoreNEURON simulations [default: False]
        --dry-run               Dry-run simulation to estimate memory usage [default: False]
        --num-target-ranks=<number>  Number of ranks to target for dry-run load balancing
    """
    options = docopt_sanitize(docopt(neurodamus.__doc__, args))
    config_file = options.pop("ConfigFile")
    log_level = _pop_log_level(options)

    if not os.path.isfile(config_file):
        logging.error("Config file not found: %s", config_file)
        return 1

    # Shall replace process with special? Don't if is special or already replaced
    if not sys.argv[0].endswith("special") and not os.environ.get("neurodamus_special"):
        _attempt_launch_special(config_file)

    # Warning control before starting the process
    _filter_warnings()

    try:
        Neurodamus(config_file, True, logging_level=log_level, **options).run()
    except ConfigurationError as e:  # Common, only show error in Rank 0
        if MPI._rank == 0:           # Use _rank so that we avoid init
            logging.error(str(e))
        return 1
    except OtherRankError:
        return 1  # no need for _mpi_abort, error is being handled by all ranks
    except Exception:
        show_exception_abort("Unhandled Exception. Terminating...", sys.exc_info())
        return 1
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
    morph_path = abspath(options.pop("MorphologyPath"))
    log_level = _pop_log_level(options)
    neuron_nframe = options.pop("nframe")
    options.pop("help")  # never pass to the library

    # first check if it is a file
    if os.path.isfile(morph_path):
        os.environ['NEURON_NFRAME'] = str(neuron_nframe)
        # the dest file is the same as the morph file but with .hoc extension
        dest_file = Path(morph_path).with_suffix('.hoc')

        print("Hocifying {} -> {}".format(morph_path, dest_file))
        result = hocify_process_file((morph_path, str(dest_file)))
        if isinstance(result, Exception):
            logging.critical(str(result), exc_info=True)
            return 1
        print('Done.')
        return 0

    # otherwise it is a directory, use multiprocessing
    try:
        Hocify(morph_path, neuron_nframe, log_level, **options).convert()
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
        from pprint import pprint
        pprint(options)
    return log_level


def show_exception_abort(err_msg, exc_info):
    """Show an exception info in only one rank

    Several ranks are likely to be in sync so a simple touch wont work.
    Processes that dont see any file will register (append) their rank id
    First one is elected to print
    """
    err_file = Path(EXCEPTION_NODE_FILENAME)
    ALL_RANKS_SYNC_WINDOW = 1

    if err_file.exists():
        return 1

    with open(err_file, 'a') as f:
        f.write(str(MPI.rank) + "\n")

    with open(err_file, 'r') as f:
        line0 = open(err_file).readline().strip()
    if str(MPI.rank) == line0:
        logging.critical(err_msg, exc_info=exc_info)

    time.sleep(ALL_RANKS_SYNC_WINDOW)  # give time to the rank that logs the exception
    _mpi_abort()  # abort all ranks which have waited. Seems to help avoiding MPT stack


def _attempt_launch_special(config_file):
    import shutil
    special = shutil.which("special")
    if os.path.isfile("x86_64/special"):  # prefer locally compiled special
        special = abspath("x86_64/special")
    if special is None:
        logging.warning("special not found. Running neurodamus from Python with libnrnmech. "
                        "-> DO NOT USE WITH PRODUCTION RUNS")
        return
    neurodamus_py_root = os.environ.get("NEURODAMUS_PYTHON")
    if not neurodamus_py_root:
        logging.warning("No NEURODAMUS_PYTHON set. Running neurodamus from Python with libnrnmech. "
                        "-> DO NOT USE WITH PRODUCTION RUNS")
        return
    print("::INIT:: Special available. Replacing binary...")
    os.environ["neurodamus_special"] = "1"
    init_script = os.path.join(neurodamus_py_root, "init.py")
    os.execl(special,
             "-mpi",
             "-python", init_script,
             "--configFile=" + config_file,
             *sys.argv[2:])


def _mpi_abort():
    import ctypes
    c_api = ctypes.CDLL(None)
    c_api.MPI_Abort(0)


def _filter_warnings():
    """ Control matched warning to display once in rank 0.

    Warning 1:
    "special" binaries built with %intel build_type=Release,RelWithDebInfo flushes
    denormal results to zero, which triggers the numpy warning for subnormal in every rank.
    Reduce this type of warning displayed once in rank0.
    Note: "special" with build_type = FastDebug/Debug or calling the simulation process
       in python (built with gcc) does not have such flush-to-zero warning.
    """
    import warnings
    if MPI.rank == 0:
        action = "once"
    else:
        action = "ignore"
    warnings.filterwarnings(action=action,
                            message="The value of the smallest subnormal for .* type is zero.",
                            category=UserWarning, module="numpy")
