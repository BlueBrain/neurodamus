# Neurodamus
# Copyright 2018 - Blue Brain Project, EPFL

from __future__ import absolute_import
import functools
import itertools
import logging
import math
import operator
import os
from os import path as ospath
from collections import namedtuple

from .core import MPI, mpi_no_errors, return_neuron_timings
from .core import NeurodamusCore as Nd
from .core.configuration import GlobalConfig, ConfigurationError
from .cell_distributor import CellDistributor, LoadBalanceMode
from .connection_manager import SynapseRuleManager, GapJunctionManager
from .replay import SpikeManager
from .utils import compat
from .utils.logging import log_stage, log_verbose


class Node:
    """The Node class is the main entity for a distributed neurodamus execution.

    It internally instantiates parallel structures and distributes the cells among all the nodes.
    It is relatively low-level, for a standard run consider using the Neurodamus class instead.
    """

    def __init__(self, recipe):
        """ Creates a neurodamus executor.

        Args:
            recipe: The BlueRecipe file
        """
        Nd.init()

        if recipe is not None:
            # Read configuration
            self._pnm = Nd.ParallelNetManager(0)
            self._config_parser = self._open_config(recipe)
            self._blueconfig_path = ospath.dirname(recipe)
            self._simulator_conf = Nd.simConfig
            self._run_conf = compat.Map(self._config_parser.parsedRun).as_dict(True)  # type: dict
            self._output_root = self._run_conf["OutputRoot"]
            self._pr_cell_gid = self._run_conf.get("prCellGid")
            self._corenrn_conf = Nd.CoreConfig(self._output_root) \
                if self._simulator_conf.coreNeuronUsed() else None

            # BinReportHelper required for Save-Restore
            self._binreport_helper = Nd.BinReportHelper(Nd.dt, not self._corenrn_conf)
            self._buffer_time = 25 * self._run_conf.get("FlushBufferScalar", 1)
            self._core_replay_file = ''
            self._target_parser = None

        self._target_manager = None
        self._stim_list = None
        self._report_list = None
        self._stim_manager = None
        self._elec_manager = None
        self._sim_ready = False

        self._cell_distributor = None  # type: CellDistributor
        self._synapse_manager = None   # type: SynapseRuleManager
        self._gj_manager = None        # type: GapJunctionManager
        self._connection_weight_delay_list = []

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
    def __getattr__(self, item):
        # parts = item.split("_")
        # new_name = "".join(["_" + parts[0]] + [p.capitalize() for p in parts[1:]])
        logging.warning("Accessing {} via compat API".format(item))
        new_name = "".join(["_" + c.lower() if c.isupper() else c for c in item])
        return self.__getattribute__(new_name)

    # Compat
    cellDistributor = CellDistributor

    # -
    @staticmethod
    def _open_config(recipe):
        """This function will run the parser and make the data accessible.

        Args:
            recipe: Name of Config file to load
        """
        config_parser = Nd.ConfigParser()
        config_parser.open(recipe)
        if MPI.rank == 0:
            config_parser.toggleVerbose()

        # set some basic information
        if config_parser.parsedRun is None:
            raise ConfigurationError("No Run block parsed from BlueConfig %s", recipe)
        parsed_run = config_parser.parsedRun

        # confirm output_path exists and is usable -> use utility.mod
        output_path = parsed_run.get("OutputRoot").s
        if MPI.rank == 0:
            if Nd.checkDirectory(output_path) < 0:
                logging.error("Error with OutputRoot %s. Terminating", output_path)
                raise ConfigurationError("Output directory error")
        MPI.check_no_errors()

        Nd.execute("cvode = new CVode()")
        Nd.execute("celsius=34")

        Nd.simConfig.interpret(parsed_run)

        # Make sure Random Numbers are prepped
        rng_info = Nd.RNGSettings()
        rng_info.interpret(parsed_run)  # this sets a few global vars in hoc

        h = Nd.h
        h.tstop = parsed_run.valueOf("Duration")
        h.dt = parsed_run.valueOf("Dt")
        h.steps_per_ms = 1.0 / h.dt
        return config_parser

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
        if "ModelBuildingSteps" in run_conf:
            ncycles = int(run_conf["ModelBuildingSteps"])
        elif "ProspectiveHosts" in run_conf:  # compat syntax
            nphosts = run_conf["ProspectiveHosts"]
            ncycles  = int(nphosts // MPI.size) + (1 if nphosts % MPI.size > 0 else 0)
            # Prospective hosts at some point changed the semantics, as there are parts
            # in the code that show it was used to do load balance for a different CPU count
            # For now we mimick what neurodamus hoc does, but in the future the option
            # shall either be removed or reverted back to the original purpose
            # This hoc behavior requires resetting "ProspectiveHosts"
            self._run_conf["ProspectiveHosts"] = MPI.size
        else:
            return False

        logging.info("Splitting Target for multi-iteration CoreNeuron data generation")
        assert ncycles > 0, "splitdata_generation yielded 0 cycles. Please check ModelBuildingSteps"

        if not self._corenrn_conf:
            logging.warning("Splitdata DISABLED since simulator is not CoreNeuron")
            return False

        if "CircuitTarget" not in run_conf:
            raise ConfigurationError(
                "Multi-iteration coreneuron data generation requires CircuitTarget")

        target_name = run_conf["CircuitTarget"]
        target = self._target_parser.getTarget(target_name)
        allgids = target.completegids()
        new_targets = []

        for cycle_i in range(ncycles):
            target = Nd.Target()
            target.name = "{}_{}".format(target_name, cycle_i)
            new_targets.append(target)
            self._target_parser.updateTargetList(target)

        target_looper = itertools.cycle(new_targets)
        for gid in allgids.x:
            target = next(target_looper)
            target.gidMembers.append(gid)

        return new_targets

    # -
    @mpi_no_errors
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

        start_target_file = ospath.join(run_conf["CircuitPath"], "start.target")
        if not ospath.isfile(start_target_file):
            logging.warning("DEPRECATION: start.target shall be within CircuitPath. "
                            "Within nrnPath is deprecated and will be removed")
            start_target_file = ospath.join(run_conf["nrnPath"], "start.target")  # fallback

        if not ospath.isfile(start_target_file):
            raise ConfigurationError("start.target not found! Check circuit.")

        self._target_parser.open(start_target_file)

        if "TargetFile" in run_conf:
            user_target = self._find_config_file(run_conf["TargetFile"])
            self._target_parser.open(user_target)

        if MPI.rank == 0:
            self._target_parser.printCellCounts()

    # -
    @mpi_no_errors
    def compute_load_balance(self):
        """This function has the simulator instantiate the circuit (cells & synapses) to determine
        the best way to split cells and balance those pieces across the available cpus.
        """
        log_stage("Computing Load Balance")
        lb_mode = LoadBalanceMode.parse(self._run_conf.get("RunMode"))

        if lb_mode is LoadBalanceMode.MultiSplit:
            if not self._corenrn_conf:
                logging.info("Load Balancing ENABLED. Mode: MultiSplit")
            else:
                if MPI.rank == 0:
                    logging.warning("Load Balancing mode CHANGED to WholeCell for CoreNeuron")
                lb_mode = LoadBalanceMode.WholeCell
        elif lb_mode is LoadBalanceMode.WholeCell:
            logging.info("Load Balancing ENABLED. Mode: WholeCell")
        else:
            logging.info("Load Balancing DISABLED. Will use Round-Robin distribution")
            self._cell_distributor = CellDistributor(self._pnm)
            return

        # Build cell distributor according to BlueConfig
        prosp_hosts = self._run_conf.get("ProspectiveHosts")
        self._cell_distributor = CellDistributor(self._pnm, lb_mode, prosp_hosts)

        # A callback to build a basic circuit for evaluating complexity
        def build_bare_circuit_f():
            log_stage("Instantiating circuit Round-Robin for load balancing")
            self.create_cells(False)
            self.create_synapses()
            self.create_gap_junctions()

        cx_valid = self._cell_distributor.load_or_recompute_mcomplex_balance(
            self._run_conf["nrnPath"], self._run_conf.get("CircuitTarget"), build_bare_circuit_f)

        # Ready to run with LoadBal. But check if we are launching on a good sized partition
        required_cpus = self._cell_distributor.target_cpu_count
        if required_cpus != MPI.size:
            logging.warning("Load Balance computed for %d CPUs (as per ProspectiveHosts). "
                            "To continue execution launch on a partition of that size",
                            required_cpus)
            Nd.quit()

        # If there were no cx_files ready and distribution happened, we need to start over
        if not cx_valid:
            Nd.t = .0  # Reset time
            self.clear_model()
            self._cell_distributor = CellDistributor(self._pnm, lb_mode)

    # -
    @mpi_no_errors
    def create_cells(self, load_bal=True):
        """Instantiate and distributes the cells of the network.
        Any targets will be updated to know which cells are local to the cpu.
        """
        if self._cell_distributor is None:
            logging.warning("Load balancer object not present. Continuing with Round-Robin")
            self._cell_distributor = CellDistributor(self._pnm)

        self._cell_distributor.load_cells(self._run_conf, self._target_parser, load_bal)

        # localize targets, give to target manager
        self._target_parser.updateTargets(self.gidvec)

        # give a TargetManager the TargetParser's completed targetList
        self._target_manager = Nd.TargetManager(
            self._target_parser.targetList, self._cell_distributor)

        # Let the CellDistributor object have any final say in the cell objects
        self._cell_distributor.finalize(self.gidvec)

    # -
    @mpi_no_errors
    def create_synapses(self):
        """Create synapses among the cells, handling connections that appear in the config file
        """
        # quick check - if we have a single connect block and it sets a weight of zero, can skip
        # synapse creation in its entirety.  This is useful for when no nrn.h5 exists, so we don't
        # error trying to init hdf5 reader. This may not be the cleanest solution.
        log_stage("Synapses Create")
        if self._config_parser.parsedConnects.count() == 1:
            if self._config_parser.parsedConnects.o(0).valueOf("Weight") == 0:
                return

        nrn_path = self._run_conf["nrnPath"]
        synapse_mode = self._run_conf.get("SynapseMode")
        n_synapse_files = 1

        if ospath.isdir(nrn_path):
            # legacy nrnreader may require manual NumSynapseFiles
            # But with a wrapper nrn.h5 dont change from 1
            if not ospath.isfile(ospath.join(nrn_path, "nrn.h5")):
                n_synapse_files = self._run_conf.get("NumSynapseFiles", 1)

        # Pass on to Managers the given path
        self._synapse_manager = SynapseRuleManager(
            nrn_path, self._target_manager, self._cell_distributor, n_synapse_files, synapse_mode)

        if self._config_parser.parsedConnects.count() == 0:
            self._synapse_manager.connect_all(self.gidvec)
        else:
            # Do a quick scan for any ConnectionBlocks with 'Delay' keyword and put a reference on
            # a separate list to be adjusted until later. Note that this requires that another
            # connection block without a delay will connect the cells.
            for conn in compat.Map(self._config_parser.parsedConnects).values():
                if conn.exists("Delay"):
                    self._connection_weight_delay_list.append(conn)

            # Now handle the connection blocks as normal
            self._interpret_connections()

        # Check for additional synapse files.  Now requires a connection block.
        # Continue support for compatibility, but new BlueConfigs should use Projection blocks
        bonus_file = self._run_conf.get("BonusSynapseFile")
        if bonus_file:
            logging.info("Handle Bonus synapse file")
            bonus_n_synapse_files = int(self._run_conf.get("NumBonusFiles", 1))
            self._synapse_manager.open_synapse_file(bonus_file, bonus_n_synapse_files)

            if self._config_parser.parsedConnects.count() == 0:
                self._synapse_manager.connect_all(self.gidvec)
            else:
                self._interpret_connections(extend_info=False)

        # Check for Projection blocks
        if self._config_parser.parsedProjections.count() > 0:
            logging.info("Handling projections...")

            for pname, projection in compat.Map(self._config_parser.parsedProjections).items():
                logging.info(" * %s", pname)
                projection = compat.Map(projection).as_dict(True)
                n_synapse_files = projection.get("NumSynapseFiles", 1)

                # Skip projection blocks for gap junctions
                if projection.get("Type") == "GapJunction":
                    continue

                nrn_path = self._find_projection_file(projection["Path"])
                self._synapse_manager.open_synapse_file(nrn_path, n_synapse_files)

                # Temporarily patch for population IDs in BlueConfig
                if "PopulationID" in projection:
                    self._synapse_manager.select_populations(int(projection["PopulationID"]), 0)

                # Go ahead and make all the Projection connections
                self._synapse_manager.connect_all(self.gidvec)
                self._interpret_connections(extend_info=False)

        # Check if we need to override the base seed for synapse RNGs
        base_seed = self._run_conf.get("BaseSeed", 0)

        self._synapse_manager.finalize(base_seed)

    # -
    def _interpret_connections(self, extend_info=True):
        """Aux method for creating/updating connections

        Args:
            extend_info (bool): Output (log) pathsways being processed
        """
        _logmsg = "Creating connections from BlueConfig..."
        if extend_info: logging.info(_logmsg)
        else: log_verbose(_logmsg)

        for conn_conf in compat.Map(self._config_parser.parsedConnects).values():
            conn_conf = compat.Map(conn_conf).as_dict(parse_strings=True)
            if "Delay" in conn_conf:
                # Connection blocks using a 'Delay' option are handled later
                continue

            conn_src = conn_conf["Source"]
            conn_dst = conn_conf["Destination"]
            if extend_info:
                logging.info(" * Pathway %s -> %s ", conn_src, conn_dst)

            # check if we are supposed to disable creation
            # -> i.e. only change weights for existing connections
            dont_create = conn_conf.get("CreateMode") == "NoCreate"
            stdp_mode = conn_conf.get("UseSTDP", "STDPoff")
            mini_spont_rate = conn_conf.get("SpontMinis")
            weight = conn_conf.get("Weight")  # optional, None indicates no change
            # allows a helper object to grab any additional configuration values
            syn_override = conn_conf if "ModOverride" in conn_conf else None
            syn_config = conn_conf.get("SynapseConfigure")
            syn_t = conn_conf.get("SynapseID")

            # finally we have all the options checked and can now invoke the SynapseRuleManager
            self._synapse_manager.group_connect(
                conn_src, conn_dst, self.gidvec, weight, syn_config, stdp_mode,
                mini_spont_rate, syn_t, syn_override, creation_mode=not dont_create)

    # -
    @mpi_no_errors
    def create_gap_junctions(self):
        """Create gap_juntions among the cells, according to blocks in the config file,
        defined as projections with type GapJunction.
        """
        log_stage("Gap Junctions create")
        target_name = self._run_conf.get("CircuitTarget")
        if target_name is None:
            raise ConfigurationError("No circuit target. Required when using GapJunctions")

        target = self._target_manager.getTarget(target_name)

        for name, projection in compat.Map(self._config_parser.parsedProjections).items():
            # check if this Projection block is for gap junctions
            if projection.exists("Type") and projection.get("Type").s == "GapJunction":
                nrn_path = projection.get("Path").s
                logging.info(" * %s", name)

                if self._gj_manager is not None:
                    logging.warning("Neurodamus can only support loading one gap junction file. "
                                    "Skipping loading additional files...")
                    break

                self._gj_manager = GapJunctionManager(
                    nrn_path, self._target_manager, self._cell_distributor, 1, target)

        if self._gj_manager is not None:
            self._gj_manager.connect_all(self.gidvec, 1)
            self._gj_manager.finalizeGapJunctions()
        else:
            logging.info("No Gap-junctions found")

    # -
    def _find_projection_file(self, proj_path):
        """Determine the full path to a projection.
        The "Path" might specify the filename. If not, it will attempt the old 'proj_nrn.h5'
        """
        return self._find_input_file("proj_nrn.h5", proj_path, ("ProjectionPath",))

    def _find_input_file(self, filename, filepath, path_conf_entries=()):
        """Determine where to find the synapse files.
        Try relative path first, then check for config fields in Run, last use CircuitPath.
        In case filepath already points to a file, filename is disregarded
        Otherwise filename(s) are attempted (can be a tuple)

        Args:
            filename: (str,tuple) The name(s) of the file to find
            filepath: The relative or absolute path we obtained in the direct config
            path_conf_entries: (tuple) Global path configuration entries to build the absolute path
        Returns:
            The absolute path to the data file
        Raises:
            (ConfigurationError) If the file could not be found
        """
        if not isinstance(filename, tuple):
            filename = (filename,)
        path_conf_entries += ("CircuitPath",)
        run_config = self._config_parser.parsedRun

        def try_find_in(fullpath):
            if ospath.isfile(fullpath):
                return fullpath
            for fname in filename:
                nrn_path = ospath.join(fullpath, fname)
                if ospath.isfile(nrn_path):
                    return nrn_path
            return None

        if ospath.isabs(filepath):
            # if it's absolute path then can be used immediately
            file_found = try_find_in(filepath)
        else:
            file_found = None
            for path_key in path_conf_entries:
                if run_config.exists(path_key):
                    file_found = try_find_in(ospath.join(run_config.get(path_key).s, filepath))
                    if file_found:
                        break

        if not file_found:
            raise ConfigurationError("Could not find file %s", filename)

        logging.debug("data file %s path: %s", filename, file_found)
        return file_found

    def _find_config_file(self, filepath):
        """Attempts to find simulation config files (e.g. user.target or replays)
           If not an absolute path, searches in blueconfig folder
        """
        if not ospath.isabs(filepath):
            _path = ospath.join(self._blueconfig_path, filepath)
            if ospath.isfile(_path):
                filepath = _path
        if not ospath.isfile(filepath):
            raise ConfigurationError("Config file not found: " + filepath)
        return filepath

    # -
    @mpi_no_errors
    def enable_stimulus(self, only_replay=False):
        """Iterate over any stimuli/stim injects defined in the config file given to the simulation
        and instantiate them.
        This iterates over the injects, getting the stim/target combinations
        and passes the raw text in field/value pairs to a StimulusManager object to interpret the
        text and instantiate an actual stimulus object.

        Args:
            only_replay: if True, dont enable other classes of stimulus -> No ElectrodeManager and
                no StimulusManager. Only spike replays are applied. Useful for coreneuron restore.
        """
        log_stage("Stimulus apply. [only replay: %s]", only_replay)
        conf = self._config_parser

        if not only_replay:
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
            stim_dict.setdefault(stim_name, stim)
            if stim.get("Mode").s == "Extracellular":
                has_extra_cellular = True

        # Treat extracellular stimuli
        if not only_replay and has_extra_cellular:
            self._stim_manager.interpretExtracellulars(conf.parsedInjects, conf.parsedStimuli)

        logging.info("Instantiating Stimulus Injects:")
        replay_count = 0
        for name, inject in compat.Map(conf.parsedInjects).items():
            target_name = inject.get("Target").s
            stim_name = inject.get("Stimulus").s
            stim = stim_dict.get(stim_name)
            stim_map = compat.Map(stim).as_dict(True)

            # check the pattern for special cases that are handled here.
            if stim_map["Pattern"] == "SynapseReplay":
                replay_count = replay_count + 1
                # Since saveUpdate merge there are two delay concepts:
                #  - shift: times are shifted (previous delay)
                #  - delay: Spike replays are suppressed until a certain time
                tshift = 0 if stim_map.get("Timing") == "Absolute" else Nd.t
                delay = stim_map.get("Delay", .0)
                logging.info(" * [SYN REPLAY] %s (%s -> %s, time shift: %d, delay: %d)",
                             name, stim_name, target_name, tshift, delay)
                self._enable_replay(target_name, stim_map, replay_count, tshift, delay)

            elif not only_replay:
                # all other patterns the stim manager will interpret
                logging.info(" * [STIM] %s: %s (%s) -> %s",
                             name, stim_name, stim_map["Pattern"], target_name)
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
    def _enable_replay(self, target_name, stim_conf, replay_count, tshift=.0, delay=.0):
        spike_filepath = self._find_config_file(stim_conf["SpikeFile"])
        spike_manager = SpikeManager(spike_filepath, tshift)  # Disposable

        # For CoreNeuron, we should put the replays into a single file to be used as PatternStim
        if self._corenrn_conf:
            # Initialize file if non-existing
            if replay_count == 1 or not self._core_replay_file:
                self._core_replay_file = ospath.join(self._output_root, 'pattern.dat')
                if MPI.rank == 0:
                    log_verbose("Creating pattern.dat file for CoreNEURON")
                    spike_manager.dump_ascii(self._core_replay_file)
            elif replay_count > 1 and self._core_replay_file:
                if MPI.rank == 0:
                    log_verbose("Appending to pattern.dat")
                    with open(self._core_replay_file, "a") as f:
                        spike_manager.dump_ascii(f)
        else:
            # Otherwise just apply it to the current connections
            self._synapse_manager.replay(spike_manager, target_name, delay)

    # -
    @mpi_no_errors
    def enable_modifications(self):
        """Iterate over any Modification blocks read from the BlueConfig and apply them to the
        network. The steps needed are more complex than NeuronConfigures, so the user should not be
        expected to write the hoc directly, but rather access a library of already available mods.
        """
        # mod_mananger gets destroyed when function returns (not required)
        mod_manager = Nd.ModificationManager(self._target_manager)
        logging.info("Enabling modifications...")
        for mod in compat.Map(self._config_parser.parsedModifications).values():
            mod_manager.interpret(mod)

    # -
    # @mpi_no_errors - not required since theres a call inside before _binreport_helper.make_comm
    def enable_reports(self):
        """Iterate over reports defined in BlueConfig and instantiate them.
        """
        log_stage("Reports Enabling")
        n_errors = 0
        cur_t = Nd.t
        if cur_t:
            logging.info("Restoring sim at t=%f (report times are absolute!)", cur_t)
        sim_end = self._run_conf["Duration"]
        reports_conf = compat.Map(self._config_parser.parsedReports)
        self._report_list = []

        # Report count for coreneuron
        if self._corenrn_conf:
            self._corenrn_conf.write_report_count(self._config_parser.parsedReports.count())

        for rep_name, rep_conf in reports_conf.items():
            rep_conf = compat.Map(rep_conf).as_dict(parse_strings=True)
            logging.info(" * " + rep_name)
            rep_type = rep_conf["Type"]
            start_time = rep_conf["StartTime"]
            end_time = min(rep_conf["EndTime"], sim_end)

            if rep_type.lower() not in ("compartment", "summation", "synapse"):
                if MPI.rank == 0:
                    logging.error("Unsupported report type: %s.", rep_type)
                n_errors += 1
                continue
            if start_time > end_time:
                if MPI.rank == 0:
                    logging.warning("Report/Sim End-time (%s) before Start (%g). Skipping!",
                                    end_time, start_time)
                continue

            electrode = self._elec_manager.getElectrode(rep_conf["Electrode"]) \
                if not self._corenrn_conf and "Electrode" in rep_conf else None

            rep_params = namedtuple("ReportConf", "name, type, report_on, unit, format, dt, "
                                    "start, end, output_dir, electrode, scaling, isc")(
                rep_name,
                rep_type,  # rep type is case sensitive !!
                rep_conf["ReportOn"],
                rep_conf["Unit"],
                rep_conf["Format"],
                rep_conf["Dt"],
                rep_conf["StartTime"],
                end_time,
                self._output_root,
                electrode,
                rep_conf.get("Scaling"),
                rep_conf.get("ISC", "")
            )

            target_name = rep_conf["Target"]
            target = self._target_manager.getTarget(target_name)

            if self._corenrn_conf and MPI.rank == 0:
                # Init report config
                ptarget = self._target_parser.getTarget(target_name)
                self._corenrn_conf.write_report_config(
                    rep_name, target_name, rep_type, rep_params.report_on, rep_params.unit,
                    rep_params.format, ptarget.isCellTarget(), rep_params.dt, rep_params.start,
                    rep_params.end, ptarget.completegids(), self._output_root)

            if not target:
                # When restoring with coreneuron we dont even need to initialize reports
                continue

            report = Nd.Report(*rep_params)

            # Go through the target members, one cell at a time. We give a cell reference
            # For summation targets - check if we were given a Cell target because we really want
            # all points of the cell which will ultimately be collapsed to a single value
            # on the soma. Otherwise, get target points as normal.
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

        # Report Buffer Size hint in MB.
        if "ReportingBufferSize" in self._run_conf:
            self._binreport_helper.set_max_buffer_size_hint(self._run_conf["ReportingBufferSize"])

        # once all reports are created, we finalize the communicator for any bin reports
        self._binreport_helper.make_comm()

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
            return self._cell_distributor.pnm

        if self._cell_distributor is None or self._cell_distributor._gidvec is None:
            raise RuntimeError("No CellDistributor was initialized. Please create a circuit.")

        if corenrn_gen is None:
            corenrn_gen = self._simulator_conf.generateData()

        self._finalize_model(**sim_opts)

        if self._pr_cell_gid:
            self._pnm.pc.prcellstate(self._pr_cell_gid, "pydamus_t0")

        if corenrn_gen:
            self._sim_corenrn_write_config()

        if self._simulator_conf.runNeuron():
            self._sim_init_neuron()

        self._sim_ready = True
        return self._pnm

    # -
    @mpi_no_errors
    def _finalize_model(self, spike_compress=3):
        """Set up simulation run parameters and initialization.

        Handles setup_transfer, spike_compress, _record_spikes, stdinit, forward_skip, timeout
        Args:
            spike_compress: The spike_compress() parameters (tuple or int)
        """
        logging.info("Preparing to run simulation...")
        pc = self._pnm.pc
        pc.setup_transfer()

        if spike_compress:
            # multisend 13 is combination of multisend(1) + two_phase(8) + two_intervals(4)
            # to activate set spike_compress=(0, 0, 13)
            if not isinstance(spike_compress, tuple):
                spike_compress = (spike_compress, 1, 0)
            pc.spike_compress(*spike_compress)

        # LFP calculation requires WholeCell balancing and extracellular mechanism.
        # This is incompatible with efficient caching atm.
        Nd.cvode.cache_efficient("ElectrodesPath" not in self._run_conf)
        pc.set_maxstep(4)
        Nd.stdinit()

    # -
    def _record_spikes(self, gids=None):
        """Setup recording of spike events (crossing of threshold) for cells on this node
        """
        for gid in (self.gidvec if gids is None else gids):
            # only want to collect spikes off cell pieces with the soma (i.e. the real gid)
            if self._cell_distributor.getSpGid(gid) == gid:
                logging.debug("Collecting spikes for gid %d", gid)
                self._pnm.spike_record(gid)

    # -
    def _sim_init_neuron(self):
        # === Neuron specific init ===
        self._record_spikes()
        fwd_skip = self._run_conf.get("ForwardSkip", 0)
        if fwd_skip:
            logging.info("Initializing with ForwardSkip %d ms", fwd_skip)
            Nd.t = -1e9
            prev_dt = Nd.dt
            Nd.dt = fwd_skip * 0.1
            for flushIndex in range(10):
                Nd.fadvance()
            Nd.dt = prev_dt
            Nd.t = 0
            Nd.frecord_init()

        restore_path = self._run_conf.get("Restore")
        if restore_path:
            bbss = Nd.BBSaveState()
            self._stim_manager.saveStatePreparation(bbss)
            bbss.ignore(self._binreport_helper)
            self._binreport_helper.restorestate(restore_path)
            self._stim_manager.reevent()
            bbss.vector_play_init()

            if self._pr_cell_gid:
                self._pnm.pc.prcellstate(self._pr_cell_gid, "pydamus_t{}".format(Nd.t))

        # increase timeout by 10x
        self._pnm.pc.timeout(200)

    def _sim_corenrn_write_config(self):
        log_stage("Dataset generation for CoreNEURON")
        Nd.registerMapping(self._cell_distributor)
        corenrn_output = self._simulator_conf.getCoreneuronOutputDir().s
        corenrn_data = self._simulator_conf.getCoreneuronDataDir().s
        fwd_skip = self._run_conf.get("ForwardSkip", 0)

        self._pnm.pc.nrnbbcore_write(corenrn_data)
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
        if self._simulator_conf.runNeuron():
            timings = self._run_neuron()
            self.spike2file("out.dat")
        if self._corenrn_conf:
            self.clear_model()
            self._run_coreneuron()
        return timings

    # -
    @return_neuron_timings
    def _run_neuron(self):
        progress = Nd.ShowProgress(Nd.cvode, MPI.rank)
        progress.updateProgress()
        self.solve()
        logging.info("Simulation finished.")

    # -
    def _run_coreneuron(self):
        logging.info("Launching simulation with CoreNEURON")
        neurodamus2core = {"Save": "--checkpoint",
                           "Restore:": "--restore"}
        opts = [(core_opt, self._run_conf[opt])
                for opt, core_opt in neurodamus2core.items()
                if opt in self._run_conf]
        opts_expanded = functools.reduce(operator.iconcat, opts, [])
        log_verbose("solve_core(..., %s)", ", ".join(opts_expanded))
        self._corenrn_conf.psolve_core(*opts_expanded)

    # -
    @mpi_no_errors
    def solve(self, tstop=None):
        """Call solver with a given stop time (default: whole interval).
        Be sure to have sim_init()'d the simulation beforehand
        """
        if not self._sim_ready:
            raise ConfigurationError("Initialize simulation first")

        tstart = Nd.t
        tstop = tstop or Nd.tstop
        events = []  # format: [(time, handler), ...]

        # NOTE:
        # The next events are defined as function handlers so that they can be sorted.
        # In between each event _psolve_loop() is called in order to eventually split long
        # simulation blocks, where one or more report flush(es) can happen. It is a simplified
        # design relatively to the original version where the report checkpoint would not happen
        # before the checkpoint timeout (25ms default). However there shouldn't be almost any
        # performance penalty since the simulation is already halted between events.

        # handle any delayed blocks
        for conn in self._connection_weight_delay_list:
            conn_start = conn.valueOf("Delay")
            # If the first connection starts after our tstop -> dont activate anything
            if conn_start > tstop:
                break
            # Past connections (should be already activated) -> skip!
            if conn_start < tstart:
                continue

            def event_f():
                logging.info("\rDelay: Configuring %s->%s after %d ms",
                             conn.get("Source").s, conn.get("Destination").s, conn_start)
                self._synapse_manager.configure_connection_config(conn, self.gidvec)

            events.append((conn_start, event_f))

        # Handle Save
        has_save_time = "SaveTime" in self._run_conf
        if "Save" in self._run_conf:
            tsave = tstop
            if has_save_time:
                tsave = tstart + self._run_conf["SaveTime"]
                if tsave > tstop:
                    tsave = tstop
                    logging.warning("SaveTime specified beyond Simulation Duration. "
                                    "Setting SaveTime to tstop.")

            def event_f():
                logging.info("Saving State... (t=%f)", tsave)
                bbss = Nd.BBSaveState()
                MPI.barrier()
                self._stim_manager.saveStatePreparation(bbss)
                bbss.ignore(self._binreport_helper)
                log_verbose("SaveState Initialization Done")

                self._binreport_helper.pre_savestate(self._run_conf["Save"])

                # If event at the end of the sim we can actually clearModel() before savestate()
                if not has_save_time:
                    self.clear_model()

                self._binreport_helper.savestate()

            events.append((tsave, event_f))

        elif has_save_time:
            logging.warning("SaveTime IGNORED. Reason: no 'Save' config entry")

        events.sort()

        logging.info("Running simulation until t=%d ms", tstop)
        t = tstart
        for t, event in events:
            self._psolve_loop(t)
            event()
        # Run until the end
        if t < tstop:
            self._psolve_loop(tstop)

    # reporting - There was an issue where MPI collective routines for reporting and spike exchange
    # are mixed such that some cpus are blocked waiting to complete reporting while others to
    # finish spike exchange. As a work-around, periodically halt simulation and flush reports
    # Default is 25 ms / cycle
    def _psolve_loop(self, tstop):
        cur_t = Nd.t
        for _ in range(math.ceil((tstop - cur_t) / self._buffer_time)):
            next_flush = min(tstop, cur_t + self._buffer_time)
            self._pnm.psolve(next_flush)
            self._binreport_helper.flush()
            cur_t = next_flush

    # -
    @mpi_no_errors
    def clear_model(self):
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

        bbss = Nd.BBSaveState()
        bbss.ignore()
        self._binreport_helper.clear()

        Node.__init__(self, None)  # Reset vars

    # -------------------------------------------------------------------------
    #  Data retrieve / output
    # -------------------------------------------------------------------------

    @property
    def gidvec(self):
        if self._cell_distributor is None or self._cell_distributor._gidvec is None:
            raise RuntimeError("No CellDistributor was initialized. Please create a circuit.")
        return self._cell_distributor.getGidListForProcessor()

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

    # -
    def get_synapse_data_gid(self, gid):
        raise DeprecationWarning("Please use directly the synapse_manager object API, "
                                 "method: get_synapse_params_gid")

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

    # -
    def dump_circuit_config(self, suffix="dbg"):
        log_stage("Dumping cells state")
        Nd.stdinit()

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
                print("[INFO] Rank %d: Debugging %d gids in debug_gids.txt" % (MPI.rank, len(gids)))

        for gid in gids:
            self._pnm.pc.prcellstate(gid, suffix)

    # ---------------------------------------------------------------------------
    # Note: This method is called automatically from Neurodamus.__del__
    #     and therefore it must stay as simple as possible as exceptions are ignored
    def cleanup(self):
        """Have the compute nodes wrap up tasks before exiting.
        """
        # MemUsage constructor will do MPI communications
        mem_usage = Nd.MemUsage()
        mem_usage.print_mem_usage()

        # Coreneuron runs clear the model before starting
        if not self._corenrn_conf:
            self.clear_model()

        # Runworker starts a server loop in the workers and the process dies on pc.done()
        # This shall not be required anymore since we're not using timeit
        # pnm.pc.runworker()  #
        # pnm.pc.done()

        logging.info("Finished")
        Nd.quit()  # this stops neuron, so if runing with special process quits immediately


# Helper class
# ------------
class Neurodamus(Node):
    """A high level interface to Neurodamus
    """
    def __init__(self, config_file, enable_reports=True, logging_level=None):
        """Creates and initializes a neurodamus run node.

        As part of Initiazation it calls:
         * load_targets
         * compute_load_balance
         * Build the circuit (cells, synapses, GJs)
         * Add stimulus & replays
         * Activate reports if requested

        Args:
            config_file: The BlueConfig recipe file
            enable_reports: Whether reports shall be active (default: True)
            logging_level: (int) Redefine the global logging level.
                0 - Only warnings / errors
                1 - Info messages (default)
                2 - Verbose
                3 - Debug messages
        """
        self._init_ok = False
        if logging_level is not None:
            GlobalConfig.verbosity = logging_level

        Node.__init__(self, config_file)
        # Use the run_conf dict to avoid passing it around
        self._run_conf["EnableReports"] = enable_reports

        logging.info("Running Neurodamus with config from " + config_file)
        self._instantiate_simulation()
        # In case an exception occurs we must prevent the destructor from cleaning
        self._init_ok = True

    # -
    def _build_model(self):
        log_stage("================ CALCULATING LOAD BALANCE ================")
        self.compute_load_balance()

        log_stage("==================== BUILDING CIRCUIT ====================")
        self.create_cells()
        self.execute_neuron_configures()

        # Create connections
        self.create_synapses()
        self.create_gap_junctions()

        # Init resume if requested
        self.check_resume()

        self.enable_stimulus()
        self.enable_modifications()

        if ospath.isfile("debug_gids.txt"):
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
    def _instantiate_simulation(self):
        log_stage("====================== INITIALIZING ======================")
        self.load_targets()

        # Check if user wants to build the model in several steps (only for CoreNeuron)
        sub_targets = self.multicycle_data_generation()

        # Without multi-cycle, it's a trivial model build
        if not sub_targets or len(sub_targets) == 1:
            self._build_model()
            return

        n_cycles = len(sub_targets)
        logging.info("MULTI-CYCLE RUN: {} Cycles".format(n_cycles))

        for cycle_i, cur_target in enumerate(sub_targets):
            log_stage("==> CYCLE {} (OUT OF {})".format(cycle_i + 1, n_cycles))

            self.clear_model()
            self._run_conf["CircuitTarget"] = cur_target.name
            self._build_model()

            # Move generated files aside (to be merged later)
            if MPI.rank == 0:
                base_filesdat = ospath.join(self._output_root, 'coreneuron_input/files')
                os.rename(base_filesdat + '.dat', base_filesdat + "_{}.dat".format(cycle_i))

        if MPI.rank == 0:
            self._merge_filesdat(n_cycles, self._output_root)

    # -
    def run(self):
        """Prepares and launches the simulation according to the loaded config.
        """
        log_stage("==================== SIMULATION ====================")
        self.run_all()

    def __del__(self):
        if self._init_ok:
            self.cleanup()
