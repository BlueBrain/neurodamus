"""
Mechanisms to load and balance cells across the computing resources.
"""
from __future__ import absolute_import, print_function
import abc
import hashlib
import logging  # active only in rank 0 (init)
import os
import weakref
from contextlib import contextmanager
from io import StringIO
from os import path as ospath
from pathlib import Path

import numpy

from .connection_manager import ConnectionManagerBase
from .core import MPI, mpi_no_errors, run_only_rank0
from .core import NeurodamusCore as Nd
from .core import ProgressBarRank0 as ProgressBar
from .core.configuration import ConfigurationError
from .core.configuration import GlobalConfig, LoadBalanceMode, LogLevel, find_input_file, SimConfig
from .core.nodeset import NodeSet
from .io import cell_readers
from .lfp_manager import LFPManager
from .metype import Cell_V6, EmptyCell
from .target_manager import TargetSpec
from .utils import compat
from .utils.logging import log_verbose, log_all
from .utils.memory import DryRunStats, get_mem_usage_kb


class VirtualCellPopulation:
    """
    A virtual cell population offers a compatible interface with Cell Manager,
    however it doesnt instantiate cells.
    It is mostly used as source of projections
    """
    _total_count = 0

    def __init__(self, population_name, gids=None, circuit_target=None):
        """Initializes a VirtualCellPopulation

        A virtual manager will have minimal set of attributes, namely
        the population name, the target name and the NodeSet
        """
        self.population_name = population_name
        self.circuit_target = circuit_target
        self.local_nodes = NodeSet(gids).register_global(population_name or '')
        VirtualCellPopulation._total_count += 1
        if VirtualCellPopulation._total_count > 1:
            logging.warning("For non-sonata circuit, "
                            "only a single Virtual Cell Population works with REPLAY")

    is_default = property(lambda self: False)
    is_virtual = property(lambda self: True)

    def __str__(self):
        return "([VIRT] {:s})".format(self.population_name)


class _CellManager(abc.ABC):

    @abc.abstractmethod
    def get_final_gids(self):
        ...

    @abc.abstractmethod
    def get_cell(self, gid):
        ...

    def get_cellref(self, gid):
        """Retrieve a cell object given its gid.
        Note that this function handles multisplit cases incl converting to an
        spgid automatically \n
        Returns: Cell object
        """
        if self._binfo:
            # are we in load balance mode? must replace gid with spgid
            gid = self._binfo.thishost_gid(gid)
        return self._pc.gid2obj(gid)

    # Methods for compat with hoc

    @abc.abstractmethod
    def getGidListForProcessor(self):
        ...

    def getMEType(self, gid):
        return self.get_cell(gid)

    def getCell(self, gid):
        return self.get_cellref(gid)


