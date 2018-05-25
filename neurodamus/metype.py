from __future__ import absolute_import, print_function
from os import path
import logging
from collections import defaultdict
from . import Neuron
from .utils import ConfigT


class METype:
    # public init, printInfo, AddMorphNL, delete_axon,  getCell, biophys, hardcode_biophys, connect2target
    # public gid, CCell, CellRef, locateSite, locateSites, getLongestBranch, getThreshold, setThreshold, getHypAmp, setHypAmp
    # public synlist, synHelperList, ASCIIrpt, HDF5rpt, re_init_rng
    # objref this, CellRef, CCell, synlist, synHelperList, ASCIIrpt, HDF5rpt
    # public getVersion, connect2target

    def __init__(self, gid, etype_path, emodel, morpho_path, morpho_name=None):
        """
        Instantite a new Cell from METype
        Args:
            gid: Cell gid
            etype_path: path for etypes
            emodel: Emodel name
            morpho_path: path for morphologies
            morpho_file: morphology file (optional)
        """
        # local ret  localobj morphPath
        # strdef tstr
        h = Neuron.h
        self._thresholdCurrent = None
        self._hypAmpCurrent = None
        self._netcons = []

        if morpho_name is not None:
            # SSCx v6
            etype_mod = path.join(etype_path, emodel)
            rc = Neuron._load_mod(etype_mod)
            if rc == 0:
                raise ValueError("Unable to load METype file %s" % etype_mod + ".hoc")
            EModel = getattr(h, emodel)
            self.ccell = EModel(gid, path.join(morpho_path, "ascii"), morpho_name + ".asc")
            self.synlist = h.List()
            self.synHelperList = h.List()
        else:
            # Used by v5 and earlier
            EModel = getattr(h, emodel)
            self.ccell = ccell = EModel(gid, path.join(morpho_path, "ascii"))
            CellRef = ccell.CellRef
            self.synlist = CellRef.synlist
            self.synHelperList = CellRef.synHelperList
            self._thresholdCurrent = ccell.getThreshold()
            ret = h.execute1("{getHypAmp()}", ccell, 0)
            if ret != 0:
                self._hypAmpCurrent = ccell.getHypAmp()

    def getThreshold(self):
        return self._thresholdCurrent

    def setThreshold(self, value):
        self._thresholdCurrent = value

    def getHypAmp(self):
        return self._hypAmpCurrent

    def setHypAmp(self, value):
        self._hypAmpCurrent = value

    def getVersion(self):
        return 3

    @property
    def CellRef(self):
        return self.ccell.CellRef

    def connect2target(self, target_pp):
        """ Connects MEtype cell to target

        Args:
            target_pp: target point process

        Returns: NetCon obj
        """
        h = Neuron.h
        netcon = h.NetCon(self.CellRef.soma[0](1)._ref_v, target_pp, sec=self.CellRef.soma[0])
        netcon.threshold = -30
        self._netcons.append(netcon)
        return netcon

    def re_init_rng(self, _):
        Neuron.h.execute1( "re_init_rng()", self.ccell, 0)


class METypeItem(object):
    __slots__ = ("morph_name", "layer", "fullmtype", "etype", "emodel", "combo_name",
                 "threshold_current", "holding_current")

    def __init__(self, morph_name, layer, fullmtype, etype, emodel, combo_name,
                 threshold_current=0, holding_current=0):
        self.morph_name = morph_name
        self.layer = layer
        self.fullmtype = fullmtype
        self.etype = etype
        self.emodel = emodel
        self.combo_name = combo_name
        self.threshold_current = threshold_current
        self.holding_current = holding_current


class METypeManager(object):
    """ Class to read file with specific METype info and manage the containers for data retrieval
    """
    def __init__(self):
        self._me_map = {}

    def loadInfo(self, runInfo, gidvec, comboList, morphList):
        """ Read file with mecombo info, retaining only those that are local to this node
        Args:
            runInfo: Run info from config parse
            gidvec: gidvec local gids
            comboList: comboList Combos corresponding to local gids
            morphList: morphList Morpholgies corresponding to local gids
        """
        if not runInfo.exists("MEComboInfoFile"):
            logging.error("Missing BlueConfig field 'MEComboInfoFile' which has gid:mtype:emodel.")
            raise ValueError("MEComboInfoFile not specified")

        comboFile = runInfo.get("MEComboInfoFile").s
        f = open(comboFile)
        next(f)  # Skip Header

        # Optimization: index combos
        combo_ids = defaultdict(list)
        for i, c in enumerate(comboList):
            combo_ids[c].append(i)

        for tstr in f:
            vals = tstr.strip().split()
            if len(vals) not in (6, 8):
                wmsg = ("Could not parse line %s from MEComboInfoFile %s."
                        "Expecting 6 (hippocampus) or 8 (somatosensory) fields")
                logging.warning(wmsg, tstr, comboFile)
            meitem = METypeItem(*vals)

            for i in combo_ids[meitem.combo_name]:
                if morphList[i] == meitem.morph_name:
                    self._me_map[gidvec[i]] = meitem

        # confirm that all gids have been matched.
        # Otherwise, print combo + morph info to help find issues
        nerr = 0
        for gid in gidvec:
            if gid not in self._me_map:
                logging.error("MEComboInfoFile: No MEInfo for gid %d", gid)
                nerr += 1
        return -nerr

    def retrieveInfo(self, gid):
        return self._me_map.get(gid) \
               or logging.warning("No info for gid %d found.", gid)
