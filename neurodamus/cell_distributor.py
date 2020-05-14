"""
Mechanisms to load and balance cells across the computing resources.
"""
from __future__ import absolute_import, print_function
import logging  # active only in rank 0 (init)
from contextlib import contextmanager
from enum import Enum
from io import StringIO
from os import path as ospath
import numpy

from .core import MPI, mpi_no_errors, run_only_rank0
from .core import NeurodamusCore as Nd
from .core import ProgressBarRank0 as ProgressBar
from .core.configuration import SimConfig
from .io import cell_readers
from .io.cell_readers import TargetSpec
from .metype import METype
from .utils import compat
from .utils.logging import log_verbose


class LoadBalanceMode(Enum):
    """An enumeration, inc parser, of the load balance modes.
    """
    RoundRobin = 0
    WholeCell = 1
    MultiSplit = 2

    @classmethod
    def parse(cls, lb_mode):
        """Parses the load balancing mode from a string.
        Options other than WholeCell or MultiSplit are considered RR
        """
        if lb_mode is None:
            return None
        _modes = {
            "rr": cls.RoundRobin,
            "roundrobin": cls.RoundRobin,
            "wholecell": cls.WholeCell,
            "loadbalance": cls.MultiSplit,
            "multisplit": cls.MultiSplit
        }
        return _modes[lb_mode.lower()]


class NodeFormat(Enum):
    NCS = 1
    MVD3 = 2
    SONATA = 3


class CellManagerBase(object):

    def __init__(self, pnm, target_parser):
        """Initializes CellDistributor

        Args:
            pnm: The hoc ParallelNetManager object
            target_parser: the target parser hoc object, to retrieve target cell ids

        """
        self._pnm = pnm
        self._target_parser = target_parser

        # These structs are None to mark as un-init'ed
        self._gidvec = None
        self._total_cells = None
        self._cell_list = []
        self._gid2cell = {}

        self._global_seed = 0
        self._ionchannel_seed = 0

    # read-only properties
    pnm = property(lambda self: self._pnm)
    target_parser = property(lambda self: self._target_parser)
    local_gids = property(lambda self: self._gidvec)
    total_cells = property(lambda self: self._total_cells)
    cell_list = property(lambda self: self._cell_list)
    cell_refs = property(lambda self: self._pnm.cells)
    pc = property(lambda self: self._pnm.pc)
    # Compatibility with neurodamus-core
    getGidListForProcessor = lambda self: self._gidvec  # for TargetManager, CompMappping

    CellType = None
    cell_loader = None

    def load_cells(self, conf, load_balancer=None):
        """A default implementation to load cells"""
        logging.info("Loading cell parameters...")
        self._gidvec, cell_infos, _ = self.cell_loader(conf)

        logging.info("Instantiating cells...")
        for gid in ProgressBar.iter(self._gidvec):
            cell_info = cell_infos[gid]
            cell = self.CellType(gid, cell_info)
            self._store_cell(gid, cell)

    def _init_rng(self):
        rng_info = Nd.RNGSettings()
        self._global_seed = rng_info.getGlobalSeed()
        self._ionchannel_seed = rng_info.getIonChannelSeed()
        return rng_info

    def finalize(self, gids=None, target=None):
        """A default implementation for instantiating cells"""
        self._init_rng()
        if gids is None:
            gids = self._gidvec
        for i, gid in enumerate(gids):
            gid = int(gid)
            metype = self._cell_list[i]  # type: METype
            nc = metype.connect2target(None)
            self._pnm.set_gid2node(gid, self._pnm.myid)
            self._pnm.pc.cell(gid, nc)

    def _store_cell(self, gid, cell):
        self._cell_list.append(cell)
        self._gid2cell[gid] = cell
        self._pnm.cells.append(cell.CellRef)

    def __iter__(self):
        """Iterator over this node GIDs
        """
        return iter(self._gidvec)

    def clear_cells(self):
        """Clear all cells
        """
        for cell in self._cell_list:
            if cell.CellRef:
                cell.CellRef.clear()
        self._cell_list.clear()


