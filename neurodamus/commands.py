"""
Module implementing entry functions
"""
from __future__ import absolute_import
from docopt import docopt
from pprint import pprint
from . import Neurodamus
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

    """
    options = docopt_sanitize(docopt(neurodamus.__doc__, args))

    config_file = options.pop("BlueConfig")

    log_level = 1  # default
    if options.pop("debug", False):
        log_level = 3
    elif options.pop("verbose", False):
        log_level = 2

    if log_level > 2:
        pprint(options)

    Neurodamus(config_file, log_level, **options).run()
