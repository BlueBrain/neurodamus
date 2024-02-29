"""
Collection of core helpers / utilities
"""
from __future__ import absolute_import
import time
from array import array
from datetime import timedelta
from functools import wraps
from inspect import Signature, signature
from ._mpi import MPI
from ..utils import progressbar
from . import NeurodamusCore as Nd


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
        # Three scenarios:
        #   0 - all ranks return normally: they all wait in the barrier
        #   1 - all ranks throw exception: exception propagated up, no barrier hit
        #   2 - some ranks throw exception. Good ranks will wait in barrier. Two options:
        #       In program mode bad ranks must call MPI_abort (in commands.py)
        #       In API mode we must catch unhandled exception participate in collective count
        #       and raise exception in all ranks
        res = f(*args, **kw)
        if MPI.size > 1:
            MPI.check_no_errors()
        return res

    return mpi_ok_wrapper


class run_only_rank0:
    """Decorator that makes a given func to run only in rank 0.

    It will broadcast results IFF the user specifies return type notation.
    It handles nested level to avoid broadcasting while we are already in rank0_only mode
    """
    nested_depth = 0

    def __new__(cls, f):
        has_return = signature(f).return_annotation != Signature.empty

        @wraps(f)
        def rank0_wrapper(*args, **kw):
            # Situation we dont need/want the broadcast
            if MPI.size == 1 or cls.nested_depth > 0:
                return f(*args, **kw)

            cls.nested_depth += 1
            res = f(*args, **kw) if MPI.rank == 0 else None
            cls.nested_depth -= 1

            if has_return:
                return MPI.py_broadcast(res, 0)

        return rank0_wrapper


class SimulationProgress:
    def __init__(self):
        """
        Class which will set up a timer to perioducally check the amount of time lapsed
        in the simulation compared to the final tstop value. This is converted into a percentage
        of the job complete which is then printed to the console.
        """
        self.last_time_check = time.time()
        self.sim_start = self.last_time_check
        self.update_progress()

    def update_progress(self):
        """
        Callback function that refreshes the progress value (if enough time has elapsed) and then
        inserts the next call into the event queue.
        """
        current_time = time.time()
        sim_t = Nd.t
        sim_tstop = Nd.tstop
        if (current_time - self.last_time_check > 0.75) and (sim_t > 0):
            self.last_time_check = current_time
            sec_remain = (self.last_time_check - self.sim_start) * (sim_tstop / sim_t - 1)
            print(f"\r[t={sim_t:5.2f}] Completed {sim_t*100/sim_tstop:2.0f}%"
                  f" ETA: {timedelta(seconds=int(sec_remain))}  ", end='', flush=True)
        Nd.cvode.event(sim_t + 1, self.update_progress)


def return_neuron_timings(f):
    """Decorator to collect, return timings and show the progress on a neuron run
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