class CellDistributor(CellManagerBase):
    """ Handle assignment of cells to processors.

        Instantiated cells are stored locally (.cell_list), while CellRef's
        are stored in _pnm.cells hoc list
    """

    cell_loader_dict = {
        NodeFormat.NCS: cell_readers.load_ncs,
        NodeFormat.MVD3: cell_readers.load_mvd3,
        NodeFormat.SONATA: cell_readers.load_nodes
    }

    def __init__(self, pnm, target_parser):
        """Initializes CellDistributor

        Args:
            pnm: The hoc ParallelNetManager object
            target_parser: the target parser hoc object, to retrieve target cells' info

        """
        super().__init__(pnm, target_parser)
        # These wont ever be init'ed if not recomputing lb
        self._spgidvec = None   # cell parts gids
        self._binfo = None      # balanceInfo
        self._node_format = None  # NCS, Mvd, Sonata...

        # create a tmp netcon objref
        if not hasattr(Nd, "nc_"):
            Nd.execute("objref nc_")

    @mpi_no_errors
    def load_cells(self, run_conf, load_balancer=None):
        """Distribute and load target cells among CPUs.

        Args:
            run_conf (dict): Blueconfig 'Run' configuration
            load_balancer: A LoadBalance object for helping distributing cells
                or None -> Round-Robin
        """
        # for testing if xopen bcast is in use (NEURON 7.3). We will be loading
        # different templates on different cpus, so it must be disabled for now
        Nd.execute("xopen_broadcast_ = 0")

        # determine the connectivity format: start.ncs (default), circuit.mvd3 or sonata
        if "CellLibraryFile" in run_conf:
            celldb_filename = run_conf["CellLibraryFile"]
            if celldb_filename == "circuit.mvd3":
                self._node_format = NodeFormat.MVD3
            elif celldb_filename == "start.ncs":
                self._node_format = NodeFormat.NCS
            else:
                # Pass other types to mvdtool to detect
                self._node_format = NodeFormat.SONATA
        else:  # Default
            self._node_format = NodeFormat.NCS
            celldb_filename = "start.ncs"

        logging.info("Reading Nodes (METype) info from '%s' (format: %s)",
                     celldb_filename, self._node_format.name)

        total_cells = None   # total cells in this simulation
        loader = self.cell_loader_dict[self._node_format]
        target_spec = TargetSpec(run_conf.get("CircuitTarget"))

        #  are we using load balancing? If yes, init structs accordingly
        if load_balancer:
            if not load_balancer.valid_load_distribution(target_spec):
                raise RuntimeError("No valid Load Balance info could be found or derived."
                                   "Please perform a full load balance.")
            log_verbose("Distributing target '%s' using Load-Balance", target_spec.name)
            self._spgidvec = compat.Vector("I")
            self._binfo = Nd.BalanceInfo("cx_%s" % target_spec.simple_name,
                                         MPI.rank, MPI.size)

            # self._binfo has gidlist, but gids can appear multiple times
            all_gids = numpy.unique(self._binfo.gids.as_numpy().astype("uint32"))
            if target_spec:
                target = self._target_parser.getTarget(target_spec.name)
                total_cells = int(target.getCellCount())
            else:
                total_cells = len(all_gids)
            # LOAD
            gidvec, me_infos, _ = loader(run_conf, all_gids)

        elif target_spec:
            log_verbose("Distributing '%s' target cells Round-Robin", target_spec.name)
            target = self._target_parser.getTarget(target_spec.name)
            all_gids = target.completegids().as_numpy().astype("uint32")
            total_cells = len(all_gids)
            gidvec, me_infos, _ = loader(run_conf, all_gids, MPI.size, MPI.rank)

        else:
            log_verbose("Distributing ALL cells Round-Robin")
            gidvec, me_infos, total_cells = loader(run_conf, None, MPI.size, MPI.rank)

        self._gidvec = compat.Vector("I", gidvec)  # whatever it was, convert to compat V
        self._total_cells = total_cells
        MPI.check_no_errors()  # First phase (read mvd) DONE. Check all good

        if len(self._gidvec) == 0:
            logging.warning("Rank %d has no cells assigned.", MPI.rank)
            # We must not return, we have an allreduce later

        logging.info(" => Cells distributed. %d cells in network, %d in rank 0",
                     self._total_cells, len(self._gidvec))
        self._pnm.ncell = self._total_cells
        mepath = run_conf["METypePath"]
        morpho_path = SimConfig.morphology_path
        METype.morpho_extension = SimConfig.morphology_ext

        logging.info("Instantiating cells... Morphologies: %s", SimConfig.morphology_ext)
        total_created_cells = 0

        for gid in ProgressBar.iter(self._gidvec):
            if self._node_format != NodeFormat.NCS:
                # mvd3, Sonata
                meinfo_v6 = me_infos.retrieve_info(gid)
                melabel = meinfo_v6.emodel
                cell = METype(gid, mepath, melabel, morpho_path, meinfo_v6)
            else:
                # In NCS, me_infos is a plain map from gid to me_file
                melabel = self._load_template(me_infos[gid], mepath)
                cell = METype(gid, mepath, melabel, morpho_path)

            self._store_cell(gid, cell)
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

    # Accessor methods (Keep CamelCase API for compatibility with existing hoc)
    # ----------------

    def getMEType(self, gid):
        return self._gid2cell[gid]

    def getCell(self, gid):
        """Retrieve a cell object given its gid.
        Note that this function handles multisplit cases incl converting to an
        spgid automatically \n
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

    # -
    def finalize(self, gids=None, *_):
        """Do final steps to setup the network.\n
        Multisplit will handle gids depending on additional info from self.binfo
        object. Otherwise, normal cells do their finalization
        """
        rng_info = self._init_rng()
        pc = self.pc
        if gids is None:
            gids = self._gidvec

        for i, gid in enumerate(gids):
            gid = int(gid)
            metype = self._cell_list[i]  # type: METype

            # for v6 and beyond - we can just try to invoke rng initialization
            # for v5 circuits and earlier check if cell has re_init function.
            # Instantiate random123 or mcellran4 as appropriate
            # Note: should CellDist be aware that metype has CCell member?
            need_invoke = self._node_format != NodeFormat.NCS \
                          or rng_info.getRNGMode() == rng_info.COMPATIBILITY
            if not need_invoke:
                if hasattr(metype.CCell, "re_init_rng") and \
                   rng_info.getRNGMode() != rng_info.RANDOM123:
                    if gid > 400000:
                        logging.warning("mcellran4 cannot init properly with large gids")
            metype.re_init_rng(self._ionchannel_seed, need_invoke)

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


class LoadBalance:
    """
    Class handling the several types of load_balance info, including
    generating and loading the various files.

    LoadBalance instances target the current system (cpu count) and circuit
    (nrn_path) BUT check/create load distribution for any given target.
    """
    cxinfo_filename = "cxinfo.txt"
    _cx_filename_tpl = "cx_%s.dat"
    _cpu_assign_filename_tpl = "cx_%s.%s.dat"

    def __init__(self, balance_mode, nrn_path, target_parser, target_cpu_count=None):
        self.lb_mode = balance_mode
        self.nrnpath = nrn_path
        self.target_cpu_count = target_cpu_count or MPI.size
        self._target_parser = target_parser
        self._valid_loadbalance = set()
        # Properties saved in cxinfo
        self.cxinfo_nrnpath = None
        self.cxinfo_targets = []
        self._load_cxinfo()

    @run_only_rank0
    def valid_load_distribution(self, target_spec):
        """Checks whether we have valid load-balance files, attempting to
        derive from larger target distributions if possible.
        """
        target_name = target_spec.simple_name

        # Remember If the user already checked or generated
        if target_name in self._valid_loadbalance:
            logging.info(" => Cell distribution from Load Balance is valid")
            return True

        # We have to make sure that the complexity files, besides existing, must
        # be registered in cxinfo.txt, otherwise they might be from another circuit
        if self._cx_valid(target_spec):
            cpu_assign_filename = self._cpu_assign_filename_tpl % (target_name,
                                                                   self.target_cpu_count)
            if ospath.isfile(cpu_assign_filename):
                logging.info(" => Found valid cell distribution: %s", cpu_assign_filename)
                self._valid_loadbalance.add(target_name)
                return True
            else:
                logging.info(" => Found valid complexity file.")
                self._cpu_assign(target_name)
                self._valid_loadbalance.add(target_name)
                return True

        # If not found, attempt to find a cx file computed for a superset target
        # so we can derive a new cx file without instantiating cells
        if self._reuse_cell_complexity(target_spec):
            self._cpu_assign(target_name)
            self._valid_loadbalance.add(target_name)
            return True
        return False

    # -
    def _reuse_cell_complexity(self, target_spec):
        """Check if the complexities of all target gids were already calculated
        for another target.
        """
        # Abort if the circuit changed or in case now we request full circuit
        # since its Impossible to have a superset of it
        if (self.cxinfo_nrnpath != self.nrnpath
                or not target_spec
                or not self.cxinfo_targets):
            logging.info(" => Target Cx reusing is not available.")
            return False

        logging.info("Attempt reusing cx files from other targets...")
        target_gids = self._get_target_gids(target_spec)
        cx_other = {}

        for previous_target in self.cxinfo_targets:
            log_verbose("Trying previous cx file on target %s", previous_target)
            ref_filename = self._cx_filename_tpl % previous_target
            if self._cx_contains_gids(ref_filename, target_gids, cx_other):
                break  # done!
            log_verbose("  - Target is not a superset. Ignoring.")
        else:
            logging.info(" => Did not find any suitable target")
            return False

        new_cx_filename = self._cx_filename_tpl % target_spec.simple_name
        logging.info("Target %s is a subset of the target %s. Generating %s",
                     target_spec.name, previous_target, new_cx_filename)

        # Write the new cx file since Neuron needs it to do CPU assignment
        with open(new_cx_filename, "w") as newfile:
            self._write_msdat_dict(newfile, cx_other, target_gids)
        # Write updated cxinfo
        self._write_cxinfo(target_spec.simple_name)
        return True

    # -
    def _cx_valid(self, target_spec, check_contents=True):
        """Determine if valid complexity files exist for the provided
        target spec, otherwise return False -> we need to regen load balance info

        Note: We keep cxinfo to keep track of the complexity files calculated
        for a given circuit/target. In case the circuit location changes we always
        return False and a new cxinfo is generated (invalidating any existing cx_*)
        """
        if self.cxinfo_nrnpath is None:
            logging.info(" => No cx_info file found!")
            return False

        if self.cxinfo_nrnpath != self.nrnpath:
            logging.info(" => Circuit path has changed. Ignoring cx files")
            return False

        target_name = target_spec.simple_name
        if target_name not in self.cxinfo_targets:
            logging.info(" => No Cx files available for requested target")
            return False

        cx_filename = self._cx_filename_tpl % target_name
        if not ospath.isfile(cx_filename):
            logging.warning(" => %s file missing. Fixing cxinfo.txt", cx_filename)
            self._write_cxinfo()
            return False

        if target_spec and check_contents:
            target_gids = self._get_target_gids(target_spec)
            if not self._cx_contains_gids(cx_filename, target_gids):
                logging.warning(" => %s invalid: changed target definition!", cx_filename)
                return False
        return True

    @classmethod
    def _cx_contains_gids(cls, cxpath, target_gids, out_cx=None):
        """Checks a cx file contains complexities for given gids
        """
        if not ospath.isfile(cxpath):
            log_verbose("  - cxpath doesnt exist: %s", cxpath)
            return False
        with open(cxpath, "r") as f:
            cx_saved = cls._read_msdat(f)
        if not set(cx_saved.keys()) >= set(target_gids):
            log_verbose("  - Not all GIDs in target %s %s", set(cx_saved.keys()), set(target_gids))
            return False
        if out_cx is not None:
            out_cx.update(cx_saved)
        return cx_saved

    @contextmanager
    def generate_load_balance(self, target_str, cell_distributor):
        """Context manager that creates load balance for the circuit instantiated within

        Args:
            target_str: a string represesntation of the target.
            cell_distributor: the cell distributor object to which we can query
                the cells to be load balanced
        """
        mcomplex = Nd.MComplexLoadBalancer()  # init mcomplex before building circuit
        yield
        self._compute_save_complexities(target_str, mcomplex, cell_distributor)
        self._write_cxinfo(target_str)
        self._cpu_assign(target_str)
        self._valid_loadbalance.add(target_str)

    def _load_cxinfo(self):
        if not ospath.isfile(self.cxinfo_filename):
            return
        with open(self.cxinfo_filename, "r") as cxinfo:
            self.cxinfo_nrnpath = next(cxinfo).strip()
            # In case nrnpath changed ignore targets
            if self.cxinfo_nrnpath == self.nrnpath:
                self.cxinfo_targets = [t.strip() for t in cxinfo]

    @run_only_rank0
    def _write_cxinfo(self, *targets_append):
        """Write config in the cxinfo file for future usage
        """
        all_targets = sorted(set(self.cxinfo_targets) | set(targets_append))

        with open(self.cxinfo_filename, "w") as cxinfo:
            print(self.nrnpath, file=cxinfo)
            for tname in all_targets:
                if ospath.isfile(self._cx_filename_tpl % tname):
                    print(tname, file=cxinfo)
        # Update meta
        self.cxinfo_nrnpath = self.nrnpath
        self.cxinfo_targets = all_targets

    @mpi_no_errors
    def _compute_save_complexities(self, target_str, mcomplex, cell_distributor):
        gidvec = cell_distributor.local_gids
        msfactor = 1e6 if self.lb_mode == LoadBalanceMode.WholeCell else 0.8
        out_filename = self._cx_filename_tpl % target_str

        cx_cells = self._compute_complexities(mcomplex, cell_distributor)
        total_cx, max_cx = self._cell_complexity_total_max(cx_cells)
        lcx = self._get_optimal_piece_complexity(total_cx,
                                                 self.target_cpu_count,
                                                 msfactor)
        cells = cell_distributor.pnm.cells
        ms_list = []
        tmp = Nd.Vector()

        for i, gid in enumerate(gidvec):
            mcomplex.cell_complexity(cells.o(i))
            mcomplex.multisplit(gid, lcx, tmp)
            ms_list.append(tmp.c())

        # To output build independently the contents of the file then append
        ostring = StringIO()
        if MPI.rank == 0:
            ostring.write("1\n%d\n" % cell_distributor.pnm.ncell)
            logging.info("LB Info: TC=%.3f MC=%.3f OptimalCx=%.3f FileName=%s",
                         total_cx, max_cx, lcx, out_filename)
        for ms in ms_list:
            self._write_msdat(ostring, ms)

        all_ranks_cx = MPI.py_gather(ostring.getvalue(), 0)
        if MPI.rank == 0:
            with open(out_filename, "w") as fp:
                for cx_info in all_ranks_cx:
                    fp.write(cx_info)

    @staticmethod
    def _cell_complexity_total_max(cx_cells):
        """
        Returns: Tuple of (TotalComplexity, max_complexity)
        """
        local_max = max(cx_cells) if len(cx_cells) > 0 else .0
        local_sum = sum(cx_cells) if len(cx_cells) > 0 else .0

        global_total = MPI.allreduce(local_sum, MPI.SUM)
        global_max = MPI.allreduce(local_max, MPI.MAX)
        return global_total, global_max

    @classmethod
    def _compute_complexities(cls, mcomplex, cell_distributor):
        cx_cell = compat.Vector("f")
        pc = cell_distributor.pc
        for gid in cell_distributor.local_gids:
            cx_cell.append(mcomplex.cell_complexity(pc.gid2cell(gid)))
        return cx_cell

    @staticmethod
    def _get_optimal_piece_complexity(total_cx, nhost, msfactor):
        """
        Args:
            total_cx: Total complexity
            nhost: Prospective no of hosts
        """
        lps = total_cx * msfactor / nhost
        return int(lps+1)

    @run_only_rank0
    def _cpu_assign(self, target_name):
        """Assigns cells to 'prospective_hosts' cpus using mymetis3.
        """
        logging.info("Assigning Cells <-> %d CPUs [mymetis3]", self.target_cpu_count)
        Nd.mymetis3("cx_%s" % target_name, self.target_cpu_count)

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

    @staticmethod
    def _read_msdat(fp):
        """read load balancing info from an input stream
        """
        cx_saved = {}  # dict with key = gid, value = line content
        piece_count = 0
        gid = None
        next(fp)  # first line has 1. skip
        next(fp)  # ncells. skip

        for line in fp:
            if piece_count == 0:
                gid, cx, piece_count = [int(float(x)) for x in line.split()]
                cx_saved[gid] = [line]
            else:                               # Handle parts
                cx_saved[gid].append(line)
                for _ in range(2 * int(line)):  # each subtree has two lines
                    cx_saved[gid].append(next(fp))
                piece_count -= 1

        return cx_saved

    @staticmethod
    def _write_msdat_dict(fp, cx_dict, gids=None):
        """Write out selected gid cx lines from a cx_dict
        """
        if gids is None:
            gids = cx_dict.keys()
        fp.write("1\n%d\n" % len(gids))
        for gid in gids:
            for line in cx_dict[gid]:
                fp.write(line)  # raw lines, include \n

    # -
    def _get_target_gids(self, target_spec):
        return self._target_parser.getTarget(target_spec.name).completegids() \
            .as_numpy().astype(int)
