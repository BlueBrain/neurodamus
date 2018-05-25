from __future__ import absolute_import
import logging
import sys
from array import array


def setup_logging(loglevel, stream=sys.stdout):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
      stream: The output stream of log messages (default stdout)
    """
    verbosity_levels = {
        0: logging.WARNING,
        1: logging.INFO,
        2: logging.DEBUG
    }
    logformat = "(%(asctime)s) [%(levelname)s] %(message)s"
    logging.basicConfig(level=verbosity_levels[loglevel], stream=stream,
                        format=logformat, datefmt="%Y-%m-%d %H:%M:%S")


class classproperty(object):
    def __init__(self, getter):
        self.getter = getter

    def __get__(self, instance, owner):
        return self.getter(owner)


def dict_filter(dic, filter):
    # type: (dict, lambda) -> lambda
    """Creates a generator for filtering elements in a dictionary"""
    return ((key, val) for key, val in dic.items() if filter(key, val))


def docopt_sanitize(docopt_opts):
    """Sanitizes docopt parsed key names
    """
    return {opt.strip("<>-").replace("-", "_"): val for opt, val in docopt_opts.items()}


class ConfigT(object):

    def __init__(self, **opts):
        self._init(self, opts)

    @classmethod
    def global_init(cls, **opts):
        cls._init(cls, opts)

    @staticmethod
    def _init(obj, opts):
        for name, value in opts.items():
            if value is not None and not name.startswith("_") and hasattr(obj, name):
                setattr(obj, name, value)

    def _apply_f(self, o, opts_dict):
        for key, val in opts_dict.items():
            setattr(o, key, val)

    def apply(self, obj, subset=None, excludes=(), **overrides):
        """Applies the configuration to one or multiple objects (if tuple)"""
        opts = self.as_dict(subset, excludes)
        opts.update(overrides)
        if not isinstance(obj, (tuple, list)):
            obj = (obj,)
        for o in obj:
            self._apply_f(o, opts)

    def as_dict(self, subset=None, excludes=()):
        return {key: val for key, val in vars(self).items()
                if val is not None and not key.startswith("_")
                and key not in excludes and (subset is None or key in subset)}


class ArrayCompat(array):
    __slots__ = ()

    def size(self):
        return len(self)

    @property
    def x(self):
        return self
