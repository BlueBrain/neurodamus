
class GlobalConfig:
    verbosity = 0


def run(options):
    utils.setup_logging(options.log_level)
    ndamus = NeuroDamus()
    return ndamus
