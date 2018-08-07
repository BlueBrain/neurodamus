"""
    Compatibility Classes to work similar to HOC types, recreating or wrapping them
"""
from __future__ import absolute_import
from array import array
from collections import Mapping


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


class Map(Mapping):
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
        return self._hoc_map
