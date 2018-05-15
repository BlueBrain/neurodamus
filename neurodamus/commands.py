from __future__ import absolute_import
from docopt import docopt
from . import GlobalConfig
from ._neurodamus import init
from .utils.pyutils import docopt_sanitize


def neurodamus():
    """neurodamus

    Usage:
        neurodamus <BlueConfig> [--verbose]
        neurodamus --help

    Options:
        -v --verbose    Increase verbosity level
    """
    options = docopt_sanitize(docopt(neurodamus.__doc__, version="PyNDamus 0.1"))
    if options["verbose"]:
        GlobalConfig.verbosity = 2
    init(options["BlueConfig"])
