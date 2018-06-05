"""
The main Neurodamus entity

Copyright 2018 - Blue Brain Project, EPFL
"""
from __future__ import absolute_import
from os import path
import logging
from .utils import setup_logging
from .cell_distributor import CellDistributor
from .core.configuration import GlobalConfig, MPInfo
from .core import NeuronDamus as Nd
from .connection_manager import SynapseRuleManager, GapJunctionManager


class ConfigurationError(Exception):
    pass


class Node:
    pnm = None
    """NEURON Parallel Network Manager"""
    
    # OBJREF:
    # -------
    # targetManager, targetParser, cellDistributor, configParser, cellList, gidvec, stimList, reportList, gjManager
    # pnm, this, tmpCell, stimManager, elecManager, binReportHelper, synapseRuleManager, connectionWeightDelayList

    def __init__(self, recipe):
        """ Creates a neurodamus executor
        Args:
            recipe: The BlueRecipe file
        """
        self.pnm = Nd.pnm
        Nd.execute("cvode = new CVode()")

        self.configParser = self.openConfig(recipe)
        Nd.execute("celsius=34")
        self.connectionWeightDelayList = []

        # Instance Objects
        self.targetManager = None; self.targetParser = None; self.cellDistributor = None
        self.cellList = None; self.stimList = None; self.reportList = None
        self.stimManager = None; self.elecManager = None; self.binReportHelper = None

        self.runtime = 0

        #self._synapse_manager = None; self._gj_manager = None
        self._synapse_manager = None  # type: SynapseRuleManager
        self._gj_manager = None       # type: GapJunctionManager

    #
    def openConfig(self, recipe):
        """This function will run the parser and make the data accessible
        Args:
            recipe: Name of Config file to load
        """
        configParser = Nd.ConfigParser()
        configParser.open(recipe)
        if MPInfo.rank == 0:
            configParser.toggleVerbose()

        # set some basic information
        parsedRun = configParser.parsedRun
        if not Nd.object_id(parsedRun):
            raise RuntimeError("No Run block parsed from BlueConfig %s", recipe)

        # Make sure Random Numbers are prepped
        rngInfo = Nd.RNGSettings()
        rngInfo.interpret(parsedRun)  # this sets a few global vars in hoc

        h = Nd.h
        h.tstop = parsedRun.valueOf("Duration")
        h.dt = parsedRun.valueOf("Dt")
        h.steps_per_ms = 1.0 / h.dt
        return configParser

    #
    def computeLB(self):
        """This function has the simulator instantiate the circuit (cells & synapses) for the purpose
        of determining the best way to split cells and balance those pieces across the available cpus.
        """
        runMode = self.configParser.parsedRun.get("RunMode").s
        if runMode == "LoadBalance":
            logging.info("LoadBalancing enabled with multisplit capability")
        elif runMode == "WholeCell":
            logging.info("Whole Cell balancing enabled")
        else:
            logging.info("RunMode  not used for load balancing. Will use Round-Robin distribution"
                         .format(runMode.s))
            return

        # Is there a cpu count override in the BlueConfig?
        if self.configParser.parsedRun.exists("ProspectiveHosts"):
            prospectiveHosts = self.configParser.parsedRun.valueOf("ProspectiveHosts")
        else:
            prospectiveHosts = MPInfo.cpu_count

        # determine if we need to regen load balance info, or if it already exists for this config
        # to prevent excessive messages when the file is not there, have rank 0 handle file access
        doGenerate = 0
        generate_reason = None
        cxinfoFileName = "cxinfo_%d.txt" % (prospectiveHosts,)

        if MPInfo.rank == 0:
            if path.isfile(cxinfoFileName):
                with open(cxinfoFileName, "r") as cxinfo:
                    cxNrnPath = cxinfo.readline().strip()
                    cxCircuitTarget = cxinfo.readline().strip()
                    cxTargetFile = cxinfo.readline().strip()
                    if cxNrnPath != self.configParser.parsedRun.get("nrnPath").s:
                        doGenerate = 1
                        generate_reason = "nrnPath has changed"

                    # if there is no circuit target, cmp against "---"
                    if self.configParser.parsedRun.exists("CircuitTarget"):
                        if cxCircuitTarget != self.configParser.parsedRun.get("CircuitTarget").s:
                            doGenerate = 1
                            generate_reason = "CircuitTarget has changed"
                        elif cxCircuitTarget == "---":
                            doGenerate = 1
                            generate_reason = "CircuitTarget has changed"
            else:
                doGenerate = 1
                generate_reason = "no cxinfo file"

        # rank 0 broadcasts the fact whether we need to generate loadbalancing data or not
        if GlobalConfig.use_mpi:
            message = Nd.Vector(1, doGenerate)
            self.pnm.pc.broadcast(message, 0)
            doGenerate = message[0]

        # pre-existing load balance info is good. We can reuse it, so return now or quit
        if not doGenerate:
            logging.info("Using existing load balancing info")
            if MPInfo.cpu_count == prospectiveHosts:
                return
            else:
                logging.info("Relaunch on a partition of %d cpus (as per ProspectiveHosts)",
                         prospectiveHosts)
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
        if runMode == "WholeCell":
            self.cellDistributor.msfactor = 1e6

        self.cellDistributor.printLBInfo(loadbal, prospectiveHosts)

        # balancing calculations done, we can save the cxinfo file now for future usage
        if MPInfo.rank == 0:
            cxinfo = open(cxinfoFileName, "w")
            cxinfo.write(self.configParser.parsedRun.get("nrnPath").s + "\n")
            if self.configParser.parsedRun.exists("CircuitTarget"):
                cxinfo.write(self.configParser.parsedRun.get("CircuitTarget").s + "\n")
            else:
                cxinfo.write("---\n")

            if self.configParser.parsedRun.exists("TargetFile"):
                cxinfo.write(self.configParser.parsedRun.get("TargetFile").s + "\n")
            else:
                cxinfo.write("---\n")
            cxinfo.close()

        # if loadbalance was calculated for different number of cpus, then we are done
        if prospectiveHosts != MPInfo.cpu_count:
            logging.info("Loadbalancing computed for %d cpus.  Relaunch on a partition of that size",
                     prospectiveHosts)
            raise RuntimeError("Invalid CPU count. See log")

        logging.info("clearing model")
        self.clearModel()

    #
    def loadTargets(self):
        """ Provided that the circuit location is known and whether a user.target file has been specified,
        load any target files via a TargetParser.  Note that these will be moved into a TargetManager
        after the cells have been distributed, instantiated, and potentially split
        """
        self.targetParser = Nd.TargetParser()
        if MPInfo.rank == 0:
            self.targetParser.isVerbose = 1

        target_f = path.join(self.configParser.parsedRun.get("nrnPath").s, "start.target")
        self.targetParser.open(target_f)

        if self.configParser.parsedRun.exists("TargetFile"):
            self.targetParser.open(self.configParser.parsedRun.get("TargetFile").s)

    #
    def exportLB(self, lb):
        self.cellDistributor.printLBInfo(lb, self.pnm.pc.nhost())

    #
    def createCells(self, runMode=None):
        """
        Instantiate the cells of the network, handling distribution and any load balancing as needed.
        Any targets will be updated to know which cells are local to the cpu
        Args:
            runMode (str): optional argument to override RunMode as "RR" or "LoadBalance"
        """
        # local: x, cellIndex
        # localobj: synVec, target, nrnPath, allVec, allME, gidvec, nil, nc, morphPath, runMode, oldMode

        if runMode is not None:
            logging.info("override RunMode")
            if not self.configParser.parsedRun.exists("RunMode"):
                mode_obj = Nd.String("RR")
                self.configParser.parsedRun.put("RunMode", mode_obj)
            else:
                mode_obj = self.configParser.parsedRun.get("RunMode")
            oldMode = mode_obj.s
            mode_obj.s = runMode

        # will LoadBalancing need the pnm during distribution?  maybe not round-robin, but maybe split cell?
        self.cellDistributor = CellDistributor(self.configParser, self.targetParser, self.pnm)

        # instantiate full cells -> should this be in CellDistributor object?  depends on how split cases work
        gidvec = self.cellDistributor.getGidListForProcessor()
        self.cellList = self.cellDistributor.cellList

        logging.info("Created %d cells", self.pnm.cells.count())

        # localize targets, give to target manager
        self.targetParser.updateTargets(gidvec)

        # give a TargetManager the TargetParser's completed targetList
        self.targetManager = Nd.TargetManager(self.targetParser.targetList, self.cellDistributor)

        # Let the CellDistributor object have any final say in the cell objects
        self.cellDistributor.finalize(gidvec)
        self.cellDistributor.delayedSplit()

        # restore original if there was any override
        if runMode is not None:
            mode_obj.s = oldMode

    #
    def interpretConnections(self):
        # local: connectIndex, spontMiniRate, weight
        # localobj spConnect, connSource, connDestination, message, synConfig, nil

        for connectIndex in range(int(self.configParser.parsedConnects.count())):
            spConnect = self.configParser.parsedConnects.o(connectIndex)

            # Connection blocks using a 'Delay' option are handled later
            if spConnect.exists("Delay"):
                continue

            connSource = spConnect.get("Source").s
            connDestination = spConnect.get("Destination").s
            # print "connect ", connSource.s, " -> ", connDestination.s

            # check if we are supposed to disable creation
            # -> i.e. only change weights for existing connections
            if spConnect.exists("CreateMode") and spConnect.get("CreateMode").s == "NoCreate":
                self._synapse_manager.disable_creation()

            # Check for STDP flag in config file, or default to no STDP
            if spConnect.exists("UseSTDP"):
                useSTDP = spConnect.get("UseSTDP").s
            else:
                useSTDP = "STDPoff"

            spontMiniRate = 0.0
            if spConnect.exists("SpontMinis"):
                spontMiniRate = spConnect.valueOf("SpontMinis")

            # weight is now an optional argument, -1 indicates no change
            weight = -1
            if spConnect.exists("Weight"):
                weight = spConnect.valueOf("Weight")

            self._synapse_manager.synOverride = None
            if spConnect.exists("ModOverride"):
                # allows a helper object to grab any additional configuration values
                self._synapse_manager.synOverride = spConnect

            # print out a message on node 0 if SynapseConfigure option is included just to give user feedback
            synConfig = None
            if spConnect.exists("SynapseConfigure"):
                synConfig = spConnect.get("SynapseConfigure")
                logging.info("Pathway %s -> %s: configure with '%s'",
                         connSource, connDestination, spConnect.get("SynapseConfigure").s)

            # finally we have all the options checked and can now invoke the SynapseRuleManager
            if spConnect.exists("SynapseID"):
                self._synapse_manager.group_connect(
                    connSource, connDestination, weight, synConfig,
                    self.cellDistributor.getGidListForProcessor(),
                    useSTDP, spontMiniRate, spConnect.valueOf("SynapseID"))
            else:
                self._synapse_manager.group_connect(
                    connSource, connDestination, weight, synConfig,
                    self.cellDistributor.getGidListForProcessor(),
                    useSTDP, spontMiniRate)

    #
    def createGapJunctions(self):
        # local projIndex / localobj: nrnPath, circuitTarget, projection
        if self.configParser.parsedRun.exists("CircuitTarget"):
            circuitTarget = self.targetManager.getTarget(self.configParser.parsedRun.get("CircuitTarget").s)
        else:
            raise Exception("No circuit target")

        for projIndex in range(int(self.configParser.parsedProjections.count())):
            projection = self.configParser.parsedProjections.o(projIndex)

            # check if this Projection block is for gap junctions
            if projection.exists("Type") and projection.get("Type").s == "GapJunction":
                nrnPath = projection.get("Path").s
                logging.info(nrnPath)

                # use connectAll for gj_manager
                if self._gj_manager is not None:
                    logging.info("Error: neurodamus can only support loading one gap junction file."
                             "Skipping loading...",
                             level=logging.WARNING)
                    break

                self._gj_manager = Nd.GapJunctionManager(nrnPath, self.targetManager, 1, circuitTarget)
                self._gj_manager.connectAll(self.cellDistributor.getGidListForProcessor(), 1)

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
        # local:connectIndex, projIndex, nSynapseFiles, timeID
        # localobj: nrnPath, synMode, projection, fileTest, fileName

        # quick check - if we have a single connect block and it sets a weight of zero, can skip synapse creation
        # in its entirety.  This is useful for when no nrn.h5 exists, so we don't error trying to init hdf5 reader.
        # This may not be the cleanest solution.  Will keep on backburner
        if self.configParser.parsedConnects.count() == 1:
            if self.configParser.parsedConnects.o(0).valueOf("Weight") == 0:
                return

        # do I need the synapse reader outside this function?
        nrnPath = self.configParser.parsedRun.get("nrnPath").s

        synMode = self.configParser.parsedRun.get("SynapseMode").s \
            if self.configParser.parsedRun.exists("SynapseMode") else None

        # note - with larger scale circuits, we may divide synapses among several files.
        # Need to know how many from the BlueConfig
        # TODO: determine number of synapse files from nrn.h5.0; it has an info dataset where that count is stored
        # TODO: when running on fewer cpus, it is fast to use the single nrn.h5, so prefer that (but how many if 'few'?)
        nrn_filepath = path.join(nrnPath, "nrn.h5")
        if path.isfile(nrn_filepath):
            nSynapseFiles = 1
        else:
            if self.configParser.parsedRun.exists("NumSynapseFiles"):
                nSynapseFiles = self.configParser.parsedRun.valueOf("NumSynapseFiles")
            else:
                raise ConfigurationError("nrn.h5 doesnt exist and BlueConfig does not specify"
                                         "NumSynapseFiles")

        timeID = Nd.timeit_register("Synapse init")
        Nd.timeit_start(timeID)
        #self._synapse_manager = SynapseRuleManager(nrnPath, self.targetManager, nSynapseFiles, synMode)
        if synMode is None:
            synMode = "DualSyns"
        self._synapse_manager = Nd.SynapseRuleManager(nrnPath, self.targetManager, nSynapseFiles,
                                                      synMode)
        Nd.timeit_add(timeID)

        if self.configParser.parsedConnects.count() == 0:
            self._synapse_manager.connectAll(self.cellDistributor.getGidListForProcessor(), 1)
        else:
            # Do a quick scan for any ConnectionBlocks with 'Delay' keyword and put a reference on a separate list
            # to be adjusted until later.  Note that this requires that another connection
            # block without a delay will connect the cells.
            for connectIndex in range(int(self.configParser.parsedConnects.count())):
                if self.configParser.parsedConnects.o(connectIndex).exists("Delay"):
                    self.connectionWeightDelayList.append(self.configParser.parsedConnects.o(connectIndex))

            # Now handle the connection blocks as normal
            self.interpretConnections()

        # Check for additional synapse files.  Now requires a connection block.
        # Continue support for compatibility, but new BlueConfigs should use Projection blocks
        if self.configParser.parsedRun.exists("BonusSynapseFile"):
            logging.info("Handle Bonus synapse file")
            # print "Handle Bonus synapse file"
            nSynapseFiles = 1
            if self.configParser.parsedRun.exists("NumBonusFiles"):
                nSynapseFiles = int(self.configParser.parsedRun.valueOf("NumBonusFiles"))
            self._synapse_manager.open_synapse_file(self.configParser.parsedRun.get("BonusSynapseFile").s, nSynapseFiles, 0)

            if self.configParser.parsedConnects.count() == 0:
                self._synapse_manager.connectAll(self.cellDistributor.getGidListForProcessor())
            else:
                # print "self.configParser.parsedConnects"
                self.interpretConnections()

        # Check for Projection blocks
        if self.configParser.parsedProjections.count() > 0:
            logging.info("Handle Projections")

            for projIndex in range(int(self.configParser.parsedProjections.count())):
                nSynapseFiles = 1
                projection = self.configParser.parsedProjections.o(projIndex)
                if projection.exists("NumSynapseFiles"):
                    nSynapseFiles = projection.valueOf("NumSynapseFiles")

                # check if this Projection block is for gap junctions
                if projection.exists("Type") and projection.get("Type").s == "GapJunction":
                    continue

                nrnPath = self.findProjectionFiles(projection)
                self._synapse_manager.open_synapse_file(nrnPath, nSynapseFiles, 0)

                # A 'Source' field is provided that indicates a target name that contains all the gids used by the
                # presynaptic cells of the projection.  However, I don't need that at the moment

                # Go ahead and make all the Projection connections
                self._synapse_manager.connectAll(self.cellDistributor.getGidListForProcessor())

                self.interpretConnections()

        # Check if we need to override the base seed for synapse RNGs
        if self.configParser.parsedRun.exists("BaseSeed"):
            self._synapse_manager.finalize(self.configParser.parsedRun.valueOf("BaseSeed"))
        else:
            self._synapse_manager.finalizeSynapses()

    #
    def findProjectionFiles(self, projection):
        """ Determine where to find the synapse files.  Try relative path first.  Then check for
            ProjectionPath field in Run, finally use CircuitPath
            Params:
                projection - Reference to active projection block being defessed
        """
        # localobj: projection, nrnPath, strobj, helper
        nrnPath = projection.get("Path").s
        helper = projection.get("Path").s

        # if leading slash '/', then absolute path and can be used immediately
        if helper.startswith("/"):
            nrnPath = path.join(nrnPath, "proj_nrn.h5")
        elif self.configParser.parsedRun.exists("ProjectionPath"):
            nrnPath = path.join(self.configParser.parsedRun.get("ProjectionPath").s, nrnPath, "proj_nrn.h5")
        else:
            nrnPath = path.join(self.configParser.parsedRun.get("CircuitPath").s, nrnPath, "proj_nrn.h5")

        logging.info("nrnPath: %s", nrnPath)
        return nrnPath

    #
    def clearModel(self):
        """Clears appropriate lists and other stored references. For use with intrinsic load balancing.
        After creating and evaluating the network using round robin distribution, we want to clear the cells
        and synapses in order to have a clean slate on which to instantiate the balanced cells.
        """
        # local: cellIndex
        self.pnm.pc.gid_clear()
        self.pnm.nclist.remove_all()
        self.pnm.cells.remove_all()

        for cell in self.cellList:
            cell.CellRef.clear()
        del self.cellList[:]

        # remove the self._synapse_manager to destroy all underlying synapses/connections
        self._synapse_manager = None
        self._gj_manager = None
        self.connectionWeightDelayList = []
        # topologging.infoy()

        # clear reports if initialized
        if self.reportList is not None:
            self.reportList = []

    #
    def enableStimulus(self):
        """Iterate over any stimuli/stim injects defined in the config file given to the simulation and instantiate them.
        This iterates over the injects, getting the stim/target combinations and passes the raw text in field/value pairs
        to a StimulusManager object to interpret the text and instantiate an actual stimulus object.
        """
        # local:hasExtraCellular, timeID, stimIndex, injIndex \
        # localobj: injRequests, stimName, targetName, stim, synReplay, elecPath, stimDict, nil

        # setup of Electrode objects part of enable stimulus
        if self.configParser.parsedRun.exists("ElectrodesPath"):
            elecPath = self.configParser.parsedRun.get("ElectrodesPath").s
            self.elecManager = Nd.ElectrodeManager(elecPath, self.configParser.parsedElectrodes)

        # for each stimulus defined in the config file, request the stimmanager to instantiate
        if self.configParser.parsedRun.exists("BaseSeed"):
            self.stimManager = Nd.StimulusManager(self.targetManager, self.elecManager,
                                                  self.configParser.parsedRun.valueOf("BaseSeed"))
        else:
            self.stimManager = Nd.StimulusManager(self.targetManager, self.elecManager)

        # print what stims we have
        injRequests = self.configParser.parsedInjects

        # build a dictionary of stims for faster lookup : useful when applying 10k+ stims
        # while we are at it, check if any stims are using extracellular
        hasExtraCellular = 0
        logging.info("Build Stim Dictionary")

        stimDict = {}
        for stimIndex in range(int(self.configParser.parsedStimuli.count())):
            stimName = self.configParser.parsedStimuli.key(stimIndex)
            stim = self.configParser.parsedStimuli.o(stimIndex)
            stimDict.setdefault(stimName.s, stim)

            if stim.get("Mode").s == "Extracellular":
                hasExtraCellular = 1

        # Treat extracellular stimuli
        if hasExtraCellular:
            self.stimManager.interpretExtracellulars(injRequests, self.configParser.parsedStimuli)

        timeID = Nd.timeit_register("Replay init")
        for injIndex in range(int(injRequests.count())):
            targetName = injRequests.o(injIndex).get("Target").s
            stimName = injRequests.o(injIndex).get("Stimulus").s
            stim = stimDict.get(stimName)

            # check the pattern for special cases that are handled here.
            if stim.get("Pattern").s == "SynapseReplay":
                raise NotImplementedError("Currently Synapse replay is not yet available in Python")
                # Nd.timeit_start(timeID)
                # # Note: maybe I should let the StimulusManager have a reference to the SynapseRuleManager.
                # # Then I can move all this into that obj. I could then have the logging.infoic of Delay/Duration added
                # # in a more appropriate place (for now, there is no delay/duration handling, but it might be nice
                # # to be able to allow only spikes that occur within a given window to be replayed)
                #
                # # timeID = timeit_register("Replay init")
                # if stim.exists("Delay"):
                #     synReplay = Nd.SynapseReplay(self._synapse_manager, stim.get("SpikeFile").s,
                #                                  stim.valueOf("Delay"), MPInfo.rank == 0 )
                # else:
                #     synReplay = Nd.SynapseReplay(self._synapse_manager, stim.get("SpikeFile").s,
                #                                  0, MPInfo.rank == 0)
                # Nd.timeit_add(timeID)
                #
                # timeID = Nd.timeit_register("Replay inject")
                # Nd.timeit_start(timeID)
                # synReplay.replay(targetName)
                # Nd.timeit_add(timeID)
            else:
                # all other patterns the stim manager will interpret
                self.stimManager.interpret(targetName, stim)

    #
    def enableModifications(self):
        """ Iterate over any Modification blocks read from the BlueConfig and apply them to the network.
        The steps needed are more complex than NeuronConfigures, so the user should not be expected to write
        the hoc directly, but rather access a library of already available Modifications
        """
        # local:modIndex  # localobj: modificationManager
        modificationManager = Nd.ModificationManager(self.targetManager)
        for modIndex in range(int(self.configParser.parsedModifications.count())):
            modificationManager.interpret(self.configParser.parsedModifications.o(modIndex))

    #
    def enableReports(self):
        """Iterate over reports defined in the config file given to the simulation and instantiate them.
        """
        # local: reportIndex, cellIndex, simDt, repDt, startTime, endTime, reportgid, spgid
        # localobj: activeReport, reportRequests, unit, format, reportOn, targetName, type, reportName, electrodeName,
        # report, outputDir, target, points, nil, scalingOption, commandString, reportCell, iscParam
        # no report manager exists (yet?) like stimulus manager

        # need bin report helper to handle MPI communication
        simDt = self.configParser.parsedRun.valueOf("Dt")
        self.binReportHelper = Nd.BinReportHelper(simDt)

        # other useful fields from main Run object
        outputDir = self.configParser.parsedRun.get("OutputRoot").s
        simEnd = self.configParser.parsedRun.valueOf("Duration")

        # confirm outputDir exists and is usable -> use utility.mod
        if MPInfo.rank == 0:
            execResult = Nd.checkDirectory(outputDir)
            if execResult < 0:
                error = True
                logging.info("Error with OutputRoot %s. Terminating", outputDir, level=logging.ERROR)
                raise RuntimeError("Output directory error")
        self.pnm.pc.barrier()

        reportRequests = self.configParser.parsedReports
        self.reportList = []

        for reportIndex in range(int(reportRequests.count())):
            # all reports have same fields - note that reportOn field may include space separated values
            reportName = reportRequests.key(reportIndex).s
            activeReport = reportRequests.o(reportIndex)

            targetName = activeReport.get("Target").s
            type_ = activeReport.get("Type").s
            reportOn = activeReport.get("ReportOn").s
            unit = activeReport.get("Unit").s
            format = activeReport.get("Format").s
            electrodeName = None
            if activeReport.exists("Electrode"):
                electrodeName = activeReport.get("Electrode").s
            repDt = activeReport.valueOf("Dt")
            startTime = activeReport.valueOf("StartTime")
            endTime = activeReport.valueOf("EndTime")
            scalingOption = None
            if activeReport.exists("Scaling"):
                scalingOption = activeReport.get("Scaling")
            if endTime > simEnd:
                endTime = simEnd

            # Identify ISC activity
            if activeReport.exists("ISC"):
                iscParam = reportRequests.o(reportIndex).get("ISC").s
            else:
                iscParam = ""

            if electrodeName is None:
                report = Nd.Report(reportName, type_, reportOn, unit, format, repDt, startTime, endTime, outputDir,
                                   None, scalingOption, iscParam)
            else:
                report = Nd.Report(reportName, type_, reportOn, unit, format, repDt, startTime, endTime, outputDir,
                                   self.elecManager.getElectrode(electrodeName), scalingOption, iscParam)

            # Go through the target members, one cell at a time. We give a cell reference along with the
            target = self.targetManager.getTarget(targetName)

            # For summation targets - check if we were given a Cell target because we really want all points of the cell
            # which will ultimately be collapsed to a single value on the soma. Otherwise, get target points as normal.
            if target.isCellTarget() and type_ == "Summation":
                points = self.targetManager.compartmentCast(target, "").getPointList(self.cellDistributor)
            else:
                points = self.targetManager.getPointList(targetName)

            for cellIndex in range(int(points.count())):
                reportgid = points.o(cellIndex).gid
                reportCell = self.cellDistributor.getCell(reportgid)
                spgid = self.cellDistributor.getSpGid(reportgid)

                # may need to take different actions based on report type
                if type_ == "compartment":
                    report.addCompartmentReport(reportCell, points.o(cellIndex), spgid)
                elif type_ == "Summation":
                    report.addSummationReport(reportCell, points.o(cellIndex), target.isCellTarget(), spgid)
                elif type_ == "Synapse":
                    report.addSynapseReport(reportCell, points.o(cellIndex), spgid)
                else:
                    logging.info("unsupported report type: ", type_, level=logging.WARNING)

            # keep report object?  Who has the ascii/hdf5 object? (1 per cell) the bin object? (1 per report)
            self.reportList.append(report)

        # once all reports are created, we finalize the communicator for any bin reports
        self.binReportHelper.make_comm()

        # electrode manager is no longer needed. free the memory
        if self.elecManager is not None:
            self.elecManager.clear()

    #
    def want_all_spikes(self):
        """setup recording of spike events (crossing of threshold) for the cells on this node
        """
        # local:i, gid, mg  # localobj: self.gidvec
        gidvec = self.cellDistributor.getGidListForProcessor()

        for gid in gidvec:
            # only want to collect spikes off cell pieces with the soma (i.e. the real gid)
            if self.cellDistributor.getSpGid(gid) == gid:
                logging.debug("Collecting spikes for gid %d", gid)
                self.pnm.spike_record(gid)

    #
    def cleanup(self):
        """Have the compute nodes wrap up tasks before exiting
        """
        # local:i   # localobj: outf, memUsage
        # Note - MemUsage constructor will do a group communication, so must be instantiated before pc.runworker
        memUsage = Nd.MemUsage()
        Nd.timeit_init(self.pnm.pc)  # need a parallel context reference before doing final gather of timing data

        self.pnm.pc.runworker()
        # don't use the built in gather spikes function as this will overload node 0 with events
        # self.pnm.gatherspikes()
        Nd.prtime(self.pnm.pc)
        memUsage.print_node_mem_usage()
        self.pnm.pc.done()

    #
    def spike2file(self, outfile):
        """ Write the spike events that occured on each node into a single output file.  Nodes will write
        in order, one after the other.  Maybe a later update could try to have them write in parallel.
        """
        # local:i, nodeIndex  # localobj: outf
        outfile = path.join(self.configParser.parsedRun.get("OutputRoot").s, outfile)

        # root node opens file for writing, all others append
        if MPInfo.rank == 0:
            logging.info("Create file %s", outfile)
            with open(outfile, "w") as f:
                f.write("/scatter\n")  # what am I forgetting for this thing?
                logging.debug("Rank0 writing %d spikes", int(self.pnm.idvec.size()))
                for i in range(int(self.pnm.idvec.size())):
                    f.write("%.3f\t%d\n" % (self.pnm.spikevec.x[i], self.pnm.idvec.x[i]))

        # Write other nodes' result in order
        for nodeIndex in range(1, int(self.pnm.pc.nhost())):
            self.pnm.pc.barrier()
            if MPInfo.rank == nodeIndex:
                with open(outfile, "a") as f:
                    for i in range(int(self.pnm.idvec.size())):
                        f.write("%.3f\t%d\n" %(self.pnm.spikevec.x[i], self.pnm.idvec.x[i]))

    #
    def getSynapseDataForGID(self, gid):
        """ Utility function to help query synaptic data for a given gid
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
        # local:configIndex, cellIndex, x, ret  # localobj: activeConfig, message, target, points, sf
        for configIndex in range(int(self.configParser.parsedConfigures.count())):
            activeConfig = self.configParser.parsedConfigures.o(configIndex)

            logging.info("Apply configure statement \"%s\" on target %s",
                     activeConfig.get("Configure").s, activeConfig.get("Target").s)

            # if target is cell target, then cast to all sections
            target = self.targetManager.getTarget(activeConfig.get("Target").s)
            if target.isCellTarget():
                points = self.targetManager.compartmentCast(target, "").getPointList(self.cellDistributor)
            else:
                points = self.targetManager.getPointList(activeConfig.get("Target").s)

            # iterate the pointlist and execute the command on the section
            for cellIndex in range(int(points.count())):
                for x in points.o(cellIndex):
                    if x != -1:
                        tstr = activeConfig.get("Configure").s

                        # keep checking the string for '%s'; as long as one is there, rebuild the string around it
                        tstr = tstr.replace("%s", Nd.secname(cell=x))
                        tstr = tstr.replace("%g", "%g" % (x,))

                        logging.info(tstr, level=logging.DEBUG)

    #
    def prun(self, show_progress=False):
        """ Runs the simulation
        """
        # local:timeID, spike_compress, cacheeffic, forwardSkip, saveDt, flushIndex, delayIndex
        # localobj: progressIndicator, spConnect
        if show_progress:
            progress = Nd.ShowProgress(Nd.cvode, MPInfo.rank)

        self.pnm.pc.setup_transfer()
        spike_compress = 3

        self.pnm.pc.spike_compress(spike_compress, spike_compress != 0, 0)
        # LFP calculation requires WholeCell balancing and extracellular mechanism.
        # This is incompatible with efficient caching atm.
        if self.configParser.parsedRun.exists("ElectrodesPath"):
            Nd.cvode.cache_efficient(0)
        else:
            Nd.cvode.cache_efficient(1)

        self.want_all_spikes()
        self.pnm.pc.set_maxstep(4)
        self.runtime = Nd.startsw()

        # Returned timings
        tdat = [0] * 7
        tdat[0] = self.pnm.pc.wait_time()

        timeID = Nd.timeit_register("stdinit")
        Nd.timeit_start(timeID)
        Nd.stdinit()
        Nd.timeit_add(timeID)

        # check for optional argument "ForwardSkip"
        forwardSkip = 0
        if self.configParser.parsedRun.exists("ForwardSkip"):
            forwardSkip = self.configParser.parsedRun.valueOf("ForwardSkip")
        if forwardSkip > 0:
            Nd.t = -1e9
            saveDt = Nd.dt
            Nd.dt = forwardSkip * 0.1
            for flushIndex in range(9):
                Nd.fadvance()
            Nd.dt = saveDt
            Nd.t = 0
            Nd.frecord_init()

        # increase timeout by 10x
        self.pnm.pc.timeout(200)

        timeID = Nd.timeit_register("psolve")
        Nd.timeit_start(timeID)

        # I think I must use continuerun?
        if len(self.connectionWeightDelayList) == 0:
            self.pnm.psolve(Nd.tstop)
        else:
            spConnect = self.connectionWeightDelayList[0]
            logging.info("will stop after %d", spConnect.valueOf("Delay"), level=logging.DEBUG)
            self.pnm.psolve(spConnect.valueOf("Delay"))
            self._synapse_manager.apply_post_config_obj(spConnect, self.cellDistributor.getGidListForProcessor())

            # handle any additional delayed blocks
            for spConnect in self.connectionWeightDelayList:
                logging.info("will stop again after %d", spConnect.valueOf("Delay"), level=logging.DEBUG)
                self.pnm.psolve(spConnect.valueOf("Delay"))
                self._synapse_manager.apply_post_config_obj(spConnect, self.cellDistributor.getGidListForProcessor())

            logging.info("run til the end %d", Nd.tstop, level=logging.DEBUG)
            self.pnm.psolve(Nd.tstop)
            Nd.timeit_add(timeID)

        # final flush for reports
        self.binReportHelper.flush()

        tdat[0] = self.pnm.pc.wait_time() - tdat[0]
        self.runtime = Nd.startsw() - self.runtime
        tdat[1] = self.pnm.pc.step_time()
        tdat[2] = self.pnm.pc.send_time()
        tdat[3] = self.pnm.pc.vtransfer_time()
        tdat[4] = self.pnm.pc.vtransfer_time(1)  # split exchange time
        tdat[6] = self.pnm.pc.vtransfer_time(2)  # reduced tree computation time
        tdat[4] -= tdat[6]
        return tdat

    @property
    def gidvec(self):
        return self.cellDistributor.getGidListForProcessor()


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

    logging.info("\nsimulation finished. Gather spikes then clean up.")
    node.spike2file("out.dat")
    node.cleanup()
