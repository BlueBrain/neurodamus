"""
    neurodamus.core
    ---------------

    The neurodamus.core package implements several helper modules for building circuits
    with Neuron.
    They can be seen as a High-Level Neuron API, and several examples are found under `examples`.
"""

from __future__ import absolute_import
from functools import wraps
import time
from ._neuron import Neuron, MPI, ParallelNetManager
from ._neurodamus import NeuronDamus
from .cell import Cell
from .stimuli import CurrentSource
from ..utils import progressbar

__all__ = ['Neuron', 'MPI', 'NeuronDamus', 'Cell', 'CurrentSource', 'ProgressBarRank0',
           'mpi_no_errors', 'ParallelNetManager']


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
        time.sleep(1)
        return res
    return wrapper
