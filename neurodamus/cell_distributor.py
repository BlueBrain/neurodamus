"""
Mechanisms to load and balance cells across the computing resources.
"""
from __future__ import absolute_import, print_function
import logging  # active only in rank 0 (init)
import os
import weakref
from contextlib import contextmanager
from enum import Enum
from io import StringIO
from os import path as ospath

import numpy

from .connection_manager import ConnectionManagerBase
from .core import MPI, mpi_no_errors, run_only_rank0
from .core import NeurodamusCore as Nd
from .core import ProgressBarRank0 as ProgressBar
from .core.nodeset import NodeSet
from .io import cell_readers
from .metype import Cell_V5, Cell_V6, EmptyCell
from .target_manager import TargetSpec
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

    class AutoBalanceModeParams:
        """Parameters for auto-selecting a load-balance mode"""
        multisplit_cpu_cell_ratio = 1.5
        cell_count = 1000
        duration = 1000
        mpi_ranks = 200

    @classmethod
    def auto_select(cls, use_neuron, cell_count, duration, auto_params=AutoBalanceModeParams):
        """Simple heuristics for auto selecting load balance"""
        lb_mode = LoadBalanceMode.RoundRobin
        reason = ""
        if use_neuron and MPI.size > auto_params.multisplit_cpu_cell_ratio * cell_count:
            lb_mode = LoadBalanceMode.MultiSplit
            reason = "CPU-Cell ratio"
        elif (cell_count > auto_params.cell_count
              and duration > auto_params.duration
              and MPI.size > auto_params.mpi_ranks):
            lb_mode = LoadBalanceMode.WholeCell
            reason = 'Simulation size'
        return lb_mode, reason


class NodeFormat(Enum):
    NCS = 1
    MVD3 = 2
    SONATA = 3


class VirtualCellPopulation:
    """
    A virtual cell population offers a compatible interface with Cell Manager,
    however it doesnt instantiate cells.
    It is mostly used as source of projections
    """
    _total_count = 0

    def __init__(self, population_name):
        self._population_name = population_name
        self._local_nodes = NodeSet().register_global(population_name or '')
        VirtualCellPopulation._total_count += 1
        if VirtualCellPopulation._total_count > 1:
            logging.warning("At the moment only a single Virtual Cell Population works with REPLAY")

    local_nodes = property(lambda self: self._local_nodes)
    population_name = property(lambda self: self._population_name)
    is_default = property(lambda self: False)
    is_virtual = property(lambda self: True)

    def __str__(self):
        return "([VIRT] {:s})".format(self._population_name)


