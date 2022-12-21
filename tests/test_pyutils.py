"""
Tests relative to utils.pyutils package, namely the MultiMaps
"""
from __future__ import print_function, absolute_import
import numpy
import pytest
import logging
from neurodamus.utils.multimap import MultiMap, GroupedMultiMap


def test_map_1():
    a = numpy.array([3, 1, 2], "i")
    b = numpy.array([4, 5, 6], "i")
    d = MultiMap(a, b)
    assert numpy.array_equal(d.keys(), [1, 2, 3])
    assert numpy.array_equal(d.values(), [5, 6, 4])
    assert d[1] == 5
    assert d[2] == 6
    try:
        d[0]
    except KeyError:
        pass
    else:
        raise Exception("d[0] should have excepted")
    logging.info(list(d.items()))


def test_map_other_data():
    a = numpy.array([3, 1, 2], "i")
    c = ["a", "b", "c"]
    d = MultiMap(a, c)
    assert numpy.array_equal(d.keys(), [1, 2, 3])
    assert numpy.array_equal(d.values(), ["b", "c", "a"])
    assert d[1] == "b"
    assert d[2] == "c"
    try:
        d[0]
    except KeyError:
        pass
    else:
        raise Exception("d[0] should have excepted")
    logging.info("%s", list(d.items()))


def test_map_duplicates():
    keys = numpy.array([3, 1, 2, 1, 2], "i")
    vals = ["a", "b", "c", "d", "e"]
    d = MultiMap(keys, vals)
    assert numpy.array_equal(d.keys(), [1, 1, 2, 2, 3])
    assert numpy.array_equal(d.values(), ["b", "d", "c", "e", "a"])
    assert d[1] == "b"
    assert d[2] == "c"
    assert numpy.array_equal(list(d.get_items(1)), ["b", "d"])
    logging.info("%s", d.values())


def test_map_duplicates_struct():
    keys = numpy.array([3, 1, 2, 1, 2], "i")
    vals = ["a", "b", "c", "d", "e"]
    d = GroupedMultiMap(keys, vals)
    assert numpy.array_equal(d.keys(), [1, 2, 3])
    expected_list = [["b", "d"], ["c", "e"], ["a"]]
    assert all([numpy.array_equal(d_list, exp_list)
                for d_list, exp_list in zip(d.values(), expected_list)])
    assert numpy.array_equal(d.flat_values(), ["b", "d", "c", "e", "a"]), d.flat_values()
    assert d[1] == ["b", "d"]
    assert d[2] == ["c", "e"]
    assert d[3] == ["a"]
    assert numpy.array_equal(list(d.get_items(1)), ["b", "d"])
    logging.info("%s: %s | Flat: %s", d.keys(), d.values(), d.flat_values())


def test_badly_formed():
    keys = numpy.array([3, 4], "i")
    vals = []
    with pytest.raises(AssertionError):
        MultiMap(keys, vals)
    keys = numpy.array([], "i")
    d = MultiMap(keys, vals)
    assert len(d.values()) == 0
    d = GroupedMultiMap(keys, vals)
    assert len(d.values()) == 0


def test_merge():
    keys = numpy.array([3, 4, 3], "i")
    vals = [1, 2, 3]
    d = MultiMap(keys, vals)
    keys = numpy.array([2, 4, 3], "i")
    vals = ['x', 'y', 'z']
    d += MultiMap(keys, vals)
    assert d.keys() == pytest.approx([2, 3, 3, 3, 4, 4]), d.keys()
    assert d.values() == ['x', 1, 3, 'z', 2, 'y'], d.values()
    assert numpy.array_equal(list(d.get_items(4)), [2, "y"])
    logging.info("%s: %s", d.keys(), d.values())


def test_merge_grouped():
    keys = numpy.array([3, 4, 3], "i")
    vals = [1, 2, 3]
    d = GroupedMultiMap(keys, vals)
    keys = numpy.array([2, 4, 3], "i")
    vals = ['x', 'y', 'z']
    d += GroupedMultiMap(keys, vals)
    assert d[3] == [1, 3, 'z']
    logging.info("%s: %s", d._keys, d._values)


def test_flatten_grouped():
    keys = numpy.array([4, 3, 4, 3], "i")
    vals = [0, 1, 2, 3]
    d = GroupedMultiMap(keys, vals)
    assert list(d._keys) == [3, 4]
    assert list(d._values) == [[1, 3], [0, 2]]
    d2 = d.flatten()
    assert list(d2._keys) == [3, 3, 4, 4]
    assert list(d2._values) == [1, 3, 0, 2]
    logging.info("%s: %s", d._keys, d._values)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_map_1()
    test_map_other_data()
    test_map_duplicates()
    test_map_duplicates_struct()
    test_badly_formed()
    test_merge()
    test_merge_grouped()
    test_flatten_grouped()
