"""
Module implementing entry functions
"""
from __future__ import absolute_import
from docopt import docopt
from .core.configuration import GlobalConfig
from . import Neurodamus
from .utils.pyutils import docopt_sanitize


def neurodamus():
    """neurodamus

    Usage:
        neurodamus <BlueConfig> [options]
        neurodamus --help

    Options:
        -v --verbose    Increase verbosity level
        --debug         Extremely verbose mode for debugging
    """
    options = docopt_sanitize(docopt(neurodamus.__doc__))
    if options["debug"]:
        GlobalConfig.verbosity = 3
    elif options["verbose"]:
        GlobalConfig.verbosity = 2

    Neurodamus(options["BlueConfig"]).run()
