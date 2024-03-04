# Neurodamus
# Copyright 2018 - Blue Brain Project, EPFL

from __future__ import absolute_import
import gc
import glob
import itertools
import logging
import math
import os
import subprocess
from os import path as ospath
from collections import namedtuple, defaultdict
from contextlib import contextmanager

from .core import MPI, mpi_no_errors, return_neuron_timings, run_only_rank0, SimulationProgress
from .core import NeurodamusCore as Nd
from .core.configuration import CircuitConfig, Feature, GlobalConfig, SimConfig
from .core._engine import EngineBase
from .core._shmutils import SHMUtil
from .core.configuration import ConfigurationError, find_input_file, get_debug_cell_gid
from .core.nodeset import PopulationNodes
from .cell_distributor import CellDistributor, VirtualCellPopulation, GlobalCellManager
from .cell_distributor import LoadBalance, LoadBalanceMode
from .connection_manager import SynapseRuleManager, edge_node_pop_names
from .gap_junction import GapJunctionManager
from .replay import MissingSpikesPopulationError, SpikeManager
from .stimulus_manager import StimulusManager
from .modification_manager import ModificationManager
from .neuromodulation_manager import NeuroModulationManager
from .target_manager import TargetSpec, TargetManager
from .utils import compat
from .utils.logging import log_stage, log_verbose, log_all
from .utils.memory import DryRunStats, trim_memory, pool_shrink, free_event_queues, print_mem_usage
from .utils.memory import import_allocation_stats
from .utils.timeit import TimerManager, timeit
from .core.coreneuron_configuration import CoreConfig, CompartmentMapping
from .io.sonata_config import ConnectionTypes
# Internal Plugins
from . import ngv as _ngv  # NOQA


class METypeEngine(EngineBase):
    CellManagerCls = CellDistributor
    InnerConnectivityCls = SynapseRuleManager
    ConnectionTypes = {
        None: SynapseRuleManager,
        ConnectionTypes.Synaptic: SynapseRuleManager,
        ConnectionTypes.GapJunction: GapJunctionManager,
        ConnectionTypes.NeuroModulation: NeuroModulationManager
    }
    CircuitPrecedence = 0


class CircuitManager:
    """
    Holds and manages populations and associated nodes and edges

    For backward compat, base population doesnt have a population name (it is '')
    All other nodes must have a name or read from sonata pop name
    As so, Sonata is preferred when using multiple node files
    """

    def __init__(self):
        self.node_managers = {}  # dict {pop_name -> cell_manager}  # nrn pop is None
        self.virtual_node_managers = {}   # same, but for virtual ones (no cells)
        self.edge_managers = defaultdict(list)  # dict {(src_pop, dst_pop) -> list[synapse_manager]}
        self.alias = {}          # dict {name -> pop_name}
        self.global_manager = GlobalCellManager()
        self.global_target = TargetManager.create_global_target()

    def initialized(self):
        return bool(self.node_managers)

    def register_node_manager(self, cell_manager):
        pop = cell_manager.population_name
        if pop in self.node_managers:
            raise ConfigurationError("Already existing node manager for population %s" % pop)
        self.node_managers[pop] = cell_manager
        self.alias[cell_manager.circuit_name] = pop
        self.global_manager.register_manager(cell_manager)
        if cell_manager.is_initialized():
            self.global_target.append_nodeset(cell_manager.local_nodes)

    def _new_virtual_node_manager(self, circuit):
        """Instantiate a new virtual node manager explicitly."""
        # Only happens with Sonata config files
        import libsonata
        storage = libsonata.NodeStorage(circuit.CellLibraryFile)
        pop_name, _ = circuit.CircuitTarget.split(":")  # Sonata config fills population
        node_size = storage.open_population(pop_name).size
        gid_vec = list(range(1, node_size+1))
        virtual_cell_manager = VirtualCellPopulation(pop_name, gid_vec)
        self.virtual_node_managers[pop_name] = virtual_cell_manager
        self.global_target.append_nodeset(virtual_cell_manager.local_nodes)
        return virtual_cell_manager

    @staticmethod
    def new_node_manager_bare(circuit: CircuitConfig, target_manager, run_conf, **kwargs):
        engine = circuit.Engine or METypeEngine
        CellManagerCls = engine.CellManagerCls or CellDistributor
        return CellManagerCls(circuit, target_manager, run_conf, **kwargs)

    def new_node_manager(self, circuit, target_manager, run_conf, *, load_balancer=None, **kwargs):
        if circuit.get("PopulationType") == "virtual":
            return self._new_virtual_node_manager(circuit)
        cell_manager = self.new_node_manager_bare(circuit, target_manager, run_conf, **kwargs)
        cell_manager.load_nodes(load_balancer, **kwargs)
        self.register_node_manager(cell_manager)
        return cell_manager

    def get_node_manager(self, name):
        name = self.alias.get(name, name)
        return self.node_managers.get(name)

    def has_population(self, pop_name):
        return pop_name in self.node_managers

    def unalias_pop_keys(self, source, destination):
        """Un-alias population names"""
        return self.alias.get(source, source), self.alias.get(destination, destination)

    def get_edge_managers(self, source, destination):
        edge_pop_keys = self.unalias_pop_keys(source, destination)
        return self.edge_managers.get(edge_pop_keys) or []

    def get_edge_manager(self, source, destination, conn_type=SynapseRuleManager):
        managers = [manager for manager in self.get_edge_managers(source, destination)
                    if isinstance(manager, conn_type)]
        return managers[0] if managers else None

    def get_create_edge_manager(self, conn_type, source, destination, src_target,
                                manager_args=(), **kw):
        source, destination = self.unalias_pop_keys(source, destination)
        manager = self.get_edge_manager(source, destination, conn_type)
        if manager:
            return manager

        if not self.has_population(destination):
            # This is likely an error, except...
            if src_target.population == '' and self.has_population(''):
                logging.warning("Sonata Edges target population %s was not found. "
                                "Since base population is unknown, assuming that's the target.\n"
                                "To silence this warning please switch to Sonata nodes or specify "
                                "the base population by prefixing CircuitTarget with pop_name:",
                                destination)
                self.alias[destination] = ''
                destination = ''
                source = self.alias.get(source)  # refresh unaliasing
            else:
                raise ConfigurationError("Can't find projection Node population: " + destination)

        src_manager = self.node_managers.get(source) or self.virtual_node_managers.get(source)
        if src_manager is None:  # src manager may not exist -> virtual
            log_verbose("No known population %s. Creating Virtual src for projection", source)
            if conn_type not in (SynapseRuleManager, _ngv.GlioVascularManager):
                raise ConfigurationError("Custom connections require instantiated source nodes")
            src_manager = VirtualCellPopulation(source, None, src_target.name)

        target_cell_manager = kw["cell_manager"] = self.node_managers[destination]
        kw["src_cell_manager"] = src_manager
        manager = conn_type(*manager_args, **kw)
        self.edge_managers[(source, destination)].append(manager)
        target_cell_manager.register_connection_manager(manager)
        return manager

    def all_node_managers(self):
        return self.node_managers.values()

    def all_synapse_managers(self):
        return itertools.chain.from_iterable(self.edge_managers.values())

    @property
    def base_cell_manager(self):
        return self.get_node_manager(None)

    @run_only_rank0
    def write_population_offsets(self):
        """Write infor in <output_dir>/populations_offset.dat
        format population name::gid offset::population alias
        The virtual population offset is also written for synapse replay in restore.
        """
        with open(self._pop_offset_file(create=True), "w") as f:
            pop_offsets, alias_pop = self.get_population_offsets()
            virtual_pop_offsets = self.get_virtual_population_offsets()
            for alias, pop in alias_pop.items():
                f.write("{}::{}::{}\n".format(pop or ' ', pop_offsets[pop], alias or ' '))
            for pop, offset in virtual_pop_offsets.items():
                f.write("{}::{}::{}\n".format(pop, offset, 'virtual'))

    def get_population_offsets(self):
        pop_offsets = {pop_name: node_manager.local_nodes.offset
                       for pop_name, node_manager in self.node_managers.items()}
        alias_pop = {alias: pop_name for alias, pop_name in self.alias.items()}
        return pop_offsets, alias_pop

    def get_virtual_population_offsets(self):
        pop_offsets = {pop_name: node_manager.local_nodes.offset
                       for pop_name, node_manager in self.virtual_node_managers.items()}
        return pop_offsets

    @classmethod
    def read_population_offsets(cls, read_virtual_pop=False):
        """Read population offsets from populations_offset.dat
        Args:
            read_virtual_pop: read virtual population info (for replay), no need for reporting
        """
        pop_offsets = {}
        alias_pop = {}
        pop_offset_file = cls._pop_offset_file()
        if SimConfig.restore_coreneuron:
            if MPI.rank == 0 and not os.path.exists(pop_offset_file):
                # RESTORE: link to populations_offset.dat besides save directory
                os.symlink(os.path.join(SimConfig.restore, "../populations_offset.dat"),
                           pop_offset_file)
            MPI.barrier()
        with open(pop_offset_file, "r") as f:
            offsets = [line.strip().split("::") for line in f]
            for entry in offsets:
                if not read_virtual_pop and entry[2] == 'virtual':
                    continue
                pop_offsets[entry[0] or None] = int(entry[1])
                alias_pop[entry[2] or None] = entry[0] or None
        return pop_offsets, alias_pop

    @classmethod
    def _pop_offset_file(self, create=False):
        outdir = ospath.join(SimConfig.output_root)
        create and os.makedirs(outdir, exist_ok=True)
        return ospath.join(outdir, "populations_offset.dat")

    def __del__(self):
        """ De-init. Edge managers must be destructed first """
        del self.edge_managers
        del self.virtual_node_managers
        del self.node_managers


