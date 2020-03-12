"""
Module implementing entry functions
"""
from __future__ import absolute_import
from docopt import docopt
import logging
from pprint import pprint
from . import Neurodamus
from .core import MPI
from .core.configuration import ConfigurationError, LogLevel
from .utils.pyutils import docopt_sanitize
from .hocify import Hocify
from os.path import abspath


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

    """
    options = docopt_sanitize(docopt(neurodamus.__doc__, args))

    config_file = options.pop("BlueConfig")

    log_level = LogLevel.DEFAULT
    if options.pop("debug", False):
        log_level = LogLevel.DEBUG
    elif options.pop("verbose", False):
        log_level = LogLevel.VERBOSE

    if log_level >= 3:
        pprint(options)

    try:
        Neurodamus(config_file, True, log_level, **options).run()
    except ConfigurationError as e:
        if MPI._rank == 0:  # Use _raw so that we avoid init
            logging.error(str(e))
        return 1
    except Exception as e:
        logging.critical(str(e), exc_info=True)
        MPI._pc and MPI.allreduce(1, 1)  # Share error state
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
    morph_dir = abspath(options.pop("MorphologyPath"))

    log_level = LogLevel.DEFAULT
    if options.pop("verbose", False):
        log_level = LogLevel.VERBOSE
        pprint(options)
    neuron_nframe = options.pop("nframe")
    output_dir = options.pop('output_dir')

    try:
        Hocify(morph_dir, neuron_nframe, log_level, output_dir).convert()
    except Exception as e:
        logging.critical(str(e), exc_info=True)
        return 1
    from neuron import version as nrn_version
    logging.info("Neuron version used for hocifying: " + nrn_version)
    return 0
