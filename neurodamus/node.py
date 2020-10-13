# Neurodamus
# Copyright 2018 - Blue Brain Project, EPFL

from __future__ import absolute_import
import functools
import itertools
import logging
import math
import operator
import os
import subprocess
from os import path as ospath
from collections import namedtuple, defaultdict

from .core import EngineBase
from .core import MPI, mpi_no_errors, return_neuron_timings
from .core import NeurodamusCore as Nd
from .core.configuration import GlobalConfig, RunOptions, SimConfig, CircuitConfig
from .core.configuration import ConfigurationError
from .cell_distributor import CellDistributor, LoadBalance, LoadBalanceMode
from .io.cell_readers import TargetSpec
from .io.config_parser import BlueConfig
from .connection_manager import SynapseRuleManager, GapJunctionManager
from .replay import SpikeManager
from .utils import compat
from .utils.logging import log_stage, log_verbose, log_all
from .utils.timeit import TimerManager, timeit, timeit_rank0


class Node:
    """The Node class is the main entity for a distributed neurodamus execution.

    It internally instantiates parallel structures and distributes the cells among all the nodes.
    It is relatively low-level, for a standard run consider using the Neurodamus class instead.
    """

    _default_population = 'All'
    """The default population name for e.g. Reports."""

    _bbcore_fakegid_offset = None
    """The offset for creating fake gids for ARTIFICIAL CELLS in coreneuron."""

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
            self._target_parser = None
            self._pnm = Nd.ParallelNetManager(0)
            self._options = opts = RunOptions(**(options or {}))
            self._blueconfig_path = ospath.dirname(config_file)
            self._core_replay_file = ''

            self._config_parser = self._open_check_config(config_file, opts)
            self._run_conf = compat.Map(self._config_parser.parsedRun).as_dict(True)
            self._output_root = self._run_conf["OutputRoot"]
            self._pr_cell_gid = self._run_conf.get("prCellGid")
            self._base_circuit, self._extra_circuits = self._config_circuits(config_file)

            _sim_config = self._configure_simulator(self._run_conf, opts)
            self._corenrn_conf = _sim_config.core_config
            self._binreport_helper = Nd.BinReportHelper(Nd.dt, True) \
                if _sim_config.runNeuron() else None
            self._sonatareport_helper = Nd.SonataReportHelper(Nd.dt, True) \
                if _sim_config.runNeuron() else None
            self._target_spec = TargetSpec(self._run_conf.get("CircuitTarget"))
            self._corenrn_buff_size = self._run_conf["ReportingBufferSize"] \
                if "ReportingBufferSize" in self._run_conf else 8
            MPI.check_no_errors()  # Ensure no rank terminated unexpectedly

        self._target_manager = None
        self._stim_list = None
        self._report_list = None
        self._stim_manager = None
        self._elec_manager = None
        self._sim_ready = False

        self._cell_distributor = None  # type: CellDistributor
        self._synapse_manager = None   # type: SynapseRuleManager
        self._gj_manager = None        # type: GapJunctionManager
        self._jumpstarters = []

    #
    # public 'read-only' properties - object modification on user responsibility
    target_manager = property(lambda self: self._target_manager)
    synapse_manager = property(lambda self: self._synapse_manager)
    gj_manager = property(lambda self: self._gj_manager)
    stim_manager = property(lambda self: self._stim_manager)
    elec_manager = property(lambda self: self._elec_manager)
    cells = property(lambda self: self._cell_distributor.cell_list)
    stims = property(lambda self: self._stim_list)
    reports = property(lambda self: self._report_list)

    # Compat
    cellDistributor = CellDistributor

    @classmethod
    def _open_check_config(cls, config_file, user_options):
        """ Initialize config objects and set Neuron global options from BlueConfig

        Args:
            config_file: Name of Config file to load
            user_options: The object of user options
        """
        log_stage("Loading settings from BlueConfig and CLI")
        config_parser = Nd.ConfigParser()
        config_parser.open(config_file)
        if MPI.rank == 0:
            config_parser.toggleVerbose()

        if config_parser.parsedRun is None:
            raise ConfigurationError("No 'Run' block found in BlueConfig %s", config_file)
        parsed_run = config_parser.parsedRun

        # Setup source dirs
        blueconfig_dir = ospath.abspath(ospath.dirname(config_file))
        parsed_run.put("BlueConfigDir", Nd.String(blueconfig_dir))

        if parsed_run.exists("CurrentDir"):
            curdir = parsed_run.get("CurrentDir").s

            if not ospath.isabs(curdir):
                if curdir == ".":
                    logging.warning("Setting CurrentDir to '.' is discouraged and "
                                    "shall never be used in production jobs.")
                else:
                    raise ConfigurationError("CurrentDir: Relative paths not allowed")
                curdir = ospath.abspath(curdir)
                parsed_run.put("CurrentDir", Nd.String(curdir))

            if not ospath.isdir(curdir):
                raise ConfigurationError("CurrentDir doesnt exist: " + curdir)
        else:
            log_verbose("Setting CurrentDir to BlueConfig path [default]")
            curdir = blueconfig_dir

        # confirm output_path exists and is usable -> use utility.mod
        output_path_obj = parsed_run.get("OutputRoot")
        if user_options.output_path:
            output_path_obj.s = user_options.output_path
        output_path = output_path_obj.s

        # Warn about new behavior of relative path. Remove warning in next version
        if not ospath.isabs(output_path):
            logging.warning("Relative OutputRoot directories are now constructed from "
                            "CurrentDir, which defaults to BlueConfig location.\nPlease "
                            "ensure your toolchains dont expect results in CWD.")
            output_path = ospath.join(curdir, output_path)
            output_path_obj.s = output_path

        if MPI.rank == 0:
            if Nd.checkDirectory(output_path) < 0:
                logging.error("Error with OutputRoot %s. Terminating", output_path)
                raise ConfigurationError("Output directory error")

        simulator = cls._check_model_build_mode(user_options, parsed_run, output_path)

        # BlueConfig integrity checks
        if parsed_run.exists("Restore") and simulator == "CORENEURON":
            user_options.build_model = False
            if not user_options.simulate_model:
                raise ConfigurationError("CoreNeuron Restore with simulate_model=OFF")

        if not user_options.simulate_model and not user_options.build_model:
            raise ConfigurationError("NoOP: Both build and simulation have been disabled")

        # Make sure we can load mvdtool if CellLibraryFile is sonata file
        run_conf = compat.Map(parsed_run)
        if run_conf.get('CellLibraryFile', 'start.ncs') not in ('start.ncs', 'circuit.mvd3'):
            try:
                import mvdtool  # noqa: F401
            except ImportError:
                raise ConfigurationError("Cannot import mvdtool, please install py-mvdtool")
        else:
            if TargetSpec(run_conf.get("CircuitTarget")).population is not None:
                raise ConfigurationError("Targets with population require Sonata Node file")

        # Display final settings
        logging.info("Config:")
        logging.info(" - CurrentDir: %s", curdir)
        logging.info(" - OutputRoot: %s", output_path)
        logging.info(" - PHASES Build: %s, Simulate: %s",
                     user_options.build_model, user_options.simulate_model)

        return config_parser

    def _config_circuits(self, config_file):
        """Load directly from config file info about circuits and Validate
        CircuitPath and nrnPath. Values may be set to <NONE> in case the user
        wants to disable the whole circuit or the base synapses respectively.
        """
        def _make_circuit_config(config_dict, circuit_name):
            if config_dict["CircuitPath"] == "<NONE>":
                logging.info("%s Circuit DISABLED", circuit_name)
                config_dict["CircuitPath"] = False
                config_dict["nrnPath"] = False
            elif config_dict["nrnPath"] == "<NONE>":
                config_dict["nrnPath"] = False
            return CircuitConfig(config_dict)

        blueconfig = BlueConfig(config_file)
        base_circuit = _make_circuit_config(blueconfig.Run, "Default")
        extra_circuits = {}

        for name, circuit_info in blueconfig.Circuit.items():
            logging.info("Configuring circuit %s", name)
            if "Engine" in circuit_info:
                # Replace name by actual engine
                circuit_info["Engine"] = EngineBase.get(circuit_info["Engine"])
            else:
                # Without custom engine, inherit base circuit infos
                for field in ("CircuitPath", "MorphologyPath", "MorphologyType",
                              "METypePath", "CellLibraryFile"):
                    if field in base_circuit and field not in circuit_info:
                        log_verbose("Inheriting '%s' from base circuit", field)
                        circuit_info[field] = base_circuit[field]

            extra_circuits[name] = _make_circuit_config(circuit_info, name)

        return base_circuit, extra_circuits

    @staticmethod
    def _check_model_build_mode(user_config, parsed_run, output_path):
        core_config_exists = ospath.isfile(ospath.join(output_path, "sim.conf"))
        simulator = parsed_run.get("Simulator").s if parsed_run.exists("Simulator") \
            else None
        if simulator == "NEURON" and (user_config.build_model is False
                                      or user_config.simulate_model is False):
            raise ConfigurationError("Disabling model building or simulation is only"
                                     " compatible with CoreNEURON")

        if user_config.build_model is False and not core_config_exists:
            raise ConfigurationError("Model build was disabled, but sim.conf not found")

        if user_config.build_model not in (True, False):
            # No sim.conf -> can leave as is
            if not core_config_exists:
                logging.info("CoreNeuron data do not exist in '%s'. "
                             "Neurodamus will proceed to model building.", output_path)
                user_config.build_model = True
                return

            # Otherwise we can activate if the simulator supports it
            if simulator == "CORENEURON":
                user_config.build_model = False
                logging.info("CoreNeuron data found. Attempting to resume execution")
            elif simulator == "NEURON":
                logging.warning("CoreNeuron data found but simulator is NEURON. "
                                "To reuse please set 'Simulator' to CORENEURON.")
            else:
                logging.warning("Setting simulator to CORENEURON to resume execution")
                parsed_run.put("Simulator", Nd.String("CORENEURON"))
                user_config.build_model = False
        return simulator

    @staticmethod
    def _configure_simulator(run_conf, user_options):
        Nd.execute("cvode = new CVode()")
        Nd.execute("celsius=34")

        SimConfig.init(Nd.h, run_conf)

        keep_core_data = False
        if SimConfig.core_config:
            if user_options.keep_build or run_conf.get("KeepModelData", False) == "True":
                keep_core_data = True
            elif not user_options.simulate_model or "Save" in run_conf:
                logging.warning("Keeping coreneuron data for CoreNeuron Save-Restore")
                keep_core_data = True
        SimConfig.delete_corenrn_data = SimConfig.core_config and not keep_core_data

        h = Nd.h
        h.tstop = run_conf["Duration"]
        h.dt = run_conf["Dt"]
        h.steps_per_ms = 1.0 / h.dt
        second_order = SimConfig.secondorder
        if second_order is not None:
            if second_order in (0, 1, 2):
                h.secondorder = int(second_order)
                logging.info("Setting SecondOrder to: {}".format(int(second_order)))
            else:
                raise ConfigurationError("Time integration method (SecondOrder value) {} is "
                                         "invalid. Valid options are:"
                                         " '0' (implicity backward euler),"
                                         " '1' (crank-nicholson) and"
                                         " '2' (crank-nicholson with fixed ion currents)"
                                         .format(second_order))
        return SimConfig

    # -
    def check_resume(self):
        """Checks run_config for Restore info and sets simulation accordingly"""
        if "Restore" not in self._run_conf:
            return
        _ = Nd.BBSaveState()
        restore_path = self._run_conf["Restore"]
        self._binreport_helper.restoretime(restore_path)
        logging.info("RESTORE: Recovered previous time: %.3f ms", Nd.t)

    # -
    @mpi_no_errors
    def multicycle_data_generation(self):
        """To facilitate CoreNeuron data generation, we allow users to use ModelBuildingSteps to
        indicate that the CircuitTarget should be split among multiple, smaller targets that will
        be built step by step.

        Returns:
            list with generated targets, or empty if no splitting was done
        """
        run_conf = self._run_conf
        if self._options.modelbuilding_steps is not None:
            ncycles = int(self._options.modelbuilding_steps)
            src_is_cli = True
        elif "ModelBuildingSteps" in run_conf:
            ncycles = int(run_conf["ModelBuildingSteps"])
            src_is_cli = False
        else:
            return False

        logging.info("Splitting Target for multi-iteration CoreNeuron data generation")
        logging.info(" -> Cycles: %d. [src: %s]", ncycles, "CLI" if src_is_cli else "BlueConfig")
        assert ncycles > 0, "splitdata_generation yielded 0 cycles. Please check ModelBuildingSteps"

        if not self._corenrn_conf:
            logging.warning("Splitdata DISABLED since simulator is not CoreNeuron")
            return False

        if "CircuitTarget" not in run_conf:
            raise ConfigurationError(
                "Multi-iteration coreneuron data generation requires CircuitTarget")

        target_spec = TargetSpec(run_conf["CircuitTarget"])
        target = self._target_parser.getTarget(target_spec.name)
        allgids = target.completegids()
        new_targets = []

        for cycle_i in range(ncycles):
            target = Nd.Target()
            target.name = "{}_{}".format(target_spec.name, cycle_i)
            new_targets.append(target)
            self._target_parser.updateTargetList(target)

        target_looper = itertools.cycle(new_targets)
        for gid in allgids.x:
            target = next(target_looper)
            target.gidMembers.append(gid)

        return new_targets

    # -
    @mpi_no_errors
    @timeit(name="Target Load")
    def load_targets(self):
        """Provided that the circuit location is known and whether a user.target file has been
        specified, load any target files via a TargetParser.
        Note that these will be moved into a TargetManager after the cells have been distributed,
        instantiated, and potentially split.
        """
        log_stage("Loading Targets")
        run_conf = self._run_conf
        self._target_parser = Nd.TargetParser()
        if MPI.rank == 0:
            self._target_parser.isVerbose = 1

        if self._base_circuit.CircuitPath:
            start_target_file = ospath.join(run_conf["CircuitPath"], "start.target")
            if not ospath.isfile(start_target_file):
                logging.warning("DEPRECATION: start.target shall be within CircuitPath. "
                                "Within nrnPath is deprecated and will be removed")
                start_target_file = ospath.join(run_conf["nrnPath"], "start.target")  # fallback

            if not ospath.isfile(start_target_file):
                raise ConfigurationError("start.target not found! Check circuit.")

            self._target_parser.open(start_target_file)

        if "TargetFile" in run_conf:
            user_target = self._find_input_file(run_conf["TargetFile"])
            self._target_parser.open(user_target, True)

        if MPI.rank == 0:
            logging.info(" => Loaded %d targets", self._target_parser.targetList.count())
            if GlobalConfig.verbosity >= 3:
                self._target_parser.printCellCounts()

    # -
    @mpi_no_errors
    @timeit(name="Compute LB")
    def compute_load_balance(self):
        """In case the user requested load-balance this function instantiates a
        CellDistributor to split cells and balance those pieces across the available CPUs.
        """
        log_stage("Computing Load Balance")
        if not self._base_circuit.CircuitPath:
            logging.info("  => No base circuit. Skipping... ")
            return None

        # Info about the cells to be distributed
        target = self._target_spec
        target_cells, _ = self.get_targetcell_count()
        if target_cells > 100 * MPI.size:
            logging.warning("Your simulation has a very high count of cells per CPU. "
                            "Please consider launching it in a larger MPI cluster")

        # Check / set load balance mode
        lb_mode = LoadBalanceMode.parse(self._run_conf.get("RunMode"))
        if lb_mode == LoadBalanceMode.MultiSplit:
            if not self._corenrn_conf:
                logging.info("Load Balancing ENABLED. Mode: MultiSplit")
            else:
                logging.warning("Load Balancing mode CHANGED to WholeCell for CoreNeuron")
                lb_mode = LoadBalanceMode.WholeCell

        elif lb_mode == LoadBalanceMode.WholeCell:
            logging.info("Load Balancing ENABLED. Mode: WholeCell")

        elif lb_mode is None:
            # BBPBGLIB-555 - simple heuristics for auto selecting load balance
            lb_mode = LoadBalanceMode.RoundRobin
            if MPI.size > 1.5 * target_cells:
                logging.warning("Load Balance: AUTO SELECTED MultiSplit (CPU-Cell ratio)")
                lb_mode = LoadBalanceMode.MultiSplit
            elif target_cells > 1000 and (self._run_conf["Duration"] > 500 or MPI.size > 100):
                logging.warning("Load Balance: AUTO SELECTED WholeCell (Sim Size)")
                lb_mode = LoadBalanceMode.WholeCell

        if lb_mode == LoadBalanceMode.RoundRobin:
            logging.info("Load Balancing DISABLED. Will use Round-Robin distribution")
            return None

        # Build load balancer as per requested options
        prosp_hosts = self._run_conf.get("ProspectiveHosts")
        load_balancer = LoadBalance(
            lb_mode, self._run_conf["nrnPath"], self._target_parser, prosp_hosts)

        if load_balancer.valid_load_distribution(target):
            logging.info("Load Balancing done.")
            return load_balancer

        logging.info("Could not reuse load balance data. Doing a Full Load-Balance")
        cell_dist = CellDistributor(self._pnm, self._target_parser, self._run_conf)
        with load_balancer.generate_load_balance(target.simple_name, cell_dist):
            # Instantiate a basic circuit to evaluate complexities
            self.create_cells(cell_distributor=cell_dist)
            self.create_synapses()
            self.create_gap_junctions()

        # reset since we instantiated with RR distribution
        Nd.t = .0  # Reset time
        self.clear_model()

        return load_balancer

    # -
    @mpi_no_errors
    @timeit(name="Cell creation")
    def create_cells(self, load_balance=None, cell_distributor=None):
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

        log_stage("Loading circuit cells")

        if not load_balance and not cell_distributor:
            logging.info("Load-balance object not present. Continuing Round-Robin...")

        # Always create a cell_distributor even if engine is disabled.
        # Extra circuits may use it and not None is a sign of initialization done
        if cell_distributor is None:
            self._cell_distributor = CellDistributor(
                self._pnm, self._target_parser, self._run_conf)
        else:
            self._cell_distributor = cell_distributor

        # Dont use default cell_distributor if engine is disabled
        if self._base_circuit.CircuitPath:
            self._cell_distributor.load_cells(self._run_conf, load_balance)
        else:
            logging.info(" => Base Circuit has been DISABLED")

        # SUPPORT for extra/custom Circuits
        for name, circuit in self._extra_circuits.items():
            log_stage("Loading Cells for Circuit: %s", name)
            engine = circuit.Engine
            output = NotImplemented  # NotImplemented stands for 'use the default one'
            if engine:
                output = engine.create_cells(circuit.all, self._cell_distributor,
                                             self._target_parser, self._run_conf)
            if output is NotImplemented:
                self._cell_distributor.load_cells(circuit)

        # give a TargetManager the TargetParser's completed targetList
        self._target_manager = Nd.TargetManager(
            self._target_parser.targetList, self._cell_distributor)

        # Let the CellDistributor object have any final say in the cell objects
        self._cell_distributor.finalize()
        # Extra circuits
        for engine in set(circuit.Engine for circuit in self._extra_circuits.values()
                          if circuit.Engine is not None):
            engine.finalize_cells()

    # -
    @mpi_no_errors
    @timeit(name="Synapse creation")
    def create_synapses(self):
        """Create synapses among the cells, handling connections that appear in the config file
        """
        if self._base_circuit.nrnPath:
            log_stage("Creating base circuit connections")
            self._create_connections()
        else:
            # Instantiate a bare synapse manager
            self._synapse_manager = SynapseRuleManager(
                self._base_circuit, self._target_manager, self._cell_distributor)

        # Loop over additional circuits to instantiate synapses
        # Synapse creation is slightly more complex since there are three possible
        # outcomes: NotImplemented (use default), None (no connections) or custom obj
        extra_managers = []

        for name, circuit in self._extra_circuits.items():
            log_stage("Creating connections for Extra Circuit %s", name)
            engine = circuit.Engine

            if engine:
                syn_manager = engine.create_synapses(
                    circuit, self._target_manager, self._synapse_manager)
                # If syn_manager is None then, either everything was done by create_synapses
                # or SynaManagerCls was not set
                if syn_manager is None:
                    continue
                if syn_manager is NotImplemented:
                    syn_manager = self._synapse_manager
                else:
                    extra_managers.append(syn_manager)
            else:
                syn_manager = self._synapse_manager

            if circuit.nrnPath:
                syn_manager.open_synapse_file(circuit.nrnPath, 1, int(circuit.PopulationID))
                self._create_group_connections(syn_manager=syn_manager)
            else:
                logging.info(" * %s connections have been disabled", name)

        # Configure all created connections in one go
        logging.info("Configuring all Base Circuit connections...")
        self._configure_connections()

        for extra_syn_manager in extra_managers:
            logging.info("Configuring all %s connections...", extra_syn_manager.__class__.__name__)
            self._configure_connections(extra_syn_manager)

    # -
    def _create_connections(self):
        # if we have a single connect block with weight=0, skip synapse creation  entirely
        if self._config_parser.parsedConnects.count() == 1:
            if self._config_parser.parsedConnects.o(0).valueOf("Weight") == 0:
                return

        with timeit(name="Synapse init"):
            self._synapse_manager = SynapseRuleManager(
                self._base_circuit, self._target_manager, self._cell_distributor)

        # Dont attempt to create default connections if engine is disabled
        logging.info("Creating circuit connections...")
        self._create_group_connections()

        # Check for additional synapse files.  Now requires a connection block.
        # Continue support for compatibility, but new BlueConfigs should use Projection blocks
        bonus_file = self._run_conf.get("BonusSynapseFile")
        if bonus_file:
            logging.info("Creating connections from Bonus synapse file...")
            bonus_n_synapse_files = int(self._run_conf.get("NumBonusFiles", 1))
            self._synapse_manager.open_synapse_file(bonus_file, bonus_n_synapse_files)
            self._create_group_connections()

        # Check for Projection blocks
        if self._config_parser.parsedProjections.count() > 0:
            logging.info("Creating Projections connections...")

        for pname, projection in compat.Map(self._config_parser.parsedProjections).items():
            logging.info(" * %s", pname)
            projection = compat.Map(projection).as_dict(True)

            # Skip projection blocks for gap junctions
            if projection.get("Type") == "GapJunction":
                continue

            proj_path, *pop_name = projection["Path"].split(":")
            nrn_path = self._find_projection_file(proj_path)
            nrn_path = ":".join([nrn_path] + pop_name)

            # Allow overriding src PopulationID
            # Required for older nrn and syn2, otherwise connections are always merged
            pop_id = None
            if "PopulationID" in projection:
                pop_id = int(projection["PopulationID"])
            if pop_id == 0:
                raise ConfigurationError("PopulationID 0 is not allowed")

            # If the projections are to be merged with base connectivity and the base
            # population is unknown, with Sonata pop we need a way to explicitly request it.
            # Note: gid offsetting must have been previously done
            if projection.get("AppendBasePopulation"):
                assert pop_id is None, "AppendBasePopulation is incompatible with PopulationID"
                log_verbose("Appending projection to base connectivity (AppendBasePopulation)")
                pop_id = 0

            self._synapse_manager.open_synapse_file(nrn_path, 1, pop_id)
            self._create_group_connections(src_target=projection.get("Source"))

    @mpi_no_errors
    def _create_group_connections(self, *, src_target=None, synapse_manager=None):
        """Creates connections according to loaded parameters in 'Connection'
           blocks of the BlueConfig in the currently active ConnectionSet
        """
        # Create all Projection connections if no Connection block uses
        # that source. Otherwise create only specified connections
        connection_blocks = compat.Map(self._config_parser.parsedConnects)
        conn_src_pop = self._synapse_manager.current_population.src_name
        is_base_pop = self._synapse_manager.current_population.src_id == 0
        matching_conns = [
            conn for conn in connection_blocks.values()
            if TargetSpec(conn.get("Source").s).match_filter(conn_src_pop, src_target, is_base_pop)
        ]

        synapse_manager = synapse_manager or self._synapse_manager
        if not matching_conns:
            logging.info("No matching Connection blocks. Loading all synapses...")
            synapse_manager.connect_all()
            return

        for conn_conf in matching_conns:
            conn_conf = compat.Map(conn_conf).as_dict(parse_strings=True)
            if "Delay" in conn_conf:
                # Delayed connections are for configuration only, not creation
                continue

            # check if we are not supposed to create (only configure later)
            if conn_conf.get("CreateMode") == "NoCreate":
                continue

            conn_src = conn_conf["Source"]
            conn_dst = conn_conf["Destination"]
            synapse_id = conn_conf.get("SynapseID")
            synapse_manager.connect_group(conn_src, conn_dst, synapse_id)

    # -
    def _configure_connections(self, conn_manager=None):
        """Configure-only circuit connections according to BlueConfig Connection blocks
        """
        conn_manager = conn_manager or self._synapse_manager

        for conn_conf in compat.Map(self._config_parser.parsedConnects).values():
            conn_conf = compat.Map(conn_conf).as_dict(parse_strings=True)

            conn_src = conn_conf["Source"]
            conn_dst = conn_conf["Destination"]
            is_delayed_connection = "Delay" in conn_conf

            log_msg = " * Pathway {:s} -> {:s}".format(conn_src, conn_dst)
            if is_delayed_connection:
                log_msg += ":\t[DELAYED] t={0[Delay]:g}, weight={0[Weight]:g}".format(conn_conf)
            if "SynapseConfigure" in conn_conf:
                log_msg += ":\tconfigure with '{:s}'".format(conn_conf["SynapseConfigure"])
            logging.info(log_msg)

            if is_delayed_connection:
                conn_manager.setup_delayed_connection(conn_conf)
            else:
                conn_manager.configure_group(conn_conf)

    # -
    @mpi_no_errors
    @timeit(name="Gap Junction creation")
    def create_gap_junctions(self):
        """Create gap_juntions among the cells, according to blocks in the config file,
        defined as projections with type GapJunction.
        """
        log_stage("Gap Junctions create")

        for name, projection in compat.Map(self._config_parser.parsedProjections).items():
            projection = compat.Map(projection).as_dict()
            if projection.get("Type") != "GapJunction":
                continue
            logging.info(" * %s", name)

            if self._gj_manager is not None:
                logging.warning("Neurodamus can only support loading one gap junction file. "
                                "Skipping loading additional files...")
                break

            self._gj_manager = GapJunctionManager(
                projection, self._target_manager, self._cell_distributor, self._target_spec.name)

        if self._gj_manager is None:
            logging.info("No Gap-junctions found")
            return

        self._gj_manager.connect_all(only_sgid_in_target=True)
        # Currently gap junctions are not configured. Future?
        # self._configure_connections(self._gj_manager)

    # -
    def _find_projection_file(self, proj_path):
        """Determine the full path to a projection.
        The "Path" might specify the filename. If not, it will attempt the old 'proj_nrn.h5'
        """
        return self._find_input_file(proj_path,
                                     ("ProjectionPath", "CircuitPath"),
                                     alt_filename="proj_nrn.h5")

    def _find_input_file(self, filepath, path_conf_entries=(), alt_filename=None):
        """Determine the full path of input files.

        Relative paths are built from Run configuration entries, and never pwd.
        In case filepath points to a file, alt_filename is disregarded

        Args:
            filepath: The relative or absolute path of the file to find
            path_conf_entries: (tuple) Run configuration entries to build the absolute path
            alt_filename: When the filepath is a directory, attempt finding a given filename
        Returns:
            The absolute path to the data file
        Raises:
            (ConfigurationError) If the file could not be found
        """
        path_conf_entries += ("CurrentDir", "BlueConfigDir")
        run_config = self._run_conf

        def try_find_in(fullpath):
            if ospath.isfile(fullpath):
                return fullpath
            if alt_filename is not None:
                alt_file_path = ospath.join(fullpath, alt_filename)
                if ospath.isfile(alt_file_path):
                    return alt_file_path
            return None

        if ospath.isabs(filepath):
            # if it's absolute path then can be used immediately
            file_found = try_find_in(filepath)
        else:
            file_found = None
            for path_key in path_conf_entries:
                if path_key in run_config:
                    file_found = try_find_in(ospath.join(run_config.get(path_key), filepath))
                    if file_found:
                        break

            # NOTE: Using PWD is DEPRECATED so this search should be removed in next version
            if not file_found:
                file_found = try_find_in(filepath)
                if file_found:
                    logging.warning("DEPRECATION: Input files shall NOT be relative to PWD."
                                    "Please use full paths or set CurrentDir manually.")

        if not file_found:
            raise ConfigurationError("Could not find file %s" % filepath)

        logging.debug("data file %s path: %s", filepath, file_found)
        return file_found

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
        conf = self._config_parser

        # Setup of Electrode objects part of enable stimulus
        self._enable_electrodes()

        # for each stimulus defined in the config file, request the stimmanager to instantiate
        extra_params = []
        if "BaseSeed" in self._run_conf:
            extra_params.append(self._run_conf["BaseSeed"])
        self._stim_manager = Nd.StimulusManager(
            self._target_manager, self._elec_manager, *extra_params)

        # build a dictionary of stims for faster lookup : useful when applying 10k+ stims
        # while we are at it, check if any stims are using extracellular
        has_extra_cellular = False
        stim_dict = {}
        for stim_name, stim in compat.Map(conf.parsedStimuli).items():
            if stim_name in stim_dict:
                raise ConfigurationError("Stimulus declared more than once: %s", stim_name)
            stim_dict[stim_name] = stim  # keep as hoc obj for stim_manager
            if stim.get("Mode").s == "Extracellular":
                has_extra_cellular = True

        # Treat extracellular stimuli
        if has_extra_cellular:
            self._stim_manager.interpretExtracellulars(conf.parsedInjects, conf.parsedStimuli)

        logging.info("Instantiating Stimulus Injects:")

        for name, inject in compat.Map(conf.parsedInjects).items():
            target_name = inject.get("Target").s
            stim_name = inject.get("Stimulus").s
            stim = stim_dict.get(stim_name)
            if stim is None:
                logging.error("Stimulus Inject %s uses non-existing Stim %s",
                              name, stim_name)

            stim_pattern = stim.get("Pattern").s
            if stim_pattern == "SynapseReplay":
                continue  # Handled by enable_replay

            logging.info(" * [STIM] %s: %s (%s) -> %s",
                         name, stim_name, stim_pattern, target_name)
            self._stim_manager.interpret(target_name, stim)

    # -
    def _enable_electrodes(self):
        if self._corenrn_conf:
            # Coreneuron doesnt support electrodes
            return False
        conf = self._config_parser
        electrodes_path_o = None

        if conf.parsedRun.exists("ElectrodesPath"):
            electrodes_path_o = conf.parsedRun.get("ElectrodesPath")
            logging.info("ElectrodeManager using electrodes from %s", electrodes_path_o.s)
        else:
            logging.info("No electrodes ospath. Extracellular class of stimuli will be unavailable")

        self._elec_manager = Nd.ElectrodeManager(electrodes_path_o, conf.parsedElectrodes)

    # -
    @mpi_no_errors
    def enable_replay(self):
        """Activate replay according to BlueConfig. Call before connManager.finalize
        """
        log_stage("Handling Replay")
        conf = self._config_parser

        if self._corenrn_conf and bool(self._core_replay_file):
            logging.info(" -> [REPLAY] Reusing stim file from previous cycle")
            return

        replay_dict = {}
        for stim_name, stim in compat.Map(conf.parsedStimuli).items():
            if stim.get("Pattern").s == "SynapseReplay":
                replay_dict[stim_name] = compat.Map(stim).as_dict(parse_strings=True)

        for name, inject in compat.Map(conf.parsedInjects).items():
            inject = compat.Map(inject).as_dict(parse_strings=True)
            target = inject["Target"]
            source = inject.get("Source")
            stim_name = inject["Stimulus"]
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
            self._enable_replay(source, target, stim, tshift, delay)

    # -
    def _enable_replay(self, source, target, stim_conf, tshift=.0, delay=.0):
        spike_filepath = self._find_input_file(stim_conf["SpikeFile"])
        spike_manager = SpikeManager(spike_filepath, tshift)  # Disposable

        # For CoreNeuron, we should put the replays into a single file to be used as PatternStim
        if self._corenrn_conf:
            # Initialize file if non-existing
            if not self._core_replay_file:
                self._core_replay_file = ospath.join(self._output_root, 'pattern.dat')
                if MPI.rank == 0:
                    log_verbose("Creating pattern.dat file for CoreNEURON")
                    spike_manager.dump_ascii(self._core_replay_file)
            else:
                if MPI.rank == 0:
                    log_verbose("Appending to pattern.dat")
                    with open(self._core_replay_file, "a") as f:
                        spike_manager.dump_ascii(f)
        else:
            # Otherwise just apply it to the current connections
            self._synapse_manager.replay(spike_manager, source, target, delay)

    # -
    @mpi_no_errors
    @timeit(name="Enable Modifications")
    def enable_modifications(self):
        """Iterate over any Modification blocks read from the BlueConfig and apply them to the
        network. The steps needed are more complex than NeuronConfigures, so the user should not be
        expected to write the hoc directly, but rather access a library of already available mods.
        """
        # mod_mananger gets destroyed when function returns (not required)
        mod_manager = Nd.ModificationManager(self._target_manager)
        log_stage("Enabling modifications...")
        for mod in compat.Map(self._config_parser.parsedModifications).values():
            mod_manager.interpret(mod)

    # -
    # @mpi_no_errors - not required since theres a call inside before _binreport_helper.make_comm
    @timeit(name="Enable Reports")
    def enable_reports(self):
        """Iterate over reports defined in BlueConfig and instantiate them.
        """
        log_stage("Reports Enabling")
        n_errors = 0
        sim_end = self._run_conf["Duration"]
        reports_conf = compat.Map(self._config_parser.parsedReports)
        self._report_list = []

        # Report count for coreneuron
        if self._corenrn_conf:
            self._corenrn_conf.write_report_count(self._config_parser.parsedReports.count())

        for rep_name, rep_conf in reports_conf.items():
            rep_conf = compat.Map(rep_conf).as_dict(parse_strings=True)
            rep_type = rep_conf["Type"]
            start_time = rep_conf["StartTime"]
            end_time = rep_conf.get("EndTime", sim_end)
            logging.info(" * %s (Type: %s, Target: %s)", rep_name, rep_type, rep_conf["Target"])

            if rep_type.lower() not in ("compartment", "summation", "synapse"):
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
                logging.warning("Report/Sim End-time (%s) before Start (%g). Skipping!",
                                end_time, start_time)
                continue

            electrode = self._elec_manager.getElectrode(rep_conf["Electrode"]) \
                if not self._corenrn_conf and "Electrode" in rep_conf else None

            rep_target = TargetSpec(rep_conf["Target"])
            population_name = (rep_target.population or self._target_spec.population
                               or self._default_population)
            log_verbose("Report on Population: %s, Target: %s", population_name, rep_target.name)

            rep_dt = rep_conf["Dt"]
            if rep_dt < Nd.dt:
                if MPI.rank == 0:
                    logging.error("Invalid report dt %f < %f simulation dt", rep_dt, Nd.dt)
                n_errors += 1
                continue

            rep_params = namedtuple("ReportConf", "name, type, report_on, unit, format, dt, "
                                    "start, end, output_dir, electrode, scaling, isc, \
                                     population_name")(
                rep_name,
                rep_type,  # rep type is case sensitive !!
                rep_conf["ReportOn"],
                rep_conf["Unit"],
                rep_conf["Format"],
                rep_dt,
                start_time,
                end_time,
                self._output_root,
                electrode,
                Nd.String(rep_conf["Scaling"]) if "Scaling" in rep_conf else None,
                rep_conf.get("ISC", ""),
                population_name
            )

            if self._corenrn_conf and MPI.rank == 0:
                # Init report config
                ptarget = self._target_parser.getTarget(rep_target.name)
                self._corenrn_conf.write_report_config(
                    rep_name, rep_target.name, rep_type, rep_params.report_on, rep_params.unit,
                    rep_params.format, ptarget.isCellTarget(), rep_params.dt, rep_params.start,
                    rep_params.end, ptarget.completegids(), self._corenrn_buff_size,
                    population_name)

            if not self._target_manager:
                # When restoring with coreneuron we dont even need to initialize reports
                continue

            report = Nd.Report(*rep_params)

            # Go through the target members, one cell at a time. We give a cell reference
            # For summation targets - check if we were given a Cell target because we really want
            # all points of the cell which will ultimately be collapsed to a single value
            # on the soma. Otherwise, get target points as normal.
            target = self._target_manager.getTarget(rep_target.name)
            points = self.get_target_points(target, rep_type.lower() == "summation")

            for point in points:
                gid = point.gid
                cell = self._cell_distributor.getCell(gid)
                spgid = self._cell_distributor.getSpGid(gid)

                # may need to take different actions based on report type
                if rep_type.lower() == "compartment":
                    report.addCompartmentReport(cell, point, spgid, bool(self._corenrn_conf))
                elif rep_type.lower() == "summation":
                    report.addSummationReport(
                        cell, point, target.isCellTarget(), spgid, bool(self._corenrn_conf))
                elif rep_type.lower() == "synapse":
                    report.addSynapseReport(cell, point, spgid, bool(self._corenrn_conf))

            # keep report object? Who has the ascii/hdf5 object? (1 per cell)
            # the bin object? (1 per report)
            self._report_list.append(report)

        if n_errors > 0:
            raise ConfigurationError("%d reporting errors detected. Terminating" % (n_errors,))

        MPI.check_no_errors()

        if self._corenrn_conf:
            self._corenrn_conf.write_spike_population(self._target_spec.population or
                                                      self._default_population)

        if not self._corenrn_conf:
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
        for config in compat.Map(self._config_parser.parsedConfigures).values():
            target_name = config.get("Target").s
            configure_str = config.get("Configure").s
            log_verbose("Apply configuration \"%s\" on target %s",
                        config.get("Configure").s, target_name)

            points = self.get_target_points(target_name)
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
            return self._pnm

        if self._cell_distributor is None or self._cell_distributor._gidvec is None:
            raise RuntimeError("No CellDistributor was initialized. Please create a circuit.")

        self._finalize_model(**sim_opts)

        if corenrn_gen is None:
            corenrn_gen = SimConfig.use_coreneuron
        if corenrn_gen:
            self._sim_corenrn_write_config()

        if SimConfig.use_neuron:
            self._sim_init_neuron()

        self.dump_cell_config()

        self._sim_ready = True
        return self._pnm

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
        pc = self._pnm.pc
        pc.setup_transfer()

        if spike_compress and not is_save_state:
            # multisend 13 is combination of multisend(1) + two_phase(8) + two_intervals(4)
            # to activate set spike_compress=(0, 0, 13)
            if not isinstance(spike_compress, tuple):
                spike_compress = (spike_compress, 1, 0)
            pc.spike_compress(*spike_compress)

        # LFP calculation requires WholeCell balancing and extracellular mechanism.
        # This is incompatible with efficient caching atm.
        Nd.cvode.cache_efficient("ElectrodesPath" not in self._run_conf)
        pc.set_maxstep(4)
        with timeit(name="stdinit"):
            Nd.stdinit()

    # -
    def _record_spikes(self, gids=None):
        """Setup recording of spike events (crossing of threshold) for cells on this node
        """
        for gid in (self.gidvec if gids is None else gids):
            # only want to collect spikes of cell pieces with the soma (i.e. the real gid)
            if self._cell_distributor.getSpGid(gid) == gid:
                logging.debug("Collecting spikes for gid %d", gid)
                self._pnm.spike_record(gid)

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

        self._record_spikes()
        self._pnm.pc.timeout(200)  # increase by 10x

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
        self._synapse_manager.restart_events()

        logging.info("Restarting Reports events")
        nc = Nd.NetCon(None, self._binreport_helper, 10, 1, 1)
        nc.event(Nd.t)
        self._jumpstarters.append(nc)

        # TODO: ASCII and HDF5 reports
        # TODO: reports might have ALU objects which need to reactivate

    # -
    @timeit(name="corewrite")
    def _sim_corenrn_write_config(self, corenrn_restore=False):
        log_stage("Dataset generation for CoreNEURON")

        corenrn_output = SimConfig.coreneuron_ouputdir
        corenrn_data = SimConfig.coreneuron_datadir
        fwd_skip = self._run_conf.get("ForwardSkip", 0) if not corenrn_restore else 0

        if not corenrn_restore:
            Nd.registerMapping(self._cell_distributor)
            local_gids = self._cell_distributor.local_gids
            if len(local_gids) == 0 and self._bbcore_fakegid_offset is not None:
                # load the ARTIFICIAL_CELL CoreConfig with a fake_gid in this empty rank
                # to avoid errors during coreneuron model building
                fake_gid = self._bbcore_fakegid_offset + self._pnm.pc.id()
                self._cell_distributor.load_artificial_cell(int(fake_gid), SimConfig.core_config)
                # Nd.registerMapping doesn't work for this artificial cell as somatic attr is
                # missing, so create a dummy mapping file manually, required for reporting
                mapping_file = ospath.join(corenrn_data, "%d" % fake_gid + "_3.dat")
                if not ospath.isfile(mapping_file):
                    with open(mapping_file, "w") as dummyfile:
                        dummyfile.write("1.2\n0\n")
            self._pnm.pc.nrnbbcore_write(corenrn_data)
            if self._bbcore_fakegid_offset is not None:
                self._bbcore_fakegid_offset += MPI.size

        if "BaseSeed" in self._run_conf:
            self._corenrn_conf.write_sim_config(
                corenrn_output, corenrn_data, Nd.tstop, Nd.dt, fwd_skip,
                self._pr_cell_gid or -1, self._core_replay_file, self._run_conf.get("BaseSeed")
            )
        else:
            self._corenrn_conf.write_sim_config(
                corenrn_output, corenrn_data, Nd.tstop, Nd.dt, fwd_skip,
                self._pr_cell_gid or -1, self._core_replay_file
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
        if self._corenrn_conf:
            self.clear_model()
            self._run_coreneuron()
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
        self._corenrn_conf.psolve_core(*opts_expanded)

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

    # psolve_loop: There was an issue where MPI collective routines for reporting and spike exchange
    # are mixed such that some cpus are blocked waiting to complete reporting while others to
    # finish spike exchange. As a work-around, periodically halt simulation and flush reports
    # Default is 25 ms / cycle
    def _psolve_loop(self, tstop):
        cur_t = Nd.t
        buffer_t = SimConfig.buffer_time
        for _ in range(math.ceil((tstop - cur_t) / buffer_t)):
            next_flush = min(tstop, cur_t + buffer_t)
            self._pnm.psolve(next_flush)
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
        if not self._target_parser:
            # Target parser is the ground block. If not there model is clear
            return

        logging.info("Clearing model")
        pnm = self._pnm
        pnm.pc.gid_clear()
        pnm.nclist.remove_all()
        pnm.cells.remove_all()

        if self._cell_distributor:
            self._cell_distributor.clear_cells()

        if not avoid_creating_objs:
            bbss = Nd.BBSaveState()
            bbss.ignore()
            if self._binreport_helper:
                self._binreport_helper.clear()
            if self._sonatareport_helper:
                self._sonatareport_helper.clear()

        Node.__init__(self, None, None)  # Reset vars

    # -------------------------------------------------------------------------
    #  Data retrieve / output
    # -------------------------------------------------------------------------

    @property
    def gidvec(self):
        if self._cell_distributor is None or self._cell_distributor._gidvec is None:
            logging.error("No CellDistributor was initialized. Please create a circuit.")
        return self._cell_distributor.local_gids

    # -
    def get_target_points(self, target, cell_use_compartment_cast=True):
        """Helper to retrieve the points of a target.
        If target is a cell then uses compartmentCast to obtain its points.
        Otherwise returns the result of calling getPointList directly on the target.

        Args:
            target: The target name or object (faster)
            cell_use_compartment_cast: if enabled (default) will use target_manager.compartmentCast
                to get the point list.

        Returns: The target list of points
        """
        if isinstance(target, str):
            target = self._target_manager.getTarget(target)
        if target.isCellTarget() and cell_use_compartment_cast:
            return self._target_manager.compartmentCast(target, "") \
                .getPointList(self._cell_distributor)
        return target.getPointList(self._cell_distributor)

    def get_targetcell_count(self):
        """Count the total number of the target cells, and get the max gid
           if CircuitTarget is not specified in the configuration, use Mosaic target
        """
        target = self._target_spec
        if target.name:
            target_cells = self._target_parser.getTarget(target.name).getCellCount()
            all_gids = self._target_parser.getTarget(target.name).completegids()
            logging.info("CIRCUIT: Population: %s, Target: %s (%d Cells)",
                         target.population or "(default)", target.name, target_cells)
        else:
            target_cells = self._target_parser.getTarget("Mosaic").getCellCount()
            all_gids = self._target_parser.getTarget("Mosaic").completegids()
            logging.warning("No Target defined. Loading ALL cells: %d", target_cells)
        return target_cells, max(all_gids) if all_gids else 0

    # -
    @mpi_no_errors
    def spike2file(self, outfile):
        """ Write the spike events that occured on each node into a single output file.
        Nodes will write in order, one after the other.
        """
        logging.info("Writing spikes to %s", outfile)
        outfile = ospath.join(self._output_root, outfile)
        pnm = self._pnm

        # root node opens file for writing, all others append
        if MPI.rank == 0:
            with open(outfile, "w") as f:
                f.write("/scatter\n")
                for i, gid in enumerate(pnm.idvec):
                    f.write("%.3f\t%d\n" % (pnm.spikevec.x[i], gid))

        # Write other nodes' result in order
        for nodeIndex in range(1, MPI.size):
            MPI.barrier()
            if MPI.rank == nodeIndex:
                with open(outfile, "a") as f:
                    for i, gid in enumerate(pnm.idvec):
                        f.write("%.3f\t%d\n" % (pnm.spikevec.x[i], gid))

        # Write spikes in SONATA format
        if self._target_spec.population:
            self._sonatareport_helper.write_spikes(pnm.spikevec, pnm.idvec, self._output_root,
                                                   self._target_spec.population)
        else:
            self._sonatareport_helper.write_spikes(pnm.spikevec, pnm.idvec, self._output_root)

    def dump_cell_config(self):
        if not self._pr_cell_gid:
            return
        log_verbose("Dumping info about cell %d", self._pr_cell_gid)
        simulator = "CoreNeuron" if self._corenrn_conf else "Neuron"
        self._pnm.pc.prcellstate(self._pr_cell_gid, "py_{}_t{}".format(simulator, Nd.t))

    # -
    def dump_circuit_config(self, suffix="nrn_python"):
        log_stage("Dumping cells state")
        suffix += "_t=" + str(Nd.t)

        if not ospath.isfile("debug_gids.txt"):
            logging.info("Debugging all gids")
            gids = self.gidvec
        else:
            gids = []
            for line in open("debug_gids.txt"):
                line = line.strip()
                if not line: continue
                gid = int(line)
                if gid in self.gidvec:
                    gids.append(gid)
            if len(gids):
                log_all(logging.INFO, "Rank %d: Debugging %d gids from debug_gids.txt",
                        MPI.rank, len(gids))

        for gid in gids:
            self._pnm.pc.prcellstate(gid, suffix)

    # ---------------------------------------------------------------------------
    # Note: This method may be called automatically from Neurodamus.__del__
    #     and therefore it must stay as simple as possible as exceptions are ignored
    def cleanup(self):
        """Have the compute nodes wrap up tasks before exiting.
        """
        # MemUsage constructor will do MPI communications
        Nd.MemUsage().print_mem_usage()

        # Coreneuron runs clear the model before starting
        if not self._corenrn_conf or self._options.simulate_model is False:
            self.clear_model(avoid_creating_objs=True)

        if SimConfig.delete_corenrn_data:
            with timeit_rank0(name="Delete corenrn data"):
                data_folder = ospath.join(self._output_root, "coreneuron_input")
                logging.info("Deleting intermediate data in %s", data_folder)
                if MPI.rank == 0:
                    if ospath.islink(data_folder):
                        # in restore, coreneuron data is a symbolic link
                        os.unlink(data_folder)
                    else:
                        subprocess.call(['/bin/rm', '-rf', data_folder])
                    os.remove(ospath.join(self._output_root, "sim.conf"))
                    os.remove(ospath.join(self._output_root, "report.conf"))
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

        logging.info("Running Neurodamus with config from " + config_file)

        if self._corenrn_conf and "Restore" in self._run_conf:
            self._coreneuron_restore()
        elif self._options.build_model:
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
        self.create_gap_junctions()

        log_stage("================ INSTANTIATING SIMULATION ================")

        if not self._corenrn_conf:
            self.check_resume()  # For CoreNeuron there _coreneuron_restore

        # Apply replay
        self.enable_replay()

        if self._run_conf["AutoInit"]:
            self.init()

    # -
    def init(self):
        """Explicitly initialize, allowing users to make last changes before simulation
        """
        base_seed = self._run_conf.get("BaseSeed", 0)  # base seed for synapse RNG

        log_stage("Creating connections in the simulator")
        self._synapse_manager.finalize(base_seed, self._corenrn_conf)

        if self._gj_manager is not None:
            self._gj_manager.finalize()

        for name, circuit in self._extra_circuits.items():
            log_stage("Init connections for Extra Circuit %s", name)
            engine = circuit.Engine
            if engine not in (None, NotImplemented):
                engine.finalize_synapses()

        self.enable_stimulus()
        self.enable_modifications()

        if ospath.isfile("debug_gids.txt"):
            Nd.stdinit()
            self.dump_circuit_config()

        if self._run_conf["EnableReports"]:
            self.enable_reports()

        self.sim_init()

    # -
    def _merge_filesdat(self, ncycles, output_root):
        log_stage("Generating merged CoreNeuron files.dat")

        cn_entries = []
        for i in range(ncycles):
            log_verbose("files_{}.dat".format(i))
            filename = ospath.join(output_root, "coreneuron_input/files_{}.dat".format(i))
            with open(filename) as fd:
                first_line = fd.readline()
                nlines = int(fd.readline())
                for lineNumber in range(nlines):
                    line = fd.readline()
                    cn_entries.append(line)

        cnfilename = ospath.join(output_root, "coreneuron_input/files.dat")
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
        target_cells, max_gid = self.get_targetcell_count()

        # Check if user wants to build the model in several steps (only for CoreNeuron)
        sub_targets = self.multicycle_data_generation()
        n_cycles = len(sub_targets) if sub_targets else 1

        if SimConfig.use_coreneuron and target_cells/n_cycles < MPI.size and target_cells > 0:
            # coreneuron with no. ranks >> no. cells
            # need to assign fake gids to artificial cells in empty threads during module building
            # fake gids start from max_gid + 1
            # currently not support engine plugin where target is loaded later
            self._bbcore_fakegid_offset = max_gid + 1

        # Without multi-cycle, it's a trivial model build
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
            self._run_conf["CircuitTarget"] = str(tmp_target_spec)  # FQN
            self._build_model()

            # Move generated files aside (to be merged later)
            if MPI.rank == 0:
                base_filesdat = ospath.join(self._output_root, 'coreneuron_input/files')
                os.rename(base_filesdat + '.dat', base_filesdat + "_{}.dat".format(cycle_i))
            # Archive timers for this cycle
            TimerManager.archive(archive_name="Cycle Run {:d}".format(cycle_i + 1))
        if MPI.rank == 0:
            self._merge_filesdat(n_cycles, self._output_root)

    # -
    @timeit(name="finished Run")
    def run(self):
        """Prepares and launches the simulation according to the loaded config.
        If '--only-build-model' option is set, simulation is skipped.
        """
        if not self._options.simulate_model:
            self.sim_init()
            log_stage("============= SIMULATION (MODEL BUILD ONLY) =============")
        elif not self._options.build_model:
            log_stage("============= SIMULATION (SKIP MODEL BUILD) =============")
            self._run_coreneuron()
        else:
            log_stage("======================= SIMULATION =======================")
            self.run_all()

    def __del__(self):
        if self._init_ok:
            self.cleanup()
