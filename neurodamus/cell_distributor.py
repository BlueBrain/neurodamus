from __future__ import absolute_import, print_function
from collections import OrderedDict
import logging  # active only in rank 0 (init)
from os import path
import numpy as np
from .core import MPI, mpi_no_errors
from .core import NeuronDamus as Nd
from .core.configuration import ConfigurationError
from .core import ProgressBarRank0 as ProgressBar
from .metype import METype, METypeManager
from .utils import compat
from .utils.logging import log_verbose


class CellDistributor(object):
    """Handle assignment of cells to processors, instantiate and store them (locally and in _pnm)
    """

    def __init__(self, config_parser, target_parser, pnm):
        """Initializes CellDistributor obj and runs distribution from start.ncs or mvd3.
        Depending on the Config file, might apply LoadBalancing.

        Params:
            config_parser: config parser object
            target_parser: in case there is a circuit target
            pnm: The parallel node manager (to know rank and nNodes)

        Returns: gidvec and metypes

        """
        self._pnm = pnm
        self._load_balance = None
        self._lb_flag = False
        # These structs are None to mark as un-init'ed
        self._gidvec = None
        self._total_cells = None
        # These wont ever be init'ed if not using lb
        self._spgidvec = None
        self._binfo = None
        self._useMVD3 = False
        self._global_seed = 0
        self._ionchannel_seed = 0

        self._cell_list = []
        self._gid2meobj = {}
        self._gid2metype = {}

        # Public
        self.msfactor = 0.8

        if not hasattr(Nd, "nc_"):
            Nd.execute("objref nc_")

        self._setup(config_parser.parsedRun, target_parser)

    @property
    def pnm(self):
        return self._pnm

    @property
    def cell_list(self):
        return self._cell_list

    # -
    def _setup(self, run_conf, target_parser):
        logging.info("Distributing circuit cells by available CPUs")
        morpho_path = run_conf.get("MorphologyPath").s

        # for testing if xopen bcast is in use (NEURON 7.3).
        # We will be loading different templates on different cpus, so it must be disabled for now
        Nd.execute("xopen_broadcast_ = 0")

        # determine if we should get metype info from start.ncs (current default) or circuit.mvd3
        if run_conf.exists("CellLibraryFile"):
            celldb_filename = run_conf.get("CellLibraryFile").s
            if celldb_filename == "circuit.mvd3":
                log_verbose("Reading [gid:METype] info from circuit.mvd3")
                self._useMVD3 = True

            elif celldb_filename != "start.ncs":
                logging.error("Invalid CellLibraryFile %s. Terminating", celldb_filename)
                raise ConfigurationError("Invalid CellLibraryFile {}".format(celldb_filename))
        # Default
        if not self._useMVD3:
            log_verbose("Reading [gid:METype] info from start.ncs")

        gidvec = None       # Gids handled by this cpu
        total_cells = None  # total cells in this simulation (can be a subset, e.g.: target)

        #  are we using load balancing? If yes, init structs accordingly
        if run_conf.exists("RunMode") \
                and run_conf.get("RunMode").s in ("LoadBalance", "WholeCell"):
            log_verbose("Distributing cells according to load-balance")
            self._lb_flag = True
            self._spgidvec = compat.Vector("I")
            gidvec = compat.Vector("I")

            # read the cx_* files to build the gidvec
            cx_path = "cx_%d" % MPI.cpu_count
            if run_conf.exists("CWD"):
                # Should we allow for another path to facilitate reusing cx* files?
                cx_path = path.join(run_conf.get("CWD").s, cx_path)

            # self.binfo reads the files that have the predistributed cells (and pieces)
            self._binfo = Nd.BalanceInfo(cx_path, MPI.rank, MPI.cpu_count)

            # self.binfo has gidlist, but gids can appear multiple times
            _seen = set()
            for gid in self._binfo.gids:
                gid = int(gid)
                if gid not in _seen:
                    gidvec.append(gid)
                    _seen.add(gid)

            # TODO: do we have any way of knowing that a CircuitTarget found definitively matches
            #       the cells in the balance files? for now, assume the user is being honest
            if run_conf.exists("CircuitTarget"):
                target = target_parser.getTarget(run_conf.get("CircuitTarget").s)
                total_cells = int(target.completegids().size())
            else:
                total_cells = len(gidvec)

        elif run_conf.exists("CircuitTarget"):
            log_verbose("Distributing target circuit cells round-robin")
            target = target_parser.getTarget(run_conf.get("CircuitTarget").s)
            gidvec = compat.Vector("I")
            _target_gids = target.completegids()
            total_cells = int(_target_gids.size())

            for i, gid in enumerate(_target_gids):
                if i % MPI.cpu_count == MPI.rank:
                    gidvec.append(int(gid))
        else:
            # Otherwise distribute all the cells round robin style. readNCS / readMVD3 handle this
            log_verbose("Distributing all cells round-robin")

        # Determine metype; apply round-robin assignment if necessary
        if self._useMVD3:
            self._total_cells, self._gidvec, me_infos = self._load_mvd3(
                run_conf, total_cells, gidvec)
        else:
            self._total_cells, self._gidvec, me_infos = self._load_ncs(
                run_conf, total_cells, gidvec)

        log_verbose("Done gid assignment: %d cells in network, %d in rank 0",
                    self._total_cells, len(self._gidvec))

        self._pnm.ncell = self._total_cells
        mepath = run_conf.get("METypePath").s
        logging.info("Instantiating cells...")
        total_created_cells = 0

        for gid in ProgressBar.iter(self._gidvec):
            if self._useMVD3:
                meinfo_v6 = me_infos.retrieve_info(gid)
                melabel = meinfo_v6.emodel
                cell = METype(gid, mepath, melabel, morpho_path, meinfo_v6)
            else:
                # In NCS, me_infos is a plain map from gid to me_file
                melabel = self._load_template(me_infos[gid], mepath)
                cell = METype(gid, mepath, melabel, morpho_path)

            self._gid2metype[gid] = melabel
            self._cell_list.append(cell)
            self._gid2meobj[gid] = cell
            self._pnm.cells.append(cell.CellRef)
            total_created_cells += 1

        global_cells_created = MPI.allreduce(total_created_cells, MPI.SUM)
        logging.info(" => Created %d cells (%d in rank 0)",
                     global_cells_created, total_created_cells)

    # -
    @staticmethod
    def _load_ncs(run_conf, total_cells, gidvec):
        """ Load start.ncs getting the gids and the metypes for all cells in the base circuit
        (note that we may simulate less if there is a circuit target in the BlueConfig file)

        Returns: A tuple of (gids and the metypes
        """
        ncs = open(path.join(run_conf.get("nrnPath").s, "start.ncs"), "r")
        gid2mefile = OrderedDict()

        # first lines might be comments. Skip '#'
        tstr = ncs.readline().strip()
        while tstr.startswith("#"):
            tstr = ncs.readline().strip()

        try:
            # should have "Cells x"
            total_circuit_cells = int(tstr.split()[1])
        except IndexError:
            raise ConfigurationError("NCS file contains invalid config: " + tstr)

        if total_cells is None:
            log_verbose("Using all %d cells from NCS file", total_circuit_cells)
            total_cells = total_circuit_cells
        else:
            log_verbose("Reading %d target cells out of %d from NCS file",
                        total_cells, total_circuit_cells)

        def get_next_cell(f):
            for cell_i, line in enumerate(f):
                line = line.strip()
                if line == "}":
                    break
                parts = line.split()
                assert len(parts) >= 5, "Error in ncs line " + line
                _gid = int(parts[0][1:])
                metype = parts[4]
                yield cell_i, _gid, metype

        ncs.readline()  # skip the '{'

        if gidvec is None:
            # Reassign Round-Robin
            gidvec = compat.Vector("I")
            for cellIndex, gid, metype in get_next_cell(ncs):
                if cellIndex % MPI.cpu_count == MPI.rank:
                    gidvec.append(gid)
                    gid2mefile[gid] = metype
        else:
            for gid in gidvec:
                gid2mefile[gid] = None  # Same order as vec
            for cellIndex, gid, metype in get_next_cell(ncs):
                if gid in gid2mefile:
                    gid2mefile[gid] = metype

        ncs.close()
        return total_cells, gidvec, gid2mefile

    # -
    @staticmethod
    @mpi_no_errors
    def _load_mvd3(run_conf, total_cells, gidvec):
        """Load cells from MVD3, required for v6 circuits
        """
        import h5py  # Can be heavy so loaded on demand
        pth = path.join(run_conf.get("CircuitPath").s, "circuit.mvd3")
        mvd = h5py.File(pth, 'r')

        # Gidvec must be ordered. we change to numpy
        if gidvec is not None:
            gidvec = np.frombuffer(gidvec, dtype="uint32")
            gidvec.sort()
            log_verbose("Reading %d target cells from MVD file", len(gidvec))
        else:
            # Reassign Round-Robin if not gidvec, and set total_cells
            mecombo_ds = mvd["/cells/properties/me_combo"]
            total_cells = len(mecombo_ds)
            log_verbose("Reading all %d cells from MVD file", total_cells)
            # circuit.mvd3 uses intrinsic gids starting from 1
            cell_i = MPI.rank + 1
            incr = MPI.cpu_count
            gidvec = np.arange(cell_i, total_cells + 1, incr, dtype="uint32")

        if not len(gidvec):
            # Not enough cells to give this rank a few
            logging.warning("Rank %d has no cells assigned.", MPI.rank)
            return total_cells, compat.Vector('I'), METypeManager()

        # Indexes are 0-based, and cant be numpy
        indexes = compat.Vector("I", gidvec - 1)

        morph_ids = mvd["/cells/properties/morphology"][indexes]
        combo_ids = mvd["/cells/properties/me_combo"][indexes]
        morpho_ds = mvd["/library/morphology"]
        morpho_names = [str(morpho_ds[i]) for i in morph_ids]
        combo_ds = mvd["/library/me_combo"]
        combo_names = [str(combo_ds[i]) for i in combo_ids]

        # We require gidvec as compat.Vector
        gidvec = compat.Vector("I", gidvec)

        # now we can open the combo file and get the emodel + additional info
        meinfo = METypeManager()
        res = meinfo.load_info(run_conf, gidvec, combo_names, morpho_names)
        if res < 0:
            logging.info(str(gidvec))
            logging.info("Memap: " + str(meinfo._me_map.keys()))
            raise RuntimeError("Errors found during processing of mecombo file. See log")

        return total_cells, gidvec, meinfo

    # -
    @staticmethod
    def _load_template(tpl_filename, tpl_location=None):
        """Helper function which loads the template into NEURON and returns its name.
        The actual template name will have any hyphens (e.g.: R-C261296A-P1_repaired)
        replaced with underscores as hyphens must not appear in template names.

        Params:
            tpl_filename: the template file to load
            tpl_location: (Optional) path for the templates

        Returns: The name of the template as it appears inside the file (sans hyphens)
        """
        #  start.ncs gives metype names with hyphens, but the templates themselves
        #  have those hyphens replaced with underscores.
        tpl_mod = tpl_filename
        if tpl_location is not None:
            tpl_mod = path.join(tpl_location, tpl_filename)

        # first open the file manually to get the hoc template name
        tpl_name = None
        with open(tpl_mod + ".hoc", "r") as templateReader:
            for line in templateReader:
                line = line.strip()
                if line.startswith("begintemplate"):
                    tpl_name = line.split()[1]
                    break
        Nd.load_hoc(tpl_mod)
        return tpl_name
    
    # ### Accessor methods - They keep CamelCase API for compatibility with existing hoc

    def getMEType(self, gid):
        return self._gid2meobj[gid]

    def getMETypeFromGid(self, gid):
        """ Provide the name of the metype which corresponds to a gid \n
        Returns: String with the metype or None
        """
        return self._gid2metype.get(gid)

    def getMEFileFromGid(self, gid):
        """Provide the file name of the metype which corresponds to a gid
        (thise may differ from metype due to special character replacement)
        """
        raise NotImplementedError("This function was removed since it makes no sense since v6")

    def getGidListForProcessor(self):
        """Get list containing the gids on this cpu.  Note that these gids may be virtual gids.
        If real gids are required, each value in the list should be passed through getGid()
        """
        return self._gidvec

    def getCell(self, gid):
        """Retrieve a cell object given its gid.
        Note that this function handles multisplit cases incl converting to an spgid automatically
        Returns: Cell object
        """
        # are we in load balance mode? must replace gid with spgid
        if self._lb_flag:
            gid = self._binfo.thishost_gid(gid)
        return self._pnm.pc.gid2obj(gid)

    def getSpGid(self, gid):
        """Retrieve the spgid from a gid (provided we are using loadbalancing)

        Args:
            gid: The base gid (as read from start.ncs)

        Returns: The gid as it appears on this cpu (if this is the same as the base gid,
        then that is the soma piece)
        """
        if self._lb_flag:
            return self._binfo.thishost_gid(gid)
        else:
            return gid

    def __iter__(self):
        """Iterator over this node GIDs"""
        return iter(self._gidvec)

    # ### Routines to actually compute load balance

    def load_balance_cells(self, lb_obj, nhost):
        """Calculate cell complexity and write data to file
        Args:
            lb_obj: loadbal neuron object
            nhost: Number of hosts to compute for load balancing
        """
        self._load_balance = lb_obj
        self._compute_save_load_balance("cx", nhost)

    def _compute_cell_complexity(self, with_total=False):
        cx_cell = compat.Vector("f")
        id_cell = compat.Vector("I")
        ncell = self._gidvec.size()

        for gid in self._gidvec:
            id_cell.append(gid)
            cx_cell.append(self._load_balance.cell_complexity(self._pnm.pc.gid2cell(gid)))

        if with_total:
            ncell = int(self._pnm.pc.allreduce(ncell, 1))
            return cx_cell, id_cell, ncell
        else:
            return cx_cell, id_cell

    def _cell_complexity_total_max(self):
        """
        Returns: Tuple of (TotalComplexity, max_complexity)
        """
        cx_cells, id_cells = self._compute_cell_complexity()
        local_max = max(cx_cells) if len(cx_cells) > 0 else .0
        local_sum = sum(cx_cells) if len(cx_cells) > 0 else .0

        global_total = self._pnm.pc.allreduce(local_sum, 1)
        global_max = self._pnm.pc.allreduce(local_max, 1)
        return global_total, global_max

    def _get_optimal_piece_complexity(self, total_cx, max_cx, nhost):
        """
        Args:
            total_cx: Total complexity
            max_cx: Maximum cell complexity
            nhost: Prospective no of hosts
        """
        lps = total_cx * self.msfactor / nhost
        return int(lps+1)

    def _cpu_assign(self, prospective_hosts):
        """
        Args:
            prospective_hosts: How many cpus we want running with our LoadBalanced circuit
        """
        Nd.mymetis3("cx_%d" % prospective_hosts, prospective_hosts)

    # -
    def _compute_save_load_balance(self, filename, prospective_hosts):
        if prospective_hosts > 0:
            total_cx, max_cx = self._cell_complexity_total_max()
            lcx = self._get_optimal_piece_complexity(total_cx, max_cx, prospective_hosts)
            # print_load_balance_info(3, lcx, $s1)
            filename = "%s_%d.dat" % (filename, prospective_hosts)
        else:
            total_cx, max_cx = None, None
            lcx = 1e9
            filename += ".dat"

        ms_list = []
        ms = Nd.Vector()
        lb = self._load_balance

        for i, gid in enumerate(self._gidvec):
            # what should be passed into this func? the base cell? the CCell?
            lb.cell_complexity(self._pnm.cells.object(i))
            lb.multisplit(gid, lcx, ms)
            ms_list.append(ms.c())

        if MPI.rank == 0:
            with open(filename, "w") as fp:
                fp.write("1\n%d\n" % self._pnm.ncell)
            logging.info("LB Info : TC=%.3f MC=%.3f OptimalCx=%.3f FileName=%s" %
                         (total_cx, max_cx, lcx, filename))

        # Write out, 1 rank at a time
        for j in range(MPI.cpu_count):
            if j == MPI.rank:
                with open(filename, "a") as fp:
                    for ms in ms_list:
                        self._write_msdat(fp, ms)
            MPI.barrier()

        # now assign to the various cpus - use node 0 to do it
        if MPI.rank == 0:
            self._cpu_assign(prospective_hosts)
        MPI.barrier()

    @staticmethod
    def _write_msdat(fp, ms):
        """Writes load balancing info to an output stream
        """
        fp.write("%d" % ms.x[0])   # gid
        fp.write(" %g" % ms.x[1])  # total complexity of cell
        piece_count = int(ms.x[2])
        fp.write(" %d\n" % piece_count)
        i = 2
        tcx = 0  # Total accum complexity
        
        for _ in range(piece_count):
            i += 1
            subtree_count = int(ms.x[i]) 
            fp.write("  %d\n" % subtree_count)
            for _ in range(subtree_count):
                i += 1
                cx = ms.x[i]  # subtree complexity
                tcx += cx
                i += 1
                children_count = int(ms.x[i])
                fp.write("   %g %d\n" % (cx, children_count))
                if children_count > 0:
                    fp.write("    ")
                for _ in range(children_count):
                    i += 1
                    elem_id = ms.x[i]  # at next child
                    fp.write(" %d" % elem_id)
                if children_count > 0:
                    fp.write("\n")

    # -
    def finalize(self, gids):
        """Do final steps to setup the network. For example, multisplit will handle gids depending
        on additional info from self.binfo object. Otherwise, normal cells do their finalization

        Args:
            gids: The gids of the cells to finalize

        """
        # First, we need each section of a cell to assign its index value to the voltage field
        # (crazy, huh?) at this moment, this is used later during synapse creation so that sections
        # can be serialized into a single array for random acess.
        rng_info = Nd.RNGSettings()
        self._global_seed = rng_info.getGlobalSeed()
        self._ionchannel_seed = rng_info.getIonChannelSeed()

        for i, gid in enumerate(gids):
            metype = self._cell_list[i]  # type: METype

            #  for v6 and beyond - we can just try to invoke rng initialization
            if self._useMVD3 or rng_info.getRNGMode() == rng_info.COMPATIBILITY:
                metype.re_init_rng(self._ionchannel_seed)
            else:
                # for v5 circuits and earlier check if cell has re_init function.
                # Instantiate random123 or mcellran4 as appropriate
                # Note: should CellDist be aware that metype has CCell member?
                if hasattr(metype.CCell, "re_init_rng"):
                    if rng_info.getRNGMode() == rng_info.RANDOM123:
                        Nd.rng123ForStochKvInit(metype.CCell)
                    else:
                        if metype.gid > 400000:
                            logging.warning("mcellran4 cannot initialize properly with large gids")
                        Nd.rngForStochKvInit(metype.CCell)

            version = metype.getVersion()
            if version < 2:
                nc = Nd.nc_   # tmp netcon
                metype.CellRef.connect2target(Nd.nil, nc)
            else:
                nc = metype.connect2target(Nd.nil)

            if self._lb_flag:
                gid_i = int(self._binfo.gids.indwhere("==", gid))
                cb = self._binfo.bilist.object(self._binfo.cbindex.x[gid_i])

                if cb.subtrees.count() == 0:
                    #  whole cell, normal creation
                    self._pnm.set_gid2node(gid, MPI.rank)
                    self._pnm.pc.cell(gid, nc)
                    self._spgidvec.append(int(gid))
                else:
                    spgid = cb.multisplit(nc, self._binfo.msgid, self._pnm.pc, MPI.rank)
                    self._spgidvec.append(int(spgid))

            else:
                self._pnm.set_gid2node(gid, self._pnm.myid)
                self._pnm.pc.cell(gid, nc)

        if self._lb_flag:
            self._pnm.pc.multisplit()
