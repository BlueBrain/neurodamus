"""
    timeit classes, functions, decorators and context managers

NOTE: Implementation is done along the lines of timeit.hoc

You can use the @timeit as decorator for functions
    >>> from neurodamus.utils.timeit import timeit
    >>> @timeit(name="test_func")
    >>> def test_func():
    >>>     from time import sleep
    >>>     sleep(1)

or as contextmanager for blocks of code
    >>> from neurodamus.utils.timeit import timeit
    >>> def test_block():
    >>>     with timeit(name="test_block"):
    >>>         from time import sleep
    >>>         sleep(2)

Similar to timeit.hoc, you can print every timer just after the measurement.
NOTE: the printing is effectively done only if you run neurodamus with <--verbose>.
For x-reference purposes, we print with "setpvec/accum" keywords:

    [ VERB ]  -> setpvec 15                  Cell creation 12.5351

The difference is that "accum" is printed from 2nd call on + sequence no. joined with "setpvec"

   [ VERB ]  -> accum 16                  Cell creation 10.7224 => TotalTime: 21.5789

One use case would be to see the time for each iteration of a loop.
This can be done by using the ctxt manager right after the for:
    >>> from neurodamus.utils.timeit import timeit
    >>> def test_block():
    >>>     for x in range():
    >>>         with timeit(name="test_block_in_for"):
    >>>             test_block_in_for()
    >>>             ....
    [ VERB ]  -> setpvec 1                test_block_in_for 1
    [ VERB ]  -> accum 2                  test_block_in_for 1 => TotalTime: 2
    [ VERB ]  -> accum 3                  test_block_in_for 2 => TotalTime: 4
    [ VERB ]  -> accum 4                  test_block_in_for 3 => TotalTime: 7
    [ VERB ]  -> accum 5                  test_block_in_for 4 => TotalTime: 11

You can however skip printing them, useful for big loops for example; you will in turn
get the total time at the end. Set <verbose> parameter to false for that:
    >>> from neurodamus.utils.timeit import timeit
    >>> def test_block():
    >>>     for x in big_range():
    >>>         ....
    >>>         with timeit(name="test_block_in_for", verbose = False):
    >>>             test_block_in_for()
    >>>         ....


There is a TimerManager singleton that holds all the timers.
You can call <timeit_show_stats()> on it to get statistics
    >>> from neurodamus.utils.timeit import TimerManager
    >>> TimerManager.timeit_show_stats()
    [ INFO ] +====================== TIMEIT STATS =============================+
    [ INFO ] |           Event Label          | Avg.Time | Min.Time | Max.Time |
    [ INFO ] +-----------------------------------------------------------------+
    [ INFO ] |                      test_func       1.00 |     1.00 |     1.00 |
    [ INFO ] |                     test_block       2.00 |     2.00 |     2.00 |
    [ INFO ] +-----------------------------------------------------------------+

You can archive timers, useful for multiple flow runs (see node.py MULTI-CYCLE RUN)
or just to break down numbers. You need to call <archive()> from TimerManager:
    >>> for index in range(2):
    >>>     test_func()
    >>>     test_block()
    >>>     TimerManager.archive(archive_name=" Test {:d}".format(index + 1))
    >>> TimerManager.timeit_show_stats()
    ....
    [ INFO ] +==================== TIMEIT STATS ( Test 1) =====================+
    [ INFO ] |           Event Label          | Avg.Time | Min.Time | Max.Time |
    [ INFO ] +-----------------------------------------------------------------+
    [ INFO ] |                      test_func       1.00 |     1.00 |     1.00 |
    [ INFO ] |                     test_block       2.00 |     2.00 |     2.00 |
    [ INFO ] +-----------------------------------------------------------------+

    [ INFO ] +==================== TIMEIT STATS ( Test 2) =====================+
    [ INFO ] |           Event Label          | Avg.Time | Min.Time | Max.Time |
    [ INFO ] +-----------------------------------------------------------------+
    [ INFO ] |                      test_func       1.00 |     1.00 |     1.00 |
    [ INFO ] |                     test_block       2.00 |     2.00 |     2.00 |
    [ INFO ] +-----------------------------------------------------------------+
    ....

In case you want to time operations just on rank0, without impacting the STATS,you can
use @timeit_rank0 in a similar manner to @timeit. For example delete_corenrn_data,
which is happening only on rank0.

PITFALLS:
    Make sure you avoid data-driven flows for your timeits, otherwise there will be
    an MPI_Allreduce number of timers mismatch and you will get MPI errors like:
        MPT: --------stack traceback-------
        MPT ERROR: rank:3426, function:MPI_ALLREDUCE, Message truncated on receive:
                        An application bug caused the sender to send too much data
    Example:
          for conn in self.get_target_connections(None, target_name):
            if conn.sgid not in spike_manager:
                continue
            # PITFALL: May not be called on some ranks => one less timer
            with timeit(name="register replay events", verbose=False):
                conn.replay(spike_manager[conn.sgid], start_delay)
                replayed_count += 1

"""
from __future__ import absolute_import
import logging
import time

from contextlib import contextmanager, ContextDecorator
from itertools import chain
from math import log, floor