class CellManagerBase(object):

    CellType = NotImplemented  # please override
    """The underlying Cell type class
    signature:
        __init__(self, gid, cell_info, circuit_conf)
    """

    _node_loader = None
    """Default function implementing the loading of nodes data, a.k.a. MVD
    signature:
        load(circuit_conf, gidvec, stride=1, stride_offset=0)
    """

    _node_format = NodeFormat.SONATA  # NCS, Mvd, Sonata...
    """Default Node file format"""

    def __init__(self, circuit_conf, target_manager, *_):
        """Initializes CellDistributor

        Args:
            circuit_conf: The "Circuit" blueconfig block
            target_parser: the target parser hoc object, to retrieve target cells' info
            run_conf: Run configuration

        """
        self._circuit_conf = circuit_conf
        self._circuit_name = circuit_conf._name
        self._target_manager = target_manager
        self._target_spec = TargetSpec(circuit_conf.CircuitTarget)
        self._population_name = None
        self._local_nodes = None
        self._total_cells = 0   # total cells in target, being simulated
        self._gid2cell = {}

        self._global_seed = 0
        self._ionchannel_seed = 0
        self._binfo = None
        self._pc = Nd.pc
        self._conn_managers_per_src_pop = weakref.WeakValueDictionary()

        if circuit_conf.CircuitPath:
            self._init_config(circuit_conf, self._target_spec.population or '')
        else:
            logging.info(" => %s Circuit has been disabled", self.circuit_name or "(default)")

    # read-only properties
    target_manager = property(lambda self: self._target_manager)
    local_nodes = property(
        lambda self: self._local_nodes if self._local_nodes is not None else NodeSet()
    )
    total_cells = property(lambda self: self._total_cells)
    cells = property(lambda self: self._gid2cell.values())
    gid2cell = property(lambda self: self._gid2cell)
    pc = property(lambda self: self._pc)
    population_name = property(lambda self: self._population_name)
    circuit_target = property(lambda self: self._target_spec.name)
    circuit_name = property(lambda self: self._circuit_name)
    is_default = property(lambda self: self._circuit_name is None)
    is_virtual = property(lambda self: False)
    connection_managers = property(lambda self: self._conn_managers_per_src_pop)

    def __str__(self):
        return "({}: {})".format(self.__class__.__name__, str(self._population_name))

    # Compatibility with neurodamus-core (used by TargetManager, CompMapping)
    def getGidListForProcessor(self):
        return self._local_nodes.final_gids()

    def _init_config(self, circuit_conf, pop):
        if not pop and self._node_format == NodeFormat.SONATA:  # Last attempt to get pop name
            pop = self._get_sonata_population_name(circuit_conf.CellLibraryFile)
            logging.info(" -> Discovered node population name: %s", pop)
        if not pop and circuit_conf._name:
            pop = circuit_conf._name
            logging.warning("(Compat) Assuming population name from Circuit: %s", pop)
        self._population_name = pop
        # Base population should be registered as "" so it doesnt do offsetting
        if not pop and not self.is_default:
            raise Exception("Only the default population can be unnamed")
        self._local_nodes = NodeSet().register_global("" if self.is_default else pop)

    @classmethod
    def _get_sonata_population_name(self, node_file):
        import h5py  # only for Sonata
        ds = h5py.File(node_file, "r")["nodes"]
        assert len(ds) == 1  # single population
        return next(iter(ds.keys()))

    def load_nodes(self, load_balancer=None, *, _loader=None):
        """Top-level loader of nodes.
        """
        if self._local_nodes is None:
            return
        conf = self._circuit_conf
        loader_f = _loader or self._node_loader

        logging.info("Reading Nodes (METype) info from '%s'", conf.CellLibraryFile)
        if not load_balancer:
            # Use common loading routine, providing the loader
            gidvec, me_infos, *cell_counts = self._load_nodes(loader_f)
        else:
            gidvec, me_infos, *cell_counts = self._load_nodes_balance(loader_f, load_balancer)
        self._local_nodes.add_gids(gidvec, me_infos)
        self._total_cells = cell_counts[0]
        logging.info(" => Loaded info about %d target cells (out of %d)", *cell_counts)

    def _load_nodes(self, loader_f):
        """Base loader which handles targets"""
        conf = self._circuit_conf
        target_spec = self._target_spec

        if target_spec.name:
            logging.info(" -> Distributing '%s' target cells Round-Robin", target_spec)
            target_gids = self._target_manager.get_target(target_spec).get_gids()
            gidvec, me_infos, full_size = loader_f(conf, target_gids, MPI.size, MPI.rank)
            total_cells = len(target_gids)
        else:
            logging.info(" -> Distributing ALL cells Round-Robin (No target provided)")
            gidvec, me_infos, full_size = loader_f(conf, None, MPI.size, MPI.rank)
            total_cells = full_size
        return gidvec, me_infos, total_cells, full_size

    def _load_nodes_balance(self, loader_f, load_balancer):
        target_spec = self._target_spec
        if not load_balancer.valid_load_distribution(target_spec):
            raise RuntimeError("No valid Load Balance info could be found or derived."
                               "Please perform a full load balance.")

        logging.info(" -> Distributing target '%s' using Load-Balance", target_spec.name)
        self._binfo = Nd.BalanceInfo(ospath.join(load_balancer.cx_datafolder, "cx_%s")
                                     % target_spec.simple_name, MPI.rank, MPI.size)

        # self._binfo has gidlist, but gids can appear multiple times
        all_gids = numpy.unique(self._binfo.gids.as_numpy().astype("uint32"))
        total_cells = len(all_gids)
        gidvec, me_infos, full_size = loader_f(self._circuit_conf, all_gids)
        return gidvec, me_infos, total_cells, full_size

    # -
    def finalize(self, *_):
        """Instantiates cells and initializes the network in the simulator.

        Note: it should be called after all cell distributors have done load_nodes()
            so gids offsets are final.
        """
        if self._local_nodes is None:
            return
        logging.info("Finalizing cells... Gid offset: %d", self._local_nodes.offset)
        self._instantiate_cells()
        self._update_targets_local_gids()
        self._init_cell_network()
        self._local_nodes.clear_cell_info()

    @mpi_no_errors
    def _instantiate_cells(self, _CellType=None):
        CellType = _CellType or self.CellType
        assert CellType is not None, "Undefined CellType in Manager"
        Nd.execute("xopen_broadcast_ = 0")

        logging.info(" > Instantiating cells... (%d in Rank 0)", len(self._local_nodes))
        cell_offset = self._local_nodes.offset
        for gid, cell_info in ProgressBar.iter(self._local_nodes.items(), len(self._local_nodes)):
            cell = CellType(gid, cell_info, self._circuit_conf)
            self._store_cell(gid + cell_offset, cell)

    def _update_targets_local_gids(self):
        logging.info(" > Updating targets")
        cell_offset = self._local_nodes.offset
        if cell_offset and self._target_spec.name:
            target = self._target_manager.get_target(self._target_spec)
            if not hasattr(target, "set_offset"):
                raise NotImplementedError("No gid offsetting supported by neurodamus Target.hoc")
            target.set_offset(cell_offset)
        # Add local gids to matching targets
        self._target_manager.parser.updateTargets(self._local_nodes.final_gids(), 1)

    def _init_cell_network(self):
        """Init global gids for cell networking
        """
        logging.info(" > Initializing cell network")
        self._init_rng()
        pc = self._pc

        for final_gid, cell in self._gid2cell.items():
            cell.re_init_rng(self._ionchannel_seed)
            nc = cell.connect2target(None)  # Netcon doesnt require being stored

            if self._binfo:
                gid_i = int(self._binfo.gids.indwhere("==", final_gid))
                cb = self._binfo.bilist.object(self._binfo.cbindex.x[gid_i])
                # multisplit cells call cb.multisplit() instead
                if cb.subtrees.count() > 0:
                    cb.multisplit(nc, self._binfo.msgid, pc, pc.id())
                    cell.gid = final_gid
                    continue

            pc.set_gid2node(final_gid, pc.id())
            pc.cell(final_gid, nc)
            cell.gid = final_gid  # update the cell.gid last (RNGs had to use the base gid)

        pc.multisplit()

    def enable_report(self, report_conf, target_name, use_coreneuron):
        """Placeholder for Engines implementing their own reporting

        Args:
            report_conf: The dict containing the report configuration
            target_name: The target of the report
            use_coreneuron: Whether the simulator is CoreNeuron
        """
        pass

    def load_artificial_cell(self, gid, artificial_cell):
        logging.info(" > Adding Artificial cell for CoreNeuron")
        cell = EmptyCell(gid, artificial_cell)
        self._store_cell(gid, cell)
        nc = cell.connect2target(None)
        self._pc.set_gid2node(cell.gid, self._pc.id())
        self._pc.cell(cell.gid, nc)

    def _init_rng(self):
        rng_info = Nd.RNGSettings()
        self._global_seed = rng_info.getGlobalSeed()
        self._ionchannel_seed = rng_info.getIonChannelSeed()
        return rng_info

    def _store_cell(self, gid, cell):
        self._gid2cell[gid] = cell

    def getMEType(self, gid):
        return self._gid2cell[gid]

    def record_spikes(self, gids=None, append_spike_vecs=None):
        """Setup recording of spike events (crossing of threshold) for cells on this node
        """
        if not self._local_nodes:
            return
        spikevec, idvec = append_spike_vecs or (Nd.Vector(), Nd.Vector())
        if gids is None:
            gids = self._local_nodes.final_gids()

        for gid in gids:
            # only want to collect spikes of cell pieces with the soma (i.e. the real gid)
            if not self._binfo or self._binfo.thishost_gid(gid) == gid:
                self._pc.spike_record(gid, spikevec, idvec)
        return spikevec, idvec

    def register_connection_manager(self, conn_manager: ConnectionManagerBase):
        src_population = conn_manager.src_cell_manager.population_name
        if src_population in self._conn_managers_per_src_pop:
            logging.warning("Skip registering %s as a second pop source", conn_manager)
        else:
            self._conn_managers_per_src_pop[src_population] = conn_manager

    def post_stdinit(self):
        """Post stdinit actions, sublasses may override if needed"""
        pass


