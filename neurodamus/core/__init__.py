from __future__ import absolute_import
from ._neuron import Neuron
from ._neurodamus import NeuronDamus
from .cell import Cell
from .stimuli import CurrentSource
from .configuration import MPInfo
from ..utils import progressbar


# Util progressbar that only shows on Rank 0
class ProgressBarRank0(progressbar.Progress):
    """Rank dependant progressbar.
    """
    def __new__(cls, end, **kwargs):
        if MPInfo.rank == 0:
            return progressbar.ProgressBar(end, **kwargs)
        return progressbar.Progress(end, **kwargs)
