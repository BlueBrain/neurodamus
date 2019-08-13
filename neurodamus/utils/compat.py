"""
Compatibility Classes to work similar to HOC types, recreating or wrapping them
"""
from __future__ import absolute_import
from array import array
try:
    import collections.abc as collections_abc  # Py >= 3.3
except ImportError:
    import collections as collections_abc


class Vector(array):
    """Behavior similar to Hoc Vector
    """
    __slots__ = ()

    def size(self):
        return len(self)

    @property
    def x(self):
        return self


class List(list):
    """Behavior similar to Hoc List
    """
    __slots__ = ()

    def count(self):
        return len(self)

    def o(self, idx):
        return self[int(idx)]


class Map(collections_abc.Mapping):
    """Class which bring Python map API to hoc Maps
    """
    __slots__ = ('_hoc_map', '_size')

    def __init__(self, hoc_map):
        self._hoc_map = hoc_map
        self._size = int(hoc_map.count())

    def __iter__(self):
        return (self._hoc_map.key(i).s for i in range(self._size))

    def items(self):
        return ((self._hoc_map.key(i).s, self._hoc_map.o(i))
                for i in range(self._size))

    def values(self):
        return (self._hoc_map.o(i) for i in range(self._size))

    keys = __iter__

    def __getitem__(self, item):
        return self._hoc_map.get(item)

    def __contains__(self, item):
        return self._hoc_map.exists(item) > 0

    def __len__(self):
        return self._size

    @property
    def hoc_map(self):
        """Returns the raw hoc map
        """
        return self._hoc_map

    def as_dict(self, parse_strings=False):
        """Creates a real dictionary from the Map.

        Args:
            parse_strings: If true converts string objects in both key and values to
                real strings (xx.s) and attempts to convert values to float
        """
        if parse_strings:
            def parse(stri):
                try:
                    return float(stri)
                except ValueError:
                    return stri
            new_map = {key: parse(val.s) for key, val in self.items()}
        else:
            new_map = dict(self)
        new_map["_hoc"] = self.hoc_map
        return new_map
