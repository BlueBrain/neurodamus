from __future__ import absolute_import
from docopt import docopt
from .utils import setup_logging
from . import GlobalConfig
from ._neurodamus import init
from .utils.pyutils import docopt_sanitize


def neurodamus():
    """neurodamus

    Usage:
        neurodamus <BlueConfig> [-v...]

    """
    options = docopt_sanitize(docopt(neurodamus.__doc__, version="PyNDamus 0.1"))
    print(options)
    GlobalConfig.verbosity = options['v']
    setup_logging(GlobalConfig.verbosity)
    init(options["BlueConfig"])
