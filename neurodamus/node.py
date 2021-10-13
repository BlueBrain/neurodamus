# Neurodamus
# Copyright 2018 - Blue Brain Project, EPFL

from __future__ import absolute_import
import functools
import glob
import itertools
import logging
import math
import operator
import os
import subprocess
from os import path as ospath
from collections import namedtuple, defaultdict
from contextlib import contextmanager
from shutil import copyfileobj, move

from .core import MPI, mpi_no_errors, return_neuron_timings, run_only_rank0
from .core import NeurodamusCore as Nd
from .core.configuration import GlobalConfig, SimConfig
from .core._engine import EngineBase
from .core.configuration import ConfigurationError, find_input_file
from .core.nodeset import PopulationNodes
from .cell_distributor import CellDistributor, VirtualCellPopulation, GlobalCellManager
from .cell_distributor import LoadBalance, LoadBalanceMode
from .connection_manager import SynapseRuleManager, edge_node_pop_names
from .gap_junction import GapJunctionManager
from .replay import SpikeManager
from .stimulus_manager import StimulusManager
from .modification_manager import ModificationManager
from .target_manager import NodesetTarget, TargetSpec, TargetManager
from .utils import compat
from .utils.logging import log_stage, log_verbose, log_all
from .utils.timeit import TimerManager, timeit, timeit_rank0
# Internal Plugins
from . import ngv as _ngv  # NOQA
from . import point_neuron as _point # NOQA


class METypeEngine(EngineBase):
    CellManagerCls = CellDistributor
    InnerConnectivityCls = SynapseRuleManager
    ConnectionTypes = {
        None: SynapseRuleManager,
        "Synaptic": SynapseRuleManager,
        "GapJunction": GapJunctionManager
    }


