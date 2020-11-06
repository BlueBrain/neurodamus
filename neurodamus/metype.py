"""
Module which defines and handles METypes config (v5/v6 cells)
"""
from __future__ import absolute_import, print_function
import logging
from abc import abstractmethod
from os import path as ospath
from .core.configuration import SimConfig
from .core import NeurodamusCore as Nd


class METype(object):
    """
    Class representing an METype. Will instantiate a Hoc-level cell as well
    """
    morpho_extension = "asc"
    """The extension to be applied to morphology files"""

    __slots__ = ('_threshold_current', '_hypAmp_current', '_netcons', '_ccell', '_cellref',
                 '_synapses', '_syn_helper_list', '_emodel_name',
                 'exc_mini_frequency', 'inh_mini_frequency')

    def __init__(self, gid, etype_path, emodel, morpho_path, meinfos=None):
        """Instantite a new Cell from METype

        Args:
            gid: Cell gid
            etype_path: path for etypes
            emodel: Emodel name
            morpho_path: path for morphologies
            meinfos: dictionary with v6 infos (if v6 circuit)
        """
        self._threshold_current = None
        self._hypAmp_current = None
        self._netcons = []
        self._ccell = None
        self._cellref = None
        self._synapses = None
        self._syn_helper_list = None
        self._emodel_name = emodel
        self.exc_mini_frequency = None
        self.inh_mini_frequency = None

        self._instantiate_cell(gid, etype_path, emodel, morpho_path, meinfos)

    gid = property(lambda self: self._cellref.gid)

    # Ensure no METype instances created. Only Subclasses
    @abstractmethod
    def _instantiate_cell(self, *args):
        """Method which instantiates the cell in the simulator"""
        pass

    @property
    def synlist(self):
        return self._synapses

    # Named for compat with still existing HOC modules
    def getThreshold(self):
        return self._threshold_current

    def setThreshold(self, value):
        self._threshold_current = value

    def getHypAmp(self):
        if self._hypAmp_current is None:
            logging.warning("EModel %s doesnt define HypAmp current", self._emodel_name)
            return 0
        return self._hypAmp_current

    def setHypAmp(self, value):
        self._hypAmp_current = value

    @staticmethod
    def getVersion():
        return 3

    @property
    def CCell(self):
        return self._ccell

    @property
    def CellRef(self):
        return self._cellref

    def connect2target(self, target_pp=None):
        """ Connects MEtype cell to target

        Args:
            target_pp: target point process [default: None]

        Returns: NetCon obj
        """
        if SimConfig.spike_location == "soma":
            sec, seg = self.CellRef.soma[0], self.CellRef.soma[0](1)
        else:
            sec, seg = self.CellRef.axon[1], self.CellRef.axon[1](0.5)
        netcon = Nd.NetCon(seg._ref_v, target_pp, sec=sec)
        netcon.threshold = SimConfig.spike_threshold
        return netcon

    def re_init_rng(self, ion_seed, need_invoke):
        """Re-Init RNG for cell

        Args:
            ion_seed: ion channel seed
            need_invoke : True, invoke rng initialization (v6 circuits and beyond)
                          False, check if cell has re_init function (v5 and earlier)
        """
        if need_invoke:
            Nd.execute1("re_init_rng(%d)" % ion_seed, self._ccell, 0)
        else:
            rng_info = Nd.RNGSettings()
            if hasattr(self.CCell, "re_init_rng"):
                if rng_info.getRNGMode() == rng_info.RANDOM123:
                    Nd.rng123ForStochKvInit(self.CCell)
                else:
                    Nd.rngForStochKvInit(self.CCell)


class Cell_V6(METype):
    __slots__ = ()

    def __init__(self, gid, meinfo, circuit_conf):
        mepath = circuit_conf.METypePath
        morpho_path = circuit_conf.MorphologyPath
        super().__init__(gid, mepath, meinfo.emodel, morpho_path, meinfo)

    def _instantiate_cell(self, gid, etype_path, emodel, morpho_path, meinfos_v6):
        """Instantiates a SSCx v6 cell
        """
        Nd.load_hoc(ospath.join(etype_path, emodel))
        EModel = getattr(Nd, emodel)
        morpho_file = meinfos_v6.morph_name + "." + self.morpho_extension
        self._cellref = EModel(gid, morpho_path, morpho_file)
        self._ccell = self._cellref
        self._synapses = Nd.List()
        self._syn_helper_list = Nd.List()
        self._threshold_current = meinfos_v6.threshold_current
        self._hypAmp_current = meinfos_v6.holding_current
        self.exc_mini_frequency = meinfos_v6.exc_mini_frequency
        self.inh_mini_frequency = meinfos_v6.inh_mini_frequency


