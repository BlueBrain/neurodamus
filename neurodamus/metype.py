"""
Module which defines and handles METypes config (v5/v6 cells)
"""
from __future__ import absolute_import, print_function
import logging
from collections import defaultdict
from os import path as ospath
from .core.configuration import ConfigurationError
from .core import NeurodamusCore as Nd
from .utils.logging import log_verbose


class METype(object):
    """
    Class representing an METype. Will instantiate a Hoc-level cell as well
    """
    morpho_extension = "asc"
    """The extension to be applied to morphology files"""

    __slots__ = ('_threshold_current', '_hypAmp_current', '_netcons', '_ccell', '_cellref',
                 '_synapses', '_syn_helper_list', '_emodel_name')

    def __init__(self, gid, etype_path, emodel, morpho_path, meinfos_v6=None):
        """Instantite a new Cell from METype

        Args:
            gid: Cell gid
            etype_path: path for etypes
            emodel: Emodel name
            morpho_path: path for morphologies
            meinfos_v6: dictionary with v6 infos (if v6 circuit)
        """
        self._threshold_current = None
        self._hypAmp_current = None
        self._netcons = []
        self._ccell = None
        self._cellref = None
        self._synapses = None
        self._syn_helper_list = None
        self._emodel_name = emodel

        if meinfos_v6 is not None:
            self._instantiate_cell_v6(gid, etype_path, emodel, morpho_path, meinfos_v6)
        else:
            self._instantiate_cell_v5(gid, emodel, morpho_path)

    def _instantiate_cell_v6(self, gid, etype_path, emodel, morpho_path, meinfos_v6):
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

    def _instantiate_cell_v5(self, gid, emodel, morpho_path):
        """Instantiates a cell v5 or before. Asssumes emodel hoc templates are loaded
        """
        EModel = getattr(Nd, emodel)
        self._ccell = ccell = EModel(gid, morpho_path)
        self._cellref = ccell.CellRef
        self._synapses = ccell.CellRef.synlist
        self._syn_helper_list = ccell.CellRef.synHelperList
        self._threshold_current = ccell.getThreshold()
        try: self._hypAmp_current = ccell.getHypAmp()
        except Exception: pass

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

    def connect2target(self, target_pp):
        """ Connects MEtype cell to target

        Args:
            target_pp: target point process

        Returns: NetCon obj
        """
        netcon = Nd.NetCon(self.CellRef.soma[0](1)._ref_v, target_pp,
                           sec=self.CellRef.soma[0])
        netcon.threshold = -30
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


class METypeItem(object):
    __slots__ = ("morph_name", "layer", "fullmtype", "etype", "emodel", "combo_name",
                 "threshold_current", "holding_current")

    def __init__(self, morph_name, layer=None, fullmtype=None, etype=None, emodel=None,
                 combo_name=None, threshold_current=0, holding_current=0):
        self.morph_name = morph_name
        self.layer = layer
        self.fullmtype = fullmtype
        self.etype = etype
        self.emodel = emodel
        self.combo_name = combo_name
        self.threshold_current = float(threshold_current)
        self.holding_current = float(holding_current)


class METypeManager(dict):
    """ Class to read file with specific METype info and manage the containers for data retrieval
    """

    def load_info(self, run_conf, gidvec, combo_list, morph_list):
        """ Read file with mecombo info, retaining only those that are local to this node
        Args:
            run_conf: Run info from config parse
            gidvec: gidvec local gids
            combo_list: comboList Combos corresponding to local gids
            morph_list: morphList Morpholgies corresponding to local gids
        """
        combo_file = run_conf.get("MEComboInfoFile")
        if not combo_file:
            logging.error("Missing BlueConfig field 'MEComboInfoFile' which has gid:mtype:emodel.")
            raise ConfigurationError("MEComboInfoFile not specified")

        # Optimization: index combos
        combo_ids = defaultdict(list)
        for i, c in enumerate(combo_list):
            combo_ids[c].append(i)

        log_verbose("Loading emodel+additional info from Combo f %s", combo_file)
        f = open(combo_file)
        next(f)  # Skip Header

        for tstr in f:
            vals = tstr.strip().split()
            if len(vals) not in (6, 8):
                wmsg = ("Could not parse line %s from MEComboInfoFile %s."
                        "Expecting 6 (hippocampus) or 8 (somatosensory) fields")
                logging.warning(wmsg, tstr, combo_file)
            meitem = METypeItem(*vals)

            for i in combo_ids[meitem.combo_name]:
                if morph_list[i] == meitem.morph_name:
                    self[int(gidvec[i])] = meitem

        # confirm that all gids have been matched.
        # Otherwise, print combo + morph info to help find issues
        nerr = 0
        for gid in gidvec:
            gid = int(gid)
            if gid not in self:
                logging.error("MEComboInfoFile: No MEInfo for gid %d", gid)
                nerr += 1
        return -nerr

    def load_infoNP(self, gidvec, morph_list, emodels,
                    threshold_currents=None, holding_currents=None):
        for idx, gid in enumerate(gidvec):
            th_current = threshold_currents[idx] if threshold_currents is not None else 0
            hd_current = holding_currents[idx] if holding_currents is not None else 0
            self[int(gid)] = METypeItem(morph_list[idx], emodel=emodels[idx],
                                        threshold_current=th_current,
                                        holding_current=hd_current)

    def retrieve_info(self, gid):
        return self.get(gid) \
            or logging.warning("No info for gid %d found.", gid)

    @property
    def gids(self):
        return self.keys()
