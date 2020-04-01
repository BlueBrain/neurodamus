"""
A collection of Pure-Python MultiMaps
"""
import numpy as np
from functools import reduce
from operator import add
from .compat import collections_abc


class MultiMap(collections_abc.Mapping):
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
        sort_idxs = np_keys.argsort(kind="mergesort")  # need stability
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

    def data(self):
        return self._keys, self._values


class GroupedMultiMap(MultiMap):
    """A Multimap which groups values by key in a list.
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
        next(end_it)  # Discard first
        values = [values[next(beg_it):end] for end in end_it] + [values[indexes[-1]:]]  # Last
        assert len(np_keys) == len(values)
        return np_keys, values

    def get(self, key, default=()):
        return MultiMap.get(self, key, default)

    def get_items(self, key):
        return self.get(key)

    def size(self):
        """Number of entries"""
        return reduce(add, (len(v) for v in self._values))

    def __iadd__(self, other):
        MultiMap.__iadd__(self, other)
        self._keys, v_list = self._duplicates_to_list(self._keys, self._values)
        self._values = [reduce(add, subl) for subl in v_list]
        return self

    def flat_values(self):
        return reduce(self.concat, self._values)

    def flatten(self):
        """Transform the current Map to a plain Multimap, without groups.
        """
        keys = np.repeat(self._keys, [len(v) for v in self._values])
        values = np.concatenate(self._values)
        return MultiMap(keys, values, presorted=True)
