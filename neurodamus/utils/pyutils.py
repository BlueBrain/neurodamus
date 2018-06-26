from __future__ import absolute_import
import logging as _logging
import sys
from collections import OrderedDict
from bisect import bisect_left
import numpy as np
from collections import Mapping
from operator import add
from six.moves import zip, reduce

_logging_initted = False
STAGE_LOGLEVEL = 25


class classproperty(object):
    def __init__(self, getter):
        self.getter = getter

    def __get__(self, instance, owner):
        return self.getter(owner)

    def __set__(self, instance, value):
        raise AttributeError("Class properties can't be override")


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


def bin_search(container, key, keyf=None):
    """Performs binary search in a container, retrieving the index where key should be inserted
    to keep ordering. Accepts a key function to be applied to each element of the container.

    Args:
        container: The container to be searched through
        key: The key to look for
        keyf: (Optional) the function transforming container elements into comparable keys

    Returns: The position where the element is to be inserted to keep ordering.

    """
    if keyf is None:
        return bisect_left(container, key)

    binsrch_low = 0
    binsrch_high = len(container)

    while binsrch_low < binsrch_high:
        binsrch_mid = int((binsrch_low + binsrch_high) * 0.5)
        if key > keyf(container[binsrch_mid]):
            binsrch_low = binsrch_mid + 1
        else:
            binsrch_high = binsrch_mid
    return binsrch_low


class OrderedDefaultDict(OrderedDict):
    """A simple though elegant Ordered and Default dict
    """
    factory = list

    def __missing__(self, key):
        self[key] = value = self.factory()
        return value


class MultiMap(Mapping):
    """A memory-efficient map, which accepts duplicates
    """
    __slots__ = ("_keys", "_values")

    def __init__(self, np_keys, values, presorted=False):
        """Constructor for OrderedMap

        Args:
            np_keys: The numpy array of the keys. Can be empty
            values: The array of the values, can be any indexable, but better if numpy
        """
        assert len(np_keys) == len(values), "Keys and values must have the same length"
        if presorted:
            self._keys = np_keys
            self._values = values
        else:
            self._keys, self._values = self.sort_together(np_keys, values)

    @staticmethod
    def sort_together(np_keys, values):
        sort_idxs = np_keys.argsort()
        keys = np_keys[sort_idxs]
        if isinstance(values, np.ndarray):
            values = values[sort_idxs]
        else:
            values = [values[i] for i in sort_idxs]
        return keys, values

    def find(self, key):
        idx = np.searchsorted(self._keys, key)
        if idx == len(self._keys) or self._keys[idx] != key:
            return None
        return idx

    def keys(self):
        return self._keys

    def values(self):
        return self._values

    def __iter__(self):
        return iter(self._keys)

    def __len__(self):
        return len(self._keys)

    def get(self, key, default=None):
        idx = self.find(key)
        if idx is None:
            return default
        return self._values[idx]

    def get_items(self, key):
        """An iterator over all the values of a key
        """
        idx = self.find(key)
        for k, v in zip(self._keys[idx:], self._values[idx:]):
            if k != key: break
            yield v

    def __getitem__(self, key):
        idx = self.find(key)
        if idx is None:
            raise KeyError("{} does not exist".format(key))
        return self._values[idx]

    def __setitem__(self, key, value):
        raise NotImplementedError("Setitem is not allowed for performance reasons. "
                                  "Please build and add-inplace another MultiMap")

    def items(self):
        return zip(self._keys, self._values)

    def __contains__(self, key):
        return self.find(key) is not None

    exists = __contains__  # Compat. w Hoc map

    def __iadd__(self, other):
        """inplace add (incorporate other)"""
        self._keys, self._values = self.sort_together(
            np.concatenate((self._keys, other._keys)), self.concat(self._values, other._values))
        return self

    @staticmethod
    def concat(v1, v2):
        if isinstance(v1, np.ndarray) and isinstance(v2, np.ndarray):
            return np.concatenate((v1, v2))
        return (v1 if isinstance(v1, (list, tuple)) else list(v1)) + \
               (v2 if isinstance(v2, (list, tuple)) else list(v2))


