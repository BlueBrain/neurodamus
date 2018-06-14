"""
    Compatibility Classes to work similar to HOC types, recreating or wrapping them
"""
from __future__ import absolute_import
from array import array


class Vector(array):
    """Behavior similar to Hoc Vector
    """
    __slots__ = ()

    def size(self):
        return len(self)

    @property
    def x(self):
        return self


class Map(object):
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

    @property
    def hoc_map(self):
        return self._hoc_map
