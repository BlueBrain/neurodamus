import numpy
from neurodamus.utils.pyutils import EfficientOrderedDict


def test_efficient_dict():
    a = numpy.array([3, 1, 2], "i")
    b = numpy.array([4, 5, 6], "i")
    d = EfficientOrderedDict(a, b)
    assert numpy.array_equal(d.keys, [1, 2, 3])
    assert numpy.array_equal(d.values, [5, 6, 4])
    assert d[1] == 5
    assert d[2] == 6
    try:
        d[0]
    except KeyError:
        print("ok")
    else:
        raise Exception("d[0] should have excepted")

    print(list(d.items()))

    a = numpy.array([3, 1, 2], "i")
    c = ["a", "b", "c"]
    d = EfficientOrderedDict(a, c)
    assert numpy.array_equal(d.keys, [1, 2, 3])
    vals = list(d.values)
    assert numpy.array_equal(vals, ["b", "c", "a"])
    assert d[1] == "b"
    assert d[2] == "c"
    try:
        d[0]
    except KeyError:
        print("ok")
    else:
        raise Exception("d[0] should have excepted")

    print(list(d.items()))
