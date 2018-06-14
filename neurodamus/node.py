"""
The main Neurodamus entity

Copyright 2018 - Blue Brain Project, EPFL
"""
from __future__ import absolute_import
from os import path
import logging
from .utils import setup_logging, compat
from .cell_distributor import CellDistributor
from .core.configuration import GlobalConfig, MPInfo, ConfigurationError
from .core import NeuronDamus as Nd
from .connection_manager import SynapseRuleManager, GapJunctionManager


class Node:
    """
    The Node class is the main entity for a distributed neurodamus execution.
    It internally instantiates parallel structures and distributes the cells among all the nodes
    """

    _pnm = None
    """NEURON Parallel Network Manager"""

    def __init__(self, recipe):
        """ Creates a neurodamus executor
        Args:
            recipe: The BlueRecipe file
        """
        self._pnm = Nd.pnm
        Nd.execute("cvode = new CVode()")
        Nd.execute("celsius=34")

        self._config_parser = self.openConfig(recipe)
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

    # Compat
    def __getattr__(self, item):
        # parts = item.split("_")
        # new_name = "".join(["_" + parts[0]] + [p.capitalize() for p in parts[1:]])
        new_name = "".join(["_" + c.lower() if c.isupper() else c for c in item])
        if hasattr(self, new_name):
            logging.warning("Accessing attribute {} via compat API".format(item))
            return getattr(self, new_name)
        raise AttributeError("Node has no attribute {} (nor {})".format(item, new_name))

    #
    def openConfig(self, recipe):
        """This function will run the parser and make the data accessible.

        Args:
            recipe: Name of Config file to load
        """
        config_parser = Nd.ConfigParser()
        config_parser.open(recipe)
        if MPInfo.rank == 0:
            config_parser.toggleVerbose()

        # set some basic information
        parsed_run = config_parser.parsedRun
        if not Nd.object_id(parsed_run):
            raise RuntimeError("No Run block parsed from BlueConfig %s", recipe)

        # Make sure Random Numbers are prepped
        rng_info = Nd.RNGSettings()
        rng_info.interpret(parsed_run)  # this sets a few global vars in hoc

        h = Nd.h
        h.tstop = parsed_run.valueOf("Duration")
        h.dt = parsed_run.valueOf("Dt")
        h.steps_per_ms = 1.0 / h.dt
        return config_parser

    #
    def computeLB(self):
        """This function has the simulator instantiate the circuit (cells & synapses) for the purpose
        of determining the best way to split cells and balance those pieces across the available cpus.
        """
        run_mode = self._config_parser.parsedRun.get("RunMode").s
        if run_mode == "LoadBalance":
            logging.info("LoadBalancing enabled with multisplit capability")
        elif run_mode == "WholeCell":
            logging.info("Whole Cell balancing enabled")
        else:
            logging.info("RunMode  not used for load balancing. Will use Round-Robin distribution"
                         .format(run_mode.s))
            return

        # Is there a cpu count override in the BlueConfig?
        if self._config_parser.parsedRun.exists("ProspectiveHosts"):
            prospective_hosts = self._config_parser.parsedRun.valueOf("ProspectiveHosts")
        else:
            prospective_hosts = MPInfo.cpu_count

        # determine if we need to regen load balance info, or if it already exists for this config
        # to prevent excessive messages when the file is not there, have rank 0 handle file access
        do_generate = 0
        generate_reason = None
        cxinfoFileName = "cxinfo_%d.txt" % (prospective_hosts,)

        if MPInfo.rank == 0:
            if path.isfile(cxinfoFileName):
                with open(cxinfoFileName, "r") as cxinfo:
                    cxNrnPath = cxinfo.readline().strip()
                    cxCircuitTarget = cxinfo.readline().strip()
                    cxTargetFile = cxinfo.readline().strip()
                    if cxNrnPath != self._config_parser.parsedRun.get("nrnPath").s:
                        do_generate = 1
                        generate_reason = "nrnPath has changed"

                    # if there is no circuit target, cmp against "---"
                    if self._config_parser.parsedRun.exists("CircuitTarget"):
                        if cxCircuitTarget != self._config_parser.parsedRun.get("CircuitTarget").s:
                            do_generate = 1
                            generate_reason = "CircuitTarget has changed"
                        elif cxCircuitTarget == "---":
                            do_generate = 1
                            generate_reason = "CircuitTarget has changed"
            else:
                do_generate = 1
                generate_reason = "no cxinfo file"

        # rank 0 broadcasts the fact whether we need to generate loadbalancing data or not
        if GlobalConfig.use_mpi:
            message = Nd.Vector(1, do_generate)
            self._pnm.pc.broadcast(message, 0)
            do_generate = message[0]

        # pre-existing load balance info is good. We can reuse it, so return now or quit
        if not do_generate:
            logging.info("Using existing load balancing info")
            if MPInfo.cpu_count == prospective_hosts:
                return
            else:
                logging.info("Relaunch on a partition of %d cpus (as per ProspectiveHosts)",
                         prospective_hosts)
                raise RuntimeError("Invalid CPU count. See log")

        logging.info("Generating loadbalancing data. Reason: %s", generate_reason)

        # Can we use an existing mcomplex.dat?  If mechanisms change, it needs to be regenerated.
        if not path.isfile("mcomplex.dat"):
            logging.info("Generating mcomplex.dat...")
            Nd.create_mcomplex()
        else:
            logging.info("using existing mcomplex.dat")
        loadbal = Nd.LoadBalance()
        Nd.read_mcomplex(loadbal)

        logging.info("instantiate cells Round Robin style")
        self.createCells("RR")
        self.createSynapses()
        self.createGapJunctions()

        # check if we are doing whole cell balancing which requires an override of a key value
        if run_mode == "WholeCell":
            self._cell_distributor.msfactor = 1e6

        self._cell_distributor.printLBInfo(loadbal, prospective_hosts)

        # balancing calculations done, we can save the cxinfo file now for future usage
        if MPInfo.rank == 0:
            cxinfo = open(cxinfoFileName, "w")
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
        if prospective_hosts != MPInfo.cpu_count:
            logging.info("Loadbalancing computed for %d cpus. Relaunch on a partition of that size",
                         prospective_hosts)
            raise RuntimeError("Invalid CPU count. See log")

        logging.info("clearing model")
        self.clearModel()

    #
    def loadTargets(self):
        """Provided that the circuit location is known and whether a user.target file has been
        specified, load any target files via a TargetParser.  Note that these will be moved into a
        TargetManager after the cells have been distributed, instantiated, and potentially split.
        """
        self._target_parser = Nd.TargetParser()
        if MPInfo.rank == 0:
            self._target_parser.isVerbose = 1

        target_f = path.join(self._config_parser.parsedRun.get("nrnPath").s, "start.target")
        self._target_parser.open(target_f)

        if self._config_parser.parsedRun.exists("TargetFile"):
            self._target_parser.open(self._config_parser.parsedRun.get("TargetFile").s)

    #
    def exportLB(self, lb):
        self._cell_distributor.printLBInfo(lb, self._pnm.pc.nhost())

    #
    def createCells(self, run_mode=None):
        """Instantiate the cells of the network, handling distribution and any load balancing as
        needed. Any targets will be updated to know which cells are local to the cpu.

        Args:
            run_mode (str): optional argument to override RunMode as "RR" or "LoadBalance"
        """
        # local: x, cellIndex
        # synVec, target, nrnPath, allVec, allME, gidvec, nil, nc, morphPath, run_mode, old_mode
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
        self._cell_distributor = CellDistributor(self._config_parser, self._target_parser, self._pnm)

        # instantiate full cells -> should this be in CellDistributor object?
        self._cell_list = self._cell_distributor.cellList

        logging.info("Created %d cells", self._pnm.cells.count())

        # localize targets, give to target manager
        self._target_parser.updateTargets(self.gidvec)

        # give a TargetManager the TargetParser's completed targetList
        self._target_manager = Nd.TargetManager(self._target_parser.targetList, self._cell_distributor)

        # Let the CellDistributor object have any final say in the cell objects
        self._cell_distributor.finalize(self.gidvec)
        self._cell_distributor.delayedSplit()

        # restore original if there was any override
        if run_mode is not None:
            mode_obj.s = old_mode

    #
    def interpretConnections(self):
        # local: connectIndex, spontMiniRate, weight
        # localobj spConnect, connSource, connDestination, message, synConfig, nil

        for connectIndex in range(int(self._config_parser.parsedConnects.count())):
            conn_conf = self._config_parser.parsedConnects.o(connectIndex)

            # Connection blocks using a 'Delay' option are handled later
            if conn_conf.exists("Delay"):
                continue

            conn_src = conn_conf.get("Source").s
            conn_dst = conn_conf.get("Destination").s
            # print "connect ", conn_src.s, " -> ", conn_dst.s

            # check if we are supposed to disable creation
            # -> i.e. only change weights for existing connections
            if conn_conf.exists("CreateMode") and conn_conf.get("CreateMode").s == "NoCreate":
                self._synapse_manager.disable_creation()

            # Check for STDP flag in config file, or default to no STDP
            if conn_conf.exists("UseSTDP"):
                stdp_mode = conn_conf.get("UseSTDP").s
            else:
                stdp_mode = "STDPoff"

            mini_spont_rate = 0.0
            if conn_conf.exists("SpontMinis"):
                mini_spont_rate = conn_conf.valueOf("SpontMinis")

            # weight is now an optional argument, -1 indicates no change
            weight = -1
            if conn_conf.exists("Weight"):
                weight = conn_conf.valueOf("Weight")

            self._synapse_manager.synOverride = None
            if conn_conf.exists("ModOverride"):
                # allows a helper object to grab any additional configuration values
                self._synapse_manager.synOverride = conn_conf

            synapse_conf = None
            if conn_conf.exists("SynapseConfigure"):
                synapse_conf = conn_conf.get("SynapseConfigure")
                logging.info("Pathway %s -> %s: configure with '%s'",
                              conn_src, conn_dst, conn_conf.get("SynapseConfigure").s)

            # finally we have all the options checked and can now invoke the SynapseRuleManager
            if conn_conf.exists("SynapseID"):
                self._synapse_manager.group_connect(
                    conn_src, conn_dst, weight, synapse_conf,
                    self._cell_distributor.getGidListForProcessor(),
                    stdp_mode, mini_spont_rate, conn_conf.valueOf("SynapseID"))
            else:
                self._synapse_manager.group_connect(
                    conn_src, conn_dst, weight, synapse_conf,
                    self._cell_distributor.getGidListForProcessor(),
                    stdp_mode, mini_spont_rate)

    #
    def createGapJunctions(self):
        run_conf = self._config_parser.parsedRun
        if run_conf.exists("CircuitTarget"):
            target = self._target_manager.getTarget(run_conf.get("CircuitTarget").s)
        else:
            raise ConfigurationError("No circuit target")

        for projection in compat.Map(self._config_parser.parsedProjections).values():
            # check if this Projection block is for gap junctions
            if projection.exists("Type") and projection.get("Type").s == "GapJunction":
                nrn_path = projection.get("Path").s
                logging.info("Using gap junctions from %s", nrn_path)

                # use connectAll for gj_manager
                if self._gj_manager is not None:
                    logging.error("Neurodamus can only support loading one gap junction file."
                                  "Skipping loading additional files...")
                    break

                self._gj_manager = Nd.GapJunctionManager(nrn_path, self._target_manager, 1, target)
                self._gj_manager.connectAll(self._cell_distributor.getGidListForProcessor(), 1)

        if self._gj_manager is not None:
            self._gj_manager.finalizeGapJunctions()

    #
    def updateGJcon(self, GJcon):
        if self._gj_manager is not None:
            self._gj_manager.updateCond(GJcon)

    #
    def createSynapses(self):
        """Create synapses among the cells, handling any connection blocks that appear in the config file
        """
        # quick check - if we have a single connect block and it sets a weight of zero, can skip
        # synapse creation in its entirety.  This is useful for when no nrn.h5 exists, so we don't
        # error trying to init hdf5 reader. This may not be the cleanest solution.
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

        tid = Nd.timeit_register("Synapse init")
        Nd.timeit_start(tid)
        self._synapse_manager = SynapseRuleManager(nrn_path, self._target_manager,
                                                   n_synapse_files, synapse_mode)

        Nd.timeit_add(tid)

        if self._config_parser.parsedConnects.count() == 0:
            self._synapse_manager.connectAll(self._cell_distributor.getGidListForProcessor(), 1)
        else:
            # Do a quick scan for any ConnectionBlocks with 'Delay' keyword and put a reference on
            # a separate list to be adjusted until later. Note that this requires that another
            # connection block without a delay will connect the cells.
            for conn in compat.Map(self._config_parser.parsedConnects).values():
                if conn.exists("Delay"):
                    self._connection_weight_delay_list.append(conn)

            # Now handle the connection blocks as normal
            self.interpretConnections()

        # Check for additional synapse files.  Now requires a connection block.
        # Continue support for compatibility, but new BlueConfigs should use Projection blocks
        if self._config_parser.parsedRun.exists("BonusSynapseFile"):
            logging.info("Handle Bonus synapse file")
            n_synapse_files = int(self._config_parser.parsedRun.valueOf("NumBonusFiles")) \
                if self._config_parser.parsedRun.exists("NumBonusFiles") else 1

            self._synapse_manager.open_synapse_file(
                self._config_parser.parsedRun.get("BonusSynapseFile").s,
                n_synapse_files, 0)

            if self._config_parser.parsedConnects.count() == 0:
                self._synapse_manager.connectAll(self._cell_distributor.getGidListForProcessor())
            else:
                self.interpretConnections()

        # Check for Projection blocks
        if self._config_parser.parsedProjections.count() > 0:
            logging.info("Handle Projections")

            for projIndex in range(int(self._config_parser.parsedProjections.count())):
                projection = self._config_parser.parsedProjections.o(projIndex)
                n_synapse_files = projection.valueOf("NumSynapseFiles") \
                    if projection.exists("NumSynapseFiles") else 1

                # Skip projection blocks for gap junctions
                if projection.exists("Type") and projection.get("Type").s == "GapJunction":
                    continue

                nrn_path = self.findProjectionFiles(projection)
                self._synapse_manager.open_synapse_file(nrn_path, n_synapse_files, 0)

                # Go ahead and make all the Projection connections
                self._synapse_manager.connect_all(self._cell_distributor.getGidListForProcessor())
                self.interpretConnections()

        # Check if we need to override the base seed for synapse RNGs
        if self._config_parser.parsedRun.exists("BaseSeed"):
            self._synapse_manager.finalizeSynapses(self._config_parser.parsedRun.valueOf("BaseSeed"))
        else:
            self._synapse_manager.finalizeSynapses()

    #
    def findProjectionFiles(self, projection):
        """ Determine where to find the synapse files.  Try relative path first. Then check for
        ProjectionPath field in Run, finally use CircuitPath.

        Params:
            projection - Reference to active projection block being processed
        """
        nrn_path = projection.get("Path").s
        helper = projection.get("Path").s

        # if leading slash '/', then absolute path and can be used immediately
        if helper.startswith("/"):
            nrn_path = path.join(nrn_path, "proj_nrn.h5")
        else:
            if self._config_parser.parsedRun.exists("ProjectionPath"):
                base_path = self._config_parser.parsedRun.get("ProjectionPath").s,
            else:
                base_path = self._config_parser.parsedRun.get("CircuitPath").s,
            nrn_path = path.join(base_path, nrn_path, "proj_nrn.h5")

        logging.info("nrn_path: %s", nrn_path)
        return nrn_path

    #
    def clearModel(self):
        """Clears appropriate lists and other stored references. For use with intrinsic load
        balancing. After creating and evaluating the network using round robin distribution, we want
        to clear the cells and synapses in order to have a clean slate on which to instantiate the
        balanced cells.
        """
        self._pnm.pc.gid_clear()
        self._pnm.nclist.remove_all()
        self._pnm.cells.remove_all()

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

    #
    def enableStimulus(self):
        """Iterate over any stimuli/stim injects defined in the config file given to the simulation
        and instantiate them. This iterates over the injects, getting the stim/target combinations
        and passes the raw text in field/value pairs to a StimulusManager object to interpret the
        text and instantiate an actual stimulus object.
        """
        # setup of Electrode objects part of enable stimulus
        conf = self._config_parser
        if conf.parsedRun.exists("ElectrodesPath"):
            electrodes_path = conf.parsedRun.get("ElectrodesPath").s
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
        stimDict = {}
        logging.info("Build Stim Dictionary")

        for i in range(int(conf.parsedStimuli.count())):
            stim_name = conf.parsedStimuli.key(i)
            stim = conf.parsedStimuli.o(i)
            stimDict.setdefault(stim_name.s, stim)

            if stim.get("Mode").s == "Extracellular":
                has_extra_cellular = 1

        # Treat extracellular stimuli
        if has_extra_cellular:
            self._stim_manager.interpretExtracellulars(conf.parsedInjects, conf.parsedStimuli)

        tid = Nd.timeit_register("Replay setup")
        Nd.timeit_start(tid)

        for inject in compat.Map(conf.parsedInjects).values():
            target_name = inject.get("Target").s
            stim_name = inject.get("Stimulus").s
            stim = stimDict.get(stim_name)

            # check the pattern for special cases that are handled here.
            if stim.get("Pattern").s == "SynapseReplay":
                delay = stim.valueOf("Delay") if stim.exists("Delay") else 0
                syn_replay = Nd.SynapseReplay(self._synapse_manager, stim.get("SpikeFile").s,
                                              delay, MPInfo.rank == 0)
                syn_replay.replay(target_name)
                Nd.timeit_add(tid)
            else:
                # all other patterns the stim manager will interpret
                self._stim_manager.interpret(target_name, stim)
                Nd.timeit_add(tid)

    #
    def enableModifications(self):
        """Iterate over any Modification blocks read from the BlueConfig and apply them to the
        network. The steps needed are more complex than NeuronConfigures, so the user should not be
        expected to write the hoc directly, but rather access a library of already available mods.
        """
        mod_manager = Nd.ModificationManager(self._target_manager)
        for mod in compat.Map(self._config_parser.parsedModifications).values():
            mod_manager.interpret(mod)

    # -
    def enableReports(self):
        """Iterate over reports defined in the config file given to the simulation and instantiate
        them.
        """
        # need bin report helper to handle MPI communication
        sim_dt = self._config_parser.parsedRun.valueOf("Dt")
        self._binreport_helper = Nd.BinReportHelper(sim_dt)

        # other useful fields from main Run object
        output_path = self._config_parser.parsedRun.get("OutputRoot").s
        sim_end = self._config_parser.parsedRun.valueOf("Duration")

        # confirm output_path exists and is usable -> use utility.mod
        if MPInfo.rank == 0:
            execResult = Nd.checkDirectory(output_path)
            if execResult < 0:
                logging.error("Error with OutputRoot %s. Terminating", output_path)
                raise RuntimeError("Output directory error")
        self._pnm.pc.barrier()

        reports_conf = compat.Map(self._config_parser.parsedReports)
        self._report_list = []

        for rep_name, rep_conf in reports_conf.items():
            rep_type = rep_conf.get("Type").s
            end_time = rep_conf.valueOf("EndTime")
            if end_time > sim_end:
                end_time = sim_end

            report = Nd.Report(
                rep_name,
                rep_type,
                rep_conf.get("ReportOn").s,
                rep_conf.get("Unit").s,
                rep_conf.get("Format").s,
                rep_conf.valueOf("Dt"),
                rep_conf.valueOf("StartTime"),
                end_time,
                output_path,
                self._elec_manager.getElectrode(rep_conf.get("Electrode").s)
                    if rep_conf.exists("Electrode") else None,
                rep_conf.get("Scaling") if rep_conf.exists("Scaling") else None,
                rep_conf.get("ISC").s if rep_conf.exists("ISC") else ""
            )

            # Go through the target members, one cell at a time. We give a cell reference
            target_name = rep_conf.get("Target").s
            target = self._target_manager.getTarget(target_name)

            # For summation targets - check if we were given a Cell target because we really want
            # all points of the cell which will ultimately be collapsed to a single value
            # on the soma. Otherwise, get target points as normal.
            points = self.get_target_points(target)

            for cellIndex in range(int(points.count())):
                reportgid = points.o(cellIndex).gid
                reportCell = self._cell_distributor.getCell(reportgid)
                spgid = self._cell_distributor.getSpGid(reportgid)

                # may need to take different actions based on report type
                if rep_type == "compartment":
                    report.addCompartmentReport(reportCell, points.o(cellIndex), spgid)
                elif rep_type == "Summation":
                    report.addSummationReport(reportCell, points.o(cellIndex),
                                              target.isCellTarget(), spgid)
                elif rep_type == "Synapse":
                    report.addSynapseReport(reportCell, points.o(cellIndex), spgid)
                else:
                    logging.warning("unsupported report type: %s", rep_type)

            # keep report object? Who has the ascii/hdf5 object? (1 per cell)
            # the bin object? (1 per report)
            self._report_list.append(report)

        # once all reports are created, we finalize the communicator for any bin reports
        self._binreport_helper.make_comm()

        # electrode manager is no longer needed. free the memory
        if self._elec_manager is not None:
            self._elec_manager.clear()

    #
    def want_all_spikes(self):
        """setup recording of spike events (crossing of threshold) for the cells on this node
        """
        for gid in self.gidvec:
            # only want to collect spikes off cell pieces with the soma (i.e. the real gid)
            if self._cell_distributor.getSpGid(gid) == gid:
                logging.debug("Collecting spikes for gid %d", gid)
                self._pnm.spike_record(gid)

    #
    def cleanup(self):
        """Have the compute nodes wrap up tasks before exiting
        """
        # Note - MemUsage constructor will do a group communication
        # so must be instantiated before pc.runworker
        memUsage = Nd.MemUsage()
        # need a parallel context reference before doing final gather of timing data
        Nd.timeit_init(self._pnm.pc)

        self._pnm.pc.runworker()

        # don't use the built in gather spikes function as this will overload node 0 with events
        # self.pnm.gatherspikes()
        Nd.prtime(self._pnm.pc)
        memUsage.print_node_mem_usage()
        self._pnm.pc.done()

    #
    def spike2file(self, outfile):
        """ Write the spike events that occured on each node into a single output file.
        Nodes will write in order, one after the other.
        """
        outfile = path.join(self._config_parser.parsedRun.get("OutputRoot").s, outfile)

        # root node opens file for writing, all others append
        if MPInfo.rank == 0:
            logging.info("Create file %s", outfile)
            with open(outfile, "w") as f:
                f.write("/scatter\n")  # what am I forgetting for this thing?
                logging.debug("Rank0 writing %d spikes", int(self._pnm.idvec.size()))
                for i in range(int(self._pnm.idvec.size())):
                    f.write("%.3f\t%d\n" % (self._pnm.spikevec.x[i], self._pnm.idvec.x[i]))

        # Write other nodes' result in order
        for nodeIndex in range(1, int(self._pnm.pc.nhost())):
            self._pnm.pc.barrier()
            if MPInfo.rank == nodeIndex:
                with open(outfile, "a") as f:
                    for i in range(int(self._pnm.idvec.size())):
                        f.write("%.3f\t%d\n" % (self._pnm.spikevec.x[i], self._pnm.idvec.x[i]))

    #
    def getSynapseDataForGID(self, gid):
        """ Utility function to help query synaptic data for a given gid.

        Args:
            gid: gid whose data we are accessing

        Returns: list with synapse data for the gid
        """
        return self._synapse_manager.get_synapse_params_gid(gid)

    #
    def executeNeuronConfigures(self):
        """Iterate over any NeuronConfigure blocks from the BlueConfig.
        These are simple hoc statements that can be executed with minimal substitutions
        """
        for config in compat.Map(self._config_parser.parsedConfigures).values():
            target_name = config.get("Target").s
            configure_str = config.get("Configure").s
            logging.info("Apply configure statement \"%s\" on target %s",
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
    def prun(self, show_progress=False):
        """ Runs the simulation
        """
        # local:timeID, spike_compress, cacheeffic, forwardSkip, saveDt, flushIndex, delayIndex
        # localobj: progressIndicator, spConnect
        run_conf = self._config_parser.parsedRun
        if show_progress:
            progress = Nd.ShowProgress(Nd.cvode, MPInfo.rank)

        self._pnm.pc.setup_transfer()
        spike_compress = 3

        self._pnm.pc.spike_compress(spike_compress, spike_compress != 0, 0)
        # LFP calculation requires WholeCell balancing and extracellular mechanism.
        # This is incompatible with efficient caching atm.
        if run_conf.exists("ElectrodesPath"):
            Nd.cvode.cache_efficient(0)
        else:
            Nd.cvode.cache_efficient(1)

        self.want_all_spikes()
        self._pnm.pc.set_maxstep(4)
        self._runtime = Nd.startsw()

        # Returned timings
        tdat = [0] * 7
        tdat[0] = self._pnm.pc.wait_time()

        tid = Nd.timeit_register("stdinit")
        Nd.timeit_start(tid)
        Nd.stdinit()
        Nd.timeit_add(tid)

        # check for optional argument "ForwardSkip"
        fwd_skip = run_conf.valueOf("ForwardSkip") if run_conf.exists("ForwardSkip") else False
        if fwd_skip:
            Nd.t = -1e9
            saveDt = Nd.dt
            Nd.dt = fwd_skip * 0.1
            for flushIndex in range(9):
                Nd.fadvance()
            Nd.dt = saveDt
            Nd.t = 0
            Nd.frecord_init()

        # increase timeout by 10x
        self._pnm.pc.timeout(200)

        tid = Nd.timeit_register("psolve")
        Nd.timeit_start(tid)

        # I think I must use continuerun?
        if len(self._connection_weight_delay_list) == 0:
            self._pnm.psolve(Nd.tstop)
        else:
            # handle any delayed blocks
            for conn in self._connection_weight_delay_list:
                logging.debug("will stop after %d", conn.valueOf("Delay"))
                self._pnm.psolve(conn.valueOf("Delay"))
                self._synapse_manager.apply_post_config_obj(
                    conn, self._cell_distributor.getGidListForProcessor())

            logging.debug("run til the end %d", Nd.tstop)
            self._pnm.psolve(Nd.tstop)
            Nd.timeit_add(tid)

        # final flush for reports
        self._binreport_helper.flush()

        tdat[0] = self._pnm.pc.wait_time() - tdat[0]
        self._runtime = Nd.startsw() - self._runtime
        tdat[1] = self._pnm.pc.step_time()
        tdat[2] = self._pnm.pc.send_time()
        tdat[3] = self._pnm.pc.vtransfer_time()
        tdat[4] = self._pnm.pc.vtransfer_time(1)  # split exchange time
        tdat[6] = self._pnm.pc.vtransfer_time(2)  # reduced tree computation time
        tdat[4] -= tdat[6]
        return tdat

    @property
    def gidvec(self):
        return self._cell_distributor.getGidListForProcessor()

    def get_target_points(self, target):
        """Helper to retrieve the points of a target.
        If target is a cell then uses compartmentCast to obtain its points.
        Otherwise returns the result of calling getPointList directly on the target.

        Args:
            target: The target name or object (faster)

        Returns: The target list of points
        """
        if isinstance(target, str):
            target = self._target_manager.getTarget(target)
        if target.isCellTarget():
            return self._target_manager.compartmentCast(target, "") \
                .getPointList(self._cell_distributor)
        else:
            return target.getPointList(self._cell_distributor)

    #
    def dump_circuit_config(self, suffix=None):
        for gid in self.gidvec:
            self._pnm.pc.prcellstate(gid, suffix)


###################################################
# Helpers
###################################################

def setup_node(recipe_file):
    setup_logging(GlobalConfig.verbosity)
    node = Node(recipe_file)
    node.loadTargets()
    node.computeLB()
    node.createCells()
    node.executeNeuronConfigures()
    return node


def run(recipe_file):
    node = setup_node(recipe_file)
    logging.info("Create connections")
    node.createSynapses()
    node.createGapJunctions()

    logging.info("Enable Stimulus")
    node.enableStimulus()

    logging.info("Enable Modifications")
    node.enableModifications()

    logging.info("Enable Reports")
    node.enableReports()

    logging.info("Run")
    node.prun(True)

    logging.info("Simulation finished. Gather spikes then clean up.")
    node.spike2file("out.dat")
    node.cleanup()
