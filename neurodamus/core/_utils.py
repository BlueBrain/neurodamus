"""
Collection of core helpers / utilities
"""
from __future__ import absolute_import
import time
from functools import wraps
from array import array
from ._neuron import MPI, ParallelNetManager as pnm
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
    if MPI.size == 0:
        return f

    @wraps(f)
    def wrapper(*args, **kw):
        res = f(*args, **kw)
        MPI.check_no_errors()
        return res

    return wrapper


def return_neuron_timings(f):
    """Decorator to collect and return timings on a neuron run
    """
    @wraps(f)
    def wrapper(*args, **kw):
        # Timings structure (being returned)
        tdat = array("d", [.0]*8)
        tstart = time.time()
        wait_base = pnm.pc.wait_time()

        f(*args, **kw)  # Discard return values

        tdat[0] = pnm.pc.wait_time() - wait_base
        tdat[1] = pnm.pc.step_time()
        tdat[2] = pnm.pc.send_time()
        tdat[3] = pnm.pc.vtransfer_time()
        tdat[4] = pnm.pc.vtransfer_time(1)  # split exchange time
        tdat[6] = pnm.pc.vtransfer_time(2)  # reduced tree computation time
        tdat[4] -= tdat[6]
        tdat[7] = time.time() - tstart      # total time
        return tdat

    return wrapper
