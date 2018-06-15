from __future__ import print_function, absolute_import
import numpy
from neurodamus.utils.pyutils import MultiMap, GroupedMultiMap
import pytest


def test_map_1():
    a = numpy.array([3, 1, 2], "i")
    b = numpy.array([4, 5, 6], "i")
    d = MultiMap(a, b)
    assert numpy.array_equal(d.keys, [1, 2, 3])
    assert numpy.array_equal(d.values, [5, 6, 4])
    assert d[1] == 5
    assert d[2] == 6
    try:
        d[0]
    except KeyError:
        pass
    else:
        raise Exception("d[0] should have excepted")

    print(list(d.items()))


def test_map_other_data():
    a = numpy.array([3, 1, 2], "i")
    c = ["a", "b", "c"]
    d = MultiMap(a, c)
    assert numpy.array_equal(d.keys, [1, 2, 3])
    assert numpy.array_equal(d.values, ["b", "c", "a"])
    assert d[1] == "b"
    assert d[2] == "c"
    try:
        d[0]
    except KeyError:
        pass
    else:
        raise Exception("d[0] should have excepted")

    print(list(d.items()))


def test_map_duplicates():
    keys = numpy.array([3, 1, 2, 1, 2], "i")
    vals = ["a", "b", "c", "d", "e"]
    d = MultiMap(keys, vals)
    assert numpy.array_equal(d.keys, [1, 1, 2, 2, 3])
    assert numpy.array_equal(d.values, ["b", "d", "c", "e", "a"])
    assert d[1] == "b"
    assert d[2] == "c"
    assert numpy.array_equal(list(d.get_items(1)), ["b", "d"])
    print(d.values)


def test_map_duplicates_struct():
    keys = numpy.array([3, 1, 2, 1, 2], "i")
    vals = ["a", "b", "c", "d", "e"]
    d = GroupedMultiMap(keys, vals)
    assert numpy.array_equal(d.keys, [1, 2, 3])
    assert numpy.array_equal(d.values, [["b", "d"], ["c", "e"], ["a"]]), d.values
    assert d[1] == ["b", "d"]
    assert d[2] == ["c", "e"]
    assert numpy.array_equal(list(d.get_items(1)), ["b", "d"])
    print(d.values)


def test_badly_formed():
    keys = numpy.array([3, 4], "i")
    vals = []
    with pytest.raises(AssertionError):
        MultiMap(keys, vals)
    keys = numpy.array([], "i")
    d = MultiMap(keys, vals)
    print(d.values)
    d = GroupedMultiMap(keys, vals)
    assert len(d.values) == 0
    print(d.values)


def test_merge():
    keys = numpy.array([3, 4, 3], "i")
    vals = [1, 2, 3]
    d = MultiMap(keys, vals)
    keys = numpy.array([2, 4, 3], "i")
    vals = ['x', 'y', 'z']
    d += MultiMap(keys, vals)
    assert d.keys == pytest.approx([2, 3, 3, 3, 4, 4]), d.keys
    assert d.values == ['x', 1, 3, 'z', 2, 'y'], d.values
    assert numpy.array_equal(list(d.get_items(4)), [2, "y"])
    print(d.keys, d.values)


def test_merge_grouped():
    keys = numpy.array([3, 4, 3], "i")
    vals = [1, 2, 3]
    d = GroupedMultiMap(keys, vals)
    keys = numpy.array([2, 4, 3], "i")
    vals = ['x', 'y', 'z']
    d += GroupedMultiMap(keys, vals)
    assert d[3] == [1, 3, 'z']
    print(d.keys, d.values)


if __name__ == "__main__":
    test_map_1()
    test_map_other_data()
    test_map_duplicates()
    test_map_duplicates_struct()
    test_badly_formed()
    test_merge()
    test_merge_grouped()
