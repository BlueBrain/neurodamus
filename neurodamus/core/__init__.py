from __future__ import absolute_import
from ._neuron import Neuron, MPI
from ._neurodamus import NeuronDamus
from .cell import Cell
from .stimuli import CurrentSource
from ..utils import progressbar

__all__ = ['Neuron', 'MPI', 'NeuronDamus', 'Cell', 'CurrentSource', 'ProgressBarRank0']


class ProgressBarRank0(progressbar.Progress):
    """Helper Progressbar that only shows on Rank 0.
       For MPI clusters size > 1 it always uses simplified bars. Otherwise auto-detects (isatty).
    """
    def __new__(cls, end, *args, **kwargs):
        if MPI.rank == 0:
            return progressbar.ProgressBar(end, *args, tty_bar=(MPI.size == 1) and None, **kwargs)
        return progressbar.Progress(end, *args, **kwargs)