class GlobalCellManager:
    """
    GlobalCellManager is a wrapper over all Cell Managers so that we can query
    any cell from its global gid
    """

    def __init__(self):
        self._cell_managers = []  # [(offset, manager)}
        self._binfo = None
        self._pc = Nd.pc

    def register_manager(self, cell_manager):
        self._cell_managers.append(cell_manager)

    def finalize(self):
        self._cell_managers.sort(key=lambda x: x.local_nodes.offset)
        self._binfo = self._cell_managers[0]._binfo

    # Accessor methods (Keep CamelCase API for compatibility with existing hoc)
    # ----------------
    def getGidListForProcessor(self):
        from operator import add
        from functools import reduce
        return reduce(add, (man.getGidListForProcessor() for man in self._cell_managers))

    def getMEType(self, gid):
        cell_managers_iter = iter(self._cell_managers)
        prev_manager = next(cell_managers_iter)  # base cell manager
        for manager in cell_managers_iter:
            if manager.local_nodes.offset > gid:
                break
            prev_manager = manager
        return prev_manager._gid2cell[gid]

    def getCell(self, gid):
        """Retrieve a cell object given its gid.
        Note that this function handles multisplit cases incl converting to an
        spgid automatically \n
        Returns: Cell object
        """
        if self._binfo:
            # are we in load balance mode? must replace gid with spgid
            gid = self._binfo.thishost_gid(gid)
        return self._pc.gid2obj(gid)

    def getSpGid(self, gid):
        """Retrieve the spgid from a gid (provided we are using loadbalancing)

        Args:
            gid: The base gid (as read from start.ncs)

        Returns: The gid as it appears on this cpu (if this is the same as the base gid,
        then that is the soma piece)
        """
        if self._binfo:
            return self._binfo.thishost_gid(gid)
        return gid


