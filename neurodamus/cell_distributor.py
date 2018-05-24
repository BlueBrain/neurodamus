"""
Handle assignment of cells to processors, instantiate cell objects and store locally and inself.pnm
"""
from __future__ import absolute_import, print_function
from collections import OrderedDict
import logging  # active only in rank 0 (init)
from array import array
from os import path
from . import Neuron
from .metype import METype, METypeManager
from .utils import progressbar

_h = None
h5 = None
def _ensure_h5py():
    global h5
    if not h5: import h5py as h5


class ArrayCompat(array):
    __slots__ = ()

    def size(self):
        return len(self)

    @property
    def x(self):
        return self


class CellDistributor(object):
    # -----------------------------------------------------------------------------------------------
    #  Member variables in HOC
    # -----------------------------------------------------------------------------------------------

    # objref: cellList, gidvec, spgidvec, gid2meobj, gid2metype, gid2mefile, binfo, pnm, load_balance_, nilSecRef
    # objref: tmpCell, this

    # public: completeCellCount, cellCount, pnm, cellList
    # public: msfactor, nilSecRef, delayedSplit, useMVD3
    # public: globalSeed, ionchannelSeed
    # //---------------------------------------------------------------------------------------------

    # NCS_T = namedtuple("NCS_T", ("gid", "metype", "conn_count", "nrn_file", "morpho_name"))
    # NCS_T.__new__.__defaults__ = (None,) * 5

    def __init__(self, configParser, targetParser, pnm):
        """Constructor for CellDistributor object, takes information loaded from start.ncs to know what cells
        are available in the circuit and a flag to indicate the state if LoadBalancing.

        Params:
            configParser: config parser object
            targetParser: in case there is a circuit target
            pnm:  The parallel node manager (to know rank and nNodes)

        Returns: gidvec and metypes
        """
        # local: isVerbose, timeID_load, timeID_create, libraryCellCount, cellIndex
        # localobj: circuitTarget, mePath, templatePath, cxPath, runMode, rngInfo, morphPath, nil, melabel, meInfoItem, parsedRun
        global _h
        _h = Neuron.h
        self.configParser = configParser
        self.targetParser = targetParser
        self.pnm = pnm
        self.nhost = int(self.pnm.nhost)
        self.rank = int(self.pnm.myid)

        self._load_balance = None
        self.lbFlag = False
        self.gidvec = None
        self.gid2metype = None
        self.gid2mefile = None  # for NCS
        self.meinfo = None      # for MVD3
        self.cellCount = 0
        self.completeCellCount = -1  # may be filled in by CircuitTarget or cell library file
        self.useMVD3 = False

        # finalize will require a placeholder object for calling connect2target
        if not hasattr(_h, "nc_"):
            _h("objref nc_")
            _h("strdef tstr_")

        globalSeed = 0
        ionchannelSeed = 0
        msfactor = 0.8
        parsedRun = configParser.parsedRun
        morphPath = parsedRun.get("MorphologyPath").s

        # for testing if xopen bcast is in use (NEURON 7.3).
        # We will be loading different templates on different cpus, so it must be disabled at this point
        _h("xopen_broadcast_ = 0")

        # determine if we should get metype info from start.ncs (current default) or circuit.mvd3 (pending)
        if parsedRun.exists("CellLibraryFile"):
            cellLibFile = parsedRun.get("CellLibraryFile").s
            if cellLibFile == "circuit.mvd3":
                logging.info("Reading gid:METype info from circuit.mvd3")
                self.useMVD3 = True
                _ensure_h5py()
            elif cellLibFile != "start.ncs":
                logging.error("Invalid CellLibraryFile %s. Terminating", cellLibFile)
                raise ValueError("Invalid CellLibFile {}".format(cellLibFile))
        # Default
        if not self.useMVD3:
            logging.info("Reading gid:METype info from start.ncs")

        #  are we using load balancing? If yes, init structs accordingly
        if parsedRun.exists("RunMode") and parsedRun.get("RunMode").s in ("LoadBalance", "WholeCell"):
            self.lbFlag = True
        if self.lbFlag:
            # read the cx_* files to build the gidvec
            cxPath = "cx_%d" % self.nhost
            if parsedRun.exists("CWD"):  #  TODO: is checking CWD useful?
                # Should we allow for another path to facilitate reusing cx* files?
                cxPath = path.join(parsedRun.get("CWD").s, cxPath)

            # self.binfo reads the files that have the predistributed cells (and pieces)
            self.binfo = _h.BalanceInfo(cxPath, self.rank, self.nhost)

            # self.binfo has gidlist, but gids can appear multiple times
            self.gidvec = ArrayCompat("I")
            _seen = set()
            for gid in self.binfo.gids:
                gid = int(gid)
                if gid not in _seen:
                    self.gidvec.append(gid)
                    _seen.add(gid)

            self.spgidvec = _h.Vector()

            # TODO: do we have any way of knowing that a CircuitTarget found definitively matches the cells in the balance files?
            #  for now, assume the user is being honest
            if parsedRun.exists("CircuitTarget"):
                circuitTarget = targetParser.getTarget(parsedRun.get("CircuitTarget").s)
                self.completeCellCount = int(circuitTarget.completegids().size())

        elif parsedRun.exists("CircuitTarget"):
            # circuit target, so distribute those cells that are members in round-robin style
            circuitTarget = targetParser.getTarget(parsedRun.get("CircuitTarget").s)
            self.completeCellCount = int(circuitTarget.completegids().size())
            self.gidvec = ArrayCompat("I")

            c_gids = circuitTarget.completegids()
            for i, gid in enumerate(c_gids):
                gid = int(gid)
                if i % self.nhost == self.rank:
                    self.gidvec.append(gid)
        # else:
        #   if no circuitTarget, distribute all the cells round robin style; readNCS handles this further down

        #  Determine metype; apply round-robin assignment if necessary
        if self.useMVD3:  # {
            # loadMVD3 will set completeCellCount if things assigned RR (gidvec not inited)
            self.gidvec, self.meinfo = self.loadMVD3(configParser, self.gidvec)
            logging.info("done loading mvd3 and all mecombo info")
        else:
            self.gidvec, self.gid2mefile = self.loadNCS(parsedRun.get("nrnPath").s, self.gidvec)
            self.gid2metype = {}

        self.pnm.ncell = self.completeCellCount
        logging.info("Done gid assignment: %d cells in network, %d cells in rank 0",
                     self.completeCellCount, len(self.gidvec))

        self.cellList = []
        self.gid2meobj = {}

        mePath = configParser.parsedRun.get("METypePath").s

        logging.info("Loading cells...")
        pbar = progressbar.AnimatedProgressBar(end=len(self.gidvec), width=80)

        for gid in self.gidvec:
            pbar.show_progress()
            if self.useMVD3:
                meInfoItem = self.meinfo.retrieveInfo(gid)
                tmpCell = METype(gid, mePath, meInfoItem.emodel.s, morphPath, meInfoItem.morph_name.s)
                tmpCell.setThreshold(meInfoItem.threshold_current)
                tmpCell.setHypAmp(meInfoItem.holding_current)
            else:
                melabel = self.gid2metype[gid] = self.loadTemplate(self.gid2mefile[gid], mePath)
                tmpCell = METype(gid, mePath, melabel, morphPath)

            self.cellList.append(tmpCell)
            self.gid2meobj[gid] = tmpCell
            self.pnm.cells.append(tmpCell.CellRef)
            pbar + 1
        print("\r", end=" "*88 + "\r")

        # can I create a dummy section, reference it, then delte it to keep a null SectionRef for insertion into pointlists?
        # TODO: Check this PY
        # access dummy
        # nilSecRef = new SectionRef()
        # delete_section()

    #
    def loadNCS(self, nrnPath, gidvec=None):
        """ Load start.ncs getting the gids and the metypes for all cells in the base circuit
        (note that we may simulate less if there is a circuit target present in the blue config file)

        Returns: A tuple of gids and the metypes
        """
        # local useRR, cellCount, gid, nErrors  localobj ncsIn, bvec, strUtil, mePath
        ncsFile = path.join(nrnPath, "start.ncs")
        ncsIn = open(ncsFile, "r")
        reassign_RR = gidvec is None
        gid2mefile = OrderedDict()

        # first lines might be comments.  Check for leading '#' (TODO: more robust parsing)
        tstr = ncsIn.readline().strip()
        while tstr.startswith("#"):
            tstr = ncsIn.readline().strip()

        try:
            # should have "Cells x"
            cellCount = int(tstr.split()[1])
        except:
            raise ValueError("NCS file contains invalid config: " + tstr)

        logging.info("read {} cells from start.ncs".format(cellCount))

        def get_next_cell(f):
            for cell_i, line in enumerate(f):
                line = line.strip()
                if line == "}":
                    break
                parts = line.split()
                assert len(parts) >= 5, "Error in ncs line " + line
                gid = int(parts[0][1:])
                metype = parts[4]
                yield cell_i, gid, metype

        ncsIn.readline()  # skip the '{'

        if reassign_RR:
            gidvec = ArrayCompat("I")
            for cellIndex, gid, metype in get_next_cell(ncsIn):
                if cellIndex % self.nhost == self.rank:
                    gidvec.append(gid)
                    gid2mefile[gid] = metype
        else:
            gidvec = self.gidvec
            for gid in gidvec:
                gid2mefile[gid] = None  # Same order as vec
            for cellIndex, gid, metype in get_next_cell(ncsIn):
                if gid in gid2mefile:
                    gid2mefile[gid] = metype

        ncsIn.close()
        return gidvec, gid2mefile

    #
    def loadMVD3(self, configParser, gidvec=None):
        """ Loads cells from MVD3
        For circuits v6, start.ncs will no longer have sufficient metype information.  Use circuit.mvd3
        """
        import numpy as np
        # local res, incr, cellIndex, ncells, typeIndex, ntypes, mtypeMax, etypeMax, useRR
        # localobj configParser, morphList, comboList
        pth = path.join(configParser.parsedRun.get("CircuitPath").s, "circuit.mvd3")
        mvdReader = _h.HDF5Reader(pth)
        mvdFile = h5.File(pth)
        reassign_RR = gidvec is None

        if reassign_RR:
            # mvdReader.getDimensions("/cells/properties/me_combo")
            # ncells = mvdReader.numberofrows("/cells/properties/me_combo")
            # print("HOC ncells: %d" % ncells)
            mecombo_ds = mvdFile["/cells/properties/me_combo"]
            ncells = len(mecombo_ds)
            print("PYTHON ncells: %d" % len(mecombo_ds))
            
            self.completeCellCount = ncells
            incr = self.nhost
            gidvec = ArrayCompat("I")

            #  the circuit.mvd3 uses intrinsic gids starting from 1; this might change in the future
            cellIndex = self.rank
            while cellIndex < ncells:
                gidvec.append(cellIndex+1)
                cellIndex += incr
        else:
            gidvec = self.gidvec

        indexes = ArrayCompat("i", np.frombuffer(gidvec, dtype="i4") - 1)
        morphIDVec = mvdFile["/cells/properties/morphology"][indexes]
        comboIDVec = mvdFile["/cells/properties/me_combo"][indexes]

        morpho_ds = mvdFile["/library/morphology"]
        morphList = [str(morpho_ds[i]) for i in morphIDVec]

        combo_ds = mvdFile["/library/me_combo"]
        comboList = [str(combo_ds[i]) for i in comboIDVec]

        # now we can open the combo file and get the emodel + additional info
        meinfo = METypeManager()
        if self.rank == 0:
            meinfo.verbose = 1

        res = meinfo.loadInfo(configParser.parsedRun, gidvec, comboList, morphList)

        if self.nhost > 1:
            res = self.pnm.pc.allreduce(res, 1)

        if res < 0:
            if self.rank == 0:
                logging.error("errors while processing mecombo file. Terminating")
                raise RuntimeError("Could not process mecombo file. Error {}".format(res))
            self.pnm.pc.barrier()

        return gidvec, meinfo

    @staticmethod
    def loadTemplate(tpl_name, tpl_location=None):
        """Helper function which loads the template into NEURON and returns the name of the template.  The
        template name will be slightly different from the file name because the file name contains hyphens
        from the morphology instance (e.g. R-C261296A-P1_repaired) but hyphens must not appear in template names.
        The actual template name will have any hyphens replaced with underscores.

        Params:
            tpl_name: the template file to load
            tpl_location: (Optional) path for the templates

        Returns: The name of the template as it appears inside the file (sans hyphens)
        """
        # local scanCount  localobj templatePath, templateReader, templateLine, templateName

        #  start.ncs gives metype names with hyphens, but the templates themselves
        #  have those hyphens replaced with underscores.
        tpl_file = tpl_name
        if tpl_location is not None:
            tpl_file = path.join(tpl_location, tpl_name + ".hoc")

        # first open the file manually to get the template name
        templateName = None
        with open(tpl_file, "r") as templateReader:
            for l in templateReader:
                l = l.strip()
                if l.startswith("begintemplate"):
                    templateName = l.split()[1]
                    break

        _h.load_file(tpl_file)
        return templateName

    def getMEType(self, gid):
        return self.gid2meobj.get(gid)

    def getMETypeFromGid(self, gid):
        """ Provide the name of the metype which corresponds to a gid \n
        Returns: String with the metype or None
        """
        return self.gid2metype.get(gid)

    def getMEFileFromGid(self, gid):
        """Provide the file name of the metype which corresponds to a gid
        (thise may differ from metype due to special character replacement)

        Returns: String with the mefile or nil
        """
        return self.gid2mefile.get(gid)

    def getGidListForProcessor(self):
        """Get list containing the gids on this cpu.  Note that these gids may be virtual gids.
        If real gids are required, each value in the list should be passed through the getGid() func.
        """
        return self.gidvec

    def getCell(self, gid):
        """Retrieve a cell object given its gid.
        Note that this function handles multisplit cases incl converting to an spgid automatically
        Returns: Cell object
        """
        # are we in load balance mode? must replace gid with spgid
        if self.lbFlag:
            gid = self.binfo.thishost_gid(gid)
        return self.pnm.pc.gid2obj(gid)

    def getSpGid(self, gid):
        """Retrieve the spgid from a gid (provided we are using loadbalancing)

        Args:
            gid: The base gid (as read from start.ncs)

        Returns: The gid as it appears on this cpu (if this is the same as the base gid, then that is the soma piece)
        """
        if self.lbFlag:
            return self.binfo.thishost_gid(gid)
        else:
            return gid

    def printLBInfo(self, lb_obj, nhost):
        """Calculate cell complexity and write data to file
        Params:
            lb_obj: loadbal neuron object
            nhost: Number of hosts to compute for load balancing
        """
        self._load_balance = lb_obj
        self.printMSloadBalance("cx", nhost)

    def __iter__(self):
        """Iterator over this node GIDs"""
        for gid in self.gidvec:
            yield gid

    def cell_complexity(self, with_total=True):
        # local i, gid, ncell  localobj cx_cell, id_cell
        cx_cell = ArrayCompat("f")
        id_cell = ArrayCompat("I")
        ncell = self.gidvec.size()

        for gid in self.gidvec:
            id_cell.append(gid)
            cx_cell.append(self._load_balance.cell_complexity(self.pnm.pc.gid2cell(gid)))

        if with_total:
            ncell = self.pnm.pc.allreduce(ncell, 1)
            return cx_cell, id_cell, ncell
        else:
            return cx_cell, id_cell

    def getTotal_MaxMSCellcomplexity(self, ):
        """
        Returns: Tuple of (TotalComplexity, max_complexity)
        """
        cx_cells, id_cells = self.cell_complexity(with_total=False)
        local_max = max(cx_cells)
        local_sum = sum(cx_cells)

        global_total = self.pnm.pc.allreduce(local_sum, 1)
        global_max = self.pnm.pc.allreduce(local_max, 1)
        return global_total, global_max

    def getOptimalMSPieceComplexity(self, total_cx, max_cx, nhost):
        #  $1 Total complexity
        #  $2 Maximum cell complexity
        #  $3 Prospective no of hosts
        lps = total_cx/nhost * self.msfactor
        return int(lps+1)

    def cpuAssign(self, prospectiveHosts):
        """
        @param prospectiveHosts: How many cpus we want running with our LoadBalanced circuit
        """
        _h.mymetis3("cx_%d" % prospectiveHosts, prospectiveHosts)

    def printMSloadBalance(self, filename, prospectiveHosts):
        # local lTC, lMC, lcx, i, j, k, gid, prospectiveHosts  localobj  msList, ms, b, fp, str
        if prospectiveHosts > 0:
            total_cx, max_cx = self.getTotal_MaxMSCellcomplexity()
            lcx = self.getOptimalMSPieceComplexity(total_cx, max_cx, prospectiveHosts)
            # print_load_balance_info(3, lcx, $s1)
            filename = "%s_%d.dat" % (filename, prospectiveHosts)
        else:
            total_cx, max_cx = None, None
            lcx = 1e9
            filename += ".dat"

        msList = _h.List()
        ms   = _h.Vector()
        b = self._load_balance

        for i, gid in enumerate(self):
            # what should be passed into this func? the base cell?  the CCell?
            b.cell_complexity(self.pnm.cells.object(i))
            b.multisplit(gid, lcx, ms)
            msList.append(ms.c())

        if self.rank ==0:
            fp = open(filename, "w")
            fp.write("1\n%d\n" % self.pnm.ncell)
            fp.close()
            logging.info("LB Info : TC=%.3f MC=%.3f OptimalCx=%.3f FileName=%s" % (total_cx, max_cx, lcx, filename))

        for j in range(self.nhost):
            if j == self.rank:
                with open(filename, "a") as fp:
                    for ms in msList:
                        self.pmsdat(fp, ms)
            self.pnm.pc.barrier()

        # now assign to the various cpus - but only the one cpu needs to do the assignment, so use node 0
        if self.rank == 0:
            self.cpuAssign(prospectiveHosts)
        self.pnm.pc.barrier()

    #  File, dataVec, gid
    def pmsdat(self, fp, ms):  # {local i, i1, n1, i2, n2, i3, n3, id, cx, tcx
        tcx = 0
        fp.write("%d" % ms.x[0])  # gid
        fp.write(" %g" % ms.x[1])  # total complexity of cell
        n1 = ms.x[2]
        i = 2
        fp.write(" %d\n" % n1)  # number of pieces
        for i1 in range(int(n1)):
            i += 1
            n2 = ms.x[i]  # at number of subtrees
            fp.write("  %d\n" % n2)  # number of subtrees
            for i2 in range(int(n2)):
                i += 1
                cx = ms.x[i]  # at subtree complexity
                tcx += cx
                i += 1
                n3 = ms.x[i]  # at number of children in a subtree
                fp.write("   %g %d\n" % (cx, n3))  # subtree complexity
                if n3 > 0:
                    fp.write("    ")
                for i3 in range(n3):
                    i += 1
                    id = ms.x[i] #  at next child
                    fp.write(" %d" % id)
                if n3 > 0:
                    fp.write("\n")

            #printf("gid=%d cell complexity = %g  sum of pieces = %g\n", \
            #    $o2.x[0], $o2.x[1], tcx)

    def rngForStochKvInit(self, ccell):
        """In place of using a CCell's re_init_rng function, we will check for cells that define the re_init_rng function,
        but then setRNG using global seed as well
        @param $o1 CCell which is to be checked for setRNG
        """
        #local channelID, hasStochKv  localobj CCell, rng, rngInfo
        # print "Replace rng for stochKv in gid ", CCell.CellRef.gid

        #  quick check to verify this object contains StochKv
        hasStochKv = _h.ismembrane("StochKv", sec=ccell.CellRef.soma)
        if not hasStochKv:
            return

    def finalize(self, cellList):
        """Do final steps to setup the network.  For example, multisplit will handle gids depending on additional info
        from self.binfo object.  Otherwise, normal cells do their finalization
        Args:
            cellList: List containing all CCells
        """
        # local cellIndex, ic, gid, spgid, ret, version  localobj cell, metype, cb, nc, nil, rngInfo

        # First, we need each section of a cell to assign its index value to the voltage field (crazy, huh?)
        # at this moment, this is used later during synapse creation so that sections can be serialized
        # into a single array for random acess.
        rngInfo = _h.RNGSettings()
        globalSeed = rngInfo.getGlobalSeed()
        ionchannelSeed = rngInfo.getIonChannelSeed()

        for i, gid in enumerate(self.gidvec):
            metype = self.cellList[i]

            #  for v6 and beyond - we can just try to invoke rng initialization
            if self.useMVD3 or rngInfo.getRNGMode() == rngInfo.COMPATIBILITY:
                metype.re_init_rng(ionchannelSeed)
            else:
                # for v5 circuits and earlier
                # check if cell has re_init function.  Instantiate random123 or mcellran4 as appropriate
                # Note: should CellDist be aware that metype has CCell member?
                ret = _h.name_declared("re_init_rng", 1, c=metype.CCell)

                if ret:
                    if rngInfo.getRNGMode() == rngInfo.RANDOM123:
                        _h.rng123ForStochKvInit(metype.CCell)
                    else:
                        if metype.gid > 400000:
                            logging.warning("Warning: mcellran4 cannot initialize properly with large gids")
                        _h.rngForStochKvInit(metype.CCell)

            # TODO: CCell backwards compatibility
            # if we drop support for older versions, then we can just use cell.CCellRef.connect2target(nil, nc)
            # without the complexity of checking if a getVersion func exists, what is that version, etc.
            version = metype.getVersion()
            if version < 2:
                nc = _h.nc_
                metype.CellRef.connect2target(_h.nil, nc)
            else:
                nc = metype.connect2target(_h.nil)

            if self.lbFlag:
                ic = int(self.binfo.gids.indwhere("==", gid))
                cb = self.binfo.bilist.object(self.binfo.cbindex.x[ic])

                if cb.subtrees.count() == 0:
                    #  whole cell, normal creation
                    self.pnm.set_gid2node(gid, self.rank)
                    self.pnm.pc.cell(gid, nc)
                    self.spgidvec.append(gid)
                else:
                    spgid = cb.multisplit(nc, self.binfo.msgid, self.pnm.pc, self.rank)
                    self.spgidvec.append(spgid)

            else:
                self.pnm.set_gid2node(gid, self.pnm.myid)
                self.pnm.pc.cell(gid, nc)

        # TODO: on bbplinsrv, calling pc.multisplit function now causes problem, but if it is called in a separate
        #  function after return, then it is fine.  Maybe contact Michael for advice?  Works fine leaving
        #  the call here on bluegene
        if self.lbFlag:
            "self.pnm.pc.multisplit()"

    def delayedSplit(self):
        if self.lbFlag:
            self.pnm.pc.multisplit()
