import numpy
from neurodamus.utils.pyutils import OrderedMap


def test_map_1():
    a = numpy.array([3, 1, 2], "i")
    b = numpy.array([4, 5, 6], "i")
    d = OrderedMap(a, b)
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
    d = OrderedMap(a, c)
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
    d = OrderedMap(keys, vals)
    assert numpy.array_equal(d.keys, [1, 1, 2, 2, 3])
    assert numpy.array_equal(d.values, ["b", "d", "c", "e", "a"])
    assert d[1] == "b"
    assert d[2] == "c"
    assert numpy.array_equal(list(d.get_items(1)), ["b", "d"])
    print(d.values)


def test_map_duplicates_struct():
    keys = numpy.array([3, 1, 2, 1, 2], "i")
    vals = ["a", "b", "c", "d", "e"]
    d = OrderedMap.create_duplicates_as_list(keys, vals)
    assert numpy.array_equal(d.keys, [1, 2, 3])
    assert numpy.array_equal(d.values, [["b", "d"], ["c", "e"], ["a"]]), d.values
    assert d[1] == ["b", "d"]
    assert d[2] == ["c", "e"]
    assert numpy.array_equal(list(d.get_items(1)), [["b", "d"]])
    print(d.values)



if __name__ == "__main__":
    test_map_1()
    test_map_other_data()
    test_map_duplicates()
    test_map_duplicates_struct()