class CellDistributor(CellManagerBase):
    """ Manages a group of cells for BBP simulations, V5 and V6

        Instantiated cells are stored locally (.cells property)
    """

    _cell_loaders = {
        "start.ncs": cell_readers.load_ncs,
        "circuit.mvd3": cell_readers.load_mvd3,
    }

    _sonata_with_extra_attrs = True  # Enable search extra node attributes

    def _init_config(self, circuit_conf, _pop):
        if not circuit_conf.CellLibraryFile:
            logging.warning("CellLibraryFile not set. Assuming legacy 'start.ncs'")
            circuit_conf.CellLibraryFile = "start.ncs"
        if circuit_conf.CellLibraryFile.endswith(".ncs"):
            self._node_format = NodeFormat.NCS
        elif circuit_conf.CellLibraryFile.endswith(".mvd3"):
            self._node_format = NodeFormat.MVD3
        self._is_v5_circuit = circuit_conf.CellLibraryFile == "start.ncs" or (
            circuit_conf.nrnPath and ospath.isfile(ospath.join(circuit_conf.nrnPath, "start.ncs"))
            and not ospath.isfile(ospath.join(circuit_conf.CircuitPath, "circuit.mvd3"))
        )
        super()._init_config(circuit_conf, _pop)

    def load_nodes(self, load_balancer=None, **kw):
        """gets gids from target, splits and returns a GidSet with all metadata
        """
        if self._node_format == NodeFormat.SONATA and self._sonata_with_extra_attrs:
            loader = lambda *args, **kw: cell_readers.load_nodes(*args, **kw, has_extra_data=True)
        else:
            loader = self._cell_loaders.get(self._circuit_conf.CellLibraryFile,
                                            cell_readers.load_nodes)
        log_verbose("Nodes Format: %s, Loader: %s", self._node_format, loader.__name__)
        return super().load_nodes(load_balancer, _loader=loader, **kw)

    def _instantiate_cells(self, *_):
        if self.CellType is not NotImplemented:
            return super()._instantiate_cells(self.CellType)
        conf = self._circuit_conf
        CellType = Cell_V5 if self._is_v5_circuit else Cell_V6
        CellType.morpho_extension = conf.MorphologyType
        log_verbose("Loading metypes from: %s", conf.METypePath)
        log_verbose("Loading '%s' morphologies from: %s",
                    conf.MorphologyType, conf.MorphologyPath)
        super()._instantiate_cells(CellType)


