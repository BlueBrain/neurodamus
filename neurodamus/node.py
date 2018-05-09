"""
The main Neurodamus entity

Copyright 2018 - Blue Brain Project, EPFL
"""
from __future__ import absolute_import
from os import path
import sys
from mpi4py import MPI
from . import Neuron
import logging
logging.basicConfig(level=logging.DEBUG)

# Override default excepthook so that exceptions terminate all ranks
sys_excepthook = sys.excepthook
def mpi_excepthook(v, t, tb):
    sys_excepthook(v, t, tb)
    MPI.COMM_WORLD.Abort(1)
sys.excepthook = mpi_excepthook

LIB_PATH = path.normpath(path.join(path.abspath(path.dirname(__file__)), "../../lib"))
MOD_LIB = path.join(LIB_PATH, "modlib", "libnrnmech.so")
HOC_LIB = path.join(LIB_PATH, "hoclib", "neurodamus.hoc")

# Initialized h
_h = None


class Node:
    # OBJREF:
    # -------
    # targetManager, targetParser, cellDistributor, configParser, cellList, gidvec, stimList, reportList, gjManager
    # pnm, this, tmpCell, stimManager, elecManager, binReportHelper, synapseRuleManager, connectionWeightDelayList
    #
    # PUBLIC:
    # -------
    # pnm, updateGJcont, dat_
    # init, loadTargets, createCells, createGapJunctions, createSynapses, cleanup, basicStim, prun, clearModel, log, exportLB, enableStimulus, enableReports, enableModifications, readNCS, spike2file
    # computeLB, myid, openConfig, execResult, cellDistributor, configParser, cellList, getSynapseDataForGID, executeNeuronConfigures

    @classmethod
    def init_neuron(cls):
        global _h
        if _h is None:
            _h = Neuron.h
            _h.nrn_load_dll(MOD_LIB)
            _h.load_file(HOC_LIB)

    def __init__(self, recipe):
        self.init_neuron()
        _h.execute("cvode = new CVode()")
        self.pnm = _h.ParallelNetManager(0)
        self.rank = self.pnm.myid
        self.verbose = int(self.rank) == 0
        print("I am node . Verbosity is ".format(self.rank, self.verbose))
        self.configParser = self.openConfig(recipe)
        _h.execute("celsius=34")
        self.execResult = 0
        self.connectionWeightDelayList = _h.List()
        if self.verbose:
            _h.timeit_setVerbose(1)
        # Instance Objects
        self.targetManager = None; self.targetParser = None; self.cellDistributor = None
        self.cellList = None; self.gidvec = None; self.stimList = None; self.reportList = None
        self.stimManager = None; self.elecManager = None; self.binReportHelper = None
        self.synapseRuleManager = None; self.gjManager = None
        self.runtime = 0

    #
    def openConfig(self, recipe):
        configParser = _h.ConfigParser()
        configParser.open(recipe)
        if self.verbose:
            configParser.toggleVerbose()

        # set some basic information
        parsedRun = configParser.parsedRun
        if not _h.object_id(parsedRun):
            raise RuntimeError("No Run block parsed from BlueConfig %s", recipe)

        # Make sure Random Numbers are prepped
        rngInfo = _h.RNGSettings()
        rngInfo.interpret(parsedRun)  # this sets a few global vars in hoc

        _h.tstop = parsedRun.valueOf("Duration")
        _h.dt = parsedRun.valueOf("Dt")
        _h.steps_per_ms = 1.0 / _h.dt
        return configParser

    #
    def computeLB(self):
        runMode = self.configParser.parsedRun.get("RunMode").s
        if runMode == "LoadBalance":
            self.log("LoadBalancing enabled with multisplit capability")
        elif runMode == "WholeCell":
            self.log("Whole Cell balancing enabled")
        else:
            self.log("RunMode  not used for load balancing. Will use Round-Robin distribution"
                     .format(runMode.s))
            return

        # Is there a cpu count override in the BlueConfig?
        if self.configParser.parsedRun.exists("ProspectiveHosts"):
            prospectiveHosts = self.configParser.parsedRun.valueOf("ProspectiveHosts")
        else:
            prospectiveHosts = self.pnm.pc.nhost()

        # determine if we need to regen load balance info, or if it already exists for this config
        # to prevent excessive messages when the file is not there, have rank 0 handle file access
        doGenerate = 0
        cxinfoFileName = "cxinfo_.txt".format(prospectiveHosts)

        if self.rank == 0:
            if path.isfile(cxinfoFileName):
                with open(cxinfoFileName, "r") as cxinfo:
                    cxNrnPath = cxinfo.readline()
                    cxCircuitTarget = cxinfo.readline()
                    cxTargetFile = cxinfo.readline()

                    if cxNrnPath != self.configParser.parsedRun.get("nrnPath").s:
                        self.log("nrnPath has changed")
                        doGenerate = 1

                    # if there is no circuit target, cmp against "---"
                    if self.configParser.parsedRun.exists("CircuitTarget"):
                        if cxCircuitTarget != self.configParser.parsedRun.get("CircuitTarget").s:
                            self.log("CircuitTarget has changed")
                            doGenerate = 1
                        elif cxCircuitTarget == "---":
                            self.log("CircuitTarget has changed")
                            doGenerate = 1
            else:
                self.log("no cxinfo file")
                doGenerate = 1

        # rank 0 broadcasts the fact whether we need to generate loadbalancing data or not
        message = _h.Vector(1, doGenerate)
        self.pnm.pc.broadcast(message, 0)
        doGenerate = message[0]

        # pre-existing load balance info is good. We can reuse it, so return now or quit
        if not doGenerate:
            self.log("Using existing load balancing info")
            if self.pnm.nhost == prospectiveHosts:
                return
            else:
                self.log("Relaunch on a partition of %d cpus (as per ProspectiveHosts)",
                         prospectiveHosts)
                raise RuntimeError("Invalid CPU count. See log")

        self.log("Generating loadbalancing data")
        # Can we use an existing mcomplex.dat?  If mechanisms change, it needs to be regenerated.
        doGenerate = 0
        if self.rank == 0:
            doGenerate = not path.isfile("mcomplex.dat")
        message.x[0] = doGenerate
        self.pnm.pc.broadcast(message, 0)
        doGenerate = message.x[0]

        if doGenerate:
            self.log("generate mcomplex.dat")
            _h.create_mcomplex()
        else:
            self.log("using existing mcomplex.dat")
        loadbal = _h.LoadBalance()
        _h.read_mcomplex(loadbal)

        self.log("instantiate cells Round Robin style")
        self.createCells("RR")
        self.createSynapses()
        self.createGapJunctions()

        # check if we are doing whole cell balancing which requires an override of a key value
        if runMode == "WholeCell":
            self.cellDistributor.msfactor = 1e6

        self.cellDistributor.printLBInfo(loadbal, prospectiveHosts)

        # balancing calculations done, we can save the cxinfo file now for future usage
        if self.rank == 0:
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
        if prospectiveHosts != self.pnm.pc.nhost():
            self.log("Loadbalancing computed for %d cpus.  Relaunch on a partition of that size",
                     prospectiveHosts)
            raise RuntimeError("Invalid CPU count. See log")

        self.log("clearing model")
        self.clearModel()

    #
    def loadTargets(self):
        # use hard-coded locations for now. These should come from the BlueConfig file
        self.targetParser = _h.TargetParser()
        if self.rank == 0:
            self.targetParser.isVerbose = 1

        target_f = path.join(self.configParser.parsedRun.get("nrnPath").s, "start.target")
        self.targetParser.open(target_f)

        if self.configParser.parsedRun.exists("TargetFile"):
            self.targetParser.open(self.configParser.parsedRun.get("TargetFile").s)

    #
    def log(self, msg, *args, **kw):
        if self.verbose:
            level = kw.get("level", logging.INFO)
            logging.log(level, msg, *args)

    #
    def exportLB(self, lb):
        self.cellDistributor.printLBInfo(lb, self.pnm.pc.nhost())

    #
    def readNCS(self, ncs_path):
        # strdef ncsFile, tstr, metype, commentCheck
        self.log("Node::readNCS will soon be deprecated. Investigate CellDistributor "
                 "for gid assignement, metype determination")

        ncsIn = open(path.join(ncs_path, "start.ncs"), "r")

        gids = _h.Vector()
        metypes = _h.List()

        # first lines might be comments.  Check for leading '#' (TODO: more robust parsing)
        line = ""
        for line in ncsIn:
            if line.strip().startswith("#"):
                continue
            else:
                break

        # line should have "Cells x"
        cell, count = line.split()
        cellCount = int(count)

        # sanity check -> did all cpus read the same count?  Use node 0 to confirm
        bvec = _h.Vector()
        if self.rank == 0:
            bvec.append(cellCount)
        else:
            bvec.append(-1)
        self.pnm.pc.broadcast(bvec, 0)
        nErrors = 0
        if bvec[0] != cellCount:
            logging.error("cell count mismatch between nodes. Node 0 has %d vs Node %d with %d",
                          bvec[0], self.rank, cellCount)

        nErrors = self.pnm.pc.allreduce(nErrors, 1)
        if nErrors > 0:
            raise RuntimeError("File read failure, %d errors".format(nErrors))

        ncsIn.readline()  # skip the ''

        for i in range(cellCount):
            line = ncsIn.readline().strip()
            infos = line.split()
            if len(infos) != 5:
                self.log("error in start.ncs format: %s", line)
                break

            gids.append(int(infos[0]))
            metypes.append(infos[1])

        ncsIn.close()
        return gids, metypes

    #
    def createCells(self, runMode=None):
        """
        Instantiate the cells of the network, handling distribution and any load balancing as needed.
        Any targets will be updated to know which cells are local to the cpu
        Args:
            runMode (str): optional argument to override RunMode as "RR" or "LoadBalance"
        """
        if runMode is not None:
            self.log("override RunMode")
            if not self.configParser.parsedRun.exists("RunMode"):
                mode_obj = _h.String("RR")
                self.configParser.parsedRun.put("RunMode", mode_obj)
            else:
                mode_obj = self.configParser.parsedRun.get("RunMode")
            oldMode = mode_obj.s
            mode_obj.s = runMode

        # read start.ncs from the nrnPath
        # nrnPath = configParser.parsedRun.get("nrnPath")
        # readNCS(nrnPath.s, allVec, allME)

        # will LoadBalancing need the pnm during distribution?  maybe not round-robin, but maybe split cell?
        allVec = _h.Vector()
        allME = _h.List()
        self.cellDistributor = _h.CellDistributor(allVec, allME, self.configParser, self.targetParser, self.pnm)

        # instantiate full cells -> should this be in CellDistributor object?  depends on how split cases work
        gidvec = self.cellDistributor.getGidListForProcessor()
        self.cellList = self.cellDistributor.cellList

        self.log("Created %d cells", self.pnm.cells.count())

        # localize targets, give to target manager
        self.targetParser.updateTargets(gidvec)

        # give a TargetManager the TargetParser's completed targetList
        self.targetManager = _h.TargetManager(self.targetParser.targetList, self.cellDistributor)

        # Let the CellDistributor object have any final say in the cell objects
        self.cellDistributor.finalize(self.cellList)
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

            self.synapseRuleManager.creationMode = 1
            # check if we are supposed to disable creation -> i.e. only change weights for existing connections
            if spConnect.exists("CreateMode") and spConnect.get("CreateMode").s == "NoCreate":
                self.synapseRuleManager.creationMode = 0

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

            self.synapseRuleManager.synOverride = None
            if spConnect.exists("ModOverride"):
                # allows a helper object to grab any additional configuration values
                self.synapseRuleManager.synOverride = spConnect

            # print out a message on node 0 if SynapseConfigure option is included just to give user feedback
            synConfig = None
            if spConnect.exists("SynapseConfigure"):
                synConfig = spConnect.get("SynapseConfigure")
                self.log("Pathway %s -> %s: configure with '%s'",
                         connSource, connDestination, spConnect.get("SynapseConfigure").s)

            # finally we have all the options checked and can now invoke the SynapseRuleManager
            if spConnect.exists("SynapseID"):
                self.synapseRuleManager.groupConnect(
                    connSource, connDestination, weight, synConfig, self.cellDistributor.getGidListForProcessor(),
                    useSTDP, spontMiniRate, spConnect.valueOf("SynapseID"))
            else:
                self.synapseRuleManager.groupConnect(
                    connSource, connDestination, weight, synConfig, self.cellDistributor.getGidListForProcessor(),
                    useSTDP, spontMiniRate)

    def createGapJunctions(self):
        # local projIndex localobj, nrnPath, circuitTarget, projection
        if self.configParser.parsedRun.exists("CircuitTarget"):
            circuitTarget = self.targetManager.getTarget(self.configParser.parsedRun.get("CircuitTarget").s)
        else:
            raise Exception("No circuit target")

        for projIndex in range(int(self.configParser.parsedProjections.count())):
            projection = self.configParser.parsedProjections.o(projIndex)

            # check if this Projection block is for gap junctions
            if projection.exists("Type") and projection.get("Type").s == "GapJunction":
                nrnPath = projection.get("Path").s
                self.log(nrnPath)

                # use connectAll for gj_manager
                if self.gjManager is not None:
                    self.log("Error: neurodamus can only support loading one gap junction file."
                             "Skipping loading...",
                             level=logging.WARNING)
                    break

                self.gjManager = _h.GapJunctionManager(nrnPath, self.targetManager, 1, circuitTarget)
                self.gjManager.connectAll(self.cellDistributor.getGidListForProcessor(), 1)

        if self.gjManager is not None:
            self.gjManager.finalizeGapJunctions()

    #
    def updateGJcon(self, GJcon):
        if self.gjManager is not None:
            self.gjManager.updateCond(GJcon)

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
        synMode = None
        if self.configParser.parsedRun.exists("SynapseMode"):
            synMode = self.configParser.parsedRun.get("SynapseMode").s

        # note - with larger scale circuits, we may divide synapses among several files.
        # Need to know how many from the BlueConfig
        # TODO: determine number of synapse files from nrn.h5.0; it has an info dataset where that count is stored
        # TODO: when running on fewer cpus, it is fast to use the single nrn.h5, so prefer that (but how many if 'few'?)
        nSynapseFiles = 1
        if self.configParser.parsedRun.exists("NumSynapseFiles"):
            nSynapseFiles = self.configParser.parsedRun.valueOf("NumSynapseFiles")

        # Even if the user specifies how many synapse files were created by circuit building,
        # check if we have the single nrn.h5 file
        fileTest = _h.Vector()
        if self.rank == 0:
            nrn_filepath = path.join(nrnPath, "nrn.h5")
            if path.isfile(nrn_filepath):
                nSynapseFiles = 1
            fileTest.append(nSynapseFiles)

        self.pnm.pc.broadcast(fileTest, 0)
        nSynapseFiles = fileTest.x[0]

        timeID = _h.timeit_register("Synapse init")
        _h.timeit_start(timeID)
        if synMode is None:
            # use default synMode, DUAL_SYNS at last check
            self.synapseRuleManager = _h.SynapseRuleManager(nrnPath, self.targetManager, nSynapseFiles)
        else:
            self.synapseRuleManager = _h.SynapseRuleManager(nrnPath, self.targetManager, nSynapseFiles, synMode)
        _h.timeit_add(timeID)

        if self.configParser.parsedConnects.count() == 0:
            self.synapseRuleManager.connectAll(self.cellDistributor.getGidListForProcessor(), 1)
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
            self.log("Handle Bonus synapse file")
            # print "Handle Bonus synapse file"
            nSynapseFiles = 1
            if self.configParser.parsedRun.exists("NumBonusFiles"):
                nSynapseFiles = int(self.configParser.parsedRun.valueOf("NumBonusFiles"))
            self.synapseRuleManager.openSynapseFile(self.configParser.parsedRun.get("BonusSynapseFile").s, nSynapseFiles, 0)

            if self.configParser.parsedConnects.count() == 0:
                self.synapseRuleManager.connectAll(self.cellDistributor.getGidListForProcessor())
            else:
                # print "self.configParser.parsedConnects"
                self.interpretConnections()

        # Check for Projection blocks
        if self.configParser.parsedProjections.count() > 0:
            self.log("Handle Projections")

        for projIndex in range(int(self.configParser.parsedProjections.count())):
            nSynapseFiles = 1
            projection = self.configParser.parsedProjections.o(projIndex)
            if projection.exists("NumSynapseFiles"):
                nSynapseFiles = projection.valueOf("NumSynapseFiles")

            # check if this Projection block is for gap junctions
            if projection.exists("Type") and projection.get("Type").s == "GapJunction":
                continue

            nrnPath = self.findProjectionFiles(projection)
            self.synapseRuleManager.openSynapseFile(nrnPath, nSynapseFiles, 0)

            # A 'Source' field is provided that indicates a target name that contains all the gids used by the
            # presynaptic cells of the projection.  However, I don't need that at the moment

            # Go ahead and make all the Projection connections
            self.synapseRuleManager.connectAll(self.cellDistributor.getGidListForProcessor())

            self.interpretConnections()

        # Check if we need to override the base seed for synapse RNGs
        if self.configParser.parsedRun.exists("BaseSeed"):
            self.synapseRuleManager.finalizeSynapses(self.configParser.parsedRun.valueOf("BaseSeed"))
        else:
            self.synapseRuleManager.finalizeSynapses()

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

        self.log("nrnPath: %s", nrnPath)
        return nrnPath

    #
    def clearModel(self):
        """For use with intrinsic load balancing.  After creating and evaluating the network using round robin distribution,
        we want to clear the cells and synapses in order to have a clean slate on which to instantiate the balanced cells.
        Clears appropriate lists and other stored references.
        """
        # local:cellIndex
        self.pnm.pc.gid_clear()
        self.pnm.nclist.remove_all()
        self.pnm.cells.remove_all()

        for cellIndex in range(int(self.cellList.count())):
            self.cellList.o(cellIndex).CellRef.clear()
        self.cellList.remove_all()

        # remove the self.synapseRuleManager to destroy all underlying synapses/connections
        self.synapseRuleManager = None
        self.gjManager = None
        self.connectionWeightDelayList = _h.List()
        # topoself.logy()

        # clear reports
        if self.reportList is not None:
            self.reportList.remove_all()

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
            self.elecManager = _h.ElectrodeManager(elecPath, self.configParser.parsedElectrodes)

        # for each stimulus defined in the config file, request the stimmanager to instantiate
        if self.configParser.parsedRun.exists("BaseSeed"):
            self.stimManager = _h.StimulusManager(self.targetManager, self.elecManager,
                                                  self.configParser.parsedRun.valueOf("BaseSeed"))
        else:
            self.stimManager = _h.StimulusManager(self.targetManager, self.elecManager)

        # print what stims we have
        injRequests = self.configParser.parsedInjects

        # build a dictionary of stims for faster lookup : useful when applying 10k+ stims
        # while we are at it, check if any stims are using extracellular
        hasExtraCellular = 0
        self.log("Build Stim Dictionary")

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

        timeID = _h.timeit_register("Replay init")
        for injIndex in range(int(injRequests.count())):
            targetName = injRequests.o(injIndex).get("Target").s
            stimName = injRequests.o(injIndex).get("Stimulus").s
            stim = stimDict.get(stimName)
            
            # check the pattern for special cases that are handled here.
            if stim.get("Pattern").s == "SynapseReplay": 
                _h.timeit_start(timeID)
                # Note: maybe I should let the StimulusManager have a reference to the SynapseRuleManager.
                # Then I can move all this into that obj. I could then have the self.logic of Delay/Duration added
                # in a more appropriate place (for now, there is no delay/duration handling, but it might be nice
                # to be able to allow only spikes that occur within a given window to be replayed)

                # timeID = timeit_register("Replay init")
                if stim.exists("Delay"):
                    synReplay = _h.SynapseReplay(self.synapseRuleManager, stim.get("SpikeFile").s, 
                                                 stim.valueOf("Delay"), self.rank == 0 )
                else:
                    synReplay = _h.SynapseReplay(self.synapseRuleManager, stim.get("SpikeFile").s, 
                                                 0, self.rank == 0)
                _h.timeit_add(timeID)

                timeID = _h.timeit_register("Replay inject")
                _h.timeit_start(timeID)
                synReplay.replay(targetName)
                _h.timeit_add(timeID)
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
        modificationManager = _h.ModificationManager(self.targetManager)
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
        self.binReportHelper = _h.BinReportHelper(simDt)

        # other useful fields from main Run object
        outputDir = self.configParser.parsedRun.get("OutputRoot").s
        simEnd = self.configParser.parsedRun.valueOf("Duration")

        # confirm outputDir exists and is usable -> use utility.mod
        if self.rank == 0:
            execResult = _h.checkDirectory(outputDir)
            if execResult < 0:
                error = True
                self.log("Error with OutputRoot %s. Terminating", outputDir, level=logging.ERROR)
                raise RuntimeError("Output directory error")
        self.pnm.pc.barrier()

        reportRequests = self.configParser.parsedReports

        self.reportList = _h.List()

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
                report = _h.Report(reportName, type_, reportOn, unit, format, repDt, startTime, endTime, outputDir,
                                   None, scalingOption, iscParam)
            else:
                report = _h.Report(reportName, type_, reportOn, unit, format, repDt, startTime, endTime, outputDir,
                                   self.elecManager.getElectrode(electrodeName), scalingOption, iscParam)

            # Go through the target members, one cell at a time.  We give a cell reference along with the
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
                    self.log("unsupported report type: ", type_, level=logging.WARNING)

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
        self.gidvec = self.cellDistributor.getGidListForProcessor()

        for i in range(int(self.gidvec.size())):
            # only want to collect spikes off cell pieces with the soma (i.e. the real gid)
            if self.cellDistributor.getSpGid(self.gidvec.x[i]) == self.gidvec.x[i]:
                # print "collect spikes for gid ", self.gidvec.x[i]
                self.pnm.spike_record(self.gidvec.x[i])

    #
    def cleanup(self):
        """Have the compute nodes wrap up tasks before exiting
        """
        # local:i   # localobj: outf, memUsage
        # Note - the constructor for MemUsage will do a group communication, so must be instantiated
        # before pc.runworker
        memUsage = _h.MemUsage()

        _h.timeit_init(self.pnm.pc)  #need a parallel context reference before doing final gather of timing data

        # spike2file now coordinates the nodes to write out all spike data in place of gatherspikes
        # it can be called before the cleanup step in init.hoc
        # spike2file("out.dat")

        self.pnm.pc.runworker()
        # don't use the built in gather spikes function as this will overload node 0 with events
        # self.pnm.gatherspikes()
        _h.prtime(self.pnm.pc)
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
        if self.rank == 0:
            f = open(outfile, "w")
            logging.info("Create file %s", outfile)
            f.write("/scatter\n")  # what am I forgetting for this thing?
            for i in range(int(self.pnm.idvec.size())):
                f.write("%.3f\t%d\n" % (self.pnm.spikevec.x[i], self.pnm.idvec.x[i]))
            f.close()

        # Write other nodes' result in order
        for nodeIndex in range(1, int(self.pnm.pc.nhost())):
            self.pnm.pc.barrier()
            if self.rank == nodeIndex:
                f = open(outfile, "a")
                for i in range(int(self.pnm.idvec.size())):
                    f.write("%.3f\t%d\n" %(self.pnm.spikevec.x[i], self.pnm.idvec.x[i]))
                f.close()

    #
    def getSynapseDataForGID(self, gid):
        """ Utility function to help query synaptic data for a given gid
        Args:
            gid: gid whose data we are accessing

        Returns: list with synapse data for the gid
        """
        return self.synapseRuleManager.getSynapseDataForGID(gid)

    #
    def executeNeuronConfigures(self):
        """Iterate over any NeuronConfigure blocks from the BlueConfig.
        These are simple hoc statements that can be executed with minimal substitutions
        """
        # local:configIndex, cellIndex, x, ret  # localobj: activeConfig, message, target, points, sf
        for configIndex in range(int(self.configParser.parsedConfigures.count())):
            activeConfig = self.configParser.parsedConfigures.o(configIndex)

            self.log("Apply configure statement \"%s\" on target %s",
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
                        tstr = tstr.replace("%s", _h.secname(cell=x))
                        tstr = tstr.replace("%g", "%g" % (x,))

                        self.log(tstr, level=logging.DEBUG)

    #
    def prun(self, show_progress=False):
        """ Runs the simulation
        """
        # local:timeID, spike_compress, cacheeffic, forwardSkip, saveDt, flushIndex, delayIndex
        # localobj: progressIndicator, spConnect
        if show_progress:
            progress = _h.ShowProgress(_h.cvode, self.rank)

        self.pnm.pc.setup_transfer()
        spike_compress = 3

        self.pnm.pc.spike_compress(spike_compress, spike_compress != 0, 0)
        # LFP calculation requires WholeCell balancing and extracellular mechanism.
        # This is incompatible with efficient caching atm.
        if self.configParser.parsedRun.exists("ElectrodesPath"):
            _h.cvode.cache_efficient(0)
        else:
            _h.cvode.cache_efficient(1)

        self.want_all_spikes()
        tdat_ = _h.Vector(7)
        self.pnm.pc.set_maxstep(4)
        self.runtime = _h.startsw()
        tdat_.x[0] = self.pnm.pc.wait_time()

        timeID = _h.timeit_register("stdinit")
        _h.timeit_start(timeID)
        _h.stdinit()
        _h.timeit_add(timeID)

        # check for optional argument "ForwardSkip"
        forwardSkip = 0
        if self.configParser.parsedRun.exists("ForwardSkip"):
            forwardSkip = self.configParser.parsedRun.valueOf("ForwardSkip")
        if forwardSkip > 0:
            _h.t = -1e9
            saveDt = _h.dt
            _h.dt = forwardSkip * 0.1
            for flushIndex in range(9):
                _h.fadvance()
            _h.dt = saveDt
            _h.t = 0
            _h.frecord_init()

        # increase timeout by 10x
        self.pnm.pc.timeout(200)

        timeID = _h.timeit_register("psolve")
        _h.timeit_start(timeID)

        # I think I must use continuerun?
        if self.connectionWeightDelayList.count() == 0:
            self.pnm.psolve(_h.tstop)
        else:
            spConnect = self.connectionWeightDelayList.o(0)
            self.log("will stop after %d", spConnect.valueOf("Delay"), level=logging.DEBUG)
            self.pnm.psolve(spConnect.valueOf("Delay"))
            self.synapseRuleManager.applyDelayedConnection(spConnect, self.cellDistributor.getGidListForProcessor())

            # handle any additional delayed blocks
            for delayIndex in range(int(self.connectionWeightDelayList.count())):
                spConnect = self.connectionWeightDelayList.o(delayIndex)
                self.log("will stop again after %d", spConnect.valueOf("Delay"), level=logging.DEBUG)
                self.pnm.psolve(spConnect.valueOf("Delay"))
                self.synapseRuleManager.applyDelayedConnection(spConnect, self.cellDistributor.getGidListForProcessor())

            self.log("run til the end %d", _h.tstop, level=logging.DEBUG)
            self.pnm.psolve(_h.tstop)
            _h.timeit_add(timeID)

        # final flush for reports
        self.binReportHelper.flush()

        tdat_.x[0] = self.pnm.pc.wait_time() - tdat_.x[0]
        self.runtime = _h.startsw() - self.runtime
        tdat_.x[1] = self.pnm.pc.step_time()
        tdat_.x[2] = self.pnm.pc.send_time()
        tdat_.x[3] = self.pnm.pc.vtransfer_time()
        tdat_.x[4] = self.pnm.pc.vtransfer_time(1)  # split exchange time
        tdat_.x[6] = self.pnm.pc.vtransfer_time(2)  # reduced tree computation time
        tdat_.x[4] -= tdat_.x[6]
