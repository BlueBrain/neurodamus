from __future__ import absolute_import
import logging as _logging
import sys
from copy import copy
from .pyutils import ConsoleColors

STAGE_LOGLEVEL = 25
VERBOSE_LOGLEVEL = 15

# New log levels, for stage (minimal output, verbose)
_logging.addLevelName(STAGE_LOGLEVEL, "STEP")
_logging.STAGE = STAGE_LOGLEVEL
_logging.addLevelName(VERBOSE_LOGLEVEL, "VERB")
_logging.VERBOSE = VERBOSE_LOGLEVEL


def log_stage(msg, *args):
    """Shortcut to log a messge with the STAGE level"""
    _logging.log(STAGE_LOGLEVEL, msg, *args)


def log_verbose(msg, *args):
    """Shortcut to log a messge with the VERBOSE level"""
    _logging.log(VERBOSE_LOGLEVEL, msg, *args)


class _ColoredFormatter(_logging.Formatter):
    COLORS = {
        _logging.CRITICAL: ConsoleColors.RED,
        _logging.ERROR: ConsoleColors.RED,
        _logging.WARNING: ConsoleColors.YELLOW,
        STAGE_LOGLEVEL: ConsoleColors.DEFAULT + ConsoleColors.BOLD,
        _logging.INFO: ConsoleColors.BLUE,
        VERBOSE_LOGLEVEL: ConsoleColors.BLUE,
        _logging.DEBUG: ConsoleColors.DEFAULT + ConsoleColors.DIM,
    }

    def format(self, record):
        levelno = record.levelno
        style = self.COLORS.get(levelno)
        if style is not None:
            record.levelname = ConsoleColors.format_text(record.levelname, style)
            record.msg = ConsoleColors.format_text(record.msg, style) \
                if levelno >= _logging.WARNING or levelno == VERBOSE_LOGLEVEL \
                else ConsoleColors.format_text(record.msg, ConsoleColors.DEFAULT, style)
        return super(_ColoredFormatter, self).format(record)


class _LevelFormatter(_ColoredFormatter):
    _logfmt = "[%(levelname)s] %(message)s"
    _datefmt = "%b.%d %H:%M:%S"
    _level_tabs = {VERBOSE_LOGLEVEL: ' -> ', _logging.DEBUG: '    + '}

    def __init__(self, with_time=True, **kw):
        _ColoredFormatter.__init__(self, self._logfmt, self._datefmt, **kw)
        self._with_time = with_time

    def format(self, record):
        record = copy(record)  # All changes done here dont persist
        record.levelname = record.levelname.center(6)
        record.msg = self._level_tabs.get(record.levelno, "") + record.msg
        msg = _ColoredFormatter.format(self, record)
        if self._with_time:
            msg = "(%s) " % self.formatTime(record, self._datefmt) + msg
        return msg


def setup_logging(loglevel, logfile="pydamus.log"):
    """Setup neurodamus logging.
    Features tabs and colors output to stdout and pydamus.log

    Args:
      loglevel (int): minimum loglevel for emitting messages
      logfile: The destination for log messages besides stdout
    """
    if getattr(setup_logging, "logging_initted", False):
        return
    assert isinstance(loglevel, int)
    loglevel = min(loglevel, 3)

    verbosity_levels = {
        0: _logging.WARNING,
        1: _logging.INFO,
        2: _logging.VERBOSE,
        3: _logging.DEBUG,
    }

    # Stdout
    hdlr = _logging.StreamHandler(sys.stdout)
    hdlr.setFormatter(_LevelFormatter(False))
    _logging.root.setLevel(verbosity_levels[loglevel])
    del _logging.root.handlers[:]
    _logging.root.addHandler(hdlr)

    # Logfile
    fileh = _logging.FileHandler(logfile, 'w+')
    fileh.setFormatter(_LevelFormatter())
    _logging.root.addHandler(fileh)

    setup_logging.logging_initted = True
