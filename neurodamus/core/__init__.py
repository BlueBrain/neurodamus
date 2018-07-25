from __future__ import absolute_import
from ._neuron import Neuron, MPI
from ._neurodamus import NeuronDamus
from .cell import Cell
from .stimuli import CurrentSource
from ..utils import progressbar


# Util progressbar that only shows on Rank 0
class ProgressBarRank0(progressbar.Progress):
    """Rank dependant progressbar.
    """
    def __new__(cls, end, *args, **kwargs):
        if MPI.rank == 0:
            return progressbar.ProgressBar(end, *args, **kwargs)
        return progressbar.Progress(end, *args, **kwargs)