class LoadBalance:
    """
    Class handling the several types of load_balance info, including
    generating and loading the various files.

    LoadBalance instances target the current system (cpu count) and circuit
    (nrn_path) BUT check/create load distribution for any given target.
    """
    cx_datafolder = "sim_conf"
    cxinfo_filename = ospath.join(cx_datafolder, "cxinfo.txt")
    _cx_filename_tpl = ospath.join(cx_datafolder, "cx_%s.dat")
    _cpu_assign_filename_tpl = ospath.join(cx_datafolder, "cx_%s.%s.dat")

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
    def valid_load_distribution(self, target_spec) -> bool:
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
                or not target_spec.name
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
        if not ospath.isdir(ospath.dirname(new_cx_filename)):
            os.mkdir(ospath.dirname(new_cx_filename))
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

        if not ospath.isdir(ospath.dirname(self.cxinfo_filename)):
            os.mkdir(ospath.dirname(self.cxinfo_filename))
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
        msfactor = 1e6 if self.lb_mode == LoadBalanceMode.WholeCell else 0.8
        out_filename = self._cx_filename_tpl % target_str

        cx_cells = self._compute_complexities(mcomplex, cell_distributor)
        total_cx, max_cx = self._cell_complexity_total_max(cx_cells)
        lcx = self._get_optimal_piece_complexity(total_cx,
                                                 self.target_cpu_count,
                                                 msfactor)
        ms_list = []
        tmp = Nd.Vector()

        for cell in cell_distributor.cells:
            mcomplex.cell_complexity(cell.CellRef)
            mcomplex.multisplit(cell.gid, lcx, tmp)
            ms_list.append(tmp.c())

        # To output build independently the contents of the file then append
        ostring = StringIO()
        if MPI.rank == 0:
            ostring.write("1\n%d\n" % cell_distributor.total_cells)
            logging.info("LB Info: TC=%.3f MC=%.3f OptimalCx=%.3f FileName=%s",
                         total_cx, max_cx, lcx, out_filename)
        for ms in ms_list:
            self._write_msdat(ostring, ms)

        all_ranks_cx = MPI.py_gather(ostring.getvalue(), 0)
        if MPI.rank == 0:
            if not ospath.isdir(ospath.dirname(out_filename)):
                os.mkdir(ospath.dirname(out_filename))
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
        for gid in cell_distributor.local_nodes.final_gids():
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
        Nd.mymetis3(ospath.join(self.cx_datafolder, "cx_%s" % target_name), self.target_cpu_count)

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