class Node:
    """The Node class is the main entity for a distributed neurodamus execution.

    It internally instantiates parallel structures and distributes the cells among all the nodes.
    It is relatively low-level, for a standard run consider using the Neurodamus class instead.
    """

    _default_population = 'All'
    """The default population name for e.g. Reports."""

    def __init__(self, config_file, options=None):
        """ Creates a neurodamus executor
        Args:
            config_file: A Sonata config file
            options: A dictionary of run options typically coming from cmd line
        """
        if config_file:
            if config_file.endswith("BlueConfig"):
                raise ConfigurationError(
                    "Legacy format BlueConfig is not supported, please migrate to SONATA config")
            import libsonata
            conf = libsonata.SimulationConfig.from_file(config_file)
            Nd.init(log_filename=conf.output.log_file)
        else:
            Nd.init()  # ensure/load neurodamus mods
        self._run_conf: dict  # Multi-cycle runs preserve this

        # The Recipe being None is allowed internally for e.g. setting up multi-cycle runs
        # It shall not be used as Public API
        if config_file is not None:
            # This is global initialization, happening once, regardless of number of cycles
            log_stage("Setting up Neurodamus configuration")
            self._pc = Nd.pc
            self._spike_vecs = []
            self._spike_populations = []
            Nd.execute("cvode = new CVode()")
            SimConfig.init(config_file, options)
            if SimConfig.use_coreneuron:
                CoreConfig.output_root = SimConfig.output_root
                CoreConfig.datadir = SimConfig.coreneuron_datadir
                # Instantiate the CoreNEURON artificial cell object which is used to fill up
                # the empty ranks. This need to be done before the circuit is finitialized
                CoreConfig.instantiate_artificial_cell()
            self._run_conf = SimConfig.run_conf
            self._target_manager = TargetManager(self._run_conf)
            self._target_spec = TargetSpec(self._run_conf.get("CircuitTarget"))
            if SimConfig.use_neuron:
                self._sonatareport_helper = Nd.SonataReportHelper(Nd.dt, True)
            self._base_circuit: CircuitConfig = SimConfig.base_circuit
            self._extra_circuits = SimConfig.extra_circuits
            self._pr_cell_gid = get_debug_cell_gid(options)
            self._core_replay_file = ""
            self._is_ngv_run = any(c.Engine.__name__ == "NGVEngine"
                                   for c in self._extra_circuits.values() if c.Engine)
            self._initial_rss = 0
            self._cycle_i = 0
            self._n_cycles = 1
            self._shm_enabled = False
            self._dry_run_stats = None
        else:
            self._run_conf  # Assert this is defined (if not multicyle runs are not properly set)

        # Init unconditionally
        self._circuits = CircuitManager()
        self._stim_list = None
        self._report_list = None
        self._stim_manager = None
        self._sim_ready = False
        self._jumpstarters = []
        self._cell_state_dump_t = None
        self._bbss = Nd.BBSaveState()

        # Register the global target and cell manager
        self._target_manager.register_target(self._circuits.global_target)
        self._target_manager.register_cell_manager(self._circuits.global_manager)

    #
    # public 'read-only' properties - object modification on user responsibility
    circuits = property(lambda self: self._circuits)
    target_manager = property(lambda self: self._target_manager)
    stim_manager = property(lambda self: self._stim_manager)
    stims = property(lambda self: self._stim_list)
    reports = property(lambda self: self._report_list)

    def all_circuits(self, exclude_disabled=True):
        if not exclude_disabled or self._base_circuit.CircuitPath:
            yield self._base_circuit
        yield from self._extra_circuits.values()

    # -
    def load_targets(self):
        """Initialize targets. Nodesets are loaded on demand.
        """
        # If a base population is specified register it before targets to create on demand
        base_population = self._run_conf.get("BasePopulation")
        if base_population:
            logging.info("Default population selected: %s", base_population)
            PopulationNodes.create_pop(base_population, is_base_pop=True)

        for circuit in self.all_circuits():
            log_verbose("Loading targets for circuit %s", circuit._name or "(default)")
            self._target_manager.load_targets(circuit)

    # -
    @mpi_no_errors
    @timeit(name="Compute LB")
    def compute_load_balance(self):
        """In case the user requested load-balance this function instantiates a
        CellDistributor to split cells and balance those pieces across the available CPUs.
        """
        log_stage("Computing Load Balance")
        circuit = self._base_circuit
        for name, circuit in self._extra_circuits.items():
            if circuit.get("PopulationType") != "virtual":
                break
        if circuit.get("PopulationType") == "virtual":
            logging.warning(
                "Cannot calculate the load balance because only virtual populations were found"
            )
            return None
        logging.info("Activating experimental LB for Sonata circuit '%s'", name)

        if not circuit.CircuitPath:
            logging.info(" => No circuit for Load Balancing. Skipping... ")
            return None

        _ = PopulationNodes.offset_freezer()  # Dont offset while in loadbal

        # Info about the cells to be distributed
        target_spec = TargetSpec(circuit.CircuitTarget)
        target = self.target_manager.get_target(target_spec)

        # Check / set load balance mode
        lb_mode = LoadBalance.select_lb_mode(SimConfig, self._run_conf, target)
        if lb_mode == LoadBalanceMode.RoundRobin:
            return None
        elif lb_mode == LoadBalanceMode.Memory:
            logging.info("Load Balancing ENABLED. Mode: Memory")
            alloc = import_allocation_stats("allocation.pkl.gz")
            for pop, ranks in alloc.items():
                for rank, gids in ranks.items():
                    logging.debug(f"Population: {pop}, Rank: {rank}, Number of GIDs: {len(gids)}")
            if MPI.rank == 0:
                unique_ranks = set(rank for pop in alloc.values() for rank in pop.keys())
                logging.debug("Unique ranks in allocation file: %s", len(unique_ranks))
                if MPI.size != len(unique_ranks):
                    raise ConfigurationError(
                        "The number of ranks in the allocation file is different from the number "
                        "of ranks in the current run. The allocation file was created with a "
                        "different number of ranks."
                    )
            return alloc

        # Build load balancer as per requested options
        data_src = circuit.CircuitPath
        pop = target_spec.population
        load_balancer = LoadBalance(lb_mode, data_src, pop, self._target_manager)

        if load_balancer.valid_load_distribution(target_spec):
            logging.info("Load Balancing done.")
            return load_balancer

        logging.info("Could not reuse load balance data. Doing a Full Load-Balance")
        cell_dist = self._circuits.new_node_manager(circuit, self._target_manager, self._run_conf)
        with load_balancer.generate_load_balance(target_spec, cell_dist):
            # Instantiate a basic circuit to evaluate complexities
            cell_dist.finalize()
            self._circuits.global_manager.finalize()
            SimConfig.update_connection_blocks(self._circuits.alias)
            target_manager = self._target_manager
            self._create_synapse_manager(SynapseRuleManager, self._base_circuit, target_manager)

        # reset since we instantiated with RR distribution
        Nd.t = .0  # Reset time
        self.clear_model()

        return load_balancer

    # -
    @mpi_no_errors
    @timeit(name="Cell creation")
    def create_cells(self, load_balance=None):
        """Instantiate and distributes the cells of the network.
        Any targets will be updated to know which cells are local to the cpu.
        """
        if SimConfig.dry_run:
            logging.info("Memory usage after inizialization:")
            print_mem_usage()
            self._dry_run_stats = DryRunStats()
            self._dry_run_stats.try_import_cell_memory_usage()
            loader_opts = {"dry_run_stats": self._dry_run_stats}
        else:
            loader_opts = {}

        # Check dynamic attributes required before loading cells
        SimConfig.check_cell_requirements(self.target_manager)

        log_stage("LOADING NODES")
        config = SimConfig.cli_options
        if not load_balance:
            logging.info("Load-balance object not present. Continuing Round-Robin...")

        # Always create a cell_distributor even if engine is disabled.
        # Fake CoreNeuron cells are created in it
        cell_distributor = CellDistributor(self._base_circuit, self._target_manager, self._run_conf)
        cell_distributor.load_nodes(load_balance, loader_opts=loader_opts)  # no-op if disabled
        self._circuits.register_node_manager(cell_distributor)

        # SUPPORT for extra/custom Circuits
        for name, circuit in self._extra_circuits.items():
            log_stage("Circuit %s", name)
            if config.restrict_node_populations and name not in config.restrict_node_populations:
                logging.warning("Skipped node population (restrict_node_populations)")
                continue
            self._circuits.new_node_manager(circuit, self._target_manager, self._run_conf,
                                            load_balancer=load_balance,
                                            loader_opts=loader_opts)

        lfp_weights_file = self._run_conf.get("LFPWeightsPath")
        if lfp_weights_file:
            if SimConfig.use_coreneuron:
                lfp_manager = self._circuits.global_manager._lfp_manager
                cell_managers = self._circuits.global_manager._cell_managers
                population_list = [
                    manager.population_name
                    for manager in cell_managers
                    if manager.population_name is not None
                ]
                lfp_manager.load_lfp_config(lfp_weights_file, population_list)
            else:
                logging.warning("Online LFP supported only with CoreNEURON.")

        PopulationNodes.freeze_offsets()  # Dont offset further, could change gids

        # Let the cell managers have any final say in the cell objects
        log_stage("FINALIZING CIRCUIT CELLS")

        for cell_manager in self._circuits.all_node_managers():
            log_stage("Circuit %s", cell_manager.circuit_name or "(default)")
            if SimConfig.dry_run:
                cell_manager.finalize(dry_run_stats_obj=self._dry_run_stats)
            else:
                cell_manager.finalize()

        if SimConfig.dry_run:
            self._dry_run_stats.collect_all_mpi()
            self._dry_run_stats.export_cell_memory_usage()
            self._dry_run_stats.estimate_cell_memory()

        # Final bits after we have all cell managers
        self._circuits.global_manager.finalize()
        SimConfig.update_connection_blocks(self._circuits.alias)

    # -
    @mpi_no_errors
    @timeit(name="Synapse creation")
    def create_synapses(self):
        """Create synapses among the cells, handling connections that appear in the config file
        """
        log_stage("LOADING CIRCUIT CONNECTIVITY")
        target_manager = self._target_manager
        manager_kwa = {"load_offsets": self._is_ngv_run, "dry_run_stats": self._dry_run_stats}

        if circuit := self._base_circuit:
            self._create_synapse_manager(SynapseRuleManager, circuit, target_manager, **manager_kwa)

        for circuit in self._extra_circuits.values():
            Engine = circuit.Engine or METypeEngine
            SynManagerCls = Engine.InnerConnectivityCls
            self._create_synapse_manager(SynManagerCls, circuit, target_manager, **manager_kwa)

        MPI.check_no_errors()
        log_stage("Handling projections...")
        for pname, projection in SimConfig.projections.items():
            self._load_projections(pname, projection, **manager_kwa)

        if SimConfig.dry_run:
            self.syn_total_memory = self._dry_run_stats.collect_display_syn_counts()
            return

        log_stage("Configuring connections...")
        for conn_conf in SimConfig.connections.values():
            self._process_connection_configure(conn_conf)

        logging.info("Done, but waiting for all ranks")

    def _create_synapse_manager(self, ctype, conf, *args, **kwargs):
        """Create a synapse manager for intra-circuit connectivity
        """
        log_stage("Circuit %s", conf._name or "(default)")
        if not conf.get("nrnPath"):
            logging.info(" => No connectivity set as internal. See projections")
            return

        if SimConfig.cli_options.restrict_connectivity >= 2:
            logging.warning("Skipped connectivity (restrict_connectivity)")
            return

        c_target = TargetSpec(conf.get("CircuitTarget"))
        if c_target.population is None:
            c_target.population = self._circuits.alias.get(conf._name)

        edge_file, *pop = conf.get("nrnPath").split(":")
        edge_pop = pop[0] if pop else None
        if not os.path.isabs(edge_file):
            edge_file = find_input_file(edge_file)
        src, dst = edge_node_pop_names(edge_file, edge_pop)

        logging.info("Processing edge file %s, pop: %s", edge_file, edge_pop)

        if src and dst and src != dst:
            raise ConfigurationError("Inner connectivity with different populations")

        dst = self.circuits.alias.get(dst, dst)
        if dst not in SimConfig.cli_options.restrict_node_populations:
            logging.warning("Skipped connectivity (restrict_node_populations)")
            return

        manager = self._circuits.get_create_edge_manager(
            ctype, src, dst, c_target, (conf, *args), **kwargs
        )
        self._load_connections(conf, manager)  # load internal connections right away

    def _process_connection_configure(self, conn_conf):
        source_t = TargetSpec(conn_conf["Source"])
        dest_t = TargetSpec(conn_conf["Destination"])
        source_t.population, dest_t.population = self._circuits.unalias_pop_keys(
            source_t.population, dest_t.population
        )
        src_target = self.target_manager.get_target(source_t)
        dst_target = self.target_manager.get_target(dest_t)
        # Loop over population pairs
        for src_pop in src_target.population_names:
            for dst_pop in dst_target.population_names:
                # Loop over all managers having connections between the populations
                for conn_manager in self._circuits.get_edge_managers(src_pop, dst_pop):
                    logging.debug("Using connection manager: %s", conn_manager)
                    conn_manager.configure_connections(conn_conf)

    # -
    def _load_connections(self, circuit_conf, conn_manager):
        if conn_manager.is_file_open:  # Base connectivity
            conn_manager.create_connections()

    # -
    @mpi_no_errors
    def _load_projections(self, pname, projection, **kw):
        """Check for Projection blocks
        """
        target_manager = self._target_manager
        projection = compat.Map(projection).as_dict(True)
        ptype = projection.get("Type")  # None, GapJunctions, NeuroGlial, NeuroModulation...
        ptype_cls = EngineBase.connection_types.get(ptype)
        source_t = TargetSpec(projection.get("Source"))
        dest_t = TargetSpec(projection.get("Destination"))

        if SimConfig.cli_options.restrict_connectivity >= 1:
            logging.warning("Skipped projections %s->%s (restrict_connectivity)", source_t, dest_t)
            return

        if not ptype_cls:
            raise RuntimeError("No Engine to handle connectivity of type '%s'" % ptype)

        ppath, *pop_name = projection["Path"].split(":")
        edge_pop_name = pop_name[0] if pop_name else None
        if not os.path.exists(ppath):
            ppath = self._find_projection_file(ppath)

        logging.info("Processing Edge file: %s", ppath)

        # Update the target spec with the actual populations
        src_pop, dst_pop = edge_node_pop_names(
            ppath, edge_pop_name, source_t.population, dest_t.population
        )
        source_t.population, dest_t.population = self._circuits.unalias_pop_keys(src_pop, dst_pop)
        src_target = self.target_manager.get_target(source_t)
        dst_target = self.target_manager.get_target(dest_t)

        # If the src_pop is not a known node population, allow creating a Virtual one
        src_populations = src_target.population_names or [source_t.population]

        for src_pop in src_populations:
            for dst_pop in dst_target.population_names:
                logging.info(" * %s (Type: %s, Src: %s, Dst: %s)", pname, ptype, src_pop, dst_pop)
                conn_manager = self._circuits.get_create_edge_manager(
                    ptype_cls, src_pop, dst_pop, source_t,
                    (projection, target_manager), **kw  # args to ptype_cls if creating
                )
                logging.debug("Using connection manager: %s", conn_manager)
                proj_source = ":".join([ppath] + pop_name)
                conn_manager.open_edge_location(proj_source, projection, src_name=src_pop)
                conn_manager.create_connections(source_t.name, dest_t.name)

    # -
    def _find_projection_file(self, proj_path):
        """Determine the full path to a projection.
        The "Path" might specify the filename. If not, it will attempt the old 'proj_nrn.h5'
        """
        return self._find_config_file(
            proj_path, ("ProjectionPath", "CircuitPath"), alt_filename="proj_nrn.h5")

    def _find_config_file(self, filepath, path_conf_entries=(), alt_filename=None):
        search_paths = [self._run_conf[path_key]
                        for path_key in path_conf_entries
                        if self._run_conf.get(path_key)]
        return find_input_file(filepath, search_paths, alt_filename)

    # -
    @mpi_no_errors
    @timeit(name="Enable Stimulus")
    def enable_stimulus(self):
        """Iterate over any stimuli/stim injects defined in the config file given to the simulation
        and instantiate them.
        This iterates over the injects, getting the stim/target combinations
        and passes the raw text in field/value pairs to a StimulusManager object to interpret the
        text and instantiate an actual stimulus object.
        """
        if Feature.Stimulus not in SimConfig.cli_options.restrict_features:
            logging.warning("Skipped Stimulus (restrict_features)")
            return

        log_stage("Stimulus Apply.")

        # for each stimulus defined in the config file, request the stimmanager to instantiate
        self._stim_manager = StimulusManager(self._target_manager)

        # build a dictionary of stims for faster lookup : useful when applying 10k+ stims
        # while we are at it, check if any stims are using extracellular
        has_extra_cellular = False
        stim_dict = {}
        for stim_name, stim in SimConfig.stimuli.items():
            stim = compat.Map(stim)
            if stim_name in stim_dict:
                raise ConfigurationError("Stimulus declared more than once: %s", stim_name)
            stim_dict[stim_name] = stim
            if stim.get("Mode") == "Extracellular":
                has_extra_cellular = True

        # Treat extracellular stimuli
        if has_extra_cellular:
            self._stim_manager.interpret_extracellulars(SimConfig.injects, SimConfig.stimuli)

        logging.info("Instantiating Stimulus Injects:")

        for name, inject in SimConfig.injects.items():
            target_spec = TargetSpec(inject.get("Target")) if isinstance(inject.get("Target"), str)\
                else TargetSpec(inject.get("Target").s)
            stim_name = inject.get("Stimulus") if isinstance(inject.get("Stimulus"), str) \
                else inject.get("Stimulus").s
            stim = stim_dict.get(stim_name)
            if stim is None:
                raise ConfigurationError("Stimulus Inject %s uses non-existing Stim %s",
                                         name, stim_name)

            stim_pattern = stim["Pattern"]
            if stim_pattern == "SynapseReplay":
                continue  # Handled by enable_replay

            logging.info(" * [STIM] %s: %s (%s) -> %s", name, stim_name, stim_pattern, target_spec)
            self._stim_manager.interpret(target_spec, stim)

    # -
    @mpi_no_errors
    def enable_replay(self):
        """Activate replay according to config file. Call before connManager.finalize
        """
        if Feature.Replay not in SimConfig.cli_options.restrict_features:
            logging.warning("Skipped Replay (restrict_features)")
            return

        log_stage("Handling Replay")

        if SimConfig.use_coreneuron and bool(self._core_replay_file):
            logging.info(" -> [REPLAY] Reusing stim file from previous cycle")
            return

        replay_dict = {}
        for stim_name, stim in SimConfig.stimuli.items():
            pattern = stim.get("Pattern") if isinstance(stim.get("Pattern"), str) \
                else stim.get("Pattern").s
            if pattern == "SynapseReplay":
                replay_dict[stim_name] = compat.Map(stim).as_dict(parse_strings=True)

        for name, inject in SimConfig.injects.items():
            inject = compat.Map(inject).as_dict(parse_strings=True)
            target = inject["Target"]
            source = inject.get("Source")
            stim_name = inject["Stimulus"]
            connectivity_type = inject.get("Type")
            stim = replay_dict.get(stim_name)
            if stim is None:  # It's a non-replay inject. Injects are checked in enable_stimulus
                continue

            # Since saveUpdate merge there are two delay concepts:
            #  - shift: times are shifted (previous delay)
            #  - delay: Spike replays are suppressed until a certain time
            tshift = Nd.t if stim.get("Timing") == "Relative" else .0
            delay = stim.get("Delay", .0)
            logging.info(" * [SYN REPLAY] %s (%s -> %s, time shift: %d, delay: %d)",
                         name, stim_name, target, tshift, delay)
            self._enable_replay(source, target, stim, tshift, delay, connectivity_type)

    # -
    def _enable_replay(self, source, target, stim_conf, tshift=.0, delay=.0,
                       connectivity_type=None):
        spike_filepath = find_input_file(stim_conf["SpikeFile"])
        ptype_cls = EngineBase.connection_types.get(connectivity_type)
        src_target = self.target_manager.get_target(source)
        dst_target = self.target_manager.get_target(target)

        if SimConfig.restore_coreneuron:
            pop_offsets, alias_pop = CircuitManager.read_population_offsets(read_virtual_pop=True)

        for src_pop in src_target.population_names:
            try:
                log_verbose("Loading replay spikes for population '%s'", src_pop)
                spike_manager = SpikeManager(spike_filepath, tshift, src_pop)  # Disposable
            except MissingSpikesPopulationError:
                logging.info("  > No replay for src population: '%s'", src_pop)
                continue

            for dst_pop in dst_target.population_names:
                src_pop_str, dst_pop_str = src_pop or "(base)", dst_pop or "(base)"

                if SimConfig.restore_coreneuron:  # Node and Edges managers not initialized
                    src_pop_offset = pop_offsets[src_pop] if src_pop in pop_offsets \
                        else pop_offsets[alias_pop[src_pop]]
                else:
                    conn_manager = self._circuits.get_edge_manager(src_pop, dst_pop, ptype_cls)
                    if not conn_manager and SimConfig.cli_options.restrict_connectivity >= 1:
                        continue
                    assert conn_manager, f"Missing edge manager for {src_pop_str} -> {dst_pop_str}"
                    src_pop_offset = conn_manager.src_pop_offset

                logging.info("=> Population pathway %s -> %s. Source offset: %d",
                             src_pop_str, dst_pop_str, src_pop_offset)
                if SimConfig.use_coreneuron:
                    self._coreneuron_replay_append(spike_manager, src_pop_offset)
                else:
                    conn_manager.replay(spike_manager, source, target, delay)

    def _coreneuron_replay_append(self, spike_manager, gid_offset=None):
        """Write replay spikes in single file for CoreNeuron"""
        # To be loaded as PatternStim, requires final gids (with offset)
        # Initialize file if non-existing
        if not self._core_replay_file:
            self._core_replay_file = ospath.join(SimConfig.output_root, 'pattern.dat')
            if MPI.rank == 0:
                log_verbose("Creating pattern.dat file for CoreNEURON. Gid offset: %d", gid_offset)
                spike_manager.dump_ascii(self._core_replay_file, gid_offset)
        else:
            if MPI.rank == 0:
                log_verbose("Appending to pattern.dat. Gid offset: %d", gid_offset)
                with open(self._core_replay_file, "a") as f:
                    spike_manager.dump_ascii(f, gid_offset)

    # -
    @mpi_no_errors
    @timeit(name="Enable Modifications")
    def enable_modifications(self):
        """Iterate over any Modification blocks read from the config file and apply them to the
        network. The steps needed are more complex than NeuronConfigures, so the user should not be
        expected to write the hoc directly, but rather access a library of already available mods.
        """
        # mod_mananger gets destroyed when function returns (not required)
        # mod_manager = Nd.ModificationManager(self._target_manager.hoc)
        log_stage("Enabling modifications...")

        mod_manager = ModificationManager(self._target_manager)
        for name, mod in SimConfig.modifications.items():
            mod_info = compat.Map(mod)
            target_spec = TargetSpec(mod_info["Target"])
            logging.info(" * [MOD] %s: %s -> %s", name, mod_info["Type"], target_spec)
            mod_manager.interpret(target_spec, mod_info)

    # Reporting
    ReportParams = namedtuple("ReportParams", "name, rep_type, report_on, unit, format, dt, "
                              "start, end, output_dir, electrode, scaling, isc")

    # -
    # @mpi_no_errors - not required since theres a call inside before make_comm()
    @timeit(name="Enable Reports")
    def enable_reports(self):
        """Iterate over reports defined in the config file and instantiate them.
        """
        log_stage("Reports Enabling")
        n_errors = 0
        reports_conf = SimConfig.reports
        self._report_list = []

        # Create a map of offsets so that it can be used even on coreneuron save-restore
        if self._circuits.initialized():
            self._circuits.write_population_offsets()
            pop_offsets_alias = self._circuits.get_population_offsets()
        else:
            pop_offsets_alias = CircuitManager.read_population_offsets()
        if SimConfig.use_coreneuron:
            CoreConfig.write_report_count(len(reports_conf))

        for rep_name, rep_conf in reports_conf.items():
            target_spec = TargetSpec(rep_conf["Target"])
            target = self._target_manager.get_target(target_spec)

            # Build final config. On errors log, stop only after all reports processed
            rep_params = self._report_build_params(rep_name, rep_conf, target, pop_offsets_alias)
            if rep_params is None:
                n_errors += 1
                continue

            if SimConfig.use_coreneuron and MPI.rank == 0:
                if not self._report_write_coreneuron_config(rep_name, rep_conf, target, rep_params):
                    n_errors += 1
                    continue

            if SimConfig.restore_coreneuron:
                continue  # we dont even need to initialize reports

            report = Nd.Report(*rep_params)

            if not SimConfig.use_coreneuron or rep_params.rep_type == "Synapse":
                self._report_setup(report, rep_conf, target, rep_params.rep_type)

            # Custom reporting. TODO: Move `_report_setup` to cellManager.enable_report
            target_population = target_spec.population or self._target_spec.population
            cell_manager = self._circuits.get_node_manager(target_population)
            cell_manager.enable_report(report, target, SimConfig.use_coreneuron)

            self._report_list.append(report)

        if n_errors > 0:
            raise ConfigurationError("%d reporting errors detected. Terminating" % (n_errors,))

        MPI.check_no_errors()

        self._reports_init(pop_offsets_alias)

    #
    def _report_build_params(self, rep_name, rep_conf, target, pop_offsets_alias_pop):
        sim_end = self._run_conf["Duration"]
        rep_type = rep_conf["Type"]
        start_time = rep_conf["StartTime"]
        end_time = rep_conf.get("EndTime", sim_end)
        rep_dt = rep_conf["Dt"]
        rep_format = rep_conf["Format"]

        lfp_disabled = not self._circuits.global_manager._lfp_manager._lfp_file
        if rep_type == "lfp" and lfp_disabled:
            logging.error("LFP reports are disabled. Electrodes file might be missing"
                          " or simulator is not set to CoreNEURON")
            return None
        logging.info(
            " * %s (Type: %s, Target: %s, Dt: %f)",
            rep_name,
            rep_type,
            rep_conf["Target"],
            rep_dt
        )

        if rep_format != "SONATA":
            if MPI.rank == 0:
                logging.error("Unsupported report format: '%s'. "
                              "Use 'SONATA' instead.", rep_format)
                return None

        if Nd.t > 0:
            start_time += Nd.t
            end_time += Nd.t
        if end_time > sim_end:
            end_time = sim_end
        if start_time > end_time:
            if MPI.rank == 0:
                logging.error("Report/Sim End-time (%s) before Start (%g).",
                                end_time, start_time)
            return None

        if rep_dt < Nd.dt:
            if MPI.rank == 0:
                logging.error("Invalid report dt %f < %f simulation dt", rep_dt, Nd.dt)
            return None

        rep_target = TargetSpec(rep_conf["Target"])
        population_name = (rep_target.population or self._target_spec.population
                            or self._default_population)
        log_verbose("Report on Population: %s, Target: %s", population_name, rep_target.name)

        report_on = rep_conf["ReportOn"]
        return self.ReportParams(
            os.path.basename(rep_conf.get("FileName", rep_name)),
            rep_type,  # rep type is case sensitive !!
            report_on,
            rep_conf["Unit"],
            rep_format,
            rep_dt,
            start_time,
            end_time,
            SimConfig.output_root,
            None,
            Nd.String(rep_conf["Scaling"]) if "Scaling" in rep_conf else None,
            rep_conf.get("ISC", "")
        )

    #
    def _report_write_coreneuron_config(self, rep_name, rep_conf, target, rep_params):
        target_spec = TargetSpec(rep_conf["Target"])

        # for sonata config, compute target_type from user inputs
        if "Sections" in rep_conf and "Compartments" in rep_conf:
            def _compute_corenrn_target_type(section_type, compartment_type):
                sections = ["all", "soma", "axon", "dend", "apic"]
                compartments = ["center", "all"]
                if section_type not in sections:
                    raise ConfigurationError(f"Report: invalid section type '{section_type}'")
                if compartment_type not in compartments:
                    raise ConfigurationError(f"Report: invalid compartment type {compartment_type}")
                if section_type == "all":  # for "all sections", support only target_type=0
                    return 0
                # 0=Compartment, Section { 2=Soma, 3=Axon, 4=Dendrite, 5=Apical, 6=SomaAll ... }
                return sections.index(section_type)+1+4*compartments.index(compartment_type)

            section_type = rep_conf.get("Sections")
            compartment_type = rep_conf.get("Compartments")
            target_type = _compute_corenrn_target_type(section_type, compartment_type)

        reporton_comma_separated = ",".join(rep_params.report_on.split())
        core_report_params = (
            (os.path.basename(rep_conf.get("FileName", rep_name)),
                target_spec.name, rep_params.rep_type, reporton_comma_separated)
            + rep_params[3:5] + (target_type,) + rep_params[5:8]
            + (target.get_gids(), SimConfig.corenrn_buff_size)
        )
        CoreConfig.write_report_config(*core_report_params)
        return True

    def _report_setup(self, report, rep_conf, target, rep_type):
        # TODO: Move to Cell Distributor and avoid inner loop conditions
        global_manager = self._circuits.global_manager

        if rep_type not in ("compartment", "Summation", "Synapse", "lfp"):
            logging.warning("Unsupported report type: %s.", rep_type)
            return  # Nothing to do

        # Go through the target members, one cell at a time. We give a cell reference
        # For summation targets - check if we were given a Cell target because we really
        # want all points of the cell which will ultimately be collapsed to a single
        # value on the soma. Otherwise, get target points as normal.
        sections = rep_conf.get("Sections")
        compartments = rep_conf.get("Compartments")
        sum_currents_into_soma = (sections == "soma" and compartments == "center")
        # In case of summation in the soma, we need all points anyway
        if sum_currents_into_soma and rep_type == "Summation":
            sections = "all"
            compartments = "all"
        points = self._target_manager.getPointList(target,
                                                   sections=sections,
                                                   compartments=compartments)
        for point in points:
            gid = point.gid
            pop_name, pop_offset = global_manager.getPopulationInfo(gid)
            cell = global_manager.get_cellref(gid)
            spgid = global_manager.getSpGid(gid)

            # may need to take different actions based on report type
            if rep_type == "compartment":
                report.addCompartmentReport(
                    cell, point, spgid, SimConfig.use_coreneuron, pop_name, pop_offset)
            elif rep_type == "Summation":
                report.addSummationReport(
                    cell, point, sum_currents_into_soma, spgid, SimConfig.use_coreneuron,
                    pop_name, pop_offset)
            elif rep_type == "Synapse":
                report.addSynapseReport(
                    cell, point, spgid, SimConfig.use_coreneuron, pop_name, pop_offset)

    def _reports_init(self, pop_offsets_alias):
        pop_offsets = pop_offsets_alias[0]

        if SimConfig.use_coreneuron:
            # write spike populations
            if hasattr(CoreConfig, "write_population_count"):
                # Do not count populations with None pop_name
                pop_count = (len(pop_offsets) - 1 if None in pop_offsets else len(pop_offsets))
                CoreConfig.write_population_count(pop_count)
            for pop_name, offset in pop_offsets.items():
                if pop_name is not None:
                    CoreConfig.write_spike_population(pop_name or "All", offset)
            spike_path = self._run_conf.get("SpikesFile")
            if spike_path is not None:
                # Get only the spike file name
                file_name = spike_path.split('/')[-1]
            else:
                file_name = "out.h5"
            CoreConfig.write_spike_filename(file_name)
        else:
            # Report Buffer Size hint in MB.
            reporting_buffer_size = self._run_conf.get("ReportingBufferSize")
            if reporting_buffer_size is not None:
                self._sonatareport_helper.set_max_buffer_size_hint(reporting_buffer_size)

            # once all reports are created, we finalize the communicator for any reports
            self._sonatareport_helper.make_comm()
            self._sonatareport_helper.prepare_datasets()

    # -
    @mpi_no_errors
    def execute_neuron_configures(self):
        """Iterate over any NeuronConfigure blocks from the config file.
        These are simple hoc statements that can be executed with minimal substitutions
        """
        printed_warning = False

        for config in SimConfig.configures.values():
            if not printed_warning:
                logging.warning("NeuronConfigure block is deprecated")
                printed_warning = True

            target_name = config.get("Target").s
            configure_str = config.get("Configure").s
            log_verbose("Apply configuration \"%s\" on target %s",
                        config.get("Configure").s, target_name)

            points = self._target_manager.getPointList(target_name)
            # iterate the pointlist and execute the command on the section
            for tpoint_list in points:
                for sec_i, sc in enumerate(tpoint_list.sclst):
                    if not sc.exists():
                        continue
                    x = tpoint_list.x[sec_i]
                    tstr = configure_str.replace("%s", Nd.secname(sec=sc.sec))
                    tstr = tstr.replace("%g", "%g" % x)
                    Nd.execute1(tstr, sec=sc.sec)

    # -
    @mpi_no_errors
    def sim_init(self, corenrn_gen=None, **sim_opts):
        """Finalize the model and prepare to run simulation.

        After finalizing the model, will eventually write coreneuron config
        and initialize the neuron simulation if applicable.

        Args:
            corenrn_gen: Whether to generate coreneuron config. Default: None (if required)
            sim_opts - override _finalize_model options. E.g. spike_compress
        """
        if self._sim_ready:
            return self._pc

        if not len(self._circuits.all_node_managers()):
            raise RuntimeError("No CellDistributor was initialized. Please create a circuit.")

        self._finalize_model(**sim_opts)

        if corenrn_gen is None:
            corenrn_gen = SimConfig.use_coreneuron
        if corenrn_gen:
            self._sim_corenrn_write_config()

        if SimConfig.use_neuron:
            self._sim_init_neuron()

        if ospath.isfile("debug_gids.txt"):
            self.dump_circuit_config()
        if self._pr_cell_gid:
            self.dump_cell_config()

        self._sim_ready = True
        return self._pc

    # -
    @mpi_no_errors
    @timeit(name="Model Finalized")
    def _finalize_model(self, spike_compress=3):
        """Set up simulation run parameters and initialization.

        Handles setup_transfer, spike_compress, _record_spikes, stdinit, forward_skip, timeout
        Args:
            spike_compress: The spike_compress() parameters (tuple or int)
        """
        logging.info("Preparing to run simulation...")
        is_save_state = SimConfig.save or SimConfig.restore
        self._pc.setup_transfer()

        if spike_compress and not is_save_state and not self._is_ngv_run:
            # multisend 13 is combination of multisend(1) + two_phase(8) + two_intervals(4)
            # to activate set spike_compress=(0, 0, 13)
            if not isinstance(spike_compress, tuple):
                spike_compress = (spike_compress, 1, 0)
            self._pc.spike_compress(*spike_compress)

        # LFP calculation requires WholeCell balancing and extracellular mechanism.
        # This is incompatible with efficient caching atm AND Incompatible with mcd & Glut
        if not self._is_ngv_run:
            Nd.cvode.cache_efficient("ElectrodesPath" not in self._run_conf)
        self._pc.set_maxstep(4)
        with timeit(name="stdinit"):
            Nd.stdinit()

        logging.info("Executing actions after stdinit...")
        for mgr in self._circuits.all_node_managers():
            mgr.post_stdinit()

    # -
    def _sim_init_neuron(self):
        # === Neuron specific init ===
        restore_path = SimConfig.restore
        fwd_skip = self._run_conf.get("ForwardSkip", 0)

        if fwd_skip and not restore_path:
            logging.info("Initializing with ForwardSkip %d ms", fwd_skip)
            Nd.t = -1e9
            prev_dt = Nd.dt
            Nd.dt = fwd_skip * 0.1
            for flushIndex in range(10):
                Nd.fadvance()
            Nd.dt = prev_dt
            Nd.t = 0
            Nd.frecord_init()

        # create a spike_id vector which stores the pairs for spikes and timings for
        # every engine
        for cell_manager in self._circuits.all_node_managers():
            if cell_manager.population_name is not None:
                self._spike_populations.append(
                    (cell_manager.population_name, cell_manager.local_nodes.offset))
                self._spike_vecs.append(cell_manager.record_spikes() if cell_manager.record_spikes()
                                        else (Nd.Vector(), Nd.Vector()))

        self._pc.timeout(200)  # increase by 10x

        if restore_path:
            with timeit(name="restoretime"):
                logging.info("Restoring state...")
                self._stim_manager.saveStatePreparation(self._bbss)
                self._bbss.vector_play_init()
                self._restart_events()  # On restore the event queue is cleared
                return  # Upon restore sim is ready

    # -
    def _restart_events(self):
        logging.info("Restarting connections events (Replay and Spont Minis)")
        for syn_manager in self._circuits.all_synapse_managers():
            syn_manager.restart_events()

    @contextmanager
    def _coreneuron_ensure_all_ranks_have_gids(self, corenrn_data):
        local_gid_count = sum(len(manager.local_nodes)
                              for manager in self._circuits.all_node_managers())
        if local_gid_count > 0:
            yield
            return

        # create a fake node with a fake population "zzz" to get an unused gid.
        # It only works with a single cycles without enough cells, but in
        #  _instantiate_simulation we made sure we limit the number of cycles
        log_verbose("Creating fake gid for CoreNeuron")
        pop_group = PopulationNodes.get("zzz", create=True)
        fake_gid = pop_group.offset + 1 + MPI.rank
        # Add the fake cell to the base manager
        base_manager = self._circuits.base_cell_manager
        base_manager.load_artificial_cell(fake_gid, CoreConfig.artificial_cell_object)
        yield

        # register_mapping() doesn't work for this artificial cell as somatic attr is
        # missing, so create a dummy mapping file manually, required for reporting
        cur_files = glob.glob("%s/*_3.dat" % corenrn_data)
        example_mapfile = cur_files[0]
        with open(example_mapfile, 'rb') as f_mapfile:
            # read the version from the existing mapping file generated by coreneuron
            coredata_version = f_mapfile.readline().rstrip().decode("ascii")
        mapping_file = ospath.join(corenrn_data, "%d_3.dat" % fake_gid)
        if not ospath.isfile(mapping_file):
            with open(mapping_file, "w") as dummyfile:
                dummyfile.write("%s\n0\n" % coredata_version)

    # -
    def _sim_corenrn_configure_datadir(self, corenrn_restore):
        corenrn_datadir = SimConfig.coreneuron_datadir
        os.makedirs(corenrn_datadir, exist_ok=True)
        corenrn_datadir_shm = SHMUtil.get_datadir_shm(corenrn_datadir)

        # Clean-up any previous simulations in the same output directory
        if self._cycle_i == 0 and corenrn_datadir_shm:
            subprocess.call(['/bin/rm', '-rf', corenrn_datadir_shm])

        # Ensure that we have a folder in /dev/shm (i.e., 'SHMDIR' ENV variable)
        if SimConfig.cli_options.enable_shm and not corenrn_datadir_shm:
            logging.warning("Unknown SHM directory for model file transfer in CoreNEURON.")
        # Try to configure the /dev/shm folder as the output directory for the files
        elif self._cycle_i == 0 and not corenrn_restore and \
                (SimConfig.cli_options.enable_shm and SimConfig.delete_corenrn_data):
            # Check for the available memory in /dev/shm and estimate the RSS by multiplying
            # the number of cycles in the multi-step model build with an approximate factor
            mem_avail = SHMUtil.get_mem_avail()
            shm_avail = SHMUtil.get_shm_avail()
            initial_rss = self._initial_rss
            current_rss = SHMUtil.get_node_rss()
            factor = SHMUtil.get_shm_factor()
            rss_diff = (current_rss - initial_rss) if initial_rss < current_rss else current_rss
            rss_req = int(rss_diff * self._n_cycles * factor)  # 'rss_diff' prevents <0 estimates

            # Sync condition value with all ranks to ensure that all of them can use /dev/shm
            shm_possible = (rss_req < shm_avail) and (rss_req < mem_avail)
            if MPI.allreduce(int(shm_possible), MPI.SUM) == MPI.size:
                logging.info("SHM file transfer mode for CoreNEURON enabled")

                # Create SHM folder and links to GPFS for the global data structures
                os.makedirs(corenrn_datadir_shm, exist_ok=True)

                # Important: These three files must be available on every node, as they are shared
                #            across all of the processes. The trick here is to fool NEURON into
                #            thinking that the files are written in /dev/shm, but they are actually
                #            written on GPFS. The workflow is identical, meaning that rank 0 writes
                #            the content and every other rank reads it afterwards in CoreNEURON.
                for filename in {"bbcore_mech.dat", "files.dat", "globals.dat"}:
                    path = os.path.join(corenrn_datadir, filename)
                    path_shm = os.path.join(corenrn_datadir_shm, filename)

                    try:
                        os.close(os.open(path, os.O_CREAT))
                        os.symlink(path, path_shm)
                    except FileExistsError:
                        pass  # Ignore if other process has already created it

                # Update the flag to confirm the configuration
                self._shm_enabled = True
            else:
                logging.warning("Unable to utilize SHM for model file transfer in CoreNEURON. "
                                "Increase the number of nodes to reduce the memory footprint "
                                "(Current use node: %d MB / SHM Limit: %d MB / Mem. Limit: %d MB)",
                                (rss_req >> 20), (shm_avail >> 20), (mem_avail >> 20))
        return corenrn_datadir if not self._shm_enabled else corenrn_datadir_shm

    # -
    @timeit(name="corewrite")
    def _sim_corenrn_write_config(self, corenrn_restore=False):
        log_stage("Dataset generation for CoreNEURON")
        CoreConfig.datadir = self._sim_corenrn_configure_datadir(corenrn_restore)
        fwd_skip = self._run_conf.get("ForwardSkip", 0) if not corenrn_restore else 0

        if not corenrn_restore:
            CompartmentMapping(self._circuits.global_manager).register_mapping()
            with self._coreneuron_ensure_all_ranks_have_gids(CoreConfig.datadir):
                self._pc.nrnbbcore_write(CoreConfig.datadir)
                MPI.barrier()  # wait for all ranks to finish corenrn data generation

        CoreConfig.write_sim_config(
            Nd.tstop,
            Nd.dt,
            fwd_skip,
            self._pr_cell_gid or -1,
            getattr(SimConfig, 'celsius', 34.0),
            getattr(SimConfig, 'v_init', -65.0),
            self._core_replay_file,
            SimConfig.rng_info.getGlobalSeed(),
            int(SimConfig.cli_options.model_stats),
            int(self._run_conf["EnableReports"])
        )
        # Wait for rank0 to write the sim config file
        MPI.barrier()

        logging.info(" => Dataset written to '{}'".format(CoreConfig.datadir))

    # -
    def run_all(self):
        """Run the whole simulation according to the simulation config file
        """
        if not self._sim_ready:
            self.sim_init()

        timings = None
        if SimConfig.use_neuron:
            timings = self._run_neuron()
            self.sonata_spikes()
        if SimConfig.use_coreneuron:
            print_mem_usage()
            self.clear_model(avoid_clearing_queues=False)
            self._run_coreneuron()
        return timings

    # -
    @return_neuron_timings
    def _run_neuron(self):
        if MPI.rank == 0:
            _ = SimulationProgress()
        self.solve()
        logging.info("Simulation finished.")

    # -
    def _run_coreneuron(self):
        logging.info("Launching simulation with CoreNEURON")
        CoreConfig.psolve_core(
            getattr(SimConfig, "save", None),
            getattr(SimConfig, "restore", None)
        )

    #
    def _sim_event_handlers(self, tstart, tstop):
        """Create handlers for "in-simulation" events, like activating delayed
        connections, execute Save-State, etc
        """
        events = defaultdict(list)  # each key (time) points to a list of handlers

        if SimConfig.save:
            tsave = SimConfig.save_time or SimConfig.tstop  # Consider 0 as the end too!
            save_f = self._create_save_handler(tsave)
            events[tsave].append(save_f)

        event_list = [(t, events[t]) for t in sorted(events)]
        return event_list

    # -
    def _create_save_handler(self, tsave):
        @timeit(name="savetime")
        def save_f():
            logging.info("Saving State... (t=%f)", tsave)
            MPI.barrier()
            self._stim_manager.saveStatePreparation(self._bbss)
            log_verbose("SaveState Initialization Done")

            # If event at the end of the sim we can actually clearModel() before savestate()
            if SimConfig.save_time is None:
                log_verbose("Clearing model prior to final save")
                self._sonatareport_helper.flush()

            self.dump_cell_config()
            # Clear the model after saving state as the pointers are being recorded in reportinglib
            if SimConfig.save_time is None:
                self.clear_model()
            logging.info(" => Save done successfully")

        return save_f

    # -
    @mpi_no_errors
    @timeit(name="psolve")
    def solve(self, tstop=None):
        """Call solver with a given stop time (default: whole interval).
        Be sure to have sim_init()'d the simulation beforehand
        """
        if not self._sim_ready:
            raise ConfigurationError("Initialize simulation first")

        tstart = Nd.t
        tstop = tstop or Nd.tstop
        event_list = self._sim_event_handlers(tstart, tstop)

        # NOTE: _psolve_loop is called among events in order to eventually split long
        # simulation blocks, where one or more report flush(es) can happen. It is a simplified
        # design relatively to the original version where the report checkpoint would not happen
        # before the checkpoint timeout (25ms default). However there shouldn't be almost any
        # performance penalty since the simulation is already halted between events.

        logging.info("Running simulation until t=%d ms", tstop)
        t = tstart  # default if there are no events
        for t, events in event_list:
            self._psolve_loop(t)
            for event in events:
                event()
            self.dump_cell_config()  # Respect prCellGid on every state change
        # Run until the end
        if t < tstop:
            self._psolve_loop(tstop)
            self.dump_cell_config()

        # Final flush
        self._sonatareport_helper.flush()

    # psolve_loop: There was an issue where MPI collective routines for reporting and spike exchange
    # are mixed such that some cpus are blocked waiting to complete reporting while others to
    # finish spike exchange. As a work-around, periodically halt simulation and flush reports
    # Default is 25 ms / cycle
    def _psolve_loop(self, tstop):
        cur_t = round(Nd.t, 2)  # fp innnacuracies could lead to infinitesimal loops
        buffer_t = SimConfig.buffer_time
        for _ in range(math.ceil((tstop - cur_t) / buffer_t)):
            next_flush = min(tstop, cur_t + buffer_t)
            self._pc.psolve(next_flush)
            cur_t = next_flush
        Nd.t = cur_t

    # -
    @mpi_no_errors
    def clear_model(self, avoid_creating_objs=False, avoid_clearing_queues=True):
        """Clears appropriate lists and other stored references.
        For use with intrinsic load balancing. After creating and evaluating the network using
        round robin distribution, we want to clear the cells and synapses in order to have a
        clean slate on which to instantiate the balanced cells.
        """
        logging.info("Clearing model")
        self._pc.gid_clear()
        self._target_manager.clear_simulation_data()

        if not avoid_creating_objs:
            if SimConfig.use_neuron:
                if self._sonatareport_helper:
                    self._sonatareport_helper.clear()

        Node.__init__(self, None, None)  # Reset vars

        # Clear BBSaveState
        self._bbss.ignore()

        # Shrink ArrayPools holding mechanism's data in NEURON
        pool_shrink()

        # Free event queues in NEURON
        if not avoid_clearing_queues:
            free_event_queues()

        # Garbage collect all Python objects without references
        gc.collect()

        # Finally call malloc_trim to return all the freed pages back to the OS
        trim_memory()
        print_mem_usage()

    # -------------------------------------------------------------------------
    #  output
    # -------------------------------------------------------------------------

    def sonata_spikes(self):
        """ Write the spike events that occured on each node into a single output SONATA file.
        """
        output_root = SimConfig.output_root
        if hasattr(self._sonatareport_helper, "create_spikefile"):
            # Write spike report for multiple populations if exist
            spike_path = self._run_conf.get("SpikesFile")
            if spike_path is not None:
                # Get only the spike file name
                file_name = spike_path.split('/')[-1]
            else:
                file_name = "out.h5"
            # create a sonata spike file
            self._sonatareport_helper.create_spikefile(output_root, file_name)
            # write spikes per population
            for (population, population_offset), (spikevec, idvec) in zip(self._spike_populations,
                                                                          self._spike_vecs):
                extra_args = (population, population_offset) if population \
                    else ("All", population_offset)
                self._sonatareport_helper.add_spikes_population(spikevec, idvec, *extra_args)
            # write all spike populations
            self._sonatareport_helper.write_spike_populations()
            # close the spike file
            self._sonatareport_helper.close_spikefile()
        else:
            # fallback: write spike report with one single population "ALL"
            logging.warning("Writing spike reports with multiple populations is not supported. "
                            "If needed, please update to a newer version of neurodamus.")
            population = self._target_spec.population or "All"
            extra_args = (population,)
            self._sonatareport_helper.write_spikes(spikevec, idvec, output_root, *extra_args)

    def dump_cell_config(self):
        if not self._pr_cell_gid:
            return
        if self._cell_state_dump_t == Nd.t:   # avoid duplicating output
            return
        log_verbose("Dumping info about cell %d", self._pr_cell_gid)
        simulator = "CoreNeuron" if SimConfig.use_coreneuron else "Neuron"
        self._pc.prcellstate(self._pr_cell_gid, "py_{}_t{}".format(simulator, Nd.t))
        self._cell_state_dump_t = Nd.t

    # -
    def dump_circuit_config(self, suffix="nrn_python"):
        gidvec = self._circuits.base_cell_manager.local_nodes.final_gids()
        log_stage("Dumping cells state")
        suffix += "_t=" + str(Nd.t)

        if not ospath.isfile("debug_gids.txt"):
            logging.info("Debugging all gids")
            gids = gidvec
        else:
            gids = []
            for line in open("debug_gids.txt"):
                line = line.strip()
                if not line:
                    continue
                gid = int(line)
                if gid in gidvec:
                    gids.append(gid)
            if len(gids):
                log_all(logging.INFO, "Rank %d: Debugging %d gids from debug_gids.txt",
                        MPI.rank, len(gids))

        for gid in gids:
            self._pc.prcellstate(gid, suffix)

    # ---------------------------------------------------------------------------
    # Note: This method may be called automatically from Neurodamus.__del__
    #     and therefore it must stay as simple as possible as exceptions are ignored
    def cleanup(self):
        """Have the compute nodes wrap up tasks before exiting.
        """
        # MemUsage constructor will do MPI communications
        print_mem_usage()

        # Coreneuron runs clear the model before starting
        if not SimConfig.use_coreneuron or SimConfig.simulate_model is False:
            self.clear_model(avoid_creating_objs=True)

        if SimConfig.delete_corenrn_data and not SimConfig.dry_run:
            data_folder = SimConfig.coreneuron_datadir
            logging.info("Deleting intermediate data in %s", data_folder)

            with timeit(name="Delete corenrn data"):
                if MPI.rank == 0:
                    if ospath.islink(data_folder):
                        # in restore, coreneuron data is a symbolic link
                        os.unlink(data_folder)
                    else:
                        subprocess.call(['/bin/rm', '-rf', data_folder])
                    os.remove(ospath.join(SimConfig.output_root, "sim.conf"))
                    if self._run_conf["EnableReports"]:
                        os.remove(ospath.join(SimConfig.output_root, "report.conf"))

                # Delete the SHM folder if it was used
                if self._shm_enabled:
                    data_folder_shm = SHMUtil.get_datadir_shm(data_folder)
                    logging.info("Deleting intermediate SHM data in %s", data_folder_shm)
                    subprocess.call(['/bin/rm', '-rf', data_folder_shm])

            MPI.barrier()

        logging.info("Finished")
        TimerManager.timeit_show_stats()


