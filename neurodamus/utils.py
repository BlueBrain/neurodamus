from __future__ import absolute_import
import logging
import sys


def setup_logging(loglevel, stream=sys.stdout):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
      stream: The output stream of log messages (default stdout)
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(level=loglevel, stream=stream,
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


class ConfigT(object):
    def __init__(self, **opts):
        self._init(self, opts)

    @classmethod
    def global_init(cls, **opts):
        cls._init(cls, opts)

    @staticmethod
    def _init(obj, opts):
        for name, value in opts.items():
            if value is not None and hasattr(obj, name):
                setattr(obj, name, value)
