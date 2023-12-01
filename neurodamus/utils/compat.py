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

    def __new__(cls, type_="I", array=[]):
        return super().__new__(Vector, type_, array)

    def size(self):
        return len(self)

    @property
    def x(self):
        return self

    def __add__(self, other):
        array.extend(self, other)
        return self

    def as_hoc(self):
        """When API compat is not enough, convert to a true hov Vector"""
        return hoc_vector(self)


class List(list):
    """Behavior similar to Hoc List
    """
    __slots__ = ()

    def count(self, obj=None):
        return super().count(obj) if obj else len(self)

    def o(self, idx):
        return self[int(idx)]


class Map(collections_abc.Mapping):
    """Class which bring Python map API to hoc Maps
    """
    __slots__ = ('_hoc_map', '_size', 'String')

    def __new__(cls, wrapped_obj, *args, **kwargs):
        """ If the wrapped entity is not an hoc map, but a Python dict
            then also wrap it using PyMap for a similar API
        """
        if isinstance(wrapped_obj, dict):
            return PyMap(wrapped_obj)
        return object.__new__(cls)

    def __init__(self, hoc_map):
        self._hoc_map = hoc_map
        self._size = int(hoc_map.count())
        from neuron import h
        self.String = h.String

    def __iter__(self):
        return (self._hoc_map.key(i).s for i in range(self._size))

    def items(self):
        return ((self._hoc_map.key(i).s, self._hoc_map.o(i))
                for i in range(self._size))

    def values(self):
        return (self._hoc_map.o(i) for i in range(self._size))

    keys = __iter__

    def get(self, key, default=None):
        return self[key] if key in self else default

    def __getitem__(self, item):
        value = self._hoc_map.get(item)
        if hasattr(value, 's'):  # hoc strings have the value in .s attribute
            value = value.s
        return value

    def __setitem__(self, key, value):
        if self._hoc_map.exists(key):
            self._hoc_map.get(key).s = str(value)
        else:
            self._hoc_map.put(key, self.String(str(value)))
            self._size = int(self._hoc_map.count())  # update size

    def update(self, other_map):
        for key, val in other_map.items():
            self[key] = val

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


class PyMap(dict):
    """
    PyMap does basically the reverse of compat.Map: it's a true dict but capable of
    getting a hoc map, built on the fly
    """
    __slots__ = ()

    @property
    def hoc_map(self):
        """Returns the raw hoc map
        """
        return self._dict_as_hoc(self)

    @classmethod
    def _value_as_hoc(cls, value):
        from neuron import h
        if isinstance(value, dict):
            return cls._dict_as_hoc(value)
        return h.String(str(value))

    @classmethod
    def _dict_as_hoc(cls, d):
        from neuron import h
        m = h.Map()
        for key, val in d.items():
            m.put(h.String(key), cls._value_as_hoc(val))
        return m

    def as_dict(self, *_, **_kw):
        return self


def hoc_vector(np_array):
    from neuron import h
    hoc_vec = h.Vector(np_array.size)
    hoc_vec.as_numpy()[:] = np_array
    return hoc_vec
