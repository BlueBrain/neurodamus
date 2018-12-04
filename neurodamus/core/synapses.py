"""
High-Level wrapper to Neuron's cell synapse mechanisms
"""
from ..utils import ConfigT
from . import Neuron


# -------------------------
# Synapse (receptor) config
# -------------------------

class _SynapseReceptor(ConfigT):
    """A synapse configuration. Can then be instantiated among several pre-post pairs
    """
    e = None    # mV
    i = None    # nA

    def __new__(cls, segment=None, **properties):
        if cls is _SynapseReceptor:
            raise TypeError("Can't instantiate an abstract Synapse. Use a specific type instead")
        if segment is not None:
            segment = segment(0.5) if isinstance(segment, Neuron.Section) else segment
            syn = getattr(Neuron.h, cls.__name__)(segment)
            [setattr(syn, key, val) for key, val in properties.items()]
            return syn
        return object.__new__(cls)

    def create_on(self, *segments):
        return [self.__class__(seg, **self.as_dict()) for seg in segments]


# Specific Synapse Types
# NOTE: The name of the specific Synapse Makers must match that of the Hoc class

class AlphaSynapse(_SynapseReceptor):
    onset = None    # ms
    tau  = None     # ms
    gmax = None     # umho


class ExpSyn(_SynapseReceptor):
    tau = None  # ms


class Exp2Syn(_SynapseReceptor):
    tau1 = None  # ms
    tau2 = None  # ms


# ----------------------------------
# Synapse sources (Spike generators)
# ----------------------------------

class _SpikeSource(object):
    def connect_to(self, synapse_receptor, weights=None, threshold=None, delay=None):
        """Creates a synapse connection"""
        raise NotImplementedError()

    @staticmethod
    def _setup_netcon(netcon, weight=None, **props):
        for key, val in props.items():
            if val is not None and key in ["threshold", "delay"]:
                setattr(netcon, key, val)
        if isinstance(weight, dict):
            for idx, val in weight.items():
                netcon.weight[idx] = val
        else:
            netcon.weight[0] = weight
        return netcon


class VirtualSpikeSource(ConfigT, _SpikeSource):
    """
    Uses Neuron NetStim to create an artificial spike source
    """
    interval = None     # ms (mean) time between spikes
    number = None       # number of spikes
    start = None        # ms (most likely) start time of first spike
    noise = None        # range 0 to 1. Fractional randomness. (negexp distribution)

    def __init__(self, interval=None, number=None, start=None, noise=None, manage_objs=True):
        """ Creates an artificial spike generator
        Args:
            manage_objs: NetCon and Synapse receptors are stored internally to avoid
                garbage-collection at the expense of some extra memory [default: True]
        """
        self._netstim = Neuron.h.NetStim()
        ConfigT.__init__(self, **{"interval": interval, "number": number,
                                  "start": start, "noise": noise})
        self.apply(self._netstim)
        self._managed_objs = manage_objs
        self._objs = []

    def connect_to(self, synapse_receptor, weight=None, threshold=None, delay=None):
        netcon = Neuron.h.NetCon(self._netstim, synapse_receptor)
        self._setup_netcon(netcon, weight, threshold=threshold, delay=delay)
        self._objs.append((netcon, synapse_receptor))
        return netcon


# Alias
NetStim = VirtualSpikeSource


# -------------------------------------
# Full config of a synapse
# -------------------------------------
class CellSynapse(_SpikeSource, _SynapseReceptor):
    _netcon_fields = ("threshold", "delay", "weight")

    def get_synpase_conf(self):
        self.as_dict(excludes=self._netcon_fields)

    def get_netcon_conf(self):
        self.as_dict(subset=self._netcon_fields)