# Helper class
# ------------
class Neurodamus(Node):
    """A high level interface to Neurodamus
    """

    def __init__(
        self, config_file,
        auto_init=True,
        cleanup_atexit=True,
        logging_level=None,
        **user_opts
    ):
        """Creates and initializes a neurodamus run node

        As part of Initiazation it calls:
         * load_targets
         * compute_load_balance
         * Build the circuit (cells, synapses, GJs)
         * Add stimulus & replays
         * Activate reports if requested

        Args:
            config_file: The simulation config recipe file
            logging_level: (int) Redefine the global logging level.
                0 - Only warnings / errors
                1 - Info messages (default)
                2 - Verbose
                3 - Debug messages
            cleanup_atexit: (bool) Call cleanup in the destructor
                [for more see: https://bbpteam.epfl.ch/project/issues/browse/BBPBGLIB-976]
            user_opts: Options to Neurodamus overriding the simulation config file
        """
        self._init_ok = False
        self.cleanup_atexit = cleanup_atexit
        enable_reports = not user_opts.pop("disable_reports", False)

        if logging_level is not None:
            GlobalConfig.verbosity = logging_level

        Node.__init__(self, config_file, user_opts)
        # Use the run_conf dict to avoid passing it around
        self._run_conf["EnableReports"] = enable_reports
        self._run_conf["AutoInit"] = auto_init

        if SimConfig.dry_run:
            self.load_targets()
            self.create_cells()
            self.create_synapses()
            self._init_ok = True
            return

        if SimConfig.restore_coreneuron:
            self._coreneuron_restore()
        elif SimConfig.build_model:
            self._instantiate_simulation()

        # In case an exception occurs we must prevent the destructor from cleaning
        self._init_ok = True

        # Remove .SUCCESS file if exists
        self._success_file = SimConfig.config_file + ".SUCCESS"
        self._remove_file(self._success_file)

    # -
    def _build_model(self):
        log_stage("================ CALCULATING LOAD BALANCE ================")
        load_bal = self.compute_load_balance()
        print_mem_usage()

        log_stage("==================== BUILDING CIRCUIT ====================")
        self.create_cells(load_bal)
        self.execute_neuron_configures()
        print_mem_usage()

        # Create connections
        self.create_synapses()
        print_mem_usage()

        log_stage("================ INSTANTIATING SIMULATION ================")
        # Apply replay
        self.enable_replay()
        print_mem_usage()

        if self._run_conf["AutoInit"]:
            self.init()

    # -
    def init(self):
        """Explicitly initialize, allowing users to make last changes before simulation
        """
        log_stage("Creating connections in the simulator")
        base_seed = self._run_conf.get("BaseSeed", 0)  # base seed for synapse RNG
        for syn_manager in self._circuits.all_synapse_managers():
            syn_manager.finalize(base_seed, SimConfig.use_coreneuron)
        print_mem_usage()

        self.enable_stimulus()
        print_mem_usage()
        self.enable_modifications()

        if self._run_conf["EnableReports"]:
            self.enable_reports()
        print_mem_usage()

        self.sim_init()

    # -
    def _merge_filesdat(self, ncycles):
        log_stage("Generating merged CoreNeuron files.dat")
        coreneuron_datadir = SimConfig.coreneuron_datadir
        cn_entries = []
        for i in range(ncycles):
            log_verbose("files_{}.dat".format(i))
            filename = ospath.join(coreneuron_datadir, "files_{}.dat".format(i))
            with open(filename) as fd:
                first_line = fd.readline()
                nlines = int(fd.readline())
                for _ in range(nlines):
                    line = fd.readline()
                    cn_entries.append(line)

        cnfilename = ospath.join(coreneuron_datadir, "files.dat")
        with open(cnfilename, 'w') as cnfile:
            cnfile.write(first_line)
            cnfile.write(str(len(cn_entries)) + '\n')
            cnfile.writelines(cn_entries)

        logging.info(" => {} files merged successfully".format(ncycles))

    # -
    def _coreneuron_restore(self):
        log_stage(" =============== CORENEURON RESTORE ===============")
        self.load_targets()
        self.enable_replay()
        if self._run_conf["EnableReports"]:
            self.enable_reports()
        self._sim_corenrn_write_config(corenrn_restore=True)
        self._sim_ready = True

    # -
    def _instantiate_simulation(self):
        # Keep the initial RSS for the SHM file transfer calculations
        self._initial_rss = SHMUtil.get_node_rss()
        print_mem_usage()

        self.load_targets()

        # Check connection block configuration and raise warnings for overriding parameters
        SimConfig.check_connections_configure(self._target_manager)

        # Check if user wants to build the model in several steps (only for CoreNeuron)
        n_cycles = SimConfig.modelbuilding_steps

        # Without multi-cycle, it's a trivial model build. sub_targets is False
        if n_cycles == 1:
            self._build_model()
            return

        target = self._target_manager.get_target(self._target_spec)
        target_name = self._target_spec.name
        cell_count = target.gid_count()
        logging.info("Simulation target: %s, Cell count: %d", target_name, cell_count)

        if SimConfig.use_coreneuron and cell_count/n_cycles < MPI.size and cell_count > 0:
            # coreneuron with no. ranks >> no. cells
            # need to assign fake gids to artificial cells in empty threads during module building
            # fake gids start from max_gid + 1
            # currently not support engine plugin where target is loaded later
            max_num_cycles = int(cell_count / MPI.size) or 1
            if n_cycles > max_num_cycles:
                logging.warning("Your simulation is using multi-cycle without enough cells.\n"
                                "  => Number of cycles has been automatically set to the max: %d",
                                max_num_cycles)
                n_cycles = max_num_cycles

        if n_cycles == 1:
            self._build_model()
            return

        logging.info("MULTI-CYCLE RUN: {} Cycles".format(n_cycles))
        TimerManager.archive(archive_name="Before Cycle Loop")

        PopulationNodes.freeze_offsets()
        sub_targets = target.generate_subtargets(n_cycles)

        for cycle_i, cur_targets in enumerate(sub_targets):
            logging.info("")
            logging.info("-" * 60)
            log_stage("==> CYCLE {} (OUT OF {})".format(cycle_i + 1, n_cycles))
            logging.info("-" * 60)

            self.clear_model()

            for cur_target in cur_targets:
                self._target_manager.register_target(cur_target)
                pop = list(cur_target.population_names)[0]
                for circuit in itertools.chain([self._base_circuit],
                                                self._extra_circuits.values()):
                    tmp_target_spec = TargetSpec(circuit.CircuitTarget)
                    if tmp_target_spec.population == pop:
                        tmp_target_spec.name = cur_target.name
                        circuit.CircuitTarget = str(tmp_target_spec)

            self._cycle_i = cycle_i
            self._build_model()

            # Move generated files aside (to be merged later)
            if MPI.rank == 0:
                base_filesdat = ospath.join(SimConfig.coreneuron_datadir, 'files')
                os.rename(base_filesdat + '.dat', base_filesdat + "_{}.dat".format(cycle_i))
            # Archive timers for this cycle
            TimerManager.archive(archive_name="Cycle Run {:d}".format(cycle_i + 1))

        if MPI.rank == 0:
            self._merge_filesdat(n_cycles)

    # -
    @timeit(name="finished Run")
    def run(self):
        """Prepares and launches the simulation according to the loaded config.
        If '--only-build-model' option is set, simulation is skipped.
        """
        if SimConfig.dry_run:
            log_stage("============= DRY RUN (SKIP SIMULATION) =============")
            self._dry_run_stats.display_total()
            self._dry_run_stats.display_node_suggestions()
            ranks = self._dry_run_stats.get_num_target_ranks(SimConfig.num_target_ranks)
            self._dry_run_stats.collect_all_mpi()
            self._dry_run_stats.distribute_cells(ranks)
            return
        if not SimConfig.simulate_model:
            self.sim_init()
            log_stage("======== [SKIPPED] SIMULATION (MODEL BUILD ONLY) ========")
        elif not SimConfig.build_model:
            log_stage("============= SIMULATION (SKIP MODEL BUILD) =============")
            self._run_coreneuron()
        else:
            log_stage("======================= SIMULATION =======================")
            self.run_all()
        # Create SUCCESS file if the simulation finishes successfully
        self._touch_file(self._success_file)
        logging.info("Creating .SUCCESS file: '%s'", self._success_file)

    def __del__(self):
        if self._init_ok and self.cleanup_atexit:
            self.cleanup()

    @run_only_rank0
    def _remove_file(self, file_name):
        import contextlib
        with contextlib.suppress(FileNotFoundError):
            os.remove(file_name)

    @run_only_rank0
    def _touch_file(self, file_name):
        with open(file_name, 'a'):
            os.utime(file_name, None)