class GroupedMultiMap(MultiMap):
    """ A Multimap which groups values by key in a list
    """
    def __init__(self, np_keys, values, presorted=False):
        MultiMap.__init__(self, np_keys, values, presorted)
        self._keys, self._values = self._duplicates_to_list(self._keys, self._values)

    @staticmethod
    def _duplicates_to_list(np_keys, values):
        np_keys, indexes = np.unique(np_keys, return_index=True)
        if len(indexes) == 0:
            return np_keys, []
        beg_it = iter(indexes)
        end_it = iter(indexes)
        next(end_it)
        values = [values[next(beg_it):end] for end in end_it] + [values[indexes[-1]:]]
        return np_keys, values

    def get(self, key, default=()):
        return MultiMap.get(self, key, default)

    def get_items(self, key):
        return self.get(key)

    def __iadd__(self, other):
        MultiMap.__iadd__(self, other)
        self._keys, v_list = self._duplicates_to_list(self._keys, self._values)
        self._values = [reduce(add, subl) for subl in v_list]
        return self

    def flat_values(self):
        return reduce(self.concat, self._values)


# ********** LOGGING *************

class ConsoleColors:
    BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, _, DEFAULT = range(10)
    NORMAL, BOLD, DIM, UNDERLINED, BLINK, INVERTED, HIDDEN = [a << 4 for a in range(7)]

    # These are the sequences needed to control output
    _CHANGE_SEQ = "\033[{}m"
    _RESET_SEQ = "\033[0m"

    @classmethod
    def reset(cls):
        return cls._RESET_SEQ

    @classmethod
    def set_text_color(cls, color):
        return cls._CHANGE_SEQ.format(color + 30)

    @classmethod
    def format_text(cls, text, color, style=None):
        if color > 7:
            style = (color >> 4)
            color = color & 0xf
        format_seq = "" if style is None else cls._CHANGE_SEQ.format(style)

        return format_seq + cls.set_text_color(color) + text + cls._RESET_SEQ


class _ColoredFormatter(_logging.Formatter):
    COLORS = {
        'WARNING': ConsoleColors.YELLOW,
        'INFO': ConsoleColors.DEFAULT,
        'DEBUG': ConsoleColors.DIM,
        'ERROR': ConsoleColors.RED,
        'CRITICAL': ConsoleColors.RED,
        'STAGE': ConsoleColors.BLUE + ConsoleColors.BOLD
    }

    def format(self, record):
        levelname = record.levelname
        msg = super(_ColoredFormatter, self).format(record)
        if levelname == "WARNING":
            msg = "[WARNING] " + msg
        if levelname in self.COLORS:
            msg = ConsoleColors.format_text(msg, self.COLORS[levelname])
        return msg


def setup_logging(loglevel, stream=sys.stdout):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
      stream: The output stream of log messages (default stdout)
    """
    if getattr(setup_logging, "logging_initted", False):
        return
    setup_logging.logging_initted = True
    assert isinstance(loglevel, int)
    loglevel = min(loglevel, 2)
    verbosity_levels = {
        0: _logging.WARNING,
        1: _logging.INFO,
        2: _logging.DEBUG,
    }

    _logging.addLevelName(STAGE_LOGLEVEL, "STAGE")
    _logging.NEW_STAGE = STAGE_LOGLEVEL

    logformat = "(%(asctime)s) [%(levelname)s] %(message)s"
    datefmt = "%b.%d %H:%M:%S"
    hdlr = _logging.StreamHandler(stream)
    hdlr.setFormatter(_ColoredFormatter(logformat, datefmt))
    _logging.root.setLevel(verbosity_levels[loglevel])
    _logging.root.addHandler(hdlr)
