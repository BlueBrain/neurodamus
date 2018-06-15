from __future__ import absolute_import
import logging
import sys
from collections import OrderedDict
from bisect import bisect_left
import numpy as np
from itertools import islice
from operator import add
from six.moves import zip


def setup_logging(loglevel, stream=sys.stdout):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
      stream: The output stream of log messages (default stdout)
    """
    loglevel = min(loglevel, 2)
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


class MultiMap(object):
    """A memory-efficient map, which accepts duplicates
    """
    __slots__ = ("keys", "values")

    def __init__(self, np_keys, values, presorted=False):
        """Constructor for OrderedMap

        Args:
            np_keys: The numpy array of the keys. Can be empty
            values: The array of the values, can be any indexable, but better if numpy
        """
        assert len(np_keys) == len(values), "Keys and values must have the same length"
        if presorted:
            self.keys = np_keys
            self.values = values
        else:
            self.keys, self.values = self.sort_together(np_keys, values)

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
        idx = np.searchsorted(self.keys, key)
        if idx == len(self.keys) or self.keys[idx] != key:
            return None
        return idx

    def get_items(self, key):
        """An iterator over all the values of a key
        """
        idx = self.find(key)
        for k, v in zip(self.keys[idx:], self.values[idx:]):
            if k != key: break
            yield v

    def __getitem__(self, key):
        idx = self.find(key)
        if idx is None:
            raise KeyError("{} does not exist".format(key))
        return self.values[idx]

    def __setitem__(self, key, value):
        raise NotImplementedError("Setitem is not allowed for performance reasons. "
                                  "Please create new keys and values and rebuild the dict")

    def items(self):
        return zip(self.keys, self.values)

    def __contains__(self, key):
        return self.find(key) is not None

    def __iadd__(self, other):
        """inplace add (incorporate other)"""
        self.keys, self.values = self.sort_together(np.concatenate((self.keys, other.keys)),
                                                    self.concat(self.values, other.values))
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
        self.keys, self.values = self._duplicates_to_list(self.keys, self.values)

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

    def get_items(self, key):
        return self[key]

    def __iadd__(self, other):
        MultiMap.__iadd__(self, other)
        self.keys, v_list = self._duplicates_to_list(self.keys, self.values)
        self.values = [reduce(add, subl) for subl in v_list]
        return self
