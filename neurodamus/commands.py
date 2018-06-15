from __future__ import absolute_import
from docopt import docopt
from .core.configuration import GlobalConfig
from . import run
from .utils.pyutils import docopt_sanitize


def neurodamus():
    """neurodamus

    Usage:
        neurodamus <BlueConfig> [--no-mpi] [--verbose]
        neurodamus --help

    Options:
        -v --verbose    Increase verbosity level
    """
    options = docopt_sanitize(docopt(neurodamus.__doc__, version="0.1"))
    if options["verbose"]:
        GlobalConfig.verbosity = 2
    if options["no_mpi"]:
        GlobalConfig.use_mpi = False

    run(options["BlueConfig"])

