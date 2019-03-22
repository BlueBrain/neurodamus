from __future__ import absolute_import, print_function
import logging  # active only in rank 0 (init)
from os import path as Path
from lazy_property import LazyProperty
from . import cell_readers
from .core import MPI, mpi_no_errors, run_only_rank0
from .core import NeuronDamus as Nd
from .core import ProgressBarRank0 as ProgressBar
from .core.configuration import ConfigurationError
from .metype import METype
from .utils import compat
from .utils.logging import log_verbose


class LoadBalanceMode:
    """An enumeration, inc parser, of the load balance modes.
    """
    WholeCell = 1
    MultiSplit = 2

    @classmethod
    def parse(cls, lb_mode):
        _modes = {
            "WholeCell": cls.WholeCell,
            "LoadBalance": cls.MultiSplit
        }
        return _modes.get(lb_mode)


class CellDistributor(object):
    """Handle assignment of cells to processors, instantiate and store them (locally and in _pnm).
    """

    def __init__(self, pnm, lb_mode=None, prospective_hosts=None):
        """Initializes CellDistributor

        Args:
            pnm: The hoc ParallelNetManager object
            lb_mode (LoadBalanceMode): The load balance mode
            prospective_hosts (int): The level of parallelism for the simulation run

        """
        self._target_cpu_count = prospective_hosts or MPI.size
        self._lb_mode = lb_mode
        self._pnm = pnm

        # These structs are None to mark as un-init'ed
        self._gidvec = None
        self._total_cells = None
        # These wont ever be init'ed if not recomputing lb
        self._spgidvec = None   # cell parts gids
        self._mcomplex = None
        self._binfo = None      # balanceInfo

        self._useMVD3 = False
        self._global_seed = 0
        self._ionchannel_seed = 0

        self._cell_list = []
        self._gid2meobj = {}
        self._gid2metype = {}

        # complexity factor
        self._msfactor = 1e6 if self._lb_mode is LoadBalanceMode.WholeCell else 0.8

        # create a tmp netcon objref
        if not hasattr(Nd, "nc_"):
            Nd.execute("objref nc_")

    # read-only properties
    lb_mode          = property(lambda self: self._lb_mode)
    target_cpu_count = property(lambda self: self._target_cpu_count)
    pnm              = property(lambda self: self._pnm)
    local_gids       = property(lambda self: self._gidvec)
    total_cells      = property(lambda self: self._total_cells)
    cell_list        = property(lambda self: self._cell_list)
    ms_factor        = property(lambda self: self._msfactor)
    pc               = LazyProperty(lambda self: self._pnm.pc)  # avoid re-fetch hoc attr

    # -
    def load_or_recompute_mcomplex_balance(self, nrn_path, target_name, build_circuit_f):
        """Check if valid cx files exist for the cur conf, or create after building circuit.
        """
        cxinfo_filename = "cxinfo_%d.txt" % (self._target_cpu_count,)
        if self._cx_valid(cxinfo_filename, nrn_path, target_name):
            logging.info("Using existing load balancing info")
            return True

        self._mcomplex = Nd.MComplexLoadBalancer()  # init mcomplex before creating circuit
        build_circuit_f()
        self._compute_save_load_balance()

        # Write config in the cxinfo file for future usage
        if MPI.rank == 0:
            with open(cxinfo_filename, "w") as cxinfo:
                print(nrn_path, file=cxinfo)
                print(target_name or "---", file=cxinfo)
        return False

    # -
    @run_only_rank0
    def _cx_valid(self, cxinfo_filename, nrn_path, target_name):
        """Determine if we need to regen load balance info, or if it already exists for this config.
        """
        if not Path.isfile(cxinfo_filename):
            logging.info("(Re)Generating load-balancing data. Reason: no cxinfo file")
            return False

        with open(cxinfo_filename, "r") as cxinfo:
            cx_nrnpath = cxinfo.readline().strip()
            cx_target = cxinfo.readline().strip()
            if target_name is None:  # if there is no circuit target, cmp against "---"
                target_name = "---"

            if cx_nrnpath != nrn_path:
                logging.info("(Re)Generating load-balancing data. Reason: nrnPath has changed")

            elif cx_target != target_name:
                logging.info("(Re)Generating load-balancing data. Reason: %s",
                             "CircuitTarget has changed. Previously: %s" % cx_target)
            else:
                return True
        return False

    # -
    @mpi_no_errors
    def load_cells(self, run_conf, target_parser, load_bal=True):
        """Distribute and load target cells among CPUs.

        Args:
            run_conf (dict): Blueconfig 'Run' configuration
            target_parser (hoc): The Target parser object
            load_bal (bool): Whether to respect lb_mode or disable it altogether
        """
        logging.info("Loading cell METypes and Distributing by available CPUs...")
        morpho_path = run_conf["MorphologyPath"]
        if not load_bal:
            self._lb_mode = None

        # for testing if xopen bcast is in use (NEURON 7.3).
        # We will be loading different templates on different cpus, so it must be disabled for now
        Nd.execute("xopen_broadcast_ = 0")

        # determine if we should get metype info from start.ncs (current default) or circuit.mvd3
        if "CellLibraryFile" in run_conf:
            celldb_filename = run_conf["CellLibraryFile"]
            if celldb_filename == "circuit.mvd3":
                log_verbose("Reading [gid:METype] info from circuit.mvd3")
                self._useMVD3 = True

            elif celldb_filename != "start.ncs":
                logging.error("Invalid CellLibraryFile %s. Terminating", celldb_filename)
                raise ConfigurationError("Invalid CellLibraryFile {}".format(celldb_filename))
        # Default
        if not self._useMVD3:
            log_verbose("Reading [gid:METype] info from start.ncs")

        gidvec = compat.Vector("I")  # Gids handled by this cpu
        total_cells = None   # total cells in this simulation (can be a subset, e.g.: target)
        circuit_size = None  # total cells in the circuit
        loader = cell_readers.load_mvd3 if self._useMVD3 else cell_readers.load_ncs

        #  are we using load balancing? If yes, init structs accordingly
        if self._lb_mode:
            log_verbose("Distributing cells according to load-balance")
            # read the cx_* files to build the gidvec
            cx_path = "cx_%d" % MPI.size
            if "CWD" in run_conf:
                # Should we allow for another path to facilitate reusing cx* files?
                cx_path = Path.join(run_conf["CWD"], cx_path)

            assert Path.isfile(cx_path + ".dat"), "cx_path not available when reloading cells"

            self._spgidvec = compat.Vector("I")
            self._binfo = Nd.BalanceInfo(cx_path, MPI.rank, MPI.size)

            # self.binfo has gidlist, but gids can appear multiple times
            gidvec.extend(sorted(set(int(gid) for gid in self._binfo.gids)))

            # TODO: do we have any way of knowing that a CircuitTarget found definitively matches
            #       the cells in the balance files? for now, assume the user is being honest
            if "CircuitTarget" in run_conf:
                target = target_parser.getTarget(run_conf["CircuitTarget"])
                total_cells = int(target.completegids().size())
            else:
                # TODO: gidvec doesnt sound it would include all cells. Check this
                total_cells = len(gidvec)
            # LOAD
            self._gidvec, me_infos, _ = loader(run_conf, gidvec)

        elif "CircuitTarget" in run_conf:
            log_verbose("Distributing target circuit cells round-robin")
            target = target_parser.getTarget(run_conf["CircuitTarget"])
            target_gids = target.completegids()
            gidvec.extend(int(gid) for gid in target_gids)
            total_cells = int(target_gids.size())
            self._gidvec, me_infos, _ = loader(run_conf, gidvec, MPI.size, MPI.rank)

        else:
            log_verbose("Distributing all cells round-robin")
            self._gidvec, me_infos, circuit_size = loader(run_conf, None, MPI.size, MPI.rank)

        self._total_cells = total_cells or circuit_size

        if len(self._gidvec) == 0:
            logging.warning("Rank %d has no cells assigned.", MPI.rank)
            # We must not return, we have an allreduce later

        log_verbose("Done gid assignment: %d cells in network, %d in rank 0",
                    self._total_cells, len(self._gidvec))

        self._pnm.ncell = self._total_cells
        pnm_cells = self._pnm.cells
        mepath = run_conf["METypePath"]
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
            pnm_cells.append(cell.CellRef)
            total_created_cells += 1

        global_cells_created = MPI.allreduce(total_created_cells, MPI.SUM)
        logging.info(" => Created %d cells (%d in rank 0)",
                     global_cells_created, total_created_cells)

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
        tpl_path = Path.join(tpl_location, tpl_filename) if tpl_location else tpl_filename

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

    # -
    def clear_cells(self):
        """Clear all cells
        """
        for cell in self._cell_list:
            cell.CellRef.clear()
        self._cell_list.clear()

    # Accessor methods (Keep CamelCase API for compatibility with existing hoc)
    # ----------------

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
        if self._binfo:
            # are we in load balance mode? must replace gid with spgid
            gid = self._binfo.thishost_gid(gid)
        return self.pc.gid2obj(gid)

    def getSpGid(self, gid):
        """Retrieve the spgid from a gid (provided we are using loadbalancing)

        Args:
            gid: The base gid (as read from start.ncs)

        Returns: The gid as it appears on this cpu (if this is the same as the base gid,
        then that is the soma piece)
        """
        if self._binfo:
            return self._binfo.thishost_gid(gid)
        else:
            return gid

    def __iter__(self):
        """Iterator over this node GIDs"""
        return iter(self._gidvec)

    # Load balance computation
    # ------------------------

    @mpi_no_errors
    def _compute_save_load_balance(self):
        if self._target_cpu_count > 0:
            total_cx, max_cx = self._cell_complexity_total_max()
            lcx = self._get_optimal_piece_complexity(total_cx, self._target_cpu_count)
            # print_load_balance_info(3, lcx, $s1)
            filename = "cx_%d.dat" % self._target_cpu_count
        else:
            total_cx, max_cx = None, None
            lcx = 1e9
            filename = "cx.dat"

        ms_list = []
        ms = Nd.Vector()

        lb_obj = self._mcomplex
        for i, gid in enumerate(self._gidvec):
            # what should be passed into this func? the base cell? the CCell?
            lb_obj.cell_complexity(self._pnm.cells.object(i))
            lb_obj.multisplit(gid, lcx, ms)
            ms_list.append(ms.c())

        if MPI.rank == 0:
            with open(filename, "w") as fp:
                fp.write("1\n%d\n" % self._pnm.ncell)
            logging.info("LB Info : TC=%.3f MC=%.3f OptimalCx=%.3f FileName=%s" %
                         (total_cx, max_cx, lcx, filename))

        # Write out, 1 rank at a time
        for j in range(MPI.size):
            if j == MPI.rank:
                with open(filename, "a") as fp:
                    for ms in ms_list:
                        self._write_msdat(fp, ms)
            MPI.barrier()

        # now assign to the various cpus - use node 0 to do it
        if MPI.rank == 0:
            self._cpu_assign(self._target_cpu_count)

    def _compute_cells_complexity(self):
        cx_cell = compat.Vector("f")
        id_cell = compat.Vector("I")
        pc = self.pc

        for gid in self._gidvec:
            id_cell.append(gid)
            cx_cell.append(self._mcomplex.cell_complexity(pc.gid2cell(gid)))

        return cx_cell, id_cell

    def _cell_complexity_total_max(self):
        """
        Returns: Tuple of (TotalComplexity, max_complexity)
        """
        cx_cells, id_cells = self._compute_cells_complexity()
        local_max = max(cx_cells) if len(cx_cells) > 0 else .0
        local_sum = sum(cx_cells) if len(cx_cells) > 0 else .0

        global_total = MPI.allreduce(local_sum, MPI.SUM)
        global_max = MPI.allreduce(local_max, MPI.MAX)
        return global_total, global_max

    def _get_optimal_piece_complexity(self, total_cx, nhost):
        """
        Args:
            total_cx: Total complexity
            nhost: Prospective no of hosts
        """
        lps = total_cx * self._msfactor / nhost
        return int(lps+1)

    @staticmethod
    def _cpu_assign(prospective_hosts):
        """Assigns cells to 'prospective_hosts' cpus using mymetis3.
        """
        Nd.mymetis3("cx_%d" % prospective_hosts, prospective_hosts)

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
        # can be serialized into a single array for random access.
        rng_info = Nd.RNGSettings()
        pc = self.pc
        self._global_seed = rng_info.getGlobalSeed()
        self._ionchannel_seed = rng_info.getIonChannelSeed()

        for i, gid in enumerate(gids):
            gid = int(gid)
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
                        if gid > 400000:
                            logging.warning("mcellran4 cannot initialize properly with large gids")
                        Nd.rngForStochKvInit(metype.CCell)

            version = metype.getVersion()
            if version < 2:
                nc = Nd.nc_   # tmp netcon
                metype.CellRef.connect2target(Nd.nil, nc)
            else:
                nc = metype.connect2target(Nd.nil)

            if self._binfo:
                gid_i = int(self._binfo.gids.indwhere("==", gid))
                cb = self._binfo.bilist.object(self._binfo.cbindex.x[gid_i])

                if cb.subtrees.count() == 0:
                    #  whole cell, normal creation
                    self._pnm.set_gid2node(gid, MPI.rank)
                    pc.cell(gid, nc)
                    self._spgidvec.append(gid)
                else:
                    spgid = cb.multisplit(nc, self._binfo.msgid, pc, MPI.rank)
                    self._spgidvec.append(int(spgid))
            else:
                self._pnm.set_gid2node(gid, self._pnm.myid)
                pc.cell(gid, nc)

        pc.multisplit()
