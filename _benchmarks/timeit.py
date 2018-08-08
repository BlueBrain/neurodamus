from __future__ import print_function
from contextlib import contextmanager
import time as _time


@contextmanager
def time():
    start = _time.time()
    yield
    print("The function took %g secs." % (_time.time() - start))


def timeit():
    tot_time = .0
    loop = 0

    start = _time.time()
    yield 0
    stop = _time.time()
    best_time = stop - start
    tot_time = best_time

    while tot_time < 4:
        loop += 1
        start = stop
        yield loop
        stop = _time.time()
        tdiff = stop - start
        best_time = min(best_time, tdiff)
        tot_time += tdiff

    print("Best run: %.3f ms. [%d loops]" % (best_time * 1000, loop + 1))
