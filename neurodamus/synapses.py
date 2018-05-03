
from .utils import ConfigT
from . import Neuron


class SynapseMaker(ConfigT):
    """A synapse configuration. Can then be instantiated among several pre-post pairs
    """
    e = None    # mV
    i = None    # nA

    threshold = None
    delay = None
    weight = None

    _netcon_fields = ("threshold", "delay", "weight")

    def __new__(cls, segment=None, **properties):
        if segment is not None:
            syn = getattr(Neuron.h, cls.__name__)(segment)
            [setattr(syn, key, val) for key, val in properties.items()]
            return syn
        return object.__new__(cls)

    def __init__(self, **properties):
        """Creates a new Synapse properties object.
        """
        ConfigT.__init__(self, **properties)

    def create_between(self, src_seg, target_cell, target_seg, **custom_opts):
        return target_cell.add_synapse(src_seg, target_seg, self, **custom_opts)

    def get_synpase_conf(self):
        self.as_dict(excludes=self._netcon_fields)

    def get_netcon_conf(self):
        self.as_dict(subset=self._netcon_fields)


# ! The name of the specific Synapse Makers must match that of the Hoc class

class AlphaSynapse(SynapseMaker):
    onset = None    # ms
    tau  = None      # ms
    gmax = None     # umho


class ExpSyn(SynapseMaker):
    tau = None  # ms


class Exp2Syn(SynapseMaker):
    tau1 = None  # ms
    tau2 = None  # ms
