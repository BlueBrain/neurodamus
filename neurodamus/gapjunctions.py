from __future__ import absolute_import
from os import path
from .core import Neuron
from .utils import ArrayCompat

class GapJunctionManager(object):
    """
    The GapJunctionManager is similar to the SynapseRuleManager. It will open special nrn.h5 files which will
    have the locations and conductance strengths of gap junctions detected in the circuit. The user will have the
    capacity to scale the conductance weights
    """

    # external tmeit, prtime, timeit_init, timeit_setVerbose, timeit_register, timeit_start, timeit_add

    # -----------------------------------------------------------------------------------------------
    # Declare member variables
    # -----------------------------------------------------------------------------------------------
    # objref synapseReader, self._target_manager, self._connection_list, self._syn_params, this
    # objref self._circuit_target, self._gj_offsets

    # -----------------------------------------------------------------------------------------------
    # Public members
    # -----------------------------------------------------------------------------------------------
    # # Indicate if BlueConfig connection blocks create new synapses/connections, or just override values of existing ones
    # public updateCond # Oren
    # public creationMode
    # public init, connectAll, groupConnect, finalizeSynapses, replay, groupDelayedWeightAdjust, openSynapseFile, finalizeGapJunctions

    def  __init__(self, circuit_path, target_manager, n_synapse_files, circuit_target):
        """Constructor for GapJunctionManager, checks that the nrn.h5 synapse file is available for reading
        
        Args:
            circuit_path: Circuit path (note that 'ncsStructural_gp2/nrn.h5' is added by this function.
            target_manager: The TargetManager which will be used to query targets and translate locations to points
            n_synapse_files: How many nrn.h5 files to expect (typically 1)
            circuit_target: self._circuit_target Used to know if a given gid is being simulated, 
                            including off node. None if using full circuit
        """
        # localtimeID, gjSum  # localobj gjinfoFile
        # strdef synapseFile, sModeStr, gjfname

        # TODO: this should be a different name?
        synapse_file = path.join(circuit_path, "nrn_gj.h5")
        self._target_manager = target_manager
        self._circuit_target = circuit_target
        self._syn_params = {}
        self._connection_list = []
        self.creationMode = 1

        timeID = Neuron.h.timeit_register( "file read" )
        Neuron.h.timeit_start(timeID)
        synapseReader = Neuron.h.HDF5Reader(synapse_file, n_synapse_files)
        Neuron.h.timeit_add( timeID )

        if n_synapse_files > 1:
            timeID = Neuron.h.timeit_register( "syn exchange" )
            Neuron.h.timeit_start( timeID )
            synapseReader.exchangeSynapseLocations( self._target_manager.cellDistributor.getGidListForProcessor() )
            Neuron.h.timeit_add( timeID )

        # TODO: we should not use this offset map for gap junctions in the long term.
        # Note: assumes that gids of circuit are contiguous
        self._gj_offsets = ArrayCompat("d")
        gjfname = path.join(circuit_path, "gjinfo.txt")
        gj_sum = 0

        for line in open(gjfname):
            gid, offset = line.strip().split()
            self._gj_offsets.append(gj_sum)  # rem - fist gid has no offset.  the final total is not used as an offset at all.
            gj_sum += 2*offset

    # !
    # For everygid in on this node, access its synapse parameters and instantiate all synapses
    # which it receives from (note that the presynatic cells may be off node)
    # @param $o1 Vector with all local gids
    # @param $2 scalar Optional argument to scale all synapse / neetcon weights by the given factor
    def  connectAll(): # localweightScalar, cellIndex, sgid, tgid \
        # localobj gidvec, synParamsList, activeParams, activeConnection, nilConfig

        gidvec = $o1
        weightScalar = 1
        if numarg() > 1:
            weightScalar = $2
        #}

        # printf( "iterate %d cells\n", gidvec.size() )
        for cellIndex=0, gidvec.size()-1 {
            tgid = gidvec.x[cellIndex]
            synParamsList = loadSynapseParameters( tgid )

            # printf( "focus post a%d - %d items\n", gidvec.x[cellIndex], synParamsList.count() )
            for synIndex=0, synParamsList.count()-1 {

                sgid = synParamsList.o(synIndex).sgid
                # printf( "connect pre a%d to post a%d\n", sgid, tgid )
                if object_id( self._circuit_target, 1 ) != -1:
                    if !self._circuit_target.completeContains(sgid):
                        continue
                    #}

                    # should still need to check that the other side of the gap junction will be there by ensuring
                    # that other gid is in the circuit target
                #}

                # Note: The sgids in any given dataset from nrn.h5 will come in sorted order, low to high.
                # This code therefore doesn't search or sort on its own.  If the nrn.h5 file changes in the future,
                # we must update the code accordingly

                if object_id(activeConnection) == 0:
                    activeConnection = new Connection( sgid, tgid, nilConfig, "STDPoff", 0 )
                    activeConnection.setWeightScalar( weightScalar )
                    storeConnection( activeConnection )
                #}

                if activeConnection.tgid!=tgid || activeConnection.sgid != sgid:
                    activeConnection = new Connection( sgid, tgid, nilConfig, "STDPoff", 0 )
                    activeConnection.setWeightScalar( weightScalar )
                    storeConnection( activeConnection )
                #}

                # placeSynapses( activeConnection, synParamsList.o(synIndex), synIndex+1 )
                activeParams = synParamsList.o(synIndex)
                activeConnection.append( self._target_manager.locationToPoint( tgid, activeParams.isec, activeParams.ipt, activeParams.offset ), activeParams, synIndex )
            #}
        #}
    #}

    # -----------------------------------------------------------------------------------------------

    # !
    # Given some gidlists, connect those gids in the source list to those in the dest list (note
    # the cells in the source list are not limited by what is on this cpu, whereas the dest list requires
    # the cells be local)
    # @param $s1 Name of Source Target
    # @param $s2 Name of Destination Target
    # @param $3  Scaling weight to apply to the synapses
    # @param $o4 SynapseConfiguration string, or nil
    # @param $o5 Vector of gids on the local cpu
    def  groupConnect():  # localweight, cellIndex, gid, synIndex, oldsgid, sgid, tgid \
        # localobj sTarget, dTarget, gidvec, synParamsList, activeParams, pendConn, existingConn, configuration, nil

        # unlike connectAll, we must look through self._connection_list to see if sgid->tgid exists because it may be getting weights updated
        # Note that it is better to get the whole target over just the gid vector, since then we can use utility functions like 'contains'
        sTarget = self._target_manager.getTarget( $s1 )
        dTarget = self._target_manager.getTarget( $s2 )

        weight = $3
        configuration = $o4

        gidvec = $o5
        for cellIndex=0, gidvec.size()-1:
            tgid = gidvec.x[cellIndex]
            if !dTarget.contains( tgid ):
                continue
            #}

            # this cpu owns some or all of the destination gid
            synParamsList = loadSynapseParameters( gidvec.x[cellIndex] )

            oldsgid = -1
            pendConn = nil
            for synIndex=0, synParamsList.count()-1:
                sgid = synParamsList.o(synIndex).sgid

                # if this gid in the source target?
                if !sTarget.completeContains( sgid ):
                    continue
                #}

                # is this gid in the self._circuit_target (if defined)
                if object_id(self._circuit_target, 1) != -1 and !self._circuit_target.completeContains( sgid ):
                    continue
                #}

                # to reach here, 'source' target includes a cell that sends to the tgid and sgid should exist somewhere in the
                # simulation - on or off node.  Don't care

                # are we on a different sgid than the previous iteration?
                if sgid != oldsgid:
                    if pendConn != nil: # if we were putting things in a pending object, we can store that away now
                        storeConnection( pendConn )
                    #}

                    oldsgid = sgid

                    # determine what we will do with the new sgid: update weights if seen before, or prep for pending connections
                    existingConn = findConnection( sgid, tgid )
                    if object_id(existingConn, 1) != -1:
                        # since we have seen this pathway/connection before, we just need to update the weights
                        if weight != -1:
                            existingConn.setWeightScalar( weight )
                        #}
                        existingConn.appendSynapseConfiguration( configuration )
                        pendConn = nil
                    else:
                        if creationMode == 1:
                            # recently added the feature where weight is optional.  But what should happen if the initial group
                            # connect is given -1?  I would think is is an error.  For now, emit a warning
                            if weight == -1:
                                print "Warning: invalid weight value for initial connection creation"
                            #}
                            pendConn = new Connection( sgid, tgid, configuration, nil, 0, nil )
                            pendConn.setWeightScalar( weight )
                        #}
                        existingConn = nil  # should already be nil, but that's okay
                    #}
                #}

                # if we are using an object for a pending connection, then it is new and requires we place the synapse(s) for the current index
                if object_id(pendConn,1) != -1:
                    activeParams = synParamsList.o(synIndex)
                    pendConn.append( self._target_manager.locationToPoint( tgid, activeParams.isec, activeParams.ipt, activeParams.offset ), activeParams, synIndex )
                #}
            #}

            # if we have a pending connection, make sure we store it
            if object_id(pendConn,1) != -1:
                storeConnection(pendConn)
            #}
        #}
    #}

    # -----------------------------------------------------------------------------------------------

    # !
    # Given some gidlists, recover the connection objects for those gids involved and adjust the weights
    # @param $s1 Name of Source Target
    # @param $s2 Name of Destination Target
    # @param $3 Scaling weight to apply to the synapses
    # @param $o4 Vector of gids on the local cpu
    def  groupDelayedWeightAdjust(): # localweight, cellIndex, gid, synIndex, oldsgid, sgid, tgid \
        # localobj sTarget, dTarget, gidvec, synParamsList, activeParams, pendConn, existingConn, sgids, nil

        # unlike connectAll, we must look through self._connection_list to see if sgid->tgid exists because it may be getting weights updated
        # Note that it is better to get the whole target over just the gid vector, since then we can use utility functions like 'contains'
        sTarget = self._target_manager.getTarget( $s1 )
        dTarget = self._target_manager.getTarget( $s2 )
        weight = $3

        gidvec = $o4
        for cellIndex=0, gidvec.size()-1:
            # gid on local should be member of destination target
            tgid = gidvec.x[cellIndex]
            if !dTarget.contains( tgid ):
                continue
            #}

            # is it better to iterate over the cell's presyn gids or the target's gids.  Probably the former, but this is easier.  Can change later
            sgids = sTarget.completegids()
            for sgidIndex=0,sgids.size()-1:
                sgid = sgids.x[sgidIndex]
                existingConn = findConnection( sgid, tgid )
                if object_id(existingConn, 1) != -1:
                    # change the weight for all those netcons
                    existingConn.updateWeights( weight )
                #}
            #}
        #}
    #}

    # -----------------------------------------------------------------------------------------------

    # !
    # Go through list of created connections and see if any match the pathway sgid->tgid
    # @param $1 sgid Source/Presynaptic cell
    # @param $2 tgid Destination/Postsynaptic cell
    # @return Reference to existing Connection object or nil if it is the first time the pathway exists
    def findConnection():  # localconnIndex, key  # localobj nil, innerList

        key = $2
        # if self._target_manager.cellDistributor.pnm.myid == 0:
        #     print "find ", $2, "->", $1, " amongst ", self._connection_list.count(), "items"
        #}

        # search through list, using binary search to find if this target exists
        binsrch_low = 0
        binsrch_high = self._connection_list.count()

        while binsrch_low < binsrch_high:
            binsrch_mid = int(( binsrch_low+binsrch_high)*0.5 )

            #if self._target_manager.cellDistributor.pnm.myid == 0:
            #    print key, " vs ", self._connection_list.o(binsrch_mid).o(0).tgid

            if key < self._connection_list.o(binsrch_mid).o(0).tgid: # guess again, lower
                binsrch_low = binsrch_mid+1
            else:
                binsrch_high = binsrch_mid
            #}

            # if self._target_manager.cellDistributor.pnm.myid == 0:
            #     print "new range: ", binsrch_low, "..", binsrch_high
        #}

        if binsrch_low<self._connection_list.count():
            if self._connection_list.o(binsrch_low).o(0).tgid == key:
                # found it!
                innerList = self._connection_list.o(binsrch_low)
            else:
                # no inner list for this sgid, so we can return nil
                return nil
            #}
        else:  # not found, return nil
            return nil
        #}

        # if we reach here, then we have found a pre-existing inner list that we now must search
        binsrch_low = 0
        binsrch_high = innerList.count()
        key = $1

        while binsrch_low < binsrch_high:
            binsrch_mid = int(( binsrch_low+binsrch_high)*0.5 )

            if key < innerList.o(binsrch_mid).sgid: # guess again, lower
                binsrch_low = binsrch_mid+1
            else:
                binsrch_high = binsrch_mid
            #}
        #}

        if binsrch_low<innerList.count() ) and ( innerList.o(binsrch_low).sgid == key:  # found
            return innerList.o(binsrch_low)
        #}

        return nil
    #}

    # -----------------------------------------------------------------------------------------------

    # !
    # When we have created a new connection (sgid->tgid), determine where to store it in our arrangement
    # and store it for faster retrieval later
    # @param $o1 Connection object to be stored in the self._connection_list
    def  storeConnection():  # localbinsrch_low, binsrch_mid, binsrch_high, key  # localobj innerList

        key = $o1.tgid
    #    if self._target_manager.cellDistributor.pnm.myid == 0:
    #        print "store ", $o1.tgid, "->", $o1.sgid, " amongst ", self._connection_list.count(), "items"
    #    #}

        # search through list, using binary search to find if this target exists
        binsrch_low = 0
        binsrch_high = self._connection_list.count()

        while binsrch_low < binsrch_high:
            binsrch_mid = int(( binsrch_low+binsrch_high)*0.5 )

    #        if self._target_manager.cellDistributor.pnm.myid == 0:
    #            print key, " vs ", self._connection_list.o(binsrch_mid).o(0).tgid
    #        #}
            if key < self._connection_list.o(binsrch_mid).o(0).tgid: # guess again, lower
                binsrch_low = binsrch_mid+1
            else:
                binsrch_high = binsrch_mid
            #}
    #        if self._target_manager.cellDistributor.pnm.myid == 0:
    #            print "new range: ", binsrch_low, "..", binsrch_high
    #        #}

        #}

        if binsrch_low<self._connection_list.count():
            if self._connection_list.o(binsrch_low).o(0).tgid == key:
                # found it!
                innerList = self._connection_list.o(binsrch_low)
            else:
                # no inner list, but we can make one and insert it using binsrch_low which is where we expected it

                self._connection_list.insrt( binsrch_low, new List() )
                self._connection_list.o(binsrch_low).append( $o1 )
                return
            #}
        #}
        else: # not found, should be appended to list
            self._connection_list.append( new List() )
            self._connection_list.o(self._connection_list.count()-1).append( $o1 )
            return
        #}

        # if we reach here, then we have found a pre-existing inner list that we now must search
        binsrch_low = 0
        binsrch_high = innerList.count()
        key = $o1.sgid

        while binsrch_low < binsrch_high:
            binsrch_mid = int(( binsrch_low+binsrch_high)*0.5 )

            if key < innerList.o(binsrch_mid).sgid: # guess again, lower
                binsrch_low = binsrch_mid+1
            else:
                binsrch_high = binsrch_mid
            #}
        #}

        if binsrch_low<innerList.count():
            if innerList.o(binsrch_low).sgid == key:
                # error! already exists
                print "Why are we attempting to store a connection (", $o1.sgid, "->", $o1.tgid, ") twice?"
            else:
                # put Connection obj here
                innerList.insrt( binsrch_low, $o1 )
            #}
        else:  # can append Connection obj to end list
            innerList.append( $o1 )
        #}
    #}

    # All GapJunctions should be placed, all weight scalars should have their final values.  Now we can create the netcons
    def  finalizeGapJunctions():  # localinnerIndex, connIndex, spgid, baseSeed  # localobj cell, connectObj, pc
        for connIndex=0, self._connection_list.count()-1:
            for innerIndex=0, self._connection_list.o(connIndex).count()-1:
                connectObj = self._connection_list.o(connIndex).o(innerIndex)
                cell = self._target_manager.cellDistributor.getCell( connectObj.tgid )
                spgid = self._target_manager.cellDistributor.getSpGid( connectObj.tgid )

                connectObj.finalizeGapJunctions( self._target_manager.cellDistributor.pnm, cell, self._gj_offsets.x[connectObj.tgid-1], self._gj_offsets.x[connectObj.sgid-1] )
            #}
        #}

    #}

    # *
    # Helper function to update gap junction conductace
    def  updateCond():  # localinnerIndex, connIndex # localobj connectObj
        for connIndex=0, self._connection_list.count()-1:
            for innerIndex=0, self._connection_list.o(connIndex).count()-1:
                connectObj = self._connection_list.o(connIndex).o(innerIndex)
                connectObj.updateConductance($1)
            #}
        #}
    #}

    # -----------------------------------------------------------------------------------------------

    # !
    # Access the specified dataset from the nrn.h5 file to get all synapse parameters for a post-synaptic cell
    # @param $1 gid of the cell whose data is needed
    # @return $o2 List populated by SynapseParameters objects read from the nrn.h5 file
    def loadSynapseParameters()  # localgid, ret, nrow, synIndex # localobj synParamsList, activeSynParams, tmpParams
        # strdef cellName
        gid = $1

        if self._syn_params.exists(gid):
            return self._syn_params.get(gid)
        #}

        synParamsList = new List()
        tmpParams = new Vector()
        tmpParams.resize(11)

        sprint( cellName, "a%d", $1 )
        if nSynapseFiles > 1:
            ret = synapseReader.loadData($1)
        else:
            ret = synapseReader.loadData(cellName)
        #}

        if ret < 0:
            print "No synapses for ", cellName, ".  Skipping."
            self._syn_params.put( gid, synParamsList )
            return synParamsList
        #}

        nrow = synapseReader.numberofrows(cellName)

        if nrow>0:
            for synIndex=0, nrow-1:

                tmpParams.x[0] = synapseReader.getData( cellName, synIndex, 0 )    # sgid
                tmpParams.x[1] = synapseReader.getData( cellName, synIndex, 1 )    # delay
                tmpParams.x[2] = synapseReader.getData( cellName, synIndex, 2 )    # isec
                tmpParams.x[3] = synapseReader.getData( cellName, synIndex, 3 )    # ipt
                tmpParams.x[4] = synapseReader.getData( cellName, synIndex, 4 )    # offset
                tmpParams.x[5] = synapseReader.getData( cellName, synIndex, 8 )    # weight
                tmpParams.x[6] = synapseReader.getData( cellName, synIndex, 9 )    # U
                tmpParams.x[7] = synapseReader.getData( cellName, synIndex, 10 )   # D
                tmpParams.x[8] = synapseReader.getData( cellName, synIndex, 11 )   # F
                tmpParams.x[9] = synapseReader.getData( cellName, synIndex, 12 )   # DTC
                tmpParams.x[10] = synapseReader.getData( cellName, synIndex, 13 )  # isynType

                # compensate for minor floating point inaccuracies in the delay
                tmpParams.x[1] = int(tmpParams.x[1]/dt + 1e-5)*dt

                activeSynParams = new SynapseParameters( tmpParams )
                synParamsList.append(activeSynParams)
            #}
        #}

        self._syn_params.put( gid, synParamsList )

        return synParamsList
    #}