from .logging import log_verbose
from ..core import NeurodamusCore as Nd, MPI, run_only_rank0


def human_readable(num):
    """ Get a human readable version of a number.
    For example: 5200000 -> 5.20M

    Args:
        num: The number
    """
    units = ['', 'K', 'M', 'B', 'T', 'P']
    power = int(floor(log(num, 1000.)))
    return '{:.2f}{:s}'.format(num / 1000. ** power, units[power]) if power >= 1 \
        else str(int(num))


delim = u'\u255a'


class _Timer(object):
    total_time = property(lambda self: self._total_time)
    accumulated = property(lambda self: self._accumulated)
    name = property(lambda self: self._name)
    hits = property(lambda self: self._hits)

    def __init__(self, name):
        self._name = name
        self._total_time = 0
        self._start_time = None
        self._last_time = None
        self._accumulated = False
        self._hits = 0

    def start(self):
        self._start_time = time.perf_counter()
        return self

    def stop(self):
        self._last_time = time.perf_counter() - self._start_time
        if self._total_time:
            self._accumulated = True
        self._total_time += self._last_time
        self._hits += 1
        self._start_time = None  # invalidate start time

    def log(self, keyword, seq_no=None):
        log_verbose("{:s} {} {:<30s} {:.4f} {:s}".
                    format(keyword,
                           seq_no if seq_no is not None else '',
                           self._name,
                           self._last_time,
                           "=> TotalTime: {:g}".format(self._total_time) if self._accumulated
                           else ""))


class _TimerManager(object):
    _timers = dict()
    _timers_sequence = 0
    _archived_timers = {}

    # archive current timers
    def archive(self, archive_name):
        self._archived_timers[archive_name] = self._timers
        self._timers = dict()

    def init(self, name):
        self._timers.setdefault(name, _Timer(name))
        self._timers[name].start()

    def update(self, name, verbose=True):
        if name not in self._timers.keys():
            raise Exception("{} not initialized in timers dict".format(name))
        self._timers[name].stop()
        if verbose:
            self._log_timer(self._timers[name])

    @run_only_rank0
    def _log_timer(self, timer_info):
        timer_info.log(keyword="accum" if timer_info.accumulated else "setpvec",
                       seq_no=self._timers_sequence)
        self._timers_sequence += 1

    # Note: method name kept for reference wrt neurodamus-core timeit.hoc
    def timeit_show_stats(self):
        current_timers_name = "Final Stats" if len(self._archived_timers) else ""
        for timers_name, timers in chain(self._archived_timers.items(),
                                         ((current_timers_name, self._timers),)):
            mpi_times = Nd.Vector(tinfo.total_time for tinfo in timers.values())
            avg_times = mpi_times.c()
            MPI.pc.allreduce(avg_times, MPI.SUM)
            min_times = mpi_times.c()
            MPI.pc.allreduce(min_times, MPI.MIN)
            max_times = mpi_times.c()
            MPI.pc.allreduce(max_times, MPI.MAX)

            nof_hits = Nd.Vector(tinfo.hits for tinfo in timers.values())
            MPI.pc.allreduce(nof_hits, MPI.SUM)

            self._log_stats(timers_name, timers, avg_times, min_times, max_times, nof_hits)

    @run_only_rank0
    def _log_stats(self, timers_name, timers, avg_times, min_times, max_times, nof_hits):
        stats_name = " TIMEIT STATS {}".format('(' + timers_name + ') ' if timers_name
                                               else timers_name)
        logging.info("+{:=^111s}+".format(stats_name))
        logging.info("|{:^58s}|{:^10s}|{:^10s}|{:^10s}|{:^19s}|".format(
            'Event Label', 'Avg.Time', 'Min.Time', 'Max.Time', 'Hits R0 / Total '))
        logging.info("+{:-^111s}+".format('-'))

        for t, (name, tinfo) in enumerate(timers.items()):
            base_name = delim.join('  ') * name.count(delim) + name.split(delim)[-1]
            logging.info("| {:<56s} | {:8.2f} | {:8.2f} | {:8.2f} | {:>7s} / {:<7s} |".format(
                base_name,
                avg_times.x[t] / MPI.size,
                min_times.x[t],
                max_times.x[t],
                human_readable(tinfo.hits),
                human_readable(nof_hits.x[t])))
        logging.info("+{:-^111s}+".format('-'))


TimerManager = _TimerManager()  # singleton


# Can be used as context manager or decorator
class timeit(ContextDecorator):
    curr_path = []

    def __init__(self, name, verbose=True):
        self._original_name = name
        self._verbose = verbose

    def __enter__(self):
        timeit.curr_path.append(self._original_name)
        self._name = delim.join(timeit.curr_path)
        TimerManager.init(self._name)

    def __exit__(self, exc_type, exc, exc_tb):
        TimerManager.update(self._name, self._verbose)
        timeit.curr_path.pop()


# Can also be used as decorator.
# Does not use the TimerManager.
@contextmanager
def timeit_rank0(name):
    if MPI.rank == 0:
        t = _Timer(name).start()
        yield
        t.stop()
        t.log(keyword="rank0")
    else:
        yield  # No-op
