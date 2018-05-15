from __future__ import absolute_import
from os import path
from . import Neuron


class METype:
    # public init, printInfo, AddMorphNL, delete_axon,  getCell, biophys, hardcode_biophys, connect2target
    # public gid, CCell, CellRef, locateSite, locateSites, getLongestBranch, getThreshold, setThreshold, getHypAmp, setHypAmp
    # public synlist, synHelperList, ASCIIrpt, HDF5rpt, re_init_rng
    # objref this, CellRef, CCell, synlist, synHelperList, ASCIIrpt, HDF5rpt
    # public getVersion, connect2target

    def __init__(self, gid, etype_path, emodel, morpho_path, morpho_file=None):
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

        if morpho_file is not None:
            # SSCx v6
            etype_file = path.join(etype_path, emodel)
            h.load_file(etype_file)
            EModel = getattr(h, emodel)
            self.ccell = EModel(gid, path.join(morpho_path, "ascii"), morpho_file)
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