class CellManagerBase(_CellManager):

    CellType = NotImplemented  # please override
    """The underlying Cell type class

    signature:
        __init__(self, gid, cell_info, circuit_conf)
    """

    _node_loader = None
    """Default function implementing the loading of nodes data

    signature:
        load(circuit_conf, gidvec, stride=1, stride_offset=0)
    """
    def __init__(self, circuit_conf, target_manager, _run_conf=None, **_kw):
        """Initializes CellDistributor

        Args:
            circuit_conf: The "Circuit" config block
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

        if type(circuit_conf.CircuitPath) is str:
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

    def is_initialized(self):
        return self._local_nodes is not None

    def __str__(self):
        return "({}: {})".format(self.__class__.__name__, str(self._population_name))

    # Compatibility with neurodamus-core (used by TargetManager, CompMapping)
    # Create hoc vector from numpy.array
    def getGidListForProcessor(self):
        return compat.hoc_vector(self.local_nodes.final_gids())

    def get_final_gids(self):
        return numpy.array(self.local_nodes.final_gids())

    def _init_config(self, circuit_conf, pop):
        if not ospath.isabs(circuit_conf.CellLibraryFile):
            circuit_conf.CellLibraryFile = find_input_file(circuit_conf.CellLibraryFile)
        if not pop:   # Last attempt to get pop name
            pop = self._get_sonata_population_name(circuit_conf.CellLibraryFile)
            logging.info(" -> Discovered node population name: %s", pop)
        if not pop and circuit_conf._name:
            pop = circuit_conf._name
            logging.warning("(Compat) Assuming population name from Circuit: %s", pop)
        self._population_name = pop
        if not pop:
            logging.warning("Could not discover population name. Assuming '' (empty)")
            if not self.is_default:
                raise Exception("Only the default population can be unnamed")
        is_base_pop = self.is_default or circuit_conf.get("no_offset")
        self._local_nodes = NodeSet().register_global(pop, is_base_pop)

    @classmethod
    def _get_sonata_population_name(self, node_file):
        import libsonata  # only for SONATA
        pop_names = libsonata.NodeStorage(node_file).population_names
        assert len(pop_names) == 1
        return next(iter(pop_names), None)

    def load_nodes(self, load_balancer=None, *, _loader=None, loader_opts=None):
        """Top-level loader of nodes.
        """
        if self._local_nodes is None:
            return
        conf = self._circuit_conf
        _loader = _loader or self._node_loader
        loader_f = (lambda *args: _loader(*args, **loader_opts)) if loader_opts else _loader

        logging.info("Reading Nodes (METype) info from '%s'", conf.CellLibraryFile)
        if load_balancer and \
           hasattr(load_balancer, 'population') and \
           load_balancer.population != self._target_spec.population:
            log_verbose("Load balance object doesn't apply to '%s'", self._target_spec.population)
            load_balancer = None
        if not load_balancer or SimConfig.dry_run:
            gidvec, me_infos, *cell_counts = self._load_nodes(loader_f)
        elif load_balancer and SimConfig.loadbal_mode == LoadBalanceMode.Memory:
            gidvec, me_infos, *cell_counts = self._load_nodes_balance_mem(loader_f, load_balancer)
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
            target_gids = self._target_manager.get_target(target_spec).get_raw_gids()
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
        self._binfo = load_balancer.load_balance_info(target_spec)
        # self._binfo has gidlist, but gids can appear multiple times
        all_gids = numpy.unique(
            self._binfo.gids.as_numpy().astype("uint32") - self._local_nodes.offset
        )
        total_cells = len(all_gids)
        gidvec, me_infos, full_size = loader_f(self._circuit_conf, all_gids)
        return gidvec, me_infos, total_cells, full_size

    def _load_nodes_balance_mem(self, loader_f, load_balancer):
        targetspec: TargetSpec = self._target_spec

        population = targetspec.population
        all_gids = load_balancer[population][MPI.rank]
        logging.debug("Loading %d cells in rank %d", len(all_gids), MPI.rank)
        total_cells = len(all_gids)
        gidvec, me_infos, full_size = loader_f(self._circuit_conf, all_gids)
        return gidvec, me_infos, total_cells, full_size

    # -
    def finalize(self, **opts):
        """Instantiates cells and initializes the network in the simulator.

        Note: it should be called after all cell distributors have done load_nodes()
            so gids offsets are final.
        """
        if self._local_nodes is None:
            return
        logging.info("Finalizing cells... Gid offset: %d", self._local_nodes.offset)
        self._instantiate_cells(**opts)
        self._update_targets_local_gids()
        self._init_cell_network()
        self._local_nodes.clear_cell_info()

    @mpi_no_errors
    def _instantiate_cells(self, _CellType=None, **_opts):
        CellType = _CellType or self.CellType
        assert CellType is not None, "Undefined CellType in Manager"
        Nd.execute("xopen_broadcast_ = 0")

        logging.info(" > Instantiating cells... (%d in Rank 0)", len(self._local_nodes))
        cell_offset = self._local_nodes.offset

        if GlobalConfig.verbosity >= LogLevel.DEBUG:
            gid_info_items = self._local_nodes.items()
        else:
            gid_info_items = ProgressBar.iter(self._local_nodes.items(), len(self._local_nodes))

        for gid, cell_info in gid_info_items:
            cell = CellType(gid, cell_info, self._circuit_conf)
            self._store_cell(gid + cell_offset, cell)

    @mpi_no_errors
    def _instantiate_cells_dry(self, CellType, skip_metypes, **_opts):
        """
        Instantiates the subset of selected cells while measuring memory taken by each metype

        Args:
            CellType: The cell type class
            full_memory_counter: The memory counter to be updated for each metype
        """
        assert CellType is not None, "Undefined CellType in Manager"
        Nd.execute("xopen_broadcast_ = 0")

        logging.info(" > Dry run on cells... (%d in Rank 0)", len(self._local_nodes))
        cell_offset = self._local_nodes.offset
        gid_info_items = self._local_nodes.items()

        prev_metype = None
        prev_memory = get_mem_usage_kb()
        metype_n_cells = 0
        memory_dict = {}
        MAX_CELLS = 50

        def store_metype_stats(metype, n_cells):
            nonlocal prev_memory
            end_memory = get_mem_usage_kb()
            memory_allocated = end_memory - prev_memory
            log_all(logging.DEBUG, " * METype %s: %.1f KiB averaged over %d cells",
                    metype, memory_allocated/n_cells, n_cells)
            memory_dict[metype] = max(0, memory_allocated / n_cells)
            prev_memory = end_memory

        for gid, cell_info in gid_info_items:
            if cell_info is None:
                continue
            metype = "{0.mtype}-{0.etype}".format(cell_info)
            if metype in skip_metypes:
                continue
            if prev_metype is not None and metype != prev_metype:
                store_metype_stats(prev_metype, metype_n_cells)
                metype_n_cells = 0
            if metype_n_cells >= MAX_CELLS:
                continue
            cell = CellType(gid, cell_info, self._circuit_conf)
            self._store_cell(gid + cell_offset, cell)
            prev_metype = metype
            metype_n_cells += 1

        if prev_metype is not None and metype_n_cells > 0:
            store_metype_stats(prev_metype, metype_n_cells)

        return memory_dict

    def _update_targets_local_gids(self):
        logging.info(" > Updating targets")
        # Add local gids to matching targets
        self._target_manager.register_local_nodes(self._local_nodes)

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

    def get_cell(self, gid):
        return self._gid2cell[gid]

    def get_cellref(self, gid):
        return self._gid2cell[gid]._cellref

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
        """Post stdinit actions"""
        if self._circuit_conf.DetailedAxon:
            for c in self.cells:
                c.delete_axon()


class GlobalCellManager(_CellManager):
    """
    GlobalCellManager is a wrapper over all Cell Managers so that we can query
    any cell from its global gid
    """

    def __init__(self):
        self._cell_managers = []
        self._pc = Nd.pc
        self._lfp_manager = LFPManager()

    def register_manager(self, cell_manager):
        self._cell_managers.append(cell_manager)

    def finalize(self):
        self._cell_managers.sort(key=lambda x: x.local_nodes.offset)

    # Accessor methods (Keep CamelCase API for compatibility with existing hoc)
    # ----------------
    def getGidListForProcessor(self):

        def _hoc_append(vec_a, vec_b):
            return vec_a.append(vec_b)

        from functools import reduce
        return reduce(_hoc_append, (man.getGidListForProcessor() for man in self._cell_managers))

    def get_final_gids(self):
        return numpy.concatenate([man.get_final_gids() for man in self._cell_managers])

    def _find_manager(self, gid):
        cell_managers_iter = iter(self._cell_managers)
        prev_manager = next(cell_managers_iter)  # base cell manager
        for manager in cell_managers_iter:
            if manager.local_nodes.offset > gid:
                break
            prev_manager = manager
        return prev_manager

    def get_cell(self, gid):
        manager = self._find_manager(gid)
        return manager.get_cell(gid)

    def get_cellref(self, gid):
        """Retrieve a cell object given its gid.
        Note that this function handles multisplit cases incl converting to an
        spgid automatically \n
        Returns: Cell object
        """
        manager = self._find_manager(gid)
        if manager._binfo:
            # are we in load balance mode? must replace gid with spgid
            gid = manager._binfo.thishost_gid(gid)
        return self._pc.gid2obj(gid)

    def getSpGid(self, gid):
        """Retrieve the spgid from a gid (provided we are using loadbalancing)

        Args:
            gid: The base gid (as read from start.ncs)

        Returns: The gid as it appears on this cpu (if this is the same as the base gid,
        then that is the soma piece)
        """
        manager = self._find_manager(gid)
        if manager._binfo:
            return manager._binfo.thishost_gid(gid)
        return gid

    def getPopulationInfo(self, gid):
        manager = self._find_manager(gid)
        return manager.population_name, manager.local_nodes.offset


class CellDistributor(CellManagerBase):
    """ Manages a group of cells for BBP simulations, V5 and V6

        Instantiated cells are stored locally (.cells property)
    """

    _sonata_with_extra_attrs = True  # Enable search extra node attributes

    def _init_config(self, circuit_conf, _pop):
        if not circuit_conf.CellLibraryFile:
            raise ConfigurationError("CellLibraryFile not set")

        super()._init_config(circuit_conf, _pop)

    def load_nodes(self, load_balancer=None, **kw):
        """gets gids from target, splits and returns a GidSet with all metadata
        """
        loader_opts = kw.pop("loader_opts", {}).copy()
        all_cell_requirements = SimConfig.cell_requirements
        cell_requirements = all_cell_requirements.get(self._population_name) or (
            self.is_default and all_cell_requirements.get(None)
        )
        loader = cell_readers.load_sonata
        loader_opts["node_population"] = self._population_name  # mandatory in Sonata
        loader_opts["load_dynamic_props"] = cell_requirements
        loader_opts["has_extra_data"] = self._sonata_with_extra_attrs

        log_verbose("Nodes Format: SONATA , Loader: %s", loader.__name__)
        return super().load_nodes(load_balancer, _loader=loader, loader_opts=loader_opts)

    def _instantiate_cells(self, dry_run_stats_obj: DryRunStats = None, **opts):
        """
        Instantiates cells, honouring dry_run if provided

        Args:
            dry_run_store_stats: Do a dry-run and update the inner fields accordingly
        """
        if self.CellType is not NotImplemented:
            return super()._instantiate_cells(self.CellType)
        conf = self._circuit_conf
        CellType = Cell_V6
        if conf.MorphologyType:
            CellType.morpho_extension = conf.MorphologyType

        log_verbose("Loading metypes from: %s", conf.METypePath)
        log_verbose("Loading '%s' morphologies from: %s",
                    CellType.morpho_extension, conf.MorphologyPath)
        if dry_run_stats_obj is None:
            super()._instantiate_cells(CellType, **opts)
        else:
            cur_metypes_mem = dry_run_stats_obj.metype_memory
            memory_dict = self._instantiate_cells_dry(CellType, cur_metypes_mem, **opts)
            log_verbose("Updating global dry-run memory counters with %d items", len(memory_dict))
            cur_metypes_mem.update(memory_dict)


class LoadBalance:
    """
    Class handling the several types of load_balance info, including
    generating and loading the various files.

    LoadBalance instances target the current system (cpu count) and circuit
    BUT check/create load distribution for any given target.
    The circuit is identified by the nodes file AND population.

    NOTE: Given the heavy costs of computing load balance, some state files are created
    which allow the balance info to be reused. These are

     - cx_{TARGET}.dat: File with complexity information for the cells of a given target
     - cx_{TARGET}.{CPU_COUNT}.dat: The file assigning cells/pieces to individual CPUs ranks.

    For more information refer to the developer documentation.
    """
    _base_output_dir = "sim_conf"
    _circuit_lb_dir_tpl = "_loadbal_%s.%s"      # Placeholders are (file_src_hash, population)
    _cx_filename_tpl = "cx_%s#.dat"             # use # to well delimiter the target name
    _cpu_assign_filename_tpl = "cx_%s#.%s.dat"  # prefix must be same (imposed by Neuron)

    def __init__(self, balance_mode, nodes_path, pop, target_manager, target_cpu_count=None):
        """
        Creates a new Load Balance object, associated with a given node file
        """
        self.lb_mode = balance_mode
        self.target_cpu_count = target_cpu_count or MPI.size
        self._target_manager = target_manager
        self._valid_loadbalance = set()
        self.population = pop or ""
        self._lb_dir, self._cx_targets = self._get_circuit_loadbal_dir(nodes_path, self.population)
        log_verbose("Found existing targets with loadbal: %s", self._cx_targets)

    @classmethod
    @run_only_rank0
    def _get_circuit_loadbal_dir(cls, node_file, pop) -> tuple:
        """Ensure lbal dir exists. dir may be crated on rank 0"""
        lb_dir = cls._loadbal_dir(node_file, pop)
        if lb_dir.is_dir():
            return lb_dir, cls._get_lbdir_targets(lb_dir)

        logging.info("Creating load balance dir %s", lb_dir)
        os.makedirs(lb_dir)
        return lb_dir, set()

    @classmethod
    def _get_lbdir_targets(cls, lb_dir: Path) -> list:
        """Inspects the load-balance folder and detects which targets are load balanced"""
        prefix, suffix = cls._cx_filename_tpl.split("%s")
        return set(
            fname.name[len(prefix):-len(suffix)]
            for fname in lb_dir.glob(cls._cx_filename_tpl.replace("%s", "*"))
        )

    @run_only_rank0
    def valid_load_distribution(self, target_spec: TargetSpec) -> bool:
        """Checks whether we have valid load-balance files, attempting to
        derive from larger target distributions if possible.
        """
        if (target_spec.population or "") != self.population:
            logging.info(" => Load balance Population mismatch. Requested: %s, Existing: %s",
                         target_spec.population, self.population)
            return False

        target_name = target_spec.simple_name

        # Check cache
        if target_name in self._valid_loadbalance:
            logging.info(" => Cell distribution from Load Balance is valid")
            return True

        # A valid load-distribution requires BOTH the cx and the cpu_assign files.
        if self._cx_valid(target_spec):
            cpu_assign_filename = self._cpu_assign_filename(target_name)
            if cpu_assign_filename.is_file():
                logging.info(" => Found valid load balance: %s", cpu_assign_filename)
            else:
                # Still need to derive the CPU assignment
                logging.info(" => Found valid complexity file: %s", self._cx_filename(target_name))
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
    def _reuse_cell_complexity(self, target_spec: TargetSpec) -> bool:
        """Check if the complexities of all target gids were already calculated
        for another target.
        """
        # Abort if there are no cx files yet or in case now we request full circuit
        # since its impossible to have a superset of it
        if (not target_spec.name or not self._cx_targets):
            logging.info(" => Target Cx reusing is not available.")
            return False

        logging.info("Attempt reusing cx files from other targets...")
        target_gids = self._get_target_gids(target_spec)
        cx_other = {}

        for previous_target in self._cx_targets:
            log_verbose("Trying previous cx file on target %s", previous_target)
            ref_filename = self._cx_filename(previous_target)
            if self._cx_contains_gids(ref_filename, target_gids, cx_other):
                break  # done!
            log_verbose("  - Target is not a superset. Ignoring.")
        else:
            logging.info(" => Did not find any suitable target")
            return False

        new_cx_filename = self._cx_filename(target_spec.simple_name)
        logging.info("Target %s is a subset of the target %s. Generating %s",
                     target_spec.name, previous_target, new_cx_filename)

        # Write the new cx file since Neuron needs it to do CPU assignment
        with open(new_cx_filename, "w") as newfile:
            self._write_msdat_dict(newfile, cx_other, target_gids)
        # register
        self._cx_targets.add(target_spec.simple_name)
        return True

    # -
    def _cx_valid(self, target_spec) -> bool:
        """Determine if valid complexity files exist for the provided circuit and
        target spec, otherwise return False -> we need to regen load balance info
        """
        # _cx_targets populated at instantiation. If not there, no chance. If in list, verify
        if not self._cx_targets:
            logging.info(" => No complexity files for current circuit yet")
            return False

        target_name = target_spec.simple_name
        cx_filename = self._cx_filename(target_name)

        if target_name not in self._cx_targets:
            logging.info(" => No Cx files available for requested target")
            return False

        if target_spec:  # target provided, otherwise everything
            target_gids = self._get_target_gids(target_spec)
            if not self._cx_contains_gids(cx_filename, target_gids):
                logging.warning(" => %s invalid: changed target definition!", cx_filename)
                return False
        return True

    @classmethod
    def _cx_contains_gids(cls, cxpath, target_gids, out_cx=None) -> bool:
        """Checks a cx file contains complexities for given gids
        """
        if not cxpath.is_file():
            log_verbose("  - cxpath doesnt exist: %s", cxpath)
            return False
        with open(cxpath, "r") as f:
            cx_saved = cls._read_msdat(f)
        if not set(cx_saved.keys()) >= set(target_gids):
            log_verbose("  - Not all GIDs in target %s %s", set(cx_saved.keys()), set(target_gids))
            return False
        if out_cx is not None:
            out_cx.update(cx_saved)
        return True

    @contextmanager
    def generate_load_balance(self, target_spec, cell_distributor):
        """Context manager that creates load balance for the circuit instantiated within

        Args:
            target_str: a string representation of the target.
            cell_distributor: the cell distributor object to which we can query
                the cells to be load balanced
        """
        mcomplex = Nd.MComplexLoadBalancer()  # init mcomplex before building circuit
        yield
        target_str = target_spec.simple_name
        self._compute_save_complexities(target_str, mcomplex, cell_distributor)
        self._cpu_assign(target_str)
        self._valid_loadbalance.add(target_str)

    @mpi_no_errors
    def _compute_save_complexities(self, target_str, mcomplex, cell_distributor):
        msfactor = 1e6 if self.lb_mode == LoadBalanceMode.WholeCell else 0.8
        out_filename = self._cx_filename(target_str)

        cx_cells = self._compute_complexities(mcomplex, cell_distributor)
        total_cx, max_cx = self._cell_complexity_total_max(cx_cells)
        lcx = self._get_optimal_piece_complexity(total_cx,
                                                 self.target_cpu_count,
                                                 msfactor)
        logging.info("LB Info: TC=%.3f MC=%.3f OptimalCx=%.3f FileName=%s",
                     total_cx, max_cx, lcx, out_filename)

        ms_list = []
        tmp = Nd.Vector()

        for cell in cell_distributor.cells:
            mcomplex.cell_complexity(cell.CellRef)
            mcomplex.multisplit(cell.gid, lcx, tmp)
            ms_list.append(tmp.c())

        # To output build independently the contents of the file then append
        ostring = StringIO()
        for ms in ms_list:
            self._write_msdat(ostring, ms)

        all_ranks_cx = MPI.py_gather(ostring.getvalue(), 0)
        if MPI.rank == 0:
            with open(out_filename, "w") as fp:
                fp.write("1\n%d\n" % cell_distributor.total_cells)
                for cx_info in all_ranks_cx:
                    fp.write(cx_info)
        # register
        self._cx_targets.add(target_str)

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
        Results are written to file. basename.<NCPU>.dat
        """
        logging.info("Assigning Cells <-> %d CPUs [mymetis3]", self.target_cpu_count)
        base_filename = self._cx_filename(target_name, True)
        Nd.mymetis3(base_filename, self.target_cpu_count)

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
                gid, _cx, piece_count = [int(float(x)) for x in line.split()]
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
    def _get_target_gids(self, target_spec) -> numpy.ndarray:
        return self._target_manager.get_target(target_spec).get_gids()

    def load_balance_info(self, target_spec):
        """ Loads a load-balance info for a given target.
        NOTE: Please ensure the load balance exists or is derived before calling this function
        """
        bal_filename = self._cx_filename(target_spec.simple_name, True)
        return Nd.BalanceInfo(bal_filename, MPI.rank, MPI.size)

    @classmethod
    def _loadbal_dir(cls, nodefile, population) -> Path:
        """Returns the dir where load balance files are stored for a given nodes file"""
        nodefile_hash = hashlib.md5(nodefile.encode()).digest().hex()[:10]
        return Path(cls._base_output_dir) / (cls._circuit_lb_dir_tpl % (nodefile_hash, population))

    def _cx_filename(self, target_str, basename_str=False) -> Path:
        """Gets the filename of a cell complexity file for a given target"""
        fname = self._lb_dir / (self._cx_filename_tpl % target_str)
        return str(fname)[:-4] if basename_str else fname

    def _cpu_assign_filename(self, target_str) -> Path:
        """Gets the CPU assignment filename for a given target, according to target CPU count"""
        return self._lb_dir / (self._cpu_assign_filename_tpl % (target_str, self.target_cpu_count))

    @staticmethod
    def select_lb_mode(sim_config, run_conf, target):
        """ A method which selects the load balance mode according to run config
        """
        # Check / set load balance mode
        lb_mode = sim_config.loadbal_mode
        if lb_mode == LoadBalanceMode.MultiSplit:
            if not sim_config.use_coreneuron:
                logging.info("Load Balancing ENABLED. Mode: MultiSplit")
            else:
                logging.warning("Load Balancing mode CHANGED to WholeCell for CoreNeuron")
                lb_mode = LoadBalanceMode.WholeCell

        elif lb_mode == LoadBalanceMode.WholeCell:
            logging.info("Load Balancing ENABLED. Mode: WholeCell")

        elif lb_mode is None:
            if target.is_void():
                lb_mode, reason = LoadBalanceMode.RoundRobin, "No target set, unknown cell count"
            else:
                lb_mode, reason = LoadBalanceMode.auto_select(sim_config.use_neuron,
                                                              target.gid_count(),
                                                              run_conf["Duration"])
            logging.warning("Load Balance AUTO-SELECTED: %s. Reason: %s", lb_mode.name, reason)

        return lb_mode