class Cell_V5(METype):
    __slots__ = ()

    def __init__(self, gid, meinfo, circuit_conf):
        # In NCS, meinfo is simply the metype filename (string)
        mepath = circuit_conf.METypePath
        morpho_path = circuit_conf.MorphologyPath
        melabel = self._load_template(meinfo, mepath)
        super().__init__(gid, mepath, melabel, morpho_path)

    def _instantiate_cell(self, gid, etype_path, emodel, morpho_path, meinfos):
        """Instantiates a cell v5 or older. Assumes emodel hoc templates are loaded
        """
        EModel = getattr(Nd, emodel)
        self._ccell = ccell = EModel(gid, morpho_path)
        self._cellref = ccell.CellRef
        self._synapses = ccell.CellRef.synlist
        self._syn_helper_list = ccell.CellRef.synHelperList
        self._threshold_current = ccell.getThreshold()
        try:
            self._hypAmp_current = ccell.getHypAmp()
        except Exception:
            pass

    @staticmethod
    def _load_template(tpl_filename, tpl_location=None):
        """Helper function which loads the template into NEURON and returns its name.
        The actual template name will have any hyphens (e.g.: R-C261296A-P1_repaired)
        replaced with underscores as hyphens must not appear in template names.

        Args:
            tpl_filename: the template file to load
            tpl_location: (Optional) path for the templates
        Returns:
            The name of the template as it appears inside the file (sans hyphens)
        """
        #  start.ncs gives metype names with hyphens, but the templates themselves
        #  have those hyphens replaced with underscores.
        tpl_path = ospath.join(tpl_location, tpl_filename) \
            if tpl_location else tpl_filename

        # first open the file manually to get the hoc template name
        tpl_name = None
        with open(tpl_path + ".hoc", "r") as templateReader:
            for line in templateReader:
                line = line.strip()
                if line.startswith("begintemplate"):
                    tpl_name = line.split()[1]
                    break
        Nd.load_hoc(tpl_path)
        return tpl_name


class EmptyCell(METype):
    """
    Class representing an empty cell, e.g. an artificial cell
    Workaround for the neuron issue https://github.com/neuronsimulator/nrn/issues/635
    """
    def __init__(self, gid, cell):
        self._cellref = cell
        self._ccell = None
        self.gid = gid

    def connect2target(self, target_pp):
        """ Connects empty cell to target
        """
        netcon = Nd.NetCon(self.CellRef, target_pp)
        return netcon


# Metadata
# --------

class METypeItem(object):
    """ Metadata about an METype, each possibly used by several cells.
    """
    __slots__ = ("morph_name", "layer", "fullmtype", "etype", "emodel", "combo_name",
                 "threshold_current", "holding_current",
                 "exc_mini_frequency", "inh_mini_frequency")

    def __init__(self, morph_name, layer=None, fullmtype=None, etype=None, emodel=None,
                 combo_name=None, threshold_current=0, holding_current=0,
                 exc_mini_frequency=0, inh_mini_frequency=0):
        self.morph_name = morph_name
        self.layer = layer
        self.fullmtype = fullmtype
        self.etype = etype
        self.emodel = emodel
        self.combo_name = combo_name
        self.threshold_current = float(threshold_current)
        self.holding_current = float(holding_current)
        self.exc_mini_frequency = float(exc_mini_frequency)
        self.inh_mini_frequency = float(inh_mini_frequency)


class METypeManager(dict):
    """ Map to hold specific METype info and provide retrieval by gid
    """

    def insert(self, gid, morph_name, *me_data, **kwargs):
        """Function to add an METypeItem to internal data structure
        """
        self[int(gid)] = METypeItem(morph_name, *me_data, **kwargs)

    def load_infoNP(self, gidvec, morph_list, emodels,
                    threshold_currents=None, holding_currents=None,
                    exc_mini_freqs=None, inh_mini_freqs=None):
        """Loads METype information in bulk from Numpy arrays
        """
        for idx, gid in enumerate(gidvec):
            th_current = threshold_currents[idx] if threshold_currents is not None else .0
            hd_current = holding_currents[idx] if holding_currents is not None else .0
            exc_mini_freq = exc_mini_freqs[idx] if exc_mini_freqs is not None else .0
            inh_mini_freq = inh_mini_freqs[idx] if inh_mini_freqs is not None else .0
            self[int(gid)] = METypeItem(morph_list[idx], emodel=emodels[idx],
                                        threshold_current=th_current,
                                        holding_current=hd_current,
                                        exc_mini_frequency=exc_mini_freq,
                                        inh_mini_frequency=inh_mini_freq)

    def retrieve_info(self, gid):
        return self.get(gid) \
            or logging.warning("No info for gid %d found.", gid)

    @property
    def gids(self):
        return self.keys()