class CircuitManager:
    """
    Holds and manages populations and associated nodes and edges

    For backward compat, base population doesnt have a population name (it is '')
    All other nodes must have a name, read from sonata pop name, or the BlueConfig circuit
    As so, Sonata is preferred when using multiple node files
    """

    def __init__(self):
        self.node_managers = {}  # dict {pop_name -> cell_manager}  # nrn pop is None
        self.virtual_node_managers = {}   # same, but for virtual ones (no cells)
        self.edge_managers = defaultdict(list)  # dict {(src_pop, dst_pop) -> list[synapse_manager]}
        self.alias = {}          # dict {name -> pop_name}
        self.global_manager = GlobalCellManager()
        self.global_target = NodesetTarget("_ALL_", [])

    def initialized(self):
        return bool(self.node_managers)

    def register_node_manager(self, cell_manager):
        pop = cell_manager.population_name
        if pop in self.node_managers:
            raise ConfigurationError("Already existing node manager for population %s" % pop)
        self.node_managers[pop] = cell_manager
        self.alias[cell_manager.circuit_name] = pop
        self.global_manager.register_manager(cell_manager)
        self.global_target.nodesets.append(cell_manager.local_nodes)

    def new_node_manager(self, circuit, *args, **kwargs):
        engine = circuit.Engine or METypeEngine
        CellManagerCls = engine.CellManagerCls or SynapseRuleManager
        cell_manager = CellManagerCls(circuit, *args, **kwargs)
        self.register_node_manager(cell_manager)
        cell_manager.load_nodes()
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
                    if type(manager) == conn_type]
        return managers[0] if managers else None

    def get_create_edge_manager(self, conn_type, source, destination, *args,
                                _orig_target_pop=None,
                                **kw):
        source, destination = self.unalias_pop_keys(source, destination)
        manager = self.get_edge_manager(source, destination, conn_type)
        if manager:
            return manager

        if not self.has_population(destination):
            # This is likely an error, except...
            if _orig_target_pop is None and self.has_population(''):
                logging.warning("Sonata Edges target population %s was not found. "
                                "Since base population is unknown, assuming that's the target.\n"
                                "To silence this warning please switch to Sonata nodes or specify "
                                "the base population by prefixing CircuitTarget with pop_name:",
                                destination)
                self.alias[destination] = ''
                destination = ''
                source = self.alias.get(source)  # refresh unaliasing
            else:
                raise ConfigurationError("Can't find projection Node population: %s", destination)

        src_manager = self.node_managers.get(source)
        if src_manager is None:  # src manager may not exist -> virtual
            logging.info(" * No known population %s. Creating Virtual src for projection", source)
            if conn_type not in (SynapseRuleManager, _ngv.GlioVascularManager):
                raise ConfigurationError("Custom connections require instantiated source nodes")
            src_manager = VirtualCellPopulation(source)

        target_cell_manager = kw["cell_manager"] = self.node_managers[destination]
        kw["src_cell_manager"] = src_manager
        manager = conn_type(*args, **kw)
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

    """ Write infor in sim_conf/populations_offset.dat
        format population name::gid offset::population alias
    """
    def write_population_offsets(self):
        with open(self._pop_offset_file(create=True), "w") as f:
            pop_offsets, alias_pop = self.get_population_offsets()
            for alias, pop in alias_pop.items():
                f.write("{}::{}::{}\n".format(pop or ' ', pop_offsets[pop], alias or ' '))

    def get_population_offsets(self):
        pop_offsets = {pop_name: node_manager.local_nodes.offset
                       for pop_name, node_manager in self.node_managers.items()}
        alias_pop = {alias: pop_name for alias, pop_name in self.alias.items()}
        return pop_offsets, alias_pop

    @classmethod
    def read_population_offsets(cls):
        pop_offsets = {}
        alias_pop = {}
        with open(cls._pop_offset_file(), "r") as f:
            offsets = [line.strip().split("::") for line in f]
            for entry in offsets:
                pop_offsets[entry[0] or None] = int(entry[1])
                alias_pop[entry[2] or None] = entry[0] or None
        return pop_offsets, alias_pop

    @classmethod
    def _pop_offset_file(self, create=False):
        outdir = ospath.join(SimConfig.current_dir, "sim_conf")
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
            config_file: A BlueConfig file
            options: A dictionary of run options typically coming from cmd line
        """
        Nd.init()

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
            self._run_conf = SimConfig.run_conf
            self._target_manager = TargetManager(self._run_conf)
            self._target_spec = TargetSpec(self._run_conf.get("CircuitTarget"))
            if SimConfig.use_neuron:
                self._binreport_helper = Nd.BinReportHelper(Nd.dt, True)
                self._sonatareport_helper = Nd.SonataReportHelper(Nd.dt, True)
            self._base_circuit = SimConfig.base_circuit
            self._extra_circuits = SimConfig.extra_circuits
            self._pr_cell_gid = self._run_conf.get("prCellGid")
            self._core_replay_file = ""
            self._is_ngv_run = any(c.Engine.__name__ == "NGVEngine"
                                   for c in self._extra_circuits.values() if c.Engine)
        self._circuits = CircuitManager()
        self._stim_list = None
        self._report_list = None
        self._stim_manager = None
        self._elec_manager = None
        self._sim_ready = False
        self._jumpstarters = []
        self._cell_state_dump_t = None

    #
    # public 'read-only' properties - object modification on user responsibility
    circuits = property(lambda self: self._circuits)
    target_manager = property(lambda self: self._target_manager)
    stim_manager = property(lambda self: self._stim_manager)
    elec_manager = property(lambda self: self._elec_manager)
    stims = property(lambda self: self._stim_list)
    reports = property(lambda self: self._report_list)

    # -
    def check_resume(self):
        """Checks run_config for Restore info and sets simulation accordingly"""
        if not SimConfig.restore:
            return
        _ = Nd.BBSaveState()
        self._binreport_helper.restoretime(SimConfig.restore)
        logging.info("RESTORE: Recovered previous time: %.3f ms", Nd.t)

    # -
    def load_targets(self):
        self._target_manager.load_targets(self._base_circuit)
        self._target_manager.register_target(self._circuits.global_target)

    # -
    @mpi_no_errors
    @timeit(name="Compute LB")
    def compute_load_balance(self):
        """In case the user requested load-balance this function instantiates a
        CellDistributor to split cells and balance those pieces across the available CPUs.
        """
        log_stage("Computing Load Balance")
        if not self._base_circuit.CircuitPath:
            logging.info(" => No base circuit. Skipping... ")
            return None

        # Info about the cells to be distributed
        target_spec = self._target_spec
        target = self.target_manager.get_target(target_spec)
        cell_count = target.gid_count()
        if cell_count > 100 * MPI.size:
            logging.warning("Your simulation has a very high count of cells per CPU. "
                            "Please consider launching it in a larger MPI cluster")

        # Check / set load balance mode
        lb_mode = LoadBalanceMode.parse(self._run_conf.get("RunMode"))
        if lb_mode == LoadBalanceMode.MultiSplit:
            if not SimConfig.use_coreneuron:
                logging.info("Load Balancing ENABLED. Mode: MultiSplit")
            else:
                logging.warning("Load Balancing mode CHANGED to WholeCell for CoreNeuron")
                lb_mode = LoadBalanceMode.WholeCell

        elif lb_mode == LoadBalanceMode.WholeCell:
            logging.info("Load Balancing ENABLED. Mode: WholeCell")

        elif lb_mode is None:
            lb_mode, reason = LoadBalanceMode.auto_select(SimConfig.use_neuron, cell_count,
                                                          self._run_conf["Duration"])
            if lb_mode != LoadBalanceMode.RoundRobin:
                logging.warning("Load Balance AUTO-SELECTED: %s. Reason: %s", lb_mode.name, reason)

        if lb_mode == LoadBalanceMode.RoundRobin:
            logging.info("Load Balancing DISABLED. Will use Round-Robin distribution")
            return None

        # Build load balancer as per requested options
        prosp_hosts = self._run_conf.get("ProspectiveHosts")
        load_balancer = LoadBalance(
            lb_mode,
            self._run_conf["nrnPath"],
            self._target_manager.parser,
            prosp_hosts
        )

        if load_balancer.valid_load_distribution(target_spec):
            logging.info("Load Balancing done.")
            return load_balancer

        logging.info("Could not reuse load balance data. Doing a Full Load-Balance")
        cell_dist = self._circuits.new_node_manager(self._base_circuit, self._target_manager)
        with load_balancer.generate_load_balance(target_spec.simple_name, cell_dist):
            # Instantiate a basic circuit to evaluate complexities
            cell_dist.finalize()
            self.create_synapses()

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
        # We wont go further if ProspectiveHosts is defined to some other cpu count
        prosp_hosts = self._run_conf.get("ProspectiveHosts")
        if load_balance and prosp_hosts not in (None, MPI.size):
            logging.warning(
                "Load Balance requested for %d CPUs (as per ProspectiveHosts). "
                "To continue execution launch on a partition of that size",
                prosp_hosts)
            Nd.quit()

        log_stage("LOADING NODES")
        if not load_balance:
            logging.info("Load-balance object not present. Continuing Round-Robin...")

        # Always create a cell_distributor even if engine is disabled.
        # Extra circuits may use it and not None is a sign of initialization done
        cell_distributor = CellDistributor(self._base_circuit, self._target_manager, self._run_conf)
        self._circuits.register_node_manager(cell_distributor)
        cell_distributor.load_nodes(load_balance)

        # SUPPORT for extra/custom Circuits
        for name, circuit in self._extra_circuits.items():
            log_stage("Circuit %s", name)
            self._circuits.new_node_manager(circuit, self._target_manager, self._run_conf)

        # Let the cell managers have any final say in the cell objects
        log_stage("FINALIZING CIRCUIT CELLS")
        for cell_manager in self._circuits.all_node_managers():
            log_stage("Circuit %s", cell_manager.circuit_name or "(default)")
            cell_manager.finalize()

    # -
    @mpi_no_errors
    @timeit(name="Synapse creation")
    def create_synapses(self):
        """Create synapses among the cells, handling connections that appear in the config file
        """
        log_stage("LOADING CIRCUIT CONNECTIVITY")
        self._circuits.global_manager.finalize()
        self._target_manager.init_hoc_manager(self._circuits.global_manager)
        target_manager = self._target_manager.hoc
        SimConfig.update_connection_blocks(self._circuits.alias)

        def create_synapase_manager(ctype, conf, *args, population=None, **kwargs):
            log_stage("Circuit %s", conf._name or "(default)")
            if not conf.get("nrnPath"):
                logging.info(" => Circuit internal connectivity has been DISABLED")
                return
            src, dst = population, population
            if not population:
                edge_file, *pop = conf.get("nrnPath").split(":")
                src, dst = edge_node_pop_names(edge_file, pop[0] if pop else None)
            kwargs["_orig_target_pop"] = population
            manager = self._circuits.get_create_edge_manager(ctype, src, dst, conf, *args, **kwargs)
            self._load_connections(conf, manager)  # load internal connections right away

        create_synapase_manager(SynapseRuleManager, self._base_circuit, target_manager,
                                load_offsets=self._is_ngv_run)

        for c_name, circuit in self._extra_circuits.items():
            Engine = circuit.Engine or METypeEngine
            SynManagerCls = Engine.InnerConnectivityCls
            create_synapase_manager(SynManagerCls, circuit, target_manager, population=c_name)

        log_stage("Handling projections...")
        for pname, projection in SimConfig.projections.items():
            self._load_projections(pname, projection)

        log_stage("Configuring connections...")
        for conn_conf in SimConfig.connections.values():
            src_pop = TargetSpec(conn_conf["Source"]).population
            dst_pop = TargetSpec(conn_conf["Destination"]).population
            for conn_manager in self._circuits.get_edge_managers(src_pop, dst_pop):
                logging.debug("Using connection manager: %s", conn_manager)
                conn_manager.configure_connections(conn_conf)

    # -
    def _load_connections(self, circuit_conf, conn_manager):
        if conn_manager.is_file_open:  # Base connectivity
            conn_manager.create_connections()

        # Continue support for compatibility, but new BlueConfigs should use Projection blocks
        bonus_file = circuit_conf.get("BonusSynapseFile")
        if bonus_file:
            logging.info(" > Loading Circuit BonusSynapseFile")
            n_synapse_files = int(circuit_conf.get("NumBonusFiles", 1))
            conn_manager.open_synapse_file(bonus_file, None, n_synapse_files)
            conn_manager.create_connections()

    # -
    def _load_projections(self, pname, projection):
        """Check for Projection blocks
        """
        target_manager = self._target_manager.hoc
        projection = compat.Map(projection).as_dict(True)
        ptype = projection.get("Type")  # None, GapJunctions, NeuroGlial...
        ptype_cls = EngineBase.connection_types.get(ptype)
        if not ptype_cls:
            raise RuntimeError("No Engine to handle connectivity of type '%s'" % ptype)

        ppath, *pop_name = projection["Path"].split(":")
        edge_pop_name = pop_name[0] if pop_name else None
        if not os.path.exists(ppath):
            ppath = self._find_projection_file(ppath)

        source_t = TargetSpec(projection.get("Source"))
        dest_t = TargetSpec(projection.get("Destination"))
        src_pop, dst_pop = edge_node_pop_names(
            ppath, edge_pop_name, source_t.population, dest_t.population
        )
        src_pop, dst_pop = self._circuits.unalias_pop_keys(src_pop, dst_pop)  # un-alias
        logging.info(" * %s (Type: %s, Src: %s, Dst: %s)", pname, ptype, src_pop, dst_pop)

        conn_manager = self._circuits.get_create_edge_manager(
            ptype_cls, src_pop, dst_pop, projection, target_manager,
            _orig_target_pop=dest_t.population
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
                        if path_key in self._run_conf]
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
        log_stage("Stimulus Apply.")

        # Setup of Electrode objects part of enable stimulus
        self._enable_electrodes()

        # for each stimulus defined in the config file, request the stimmanager to instantiate
        add_args = []
        if "BaseSeed" in self._run_conf:
            add_args.append(self._run_conf["BaseSeed"])
        self._stim_manager = StimulusManager(self._target_manager, self._elec_manager, *add_args)
        # Nd.StimulusManager(
        #     self._target_manager.hoc, self._elec_manager, *extra_params)

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
            target_spec = TargetSpec(inject.get("Target").s)
            stim_name = inject.get("Stimulus").s
            stim = stim_dict.get(stim_name)
            if stim is None:
                raise ConfigurationError("Stimulus Inject %s uses non-existing Stim %s",
                                         name, stim_name)

            stim_pattern = stim["Pattern"]
            if stim_pattern == "SynapseReplay":
                continue  # Handled by enable_replay

            logging.info(" * [STIM] %s: %s (%s) -> %s",
                         name, stim_name, stim_pattern, target_spec)
            if stim_pattern in ["Noise", "ShotNoise", "RelativeShotNoise"] and \
                    SimConfig.run_conf.get("StimulusSeed") is None:
                logging.warning("StimulusSeed unset (default %d), "
                                "set explicitly to vary noisy stimuli across runs",
                                SimConfig.rng_info.getStimulusSeed())
            self._stim_manager.interpret(target_spec, stim)

    # -
    def _enable_electrodes(self):
        if SimConfig.use_coreneuron:
            # Coreneuron doesnt support electrodes
            return False
        electrode_path = self._run_conf.get("ElectrodesPath")
        if electrode_path is not None:
            logging.info("ElectrodeManager using electrodes from %s", electrode_path)
        else:
            logging.info("No electrodes path. Extracellular class of stimuli will be unavailable")

        self._elec_manager = Nd.ElectrodeManager(
            electrode_path and Nd.String(electrode_path),
            SimConfig.get_blueconfig_hoc_section("parsedElectrodes")
        )

    # -
    @mpi_no_errors
    def enable_replay(self):
        """Activate replay according to BlueConfig. Call before connManager.finalize
        """
        log_stage("Handling Replay")

        if SimConfig.use_coreneuron and bool(self._core_replay_file):
            logging.info(" -> [REPLAY] Reusing stim file from previous cycle")
            return

        replay_dict = {}
        for stim_name, stim in SimConfig.stimuli.items():
            if stim.get("Pattern").s == "SynapseReplay":
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
        spike_manager = SpikeManager(spike_filepath, tshift)  # Disposable

        # For CoreNeuron, we should put the replays into a single file to be used as PatternStim
        if SimConfig.use_coreneuron:
            # Initialize file if non-existing
            if not self._core_replay_file:
                self._core_replay_file = ospath.join(SimConfig.output_root, 'pattern.dat')
                if MPI.rank == 0:
                    log_verbose("Creating pattern.dat file for CoreNEURON")
                    spike_manager.dump_ascii(self._core_replay_file)
            else:
                if MPI.rank == 0:
                    log_verbose("Appending to pattern.dat")
                    with open(self._core_replay_file, "a") as f:
                        spike_manager.dump_ascii(f)
        else:
            ptype_cls = EngineBase.connection_types.get(connectivity_type)
            src_target = TargetSpec(source)
            dst_target = TargetSpec(target)
            conn_manager = self._circuits.get_edge_manager(src_target.population,
                                                           dst_target.population,
                                                           ptype_cls)
            if not conn_manager:
                logging.error("No edge manager found among populations %s -> %s",
                              src_target.population, dst_target.population)
                raise ConfigurationError("Unknown replay pathway. Check Source / Target")
            conn_manager.replay(spike_manager, src_target.name, dst_target.name, delay)

    # -
    @mpi_no_errors
    @timeit(name="Enable Modifications")
    def enable_modifications(self):
        """Iterate over any Modification blocks read from the BlueConfig and apply them to the
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

    # -
    # @mpi_no_errors - not required since theres a call inside before _binreport_helper.make_comm
    @timeit(name="Enable Reports")
    def enable_reports(self):
        """Iterate over reports defined in BlueConfig and instantiate them.
        """
        log_stage("Reports Enabling")
        n_errors = 0
        sim_end = self._run_conf["Duration"]
        reports_conf = SimConfig.reports
        self._report_list = []

        # Create a map of offsets so that it can be used even on coreneuron save-restore
        if self._circuits.initialized():
            self._circuits.write_population_offsets()
            pop_offsets, alias_pop = self._circuits.get_population_offsets()
        else:
            pop_offsets, alias_pop = CircuitManager.read_population_offsets()
        if SimConfig.use_coreneuron:
            SimConfig.coreneuron.write_report_count(len(reports_conf))

        for rep_name, rep_conf in reports_conf.items():
            rep_conf = compat.Map(rep_conf).as_dict(parse_strings=True)
            rep_type = rep_conf["Type"]
            start_time = rep_conf["StartTime"]
            end_time = rep_conf.get("EndTime", sim_end)
            logging.info(" * %s (Type: %s, Target: %s)", rep_name, rep_type, rep_conf["Target"])

            if rep_type.lower() not in ("compartment", "summation", "synapse", "pointtype"):
                if MPI.rank == 0:
                    logging.error("Unsupported report type: %s.", rep_type)
                n_errors += 1
                continue

            if Nd.t > 0:
                start_time += Nd.t
                end_time += Nd.t
            if end_time > sim_end:
                end_time = sim_end
            if start_time > end_time:
                if MPI.rank == 0:
                    logging.error("Report/Sim End-time (%s) before Start (%g).",
                                  end_time, start_time)
                n_errors += 1
                continue

            electrode = self._elec_manager.getElectrode(rep_conf["Electrode"]) \
                if SimConfig.use_neuron and "Electrode" in rep_conf else None
            rep_target = TargetSpec(rep_conf["Target"])
            target = self._target_manager.get_target(rep_target)
            population_name = (rep_target.population or self._target_spec.population
                               or self._default_population)
            log_verbose("Report on Population: %s, Target: %s", population_name, rep_target.name)

            rep_dt = rep_conf["Dt"]
            if rep_dt < Nd.dt:
                if MPI.rank == 0:
                    logging.error("Invalid report dt %f < %f simulation dt", rep_dt, Nd.dt)
                n_errors += 1
                continue

            target_population = rep_target.population or self._target_spec.population
            population_offset = 0
            cell_manager = self._circuits.get_node_manager(target_population)
            offset = pop_offsets[target_population] if target_population in pop_offsets \
                     else pop_offsets[alias_pop[target_population]]
            if offset > 0:  # dont reset if not needed (recent hoc API)
                target.set_offset(offset)
                population_offset = offset

            report_on = rep_conf["ReportOn"]
            rep_params = namedtuple("ReportConf", "name, type, report_on, unit, format, dt, "
                                    "start, end, output_dir, electrode, scaling, isc, "
                                    "population_name, population_offset")(
                rep_name,
                rep_type,  # rep type is case sensitive !!
                report_on,
                rep_conf["Unit"],
                rep_conf["Format"],
                rep_dt,
                start_time,
                end_time,
                SimConfig.output_root,
                electrode,
                Nd.String(rep_conf["Scaling"]) if "Scaling" in rep_conf else None,
                rep_conf.get("ISC", ""),
                population_name,
                population_offset
            )

            if SimConfig.use_coreneuron and MPI.rank == 0:
                corenrn_target = target

                # 0=Compartment, 1=Cell, Section { 2=Soma, 3=Axon, 4=Dendrite, 5=Apical }
                target_type = target.isCellTarget()
                compartment_offset = 0

                # Note: CoreNEURON does not support more than one Section in a Compartment target
                if target.isCompartmentTarget():
                    for activeTarget in target.subtargets:
                        if activeTarget.isSectionTarget():
                            # Ensure only one Section (i.e., number of subtargets is also 1)
                            if target.subtargets.count() > 1:
                                logging.error("Report '%s': only a single Section is allowed in a "
                                              "Compartment target", rep_name)
                                n_errors += 1
                                break

                            # If we reach this point, update original target and offset
                            corenrn_target = activeTarget
                            compartment_offset = 4

                if corenrn_target.isSectionTarget():
                    if (corenrn_target.subtargets.count() != 1
                            or not corenrn_target.subtargets[0].isCellTarget()):
                        logging.error("Report '%s': only a single Cell subtarget is allowed in a "
                                      "Section target", rep_name)
                        n_errors += 1
                        continue

                    section_type = corenrn_target.targetSubsets[0].s

                    if section_type == "soma":
                        target_type = 2 + compartment_offset
                    elif section_type == "axon":
                        target_type = 3 + compartment_offset
                    elif section_type == "dend":
                        target_type = 4 + compartment_offset
                    elif section_type == "apic":
                        target_type = 5 + compartment_offset
                    else:
                        target_type = 0

                core_report_params = (
                    (rep_name, rep_target.name, rep_type, report_on.replace(" ", ","))
                    + rep_params[3:5] + (target_type,) + rep_params[5:8]
                    + (target.completegids(), SimConfig.corenrn_buff_size, population_name)
                    + (population_offset,)
                )
                SimConfig.coreneuron.write_report_config(*core_report_params)

            if SimConfig.restore_coreneuron:
                continue  # we dont even need to initialize reports

            report = Nd.Report(*rep_params)
            global_manager = self._circuits.global_manager

            if rep_type.lower() in ("compartment", "summation", "synapse"):
                # Go through the target members, one cell at a time. We give a cell reference
                # For summation targets - check if we were given a Cell target because we really
                # want all points of the cell which will ultimately be collapsed to a single value
                # on the soma. Otherwise, get target points as normal.
                points = self._target_manager.get_target_points(target, global_manager,
                                                                rep_type.lower() == "summation")
                for point in points:
                    gid = point.gid
                    cell = global_manager.getCell(gid)
                    spgid = global_manager.getSpGid(gid)

                    # may need to take different actions based on report type
                    if rep_type.lower() == "compartment":
                        report.addCompartmentReport(cell, point, spgid, SimConfig.use_coreneuron)
                    elif rep_type.lower() == "summation":
                        report.addSummationReport(
                            cell, point, target.isCellTarget(), spgid, SimConfig.use_coreneuron)
                    elif rep_type.lower() == "synapse":
                        report.addSynapseReport(cell, point, spgid, SimConfig.use_coreneuron)

            # Custom reporting. TODO: Move above processing to SynRuleManager.enable_report
            cell_manager.enable_report(report, rep_target, SimConfig.use_coreneuron)

            # keep report object? Who has the ascii/hdf5 object? (1 per cell)
            # the bin object? (1 per report)
            self._report_list.append(report)

        if n_errors > 0:
            raise ConfigurationError("%d reporting errors detected. Terminating" % (n_errors,))

        MPI.check_no_errors()

        if SimConfig.use_coreneuron:
            # write spike populations
            if hasattr(SimConfig.coreneuron, "write_population_count"):
                SimConfig.coreneuron.write_population_count(len(pop_offsets))
            for key, value in pop_offsets.items():
                population_name = key or "All"
                population_offset = value
                SimConfig.coreneuron.write_spike_population(population_name, population_offset)

        if not SimConfig.use_coreneuron:
            # Report Buffer Size hint in MB.
            reporting_buffer_size = self._run_conf.get("ReportingBufferSize")
            if reporting_buffer_size is not None:
                self._binreport_helper.set_max_buffer_size_hint(reporting_buffer_size)
                self._sonatareport_helper.set_max_buffer_size_hint(reporting_buffer_size)

            # once all reports are created, we finalize the communicator for any bin reports
            self._binreport_helper.make_comm()
            self._sonatareport_helper.make_comm()
            self._sonatareport_helper.prepare_datasets()

        # electrode manager is no longer needed. free the memory
        if self._elec_manager is not None:
            self._elec_manager.clear()

    # -
    @mpi_no_errors
    def execute_neuron_configures(self):
        """Iterate over any NeuronConfigure blocks from the BlueConfig.
        These are simple hoc statements that can be executed with minimal substitutions
        """
        logging.info("Executing neuron configures")
        for config in SimConfig.configures.values():
            target_name = config.get("Target").s
            configure_str = config.get("Configure").s
            log_verbose("Apply configuration \"%s\" on target %s",
                        config.get("Configure").s, target_name)

            points = self._target_manager.get_target_points(target_name,
                                                            self._circuits.base_cell_manager)
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
        is_save_state = any(c in self._run_conf for c in ("SaveTime", "Save", "Restore"))
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
        restore_path = self._run_conf.get("Restore")
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
            self._spike_populations.append(
                (cell_manager.population_name, cell_manager.local_nodes.offset))
            self._spike_vecs.append(cell_manager.record_spikes() if cell_manager.record_spikes()
                                    else (Nd.Vector(), Nd.Vector()))

        self._pc.timeout(200)  # increase by 10x

        if restore_path:
            with timeit(name="restoretime"):
                logging.info("Restoring state...")
                bbss = Nd.BBSaveState()
                self._stim_manager.saveStatePreparation(bbss)
                bbss.ignore(self._binreport_helper)
                self._binreport_helper.restorestate(restore_path)
                self._stim_manager.reevent()
                bbss.vector_play_init()
                self._restart_events()  # On restore the event queue is cleared
                return  # Upon restore sim is ready

    # -
    def _restart_events(self):
        logging.info("Restarting connections events (Replay and Spont Minis)")
        for syn_manager in self._circuits.all_synapse_managers():
            syn_manager.restart_events()

        logging.info("Restarting Reports events")
        nc = Nd.NetCon(None, self._binreport_helper, 10, 1, 1)
        nc.event(Nd.t)
        self._jumpstarters.append(nc)

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
        base_manager.load_artificial_cell(fake_gid, SimConfig.coreneuron)

        yield

        # Nd.registerMapping doesn't work for this artificial cell as somatic attr is
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
    @timeit(name="corewrite")
    def _sim_corenrn_write_config(self, corenrn_restore=False):
        log_stage("Dataset generation for CoreNEURON")

        corenrn_output = SimConfig.coreneuron_ouputdir
        corenrn_data = SimConfig.coreneuron_datadir
        fwd_skip = self._run_conf.get("ForwardSkip", 0) if not corenrn_restore else 0

        if not corenrn_restore:
            Nd.registerMapping(self._circuits.global_manager)
            with self._coreneuron_ensure_all_ranks_have_gids(corenrn_data):
                self._pc.nrnbbcore_write(corenrn_data)
                MPI.barrier()  # wait for all ranks to finish corenrn data generation

        optional_params = [self._run_conf["BaseSeed"]] if "BaseSeed" in self._run_conf else []
        SimConfig.coreneuron.write_sim_config(
            corenrn_output,
            corenrn_data,
            Nd.tstop,
            Nd.dt,
            fwd_skip,
            self._pr_cell_gid or -1,
            self._core_replay_file,
            *optional_params
        )

        logging.info(" => Dataset written to '{}'".format(corenrn_data))

    # -
    def run_all(self):
        """Run the whole simulation according to BlueConfig
        """
        if not self._sim_ready:
            self.sim_init()

        timings = None
        if SimConfig.use_neuron:
            timings = self._run_neuron()
            self.spike2file("out.dat")
        if SimConfig.use_coreneuron:
            self.clear_model()
            self._run_coreneuron()
            self.adapt_spikes("out.dat")
        return timings

    # -
    @return_neuron_timings
    def _run_neuron(self):
        _ = Nd.ShowProgress(Nd.cvode, MPI.rank)
        self.solve()
        logging.info("Simulation finished.")

    # -
    def _run_coreneuron(self):
        logging.info("Launching simulation with CoreNEURON")
        neurodamus2core = {"Save": "--checkpoint",
                           "Restore": "--restore"}
        opts = [(core_opt, self._run_conf[opt])
                for opt, core_opt in neurodamus2core.items()
                if opt in self._run_conf]
        opts_expanded = functools.reduce(operator.iconcat, opts, [])

        log_verbose("solve_core(..., %s)", ", ".join(opts_expanded))
        SimConfig.coreneuron.psolve_core(*opts_expanded)

    #
    def _sim_event_handlers(self, tstart, tstop):
        """Create handlers for "in-simulation" events, like activating delayed
        connections, execute Save-State, etc
        """
        events = defaultdict(list)  # each key (time) points to a list of handlers

        # Handle Save
        save_time_config = self._run_conf.get("SaveTime")

        if "Save" in self._run_conf:
            tsave = tstop
            if save_time_config is not None:
                tsave = save_time_config
                if tsave > tstop:
                    tsave = tstop
                    logging.warning("SaveTime specified beyond Simulation Duration. "
                                    "Setting SaveTime to tstop.")

            @timeit(name="savetime")
            def save_f():
                logging.info("Saving State... (t=%f)", tsave)
                bbss = Nd.BBSaveState()
                MPI.barrier()
                self._stim_manager.saveStatePreparation(bbss)
                bbss.ignore(self._binreport_helper)
                self._binreport_helper.pre_savestate(self._run_conf["Save"])
                log_verbose("SaveState Initialization Done")

                # If event at the end of the sim we can actually clearModel() before savestate()
                if save_time_config is None:
                    log_verbose("Clearing model prior to final save")
                    self._binreport_helper.flush()
                    self._sonatareport_helper.flush()
                    self.clear_model()

                self.dump_cell_config()
                self._binreport_helper.savestate()
                logging.info(" => Save done successfully")

            events[tsave].append(save_f)

        elif save_time_config is not None:
            logging.warning("SaveTime IGNORED. Reason: no 'Save' config entry")

        event_list = [(t, events[t]) for t in sorted(events)]
        return event_list

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
        cur_t = Nd.t
        buffer_t = SimConfig.buffer_time
        for _ in range(math.ceil((tstop - cur_t) / buffer_t)):
            next_flush = min(tstop, cur_t + buffer_t)
            self._pc.psolve(next_flush)
            self._binreport_helper.flush()
            cur_t = next_flush
        Nd.t = cur_t

    # -
    @mpi_no_errors
    def clear_model(self, avoid_creating_objs=False):
        """Clears appropriate lists and other stored references.
        For use with intrinsic load balancing. After creating and evaluating the network using
        round robin distribution, we want to clear the cells and synapses in order to have a
        clean slate on which to instantiate the balanced cells.
        """
        if not self._target_manager.parser:
            # Target parser is the ground block. If not there model is clear
            return

        logging.info("Clearing model")
        self._pc.gid_clear()
        self._target_manager.parser.updateTargets(Nd.Vector())  # reset targets local cells
        self._target_manager.init_hoc_manager(None)  # Init/release cell manager

        if not avoid_creating_objs:
            bbss = Nd.BBSaveState()
            bbss.ignore()
            if SimConfig.use_neuron:
                if self._binreport_helper:
                    self._binreport_helper.clear()
                if self._sonatareport_helper:
                    self._sonatareport_helper.clear()

        Node.__init__(self, None, None)  # Reset vars

    # -------------------------------------------------------------------------
    #  output
    # -------------------------------------------------------------------------

    @run_only_rank0
    def adapt_spikes(self, outfile):
        """Prepend /scatter to spikes file after coreneuron sim finishes.
        """
        output_root = SimConfig.output_root
        outfile = ospath.join(output_root, outfile)
        tmpfile = ospath.join(output_root, 'tmp.out')
        with open(outfile, 'r') as f_src:
            with open(tmpfile, 'w') as f_dest:
                f_dest.write("/scatter\n")
                copyfileobj(f_src, f_dest)
        move(tmpfile, outfile)

    @mpi_no_errors
    def spike2file(self, outfile):
        """ Write the spike events that occured on each node into a single output file.
        Nodes will write in order, one after the other.
        """
        logging.info("Writing spikes to %s", outfile)
        output_root = SimConfig.output_root
        outfile = ospath.join(output_root, outfile)
        spikevec = Nd.Vector()
        idvec = Nd.Vector()
        # merge spike_vecs and id_vecs for SpikeWriter
        for spikes, ids in self._spike_vecs:
            spikevec.append(spikes)
            idvec.append(ids)
        spikewriter = Nd.SpikeWriter()
        spikewriter.write(spikevec, idvec, outfile)

        # SONATA SPIKES
        if hasattr(self._sonatareport_helper, "create_spikefile"):
            # Write spike report for multiple populations if exist
            # create a sonata spike file
            self._sonatareport_helper.create_spikefile(output_root)
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
        simulator = "CoreNeuron" if SimConfig.coreneuron else "Neuron"
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
        Nd.MemUsage().print_mem_usage()

        # Coreneuron runs clear the model before starting
        if not SimConfig.coreneuron or SimConfig.simulate_model is False:
            self.clear_model(avoid_creating_objs=True)

        if SimConfig.delete_corenrn_data:
            data_folder = SimConfig.coreneuron_datadir
            logging.info("Deleting intermediate data in %s", data_folder)

            with timeit_rank0(name="Delete corenrn data"):
                if MPI.rank == 0:
                    if ospath.islink(data_folder):
                        # in restore, coreneuron data is a symbolic link
                        os.unlink(data_folder)
                    else:
                        subprocess.call(['/bin/rm', '-rf', data_folder])
                    os.remove(ospath.join(SimConfig.output_root, "sim.conf"))
                    os.remove(ospath.join(SimConfig.output_root, "report.conf"))
            MPI.barrier()

        logging.info("Finished")
        TimerManager.timeit_show_stats()


