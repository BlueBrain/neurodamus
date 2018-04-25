from .utils import setup_logging
from ._neurodamus import NeuroDamus


class GlobalConfig:
    verbosity = 0


def run(options):
    setup_logging(options.log_level)
    ndamus = NeuroDamus()
    return ndamus
