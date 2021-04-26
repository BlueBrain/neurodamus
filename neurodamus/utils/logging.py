"""
Loggeers init & Formatters
"""
from __future__ import absolute_import
import logging as _logging
import os
import sys
from .pyutils import ConsoleColors

STAGE_LOGLEVEL = 25
VERBOSE_LOGLEVEL = 15
ALWAYS_LEVEL = 40

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


def log_all(level, msg, *args):
    """Like logging.log, but always displays. Level is used for style only"""
    _logging.log(ALWAYS_LEVEL, msg, *args, extra={'ulevel': level})


class _LevelColorFormatter(_logging.Formatter):
    COLORS = {
        _logging.CRITICAL: ConsoleColors.RED,
        _logging.ERROR: ConsoleColors.RED,
        _logging.WARNING: ConsoleColors.YELLOW,
        STAGE_LOGLEVEL: ConsoleColors.DEFAULT + ConsoleColors.BOLD,
        _logging.INFO: ConsoleColors.BLUE,
        VERBOSE_LOGLEVEL: ConsoleColors.BLUE,
        _logging.DEBUG: ConsoleColors.DEFAULT + ConsoleColors.DIM,
    }

    _logfmt = "[%(levelname)s] %(message)s"
    _datefmt = "%b.%d %H:%M:%S"
    _level_tabs = {VERBOSE_LOGLEVEL: ' -> ',
                   _logging.DEBUG: ' + '}

    def __init__(self, with_time=True, rank=None, use_color=True, **kw):
        super().__init__(self._logfmt, self._datefmt, **kw)
        self._rank = rank
        self._with_time = with_time
        self._use_color = use_color

    def format(self, record):
        if hasattr(record, "ulevel"):
            record.levelno = record.ulevel
            record.levelname = _logging.getLevelName(record.levelno)
        style = self.COLORS.get(record.levelno)
        if style is not None:
            record.levelname = self._format_level(record, style)
            record.msg = self._format_msg(record, style)
        return super().format(record)

    def _format_level(self, record, style):
        if not self._use_color:
            return record.levelname
        return ConsoleColors.format_text(record.levelname, style)

    def _format_msg(self, record, style):
        msg = ""
        if self._with_time:
            msg += "(%s) " % self.formatTime(record, self._datefmt) + msg
        # Show rank only for ERRORs
        if self._rank is not None and record.levelno >= _logging.ERROR:
            msg += "(rank {:d}) ".format(self._rank)

        levelno = record.levelno
        msg += self._level_tabs.get(levelno, "") + record.msg

        if not self._use_color:
            return msg
        return ConsoleColors.format_text(msg, style) \
            if levelno >= _logging.WARNING or levelno == VERBOSE_LOGLEVEL \
            else ConsoleColors.format_text(msg, ConsoleColors.DEFAULT, style)


def setup_logging(loglevel, logfile=None, rank=None):
    """Setup neurodamus logging.
    Features tabs and colors output to stdout and pydamus.log

    Args:
      loglevel (int): minimum loglevel for emitting messages
      logfile: The destination for log messages besides stdout
      rank: A tag so warnings/errors are correctly identified in case of MPI
    """
    if getattr(setup_logging, "logging_initted", False):
        return
    assert isinstance(loglevel, int)
    loglevel = min(loglevel, 3)

    verbosity_levels = [
        _logging.WARNING,  # pos 0: Minimum possible logging level
        _logging.INFO,
        _logging.VERBOSE,
        _logging.DEBUG,
    ]

    # Stdout
    hdlr = _logging.StreamHandler(sys.stdout)
    use_color = True
    if os.environ.get("ENVIRONMENT") == "BATCH":
        use_color = False
    else:
        try:
            sys.stdout.tell()   # works only if it's file
            use_color = False
        except IOError:
            pass
    hdlr.setFormatter(_LevelColorFormatter(False, rank, use_color))
    if rank == 0:
        _logging.root.setLevel(verbosity_levels[loglevel])
    else:
        _logging.root.setLevel(_logging.ERROR)

    del _logging.root.handlers[:]
    _logging.root.addHandler(hdlr)

    if logfile:
        fileh = _logging.FileHandler(logfile, encoding="utf-8")
        fileh.setFormatter(_LevelColorFormatter(rank=rank, use_color=False))
        _logging.root.addHandler(fileh)

    setup_logging.logging_initted = True
