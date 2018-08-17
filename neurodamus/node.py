"""
The main Neurodamus entity

Copyright 2018 - Blue Brain Project, EPFL
"""
from __future__ import absolute_import
from os import path
import sys
import logging
from .core import MPI, mpi_no_errors
from .core import NeuronDamus as Nd, ParallelNetManager as pnm
from .core.configuration import GlobalConfig, ConfigurationError
from .cell_distributor import CellDistributor
from .connection_manager import SynapseRuleManager, GapJunctionManager
from .replay import SpikeManager
from .utils import compat
from .utils.logging import log_stage, log_verbose


class Node:
    """
    The Node class is the main entity for a distributed neurodamus execution.
    It internally instantiates parallel structures and distributes the cells among all the nodes.
    It is relatively low-level, for a standard run consider using the Neurodamus class instead.
    """

    def __init__(self, recipe):
        """ Creates a neurodamus executor
        Args:
            recipe: The BlueRecipe file
        """
        Nd.init()
        self._config_parser = self._open_config(recipe)
        self._blueconfig_path = path.dirname(recipe)
        self._connection_weight_delay_list = []

        # Instance Objects
        self._target_manager = None
        self._target_parser = None
        self._cell_distributor = None
        self._cell_list = None
        self._stim_list = None
        self._report_list = None
        self._stim_manager = None
        self._elec_manager = None
        self._binreport_helper = None
        self._runtime = 0
        self._synapse_manager = None  # type: SynapseRuleManager
        self._gj_manager = None       # type: GapJunctionManager

    # public properties - object modification on user responsibility
    target_manager = property(lambda self: self._target_manager)
    synapse_manager = property(lambda self: self._synapse_manager)
    gj_manager = property(lambda self: self._gj_manager)
    stim_manager = property(lambda self: self._stim_manager)
    elec_manager = property(lambda self: self._elec_manager)
    cells = property(lambda self: self._cell_list)
    stims = property(lambda self: self._stim_list)
    reports = property(lambda self: self._report_list)

    # Compat
    def __getattr__(self, item):
        # parts = item.split("_")
        # new_name = "".join(["_" + parts[0]] + [p.capitalize() for p in parts[1:]])
        new_name = "".join(["_" + c.lower() if c.isupper() else c for c in item])
        if hasattr(self, new_name):
            logging.warning("Accessing attribute {} via compat API".format(item))
            return getattr(self, new_name)
        raise AttributeError("Node has no attribute {} (nor {})".format(item, new_name))

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

        # Make sure Random Numbers are prepped
        rng_info = Nd.RNGSettings()
        rng_info.interpret(parsed_run)  # this sets a few global vars in hoc

        h = Nd.h
        h.tstop = parsed_run.valueOf("Duration")
        h.dt = parsed_run.valueOf("Dt")
        h.steps_per_ms = 1.0 / h.dt

        return config_parser

 #
    @mpi_no_errors
    def load_targets(self):
        """Provided that the circuit location is known and whether a user.target file has been
        specified, load any target files via a TargetParser.  Note that these will be moved into a
        TargetManager after the cells have been distributed, instantiated, and potentially split.
        """
        log_stage("Loading Targets")
        self._target_parser = Nd.TargetParser()
        run_conf = self._config_parser.parsedRun
        if MPI.rank == 0:
            self._target_parser.isVerbose = 1

        target_f = path.join(run_conf.get("nrnPath").s, "start.target")
        self._target_parser.open(target_f)

        if run_conf.exists("TargetFile"):
            user_target = self._find_config_file(run_conf.get("TargetFile").s)
            self._target_parser.open(user_target, 1)

    #
    @mpi_no_errors
    def compute_loadbal(self):
        """This function has the simulator instantiate the circuit (cells & synapses) to determine
        the best way to split cells and balance those pieces across the available cpus.
        """
        log_stage("Computing Load Balance")
        run_cfg = self._config_parser.parsedRun
        run_mode = run_cfg.get("RunMode").s if run_cfg.exists("RunMode") else None

        if run_mode == "LoadBalance":
            logging.info("LoadBalancing enabled with multisplit capability")
        elif run_mode == "WholeCell":
            logging.info("Whole Cell balancing enabled")
        else:
            logging.info("RunMode not used for load balancing. Will use Round-Robin distribution")
            return

        # Is there a cpu count override in the BlueConfig?
        if self._config_parser.parsedRun.exists("ProspectiveHosts"):
            prospective_hosts = self._config_parser.parsedRun.valueOf("ProspectiveHosts")
        else:
            prospective_hosts = MPI.cpu_count

        # determine if we need to regen load balance info, or if it already exists for this config
        # to prevent excessive messages when the file is not there, have rank 0 handle file access
        do_generate = 0
        generate_reason = None
        cxinfo_filename = "cxinfo_%d.txt" % (prospective_hosts,)

        if MPI.rank == 0:
            if path.isfile(cxinfo_filename):
                with open(cxinfo_filename, "r") as cxinfo:
                    cx_nrnpath = cxinfo.readline().strip()
                    cx_target = cxinfo.readline().strip()
                    cxinfo.readline().strip()  # target File
                    if cx_nrnpath != self._config_parser.parsedRun.get("nrnPath").s:
                        do_generate = 1
                        generate_reason = "nrnPath has changed"

                    # if there is no circuit target, cmp against "---"
                    if self._config_parser.parsedRun.exists("CircuitTarget"):
                        if cx_target != self._config_parser.parsedRun.get("CircuitTarget").s:
                            do_generate = 1
                            generate_reason = "CircuitTarget has changed"
                        elif cx_target == "---":
                            do_generate = 1
                            generate_reason = "CircuitTarget has changed"
            else:
                do_generate = 1
                generate_reason = "no cxinfo file"

        # Before MPI broadcast check all processes fine
        MPI.check_no_errors()

        # rank 0 broadcasts the fact whether we need to generate loadbalancing data or not
        if GlobalConfig.use_mpi:
            message = Nd.Vector(1, do_generate)
            MPI.broadcast(message, 0)
            do_generate = message[0]

        # pre-existing load balance info is good. We can reuse it, so return now or quit
        if not do_generate:
            logging.info("Using existing load balancing info")
            if MPI.cpu_count == prospective_hosts:
                return
            else:
                logging.error("Requires  on a partition of %d cpus (as per ProspectiveHosts)",
                              prospective_hosts)
                raise RuntimeError("Invalid CPU count. See log")

        logging.info("Generating loadbalancing data. Reason: %s", generate_reason)
        loadbal = Nd.LoadBalance()

        # Can we use an existing mcomplex.dat?  If mechanisms change, it needs to be regenerated.
        if not path.isfile("mcomplex.dat"):
            logging.info("Generating mcomplex.dat...")
            loadbal.create_mcomplex()
        else:
            logging.info("Using existing mcomplex.dat")
        loadbal.read_mcomplex()

        logging.info("Instantiating cells Round Robin style")
        self.create_cells("RR")
        self.create_synapses()
        self.create_gap_junctions()

        # check if we are doing whole cell balancing which requires an override of a key value
        if run_mode == "WholeCell":
            self._cell_distributor.msfactor = 1e6

        self._cell_distributor.load_balance_cells(loadbal, prospective_hosts)

        # balancing calculations done, we can save the cxinfo file now for future usage
        if MPI.rank == 0:
            cxinfo = open(cxinfo_filename, "w")
            cxinfo.write(self._config_parser.parsedRun.get("nrnPath").s + "\n")
            if self._config_parser.parsedRun.exists("CircuitTarget"):
                cxinfo.write(self._config_parser.parsedRun.get("CircuitTarget").s + "\n")
            else:
                cxinfo.write("---\n")

            if self._config_parser.parsedRun.exists("TargetFile"):
                cxinfo.write(self._config_parser.parsedRun.get("TargetFile").s + "\n")
            else:
                cxinfo.write("---\n")
            cxinfo.close()

        # if loadbalance was calculated for different number of cpus, then we are done
        if prospective_hosts != MPI.cpu_count:
            raise ConfigurationError("Loadbalancing forced on %d CPUs (ProspectiveHosts). "
                                     "Launch on a partition of that size", prospective_hosts)
            sys.exit()

        self.clear_model()

    #
    @mpi_no_errors
    def export_loadbal(self, lb):
        self._cell_distributor.load_balance_cells(lb, MPI.size)

    #
    @mpi_no_errors
    def create_cells(self, run_mode=None):
        """Instantiate the cells of the network, handling distribution and any load balancing as
        needed. Any targets will be updated to know which cells are local to the cpu.

        Args:
            run_mode (str): optional argument to override RunMode as "RR" or "LoadBalance"
        """
        log_stage("Circuit build")
        mode_obj = None
        old_mode = None
        if run_mode is not None:
            logging.info("override RunMode")
            if not self._config_parser.parsedRun.exists("RunMode"):
                mode_obj = Nd.String("RR")
                self._config_parser.parsedRun.put("RunMode", mode_obj)
            else:
                mode_obj = self._config_parser.parsedRun.get("RunMode")
            old_mode = mode_obj.s
            mode_obj.s = run_mode

        # will LoadBalancing need the pnm during distribution?  not round-robin? maybe split cell?
        self._cell_distributor = CellDistributor(
            self._config_parser, self._target_parser, pnm.o)

        # instantiate full cells -> should this be in CellDistributor object?
        self._cell_list = self._cell_distributor.cell_list

        # localize targets, give to target manager
        self._target_parser.updateTargets(self.gidvec)

        # give a TargetManager the TargetParser's completed targetList
        self._target_manager = Nd.TargetManager(
            self._target_parser.targetList, self._cell_distributor)

        # Let the CellDistributor object have any final say in the cell objects
        self._cell_distributor.finalize(self.gidvec)
        self._cell_distributor.delayed_split()

        # restore original if there was any override
        if run_mode is not None:
            mode_obj.s = old_mode

    #
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

        run_conf = self._config_parser.parsedRun
        nrn_path = run_conf.get("nrnPath").s
        synapse_mode = run_conf.get("SynapseMode").s if run_conf.exists("SynapseMode") else None

        # note - with larger scale circuits, we may divide synapses among several files.
        # Need to know how many from the BlueConfig
        nrn_filepath = path.join(nrn_path, "nrn.h5")
        if path.isfile(nrn_filepath):
            n_synapse_files = 1
        else:
            if run_conf.exists("NumSynapseFiles"):
                n_synapse_files = run_conf.valueOf("NumSynapseFiles")
            else:
                raise ConfigurationError("nrn.h5 doesnt exist and BlueConfig does not specify"
                                         "NumSynapseFiles")

        self._synapse_manager = SynapseRuleManager(nrn_path, self._target_manager,
                                                   n_synapse_files, synapse_mode)

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
        if self._config_parser.parsedRun.exists("BonusSynapseFile"):
            logging.info("Handle Bonus synapse file")
            n_synapse_files = int(self._config_parser.parsedRun.valueOf("NumBonusFiles")) \
                if self._config_parser.parsedRun.exists("NumBonusFiles") else 1

            self._synapse_manager.open_synapse_file(
                self._config_parser.parsedRun.get("BonusSynapseFile").s,
                n_synapse_files)

            if self._config_parser.parsedConnects.count() == 0:
                self._synapse_manager.connect_all(self.gidvec)
            else:
                self._interpret_connections(extend_info=False)

        # Check for Projection blocks
        if self._config_parser.parsedProjections.count() > 0:
            logging.info("Handling projections...")

            for pname, projection in compat.Map(self._config_parser.parsedProjections).items():
                logging.info(" * %s", pname)
                n_synapse_files = projection.valueOf("NumSynapseFiles") \
                    if projection.exists("NumSynapseFiles") else 1

                # Skip projection blocks for gap junctions
                if projection.exists("Type") and projection.get("Type").s == "GapJunction":
                    continue

                nrn_path = self._find_projection_file(projection)
                self._synapse_manager.open_synapse_file(nrn_path, n_synapse_files)

                # Go ahead and make all the Projection connections
                self._synapse_manager.connect_all(self.gidvec)
                self._interpret_connections(extend_info=False)

        # Check if we need to override the base seed for synapse RNGs
        base_seed = run_conf.valueOf("BaseSeed") if run_conf.exists("BaseSeed") else 0

        self._synapse_manager.finalizeSynapses(base_seed)

    #
    def _interpret_connections(self, extend_info=True):
        """Aux method for creating/updating connections
        """
        _logmsg = "Creating connections from BlueConfig..."
        if extend_info: logging.info(_logmsg)
        else: log_verbose(_logmsg)

        for conn_conf in compat.Map(self._config_parser.parsedConnects).values():
            if conn_conf.exists("Delay"):
                # Connection blocks using a 'Delay' option are handled later
                continue

            conn_src = conn_conf.get("Source").s
            conn_dst = conn_conf.get("Destination").s
            if extend_info:
                logging.info(" * Pathway %s -> %s ", conn_src, conn_dst)

            # check if we are supposed to disable creation
            # -> i.e. only change weights for existing connections
            dont_create = conn_conf.exists("CreateMode") and \
                conn_conf.get("CreateMode").s == "NoCreate"

            # Check for STDP flag in config file, or default to no STDP
            stdp_mode = conn_conf.get("UseSTDP").s \
                if conn_conf.exists("UseSTDP") else "STDPoff"

            mini_spont_rate = conn_conf.valueOf("SpontMinis") \
                if conn_conf.exists("SpontMinis") else .0

            # weight is now an optional argument, None indicates no change
            weight = conn_conf.valueOf("Weight") \
                if conn_conf.exists("Weight") else None

            # allows a helper object to grab any additional configuration values
            syn_override = conn_conf if conn_conf.exists("ModOverride") else None

            syn_config = conn_conf.get("SynapseConfigure").s \
                if conn_conf.exists("SynapseConfigure") else None

            syn_t = conn_conf.valueOf("SynapseID") \
                if conn_conf.exists("SynapseID") else None

            # finally we have all the options checked and can now invoke the SynapseRuleManager
            self._synapse_manager.group_connect(
                conn_src, conn_dst, self.gidvec, weight, syn_config, stdp_mode,
                mini_spont_rate, syn_t, syn_override, creation_mode=not dont_create)

    #
    @mpi_no_errors
    def create_gap_junctions(self):
        """Create gap_juntions among the cells, according to blocks in the config file,
        defined as projections with type GapJunction.
        """
        log_stage("Gap Junctions create")
        run_conf = self._config_parser.parsedRun
        if run_conf.exists("CircuitTarget"):
            target = self._target_manager.getTarget(run_conf.get("CircuitTarget").s)
        else:
            raise ConfigurationError("No circuit target")

        for name, projection in compat.Map(self._config_parser.parsedProjections).items():
            # check if this Projection block is for gap junctions
            if projection.exists("Type") and projection.get("Type").s == "GapJunction":
                nrn_path = projection.get("Path").s
                logging.info(" * %s", name)

                if self._gj_manager is not None:
                    logging.warning("Neurodamus can only support loading one gap junction file. "
                                    "Skipping loading additional files...")
                    break

                self._gj_manager = GapJunctionManager(nrn_path, self._target_manager, 1, target)

        if self._gj_manager is not None:
            self._gj_manager.connect_all(self.gidvec, 1)
            self._gj_manager.finalizeGapJunctions()
        else:
            logging.info("No Gap-junctions found")

    #
    def _find_projection_file(self, projection):
        """Determine where to find the synapse projection files"""
        return self._find_input_file("proj_nrn.h5", projection.get("Path").s, ("ProjectionPath",))

    def _find_input_file(self, filename, filepath, path_conf_entries=()):
        """ Determine where to find the synapse files. Try relative path first. Then check for
        given config variables field in Run, finally use CircuitPath.

        Args:
            filename: The name of the file to find
            filepath: The relative or absolute path we obtained in the direct config
            path_conf_entries: Global path configuration entries to build the absolute path
        Returns:
            The absolute path to the data file
        Raises:
            (ConfigurationError) If the file could not be found
        """
        run_config = self._config_parser.parsedRun

        # if it's absolute path then can be used immediately
        if path.isabs(filepath):
            nrn_path = path.join(filepath, filename)
        else:
            for path_key in path_conf_entries:
                if run_config.exists(path_key):
                    base_path = run_config.get(path_key).s,
                    break
            else:
                base_path = run_config.get("CircuitPath").s,
            nrn_path = path.join(base_path, filepath, filename)

        if not path.isfile(nrn_path):
            raise ConfigurationError("Could not find file %s", filename)
        logging.debug("data file %s path: %s", filename, nrn_path)
        return nrn_path

    def _find_config_file(self, filepath):
        if not path.isabs(filepath):
            _path = path.join(self._blueconfig_path, filepath)
            if path.isfile(_path):
                filepath = _path
            # If not uses pwd
        if not path.isfile(filepath):
            raise ConfigurationError("Config file not found: " + filepath)
        return filepath

    #
    @mpi_no_errors
    def enable_stimulus(self):
        """Iterate over any stimuli/stim injects defined in the config file given to the simulation
        and instantiate them. This iterates over the injects, getting the stim/target combinations
        and passes the raw text in field/value pairs to a StimulusManager object to interpret the
        text and instantiate an actual stimulus object.
        """
        # setup of Electrode objects part of enable stimulus
        log_stage("Stimulus apply")
        conf = self._config_parser
        if conf.parsedRun.exists("ElectrodesPath"):
            electrodes_path = conf.parsedRun.get("ElectrodesPath")
            self._elec_manager = Nd.ElectrodeManager(electrodes_path, conf.parsedElectrodes)

        # for each stimulus defined in the config file, request the stimmanager to instantiate
        if conf.parsedRun.exists("BaseSeed"):
            self._stim_manager = Nd.StimulusManager(self._target_manager, self._elec_manager,
                                                    conf.parsedRun.valueOf("BaseSeed"))
        else:
            self._stim_manager = Nd.StimulusManager(self._target_manager, self._elec_manager)

        # build a dictionary of stims for faster lookup : useful when applying 10k+ stims
        # while we are at it, check if any stims are using extracellular
        has_extra_cellular = False
        stim_dict = {}
        for stim_name, stim in compat.Map(conf.parsedStimuli).items():
            stim_dict.setdefault(stim_name, stim)
            if stim.get("Mode").s == "Extracellular`":
                has_extra_cellular = True

        # Treat extracellular stimuli
        if has_extra_cellular:
            self._stim_manager.interpretExtracellulars(conf.parsedInjects, conf.parsedStimuli)

        logging.info("Instantiating Stimulus Injects:")
        for name, inject in compat.Map(conf.parsedInjects).items():
            target_name = inject.get("Target").s
            stim_name = inject.get("Stimulus").s
            stim = stim_dict.get(stim_name)

            # check the pattern for special cases that are handled here.
            if stim.get("Pattern").s == "SynapseReplay":
                delay = stim.valueOf("Delay") if stim.exists("Delay") else 0
                logging.info(" * [SYN REPLAY] %s (%s -> %s, delay: %d)",
                             name, stim_name, target_name, delay)
                spike_filepath = self._find_config_file(stim.get("SpikeFile").s)
                spike_manager = SpikeManager(spike_filepath, delay)
                spike_manager.replay(self._synapse_manager, target_name)
            else:
                # all other patterns the stim manager will interpret
                logging.info(" * [STIM] %s (%s -> %s)", name, stim_name, target_name)
                self._stim_manager.interpret(target_name, stim)

    #
    @mpi_no_errors
    def enable_modifications(self):
        """Iterate over any Modification blocks read from the BlueConfig and apply them to the
        network. The steps needed are more complex than NeuronConfigures, so the user should not be
        expected to write the hoc directly, but rather access a library of already available mods.
        """
        mod_manager = Nd.ModificationManager(self._target_manager)
        logging.info("Enabling modifications...")
        for mod in compat.Map(self._config_parser.parsedModifications).values():
            mod_manager.interpret(mod)

    #
    # @mpi_no_errors - not required since theres a call inside before _binreport_helper.make_comm
    def enable_reports(self):
        """Iterate over reports defined in the config file given to the simulation and
        instantiate them.
        """
        log_stage("Reports Enabling")
        run_conf = self._config_parser.parsedRun
        sim_dt = run_conf.valueOf("Dt")
        self._binreport_helper = Nd.BinReportHelper(sim_dt)
        n_errors = 0

        # other useful fields from main Run object
        output_path = run_conf.get("OutputRoot").s
        sim_end = run_conf.valueOf("Duration")

        reports_conf = compat.Map(self._config_parser.parsedReports)
        self._report_list = []

        for rep_name, rep_conf in reports_conf.items():
            logging.info(" * " + rep_name)
            rep_type = rep_conf.get("Type").s
            start_time = rep_conf.valueOf("StartTime")
            end_time = rep_conf.valueOf("EndTime")
            if end_time > sim_end:
                end_time = sim_end

            if rep_type.lower() not in ("compartment", "summation", "synapse"):
                if MPI.rank == 0: logging.error("Unsupported report type: %s.", rep_type)
                n_errors += 1
                continue

            if start_time > end_time:
                if MPI.rank == 0: logging.warning("Report or Sim End-time (%s) is before Start (%g).%s",
                                                  end_time, start_time, " Skipping...")
                continue

            electrode = self._elec_manager.getElectrode(rep_conf.get("Electrode").s)\
                if rep_conf.exists("Electrode") else None

            report = Nd.Report(
                rep_name,
                rep_type,  # rep type is case sensitive !!
                rep_conf.get("ReportOn").s,
                rep_conf.get("Unit").s,
                rep_conf.get("Format").s,
                rep_conf.valueOf("Dt"),
                rep_conf.valueOf("StartTime"),
                end_time,
                output_path,
                electrode,
                rep_conf.get("Scaling") if rep_conf.exists("Scaling") else None,  # string obj
                rep_conf.get("ISC").s if rep_conf.exists("ISC") else ""
            )

            # Go through the target members, one cell at a time. We give a cell reference
            target_name = rep_conf.get("Target").s
            target = self._target_manager.getTarget(target_name)

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
                    report.addCompartmentReport(cell, point, spgid)
                elif rep_type.lower() == "summation":
                    report.addSummationReport(cell, point, target.isCellTarget(), spgid)
                elif rep_type.lower() == "synapse":
                    report.addSynapseReport(cell, point, spgid)

            # keep report object? Who has the ascii/hdf5 object? (1 per cell)
            # the bin object? (1 per report)
            self._report_list.append(report)

        if n_errors > 0:
            raise ConfigurationError("%d reporting errors detected. Terminating" % (n_errors,))

        # Report Buffer Size hint in MB.
        if run_conf.exists("ReportingBufferSize"):
            self._binreport_helper.set_max_buffer_size_hint(
                run_conf.valueOf("ReportingBufferSize"))

        # once all reports are created, we finalize the communicator for any bin reports
        MPI.check_no_errors()
        self._binreport_helper.make_comm()

        # electrode manager is no longer needed. free the memory
        if self._elec_manager is not None:
            self._elec_manager.clear()

    #
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

    #
    @mpi_no_errors
    def run(self, show_progress=False):
        """ Runs the simulation
        """
        log_stage("Running")
        run_conf = self._config_parser.parsedRun
        if show_progress:
            _ = Nd.ShowProgress(Nd.cvode, MPI.rank)  # NOQA (required to keep obj alive)

        pnm.pc.setup_transfer()
        spike_compress = 3

        pnm.pc.spike_compress(spike_compress, spike_compress != 0, 0)
        # LFP calculation requires WholeCell balancing and extracellular mechanism.
        # This is incompatible with efficient caching atm.
        if run_conf.exists("ElectrodesPath"):
            Nd.cvode.cache_efficient(0)
        else:
            Nd.cvode.cache_efficient(1)

        self.want_all_spikes()
        pnm.pc.set_maxstep(4)
        self._runtime = Nd.startsw()

        # Returned timings
        tdat = [0] * 7
        tdat[0] = pnm.pc.wait_time()

        Nd.stdinit()

        # check for optional argument "ForwardSkip"
        fwd_skip = run_conf.valueOf("ForwardSkip") if run_conf.exists("ForwardSkip") else False
        if fwd_skip:
            logging.info("Initting with ForwardSkip %d ms", fwd_skip)
            Nd.t = -1e9
            prev_dt = Nd.dt
            Nd.dt = fwd_skip * 0.1
            for flushIndex in range(10):
                Nd.fadvance()
            Nd.dt = prev_dt
            Nd.t = 0
            Nd.frecord_init()

        # increase timeout by 10x
        pnm.pc.timeout(200)

        # I think I must use continuerun?
        if len(self._connection_weight_delay_list) == 0:
            logging.info("Running until the end (%d ms)", Nd.tstop)
            pnm.psolve(Nd.tstop)
        else:
            # handle any delayed blocks
            for conn in self._connection_weight_delay_list:
                logging.info(" * Delay: Configuring %s->%s after %d ms",
                             conn.get("Source").s, conn.get("Destination".s), conn.valueOf("Delay"))
                pnm.psolve(conn.valueOf("Delay"))
                self._synapse_manager.configure_connection_config(conn, self.gidvec)

            logging.info("Running until the end (%d ms)", Nd.tstop)
            pnm.psolve(Nd.tstop)

        # final flush for reports
        self._binreport_helper.flush()

        tdat[0] = pnm.pc.wait_time() - tdat[0]
        self._runtime = Nd.startsw() - self._runtime
        tdat[1] = pnm.pc.step_time()
        tdat[2] = pnm.pc.send_time()
        tdat[3] = pnm.pc.vtransfer_time()
        tdat[4] = pnm.pc.vtransfer_time(1)  # split exchange time
        tdat[6] = pnm.pc.vtransfer_time(2)  # reduced tree computation time
        tdat[4] -= tdat[6]

        logging.info("Simulation finished.")
        return tdat

    #
    def want_all_spikes(self):
        """setup recording of spike events (crossing of threshold) for the cells on this node
        """
        for gid in self.gidvec:
            # only want to collect spikes off cell pieces with the soma (i.e. the real gid)
            if self._cell_distributor.getSpGid(gid) == gid:
                logging.debug("Collecting spikes for gid %d", gid)
                pnm.spike_record(gid)

    #
    @mpi_no_errors
    def clear_model(self):
        """Clears appropriate lists and other stored references. For use with intrinsic load
        balancing. After creating and evaluating the network using round robin distribution, we want
        to clear the cells and synapses in order to have a clean slate on which to instantiate the
        balanced cells.
        """
        logging.info("Clearing model")
        pnm.pc.gid_clear()
        pnm.nclist.remove_all()
        pnm.cells.remove_all()

        for cell in self._cell_list:
            cell.CellRef.clear()
        del self._cell_list[:]

        # remove the self._synapse_manager to destroy all underlying synapses/connections
        self._synapse_manager = None
        self._gj_manager = None
        self._connection_weight_delay_list = []

        # clear reports if initialized
        if self._report_list is not None:
            self._report_list = []

    # -------------------------------------------------------------------------
    #  Data retrieve / output
    #-------------------------------------------------------------------------

    @property
    def gidvec(self):
        return self._cell_distributor.getGidListForProcessor()

    #
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

    #
    def get_synapse_data_gid(self, gid):
        raise DeprecationWarning("Please use directly the synapse_manager object API, "
                                 "method: get_synapse_params_gid")

    #
    @mpi_no_errors
    def spike2file(self, outfile):
        """ Write the spike events that occured on each node into a single output file.
        Nodes will write in order, one after the other.
        """
        logging.info("Writing spikes to %s", outfile)
        outfile = path.join(self._config_parser.parsedRun.get("OutputRoot").s, outfile)

        # root node opens file for writing, all others append
        if MPI.rank == 0:
            with open(outfile, "w") as f:
                f.write("/scatter\n")
                for i, gid in enumerate(pnm.idvec):
                    f.write("%.3f\t%d\n" % (pnm.spikevec.x[i], gid))

        # Write other nodes' result in order
        for nodeIndex in range(1, MPI.cpu_count):
            MPI.barrier()
            if MPI.rank == nodeIndex:
                with open(outfile, "a") as f:
                    for i, gid in enumerate(pnm.idvec):
                        f.write("%.3f\t%d\n" % (pnm.spikevec.x[i], gid))

    #
    def dump_circuit_config(self, suffix="dbg"):
        for gid in self.gidvec:
            pnm.pc.prcellstate(gid, suffix)

    # ---------------------------------------------------------------------------
    # Note: This method is called automatically from Neurodamus.__del__
    #     and therefore it must stay as simple as possible as exceptions are ignored
    def cleanup(self):
        """Have the compute nodes wrap up tasks before exiting.
        """
        # MemUsage constructor will do MPI communications
        mem_usage = Nd.MemUsage()
        mem_usage.print_mem_usage()
        # Clear model already checks if MPI is fine, and is trivial

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
    def __init__(self, recipe_file, logging_level=None):
        """Creates and initializes a neurodamus run node
        Args:
            recipe_file: The BlueConfig recipe file
            logging_level: (int) Redefine the global logging level.
                0 - Only warnings / errors
                1 - Info messages (default)
                2 - Verbose
                3 - Debug messages
        """
        self._init_ok = False
        if logging_level is not None:
            GlobalConfig.verbosity = logging_level

        Node.__init__(self, recipe_file)

        self._instantiate_simulation()
        self._init_ok = True

    def _instantiate_simulation(self):
        log_stage("============= INITIALIZING (& Load-Balancing) =============")
        self.load_targets()
        self.compute_loadbal()

        log_stage("==================== BUILDING CIRCUIT ====================")
        self.create_cells()
        self.execute_neuron_configures()

        # Create connections
        self.create_synapses()
        self.create_gap_junctions()

        self.enable_stimulus()
        self.enable_modifications()
        self.enable_reports()

    def run(self, spike_filaname='spikes.dat', show_progress=True):
        """Runs the Simulation, writing the spikes to the given file
        """
        Node.run(self, show_progress)
        self.spike2file(spike_filaname)

    def __del__(self):
        if self._init_ok:
            self.cleanup()
