"""
Collection of core helpers / utilities
"""
from __future__ import absolute_import
import time
from functools import wraps
from array import array
from ._mpi import MPI
from ..utils import progressbar


class ProgressBarRank0(progressbar.Progress):
    """Helper Progressbar that only shows on Rank 0.
       For MPI clusters size > 1 it always uses simplified bars. Otherwise auto-detects (isatty).
    """
    def __new__(cls, end, *args, **kwargs):
        if MPI.rank == 0:
            return progressbar.ProgressBar(end, *args, tty_bar=(MPI.size == 1) and None, **kwargs)
        return progressbar.Progress(end, *args, **kwargs)


def mpi_no_errors(f):
    """Convenience decorator which checks all processes are fine when f returns
    """
    @wraps(f)
    def mpi_ok_wrapper(*args, **kw):
        res = f(*args, **kw)
        if MPI.size > 0:
            MPI.check_no_errors()
        return res

    return mpi_ok_wrapper


def run_only_rank0(f):
    """Decorator that makes a given func to run only in rank 0 and then broadcast result
    """
    @wraps(f)
    def rank0_wrapper(*args, **kw):
        res = None
        if MPI.rank == 0:
            res = f(*args, **kw)
        if MPI.size == 1:
            return res
        MPI.check_no_errors()  # Ensure all procs ok before bcast

        return MPI.py_broadcast(res, 0)

    return rank0_wrapper


def return_neuron_timings(f):
    """Decorator to collect and return timings on a neuron run
    """
    @wraps(f)
    def timings_wrapper(*args, **kw):
        # Timings structure (being returned)
        tdat = array("d", [.0]*8)
        tstart = time.time()
        pc = MPI.pc
        wait_base = pc.wait_time()

        f(*args, **kw)  # Discard return values

        tdat[0] = pc.wait_time() - wait_base
        tdat[1] = pc.step_time()
        tdat[2] = pc.send_time()
        tdat[3] = pc.vtransfer_time()
        tdat[4] = pc.vtransfer_time(1)  # split exchange time
        tdat[6] = pc.vtransfer_time(2)  # reduced tree computation time
        tdat[4] -= tdat[6]
        tdat[7] = time.time() - tstart      # total time
        return tdat

    return timings_wrapper
