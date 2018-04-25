from __future__ import absolute_import
import logging
import sys

__all__ = ["setup_logging"]


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