# Helper class
# ------------
class Neurodamus(Node):
    """A high level interface to Neurodamus
    """

    def __init__(self, config_file, auto_init=True, logging_level=None, **user_opts):
        """Creates and initializes a neurodamus run node

        As part of Initiazation it calls:
         * load_targets
         * compute_load_balance
         * Build the circuit (cells, synapses, GJs)
         * Add stimulus & replays
         * Activate reports if requested

        Args:
            config_file: The BlueConfig recipe file
            logging_level: (int) Redefine the global logging level.
                0 - Only warnings / errors
                1 - Info messages (default)
                2 - Verbose
                3 - Debug messages
            user_opts: Options to Neurodamus overriding BlueConfig
        """
        self._init_ok = False
        if logging_level is not None:
            GlobalConfig.verbosity = logging_level

        enable_reports = not user_opts.pop("disable_reports", False)

        Node.__init__(self, config_file, user_opts)
        # Use the run_conf dict to avoid passing it around
        self._run_conf["EnableReports"] = enable_reports
        self._run_conf["AutoInit"] = auto_init

        if SimConfig.coreneuron and "Restore" in self._run_conf:
            self._coreneuron_restore()
        elif SimConfig.build_model:
            self._instantiate_simulation()

        # In case an exception occurs we must prevent the destructor from cleaning
        self._init_ok = True

    # -
    def _build_model(self):
        log_stage("================ CALCULATING LOAD BALANCE ================")
        load_bal = self.compute_load_balance()

        log_stage("==================== BUILDING CIRCUIT ====================")
        self.create_cells(load_bal)
        self.execute_neuron_configures()

        # Create connections
        self.create_synapses()

        log_stage("================ INSTANTIATING SIMULATION ================")
        if not SimConfig.coreneuron:
            self.check_resume()  # For CoreNeuron there _coreneuron_restore

        # Apply replay
        self.enable_replay()

        if self._run_conf["AutoInit"]:
            self.init()

    # -
    def init(self):
        """Explicitly initialize, allowing users to make last changes before simulation
        """
        log_stage("Creating connections in the simulator")
        base_seed = self._run_conf.get("BaseSeed", 0)  # base seed for synapse RNG
        for syn_manager in self._circuits.all_synapse_managers():
            syn_manager.finalize(base_seed, SimConfig.coreneuron)

        self.enable_stimulus()
        self.enable_modifications()

        if self._run_conf["EnableReports"]:
            self.enable_reports()

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
                for lineNumber in range(nlines):
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
        self.load_targets()
        self.enable_replay()
        if self._run_conf["EnableReports"]:
            self.enable_reports()
        self._sim_corenrn_write_config(corenrn_restore=True)
        self._sim_ready = True

    # -
    def _instantiate_simulation(self):
        self.load_targets()
        target: NodesetTarget = self._target_manager.get_target(self._target_spec)
        cell_count = target.gid_count()
        logging.info("Simulation target: %s, Cell count: %d", target.name, cell_count)

        # Check if user wants to build the model in several steps (only for CoreNeuron)
        target = TargetSpec(self._run_conf.get("CircuitTarget", "Mosaic")).name
        n_cycles = SimConfig.modelbuilding_steps

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

        sub_targets = self._target_manager.generate_subtargets(target, n_cycles)

        # Check connection block configuration and raise warnings for overriding parameters
        SimConfig.check_connections_configure(self._target_manager)

        # Without multi-cycle, it's a trivial model build. sub_targets is False
        if n_cycles == 1:
            self._build_model()
            return

        logging.info("MULTI-CYCLE RUN: {} Cycles".format(n_cycles))

        tmp_target_spec = TargetSpec(self._run_conf["CircuitTarget"])
        TimerManager.archive(archive_name="Before Cycle Loop")
        for cycle_i, cur_target in enumerate(sub_targets):
            logging.info("")
            logging.info("-" * 60)
            log_stage("==> CYCLE {} (OUT OF {})".format(cycle_i + 1, n_cycles))
            logging.info("-" * 60)

            self.clear_model()
            tmp_target_spec.name = cur_target.name
            self._base_circuit.CircuitTarget = str(tmp_target_spec)  # FQN
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
        if not SimConfig.simulate_model:
            self.sim_init()
            log_stage("======== [SKIPPED] SIMULATION (MODEL BUILD ONLY) ========")
        elif not SimConfig.build_model:
            log_stage("============= SIMULATION (SKIP MODEL BUILD) =============")
            self._run_coreneuron()
        else:
            log_stage("======================= SIMULATION =======================")
            self.run_all()

    def __del__(self):
        if self._init_ok:
            self.cleanup()
