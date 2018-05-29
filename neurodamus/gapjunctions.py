from __future__ import absolute_import
import logging
from os import path
from .core import Neuron
from .utils import ArrayCompat
from collections import defaultdict


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
    # objref self._synapse_reader, self._target_manager, self._connections, self._syn_params, this
    # objref self._circuit_target, self._gj_offsets

    # -----------------------------------------------------------------------------------------------
    # Public members
    # -----------------------------------------------------------------------------------------------
    # # Indicate if BlueConfig connection blocks create new synapses/connections, or just override values of existing ones
    # public updateCond # Oren
    # public creationMode
    # public init, connectAll, groupConnect, finalizeSynapses, replay, groupDelayedWeightAdjust, openSynapseFile, finalizeGapJunctions

    def  __init__(self, circuit_path, target_manager, n_synapse_files, circuit_target=None):
        """Constructor for GapJunctionManager, checks that the nrn.h5 synapse file is available for reading
        
        Args:
            circuit_path: Circuit path (note that 'ncsStructural_gp2/nrn.h5' is added by this function.
            target_manager: The TargetManager which will be used to query targets and translate locations to points
            n_synapse_files: How many nrn.h5 files to expect (typically 1)
            circuit_target: (optional) Used to know if a given gid is being simulated, including off node.
                            Default: full circuit
        """
        # localtimeID, gjSum  # localobj gjinfoFile
        # strdef synapseFile, sModeStr, gjfname

        # TODO: this should be a different name?
        synapse_file = path.join(circuit_path, "nrn_gj.h5")
        self._target_manager = target_manager
        self._circuit_target = circuit_target
        self._n_synapse_files = n_synapse_files
        self._syn_params = {}
        # Connections indexed by post-gid, then ordered by pre-gid
        self._connections = defaultdict(list)
        self.creationMode = 1

        timeID = Neuron.h.timeit_register( "file read" )
        Neuron.h.timeit_start(timeID)
        self._synapse_reader = Neuron.h.HDF5Reader(synapse_file, n_synapse_files)
        Neuron.h.timeit_add(timeID)

        if n_synapse_files > 1:
            timeID = Neuron.h.timeit_register( "syn exchange" )
            Neuron.h.timeit_start(timeID)
            self._synapse_reader.exchangeSynapseLocations(self._target_manager.cellDistributor.getGidListForProcessor())
            Neuron.h.timeit_add(timeID)

        # TODO: we should not use this offset map for gap junctions in the long term.
        # Note: assumes that gids of circuit are contiguous
        self._gj_offsets = ArrayCompat("d")
        gjfname = path.join(circuit_path, "gjinfo.txt")
        gj_sum = 0

        for line in open(gjfname):
            gid, offset = line.strip().split()
            self._gj_offsets.append(gj_sum)  # rem - fist gid has no offset.  the final total is not used as an offset at all.
            gj_sum += 2*offset

    # -
    def connectAll(self, gidvec, scaling_factor=1):
        """For every gid access its synapse parameters and instantiate all synapses.
        Args:
            gidvec: The array of local gids
            scaling_factor: (Optional) factor to scale all synapse / neetcon weights
        """
        # localscaling_factor, cellIndex, sgid, tgid
        # localobj gidvec, synParamsList, activeParams, activeConnection, nilConfig

        # printf( "iterate %d cells\n", gidvec.size() )
        for tgid in gidvec:
            synapses_params = self.loadSynapseParameters(tgid)
            cur_conn = None

            logging.debug("focus post a%d - %d items\n", tgid, len(synapses_params))
            for i, syn_params in enumerate(synapses_params):
                sgid = syn_params.sgid
                logging.debug("connect pre a%d to post a%d\n", sgid, tgid)
                if self._circuit_target and not self._circuit_target.completeContains(sgid):
                    continue
                    # should still need to check that the other side of the gap junction will be there by ensuring
                    # that other gid is in the circuit target

                # Note: The sgids in any given dataset from nrn.h5 will come in sorted order, low to high.
                # This code therefore doesn't search or sort on its own.  If the nrn.h5 file changes in the future,
                # we must update the code accordingly
                if cur_conn is None or cur_conn.tgid != tgid or cur_conn.sgid != sgid:
                    cur_conn = Neuron.h.Connection(sgid, tgid, Neuron.h.nil, "STDPoff", 0)
                    cur_conn.setWeightScalar(scaling_factor)
                    self.storeConnection(cur_conn)

                # placeSynapses( activeConnection, synParamsList.o(synIndex), synIndex+1 )
                point = self._target_manager.locationToPoint(tgid, active_params.isec,
                                                             active_params.ipt, active_params.offset)
                cur_conn.append(point, syn_params, i)


    # # !
    # # Given some gidlists, connect those gids in the source list to those in the dest list (note
    # # the cells in the source list are not limited by what is on this cpu, whereas the dest list requires
    # # the cells be local)
    # # @param $s1 Name of Source Target
    # # @param $s2 Name of Destination Target
    # # @param $3  Scaling weight to apply to the synapses
    # # @param $o4 SynapseConfiguration string, or nil
    # # @param $o5 Vector of gids on the local cpu
    # def  groupConnect():  # localweight, cellIndex, gid, synIndex, oldsgid, sgid, tgid \
    #     # localobj sTarget, dTarget, gidvec, synParamsList, activeParams, pendConn, existingConn, configuration, nil
    #
    #     # unlike connectAll, we must look through self._connections to see if sgid->tgid exists because it may be getting weights updated
    #     # Note that it is better to get the whole target over just the gid vector, since then we can use utility functions like 'contains'
    #     sTarget = self._target_manager.getTarget( $s1 )
    #     dTarget = self._target_manager.getTarget( $s2 )
    #
    #     weight = $3
    #     configuration = $o4
    #
    #     gidvec = $o5
    #     for cellIndex=0, gidvec.size()-1:
    #         tgid = gidvec.x[cellIndex]
    #         if !dTarget.contains( tgid ):
    #             continue
    #         #}
    #
    #         # this cpu owns some or all of the destination gid
    #         synParamsList = loadSynapseParameters( gidvec.x[cellIndex] )
    #
    #         oldsgid = -1
    #         pendConn = nil
    #         for synIndex=0, synParamsList.count()-1:
    #             sgid = synParamsList.o(synIndex).sgid
    #
    #             # if this gid in the source target?
    #             if !sTarget.completeContains( sgid ):
    #                 continue
    #             #}
    #
    #             # is this gid in the self._circuit_target (if defined)
    #             if object_id(self._circuit_target, 1) != -1 and !self._circuit_target.completeContains( sgid ):
    #                 continue
    #             #}
    #
    #             # to reach here, 'source' target includes a cell that sends to the tgid and sgid should exist somewhere in the
    #             # simulation - on or off node.  Don't care
    #
    #             # are we on a different sgid than the previous iteration?
    #             if sgid != oldsgid:
    #                 if pendConn != nil: # if we were putting things in a pending object, we can store that away now
    #                     storeConnection( pendConn )
    #                 #}
    #
    #                 oldsgid = sgid
    #
    #                 # determine what we will do with the new sgid: update weights if seen before, or prep for pending connections
    #                 existingConn = findConnection( sgid, tgid )
    #                 if object_id(existingConn, 1) != -1:
    #                     # since we have seen this pathway/connection before, we just need to update the weights
    #                     if weight != -1:
    #                         existingConn.setWeightScalar( weight )
    #                     #}
    #                     existingConn.appendSynapseConfiguration( configuration )
    #                     pendConn = nil
    #                 else:
    #                     if creationMode == 1:
    #                         # recently added the feature where weight is optional.  But what should happen if the initial group
    #                         # connect is given -1?  I would think is is an error.  For now, emit a warning
    #                         if weight == -1:
    #                             print "Warning: invalid weight value for initial connection creation"
    #                         #}
    #                         pendConn = new Connection( sgid, tgid, configuration, nil, 0, nil )
    #                         pendConn.setWeightScalar( weight )
    #                     #}
    #                     existingConn = nil  # should already be nil, but that's okay
    #                 #}
    #             #}
    #
    #             # if we are using an object for a pending connection, then it is new and requires we place the synapse(s) for the current index
    #             if object_id(pendConn,1) != -1:
    #                 activeParams = synParamsList.o(synIndex)
    #                 pendConn.append( self._target_manager.locationToPoint( tgid, activeParams.isec, activeParams.ipt, activeParams.offset ), activeParams, synIndex )
    #             #}
    #         #}
    #
    #         # if we have a pending connection, make sure we store it
    #         if object_id(pendConn,1) != -1:
    #             storeConnection(pendConn)
    #         #}
    #     #}
    # #}

    # # -----------------------------------------------------------------------------------------------
    #
    # # !
    # # Given some gidlists, recover the connection objects for those gids involved and adjust the weights
    # # @param $s1 Name of Source Target
    # # @param $s2 Name of Destination Target
    # # @param $3 Scaling weight to apply to the synapses
    # # @param $o4 Vector of gids on the local cpu
    # def  groupDelayedWeightAdjust(): # localweight, cellIndex, gid, synIndex, oldsgid, sgid, tgid \
    #     # localobj sTarget, dTarget, gidvec, synParamsList, activeParams, pendConn, existingConn, sgids, nil
    #
    #     # unlike connectAll, we must look through self._connections to see if sgid->tgid exists because it may be getting weights updated
    #     # Note that it is better to get the whole target over just the gid vector, since then we can use utility functions like 'contains'
    #     sTarget = self._target_manager.getTarget( $s1 )
    #     dTarget = self._target_manager.getTarget( $s2 )
    #     weight = $3
    #
    #     gidvec = $o4
    #     for cellIndex=0, gidvec.size()-1:
    #         # gid on local should be member of destination target
    #         tgid = gidvec.x[cellIndex]
    #         if !dTarget.contains( tgid ):
    #             continue
    #         #}
    #
    #         # is it better to iterate over the cell's presyn gids or the target's gids.  Probably the former, but this is easier.  Can change later
    #         sgids = sTarget.completegids()
    #         for sgidIndex=0,sgids.size()-1:
    #             sgid = sgids.x[sgidIndex]
    #             existingConn = findConnection( sgid, tgid )
    #             if object_id(existingConn, 1) != -1:
    #                 # change the weight for all those netcons
    #                 existingConn.updateWeights( weight )
    #             #}
    #         #}
    #     #}
    # #}
    #
    # # -----------------------------------------------------------------------------------------------
    #
    # # !
    # # Go through list of created connections and see if any match the pathway sgid->tgid
    # # @param $1 sgid Source/Presynaptic cell
    # # @param $2 tgid Destination/Postsynaptic cell
    # # @return Reference to existing Connection object or nil if it is the first time the pathway exists
    # def findConnection():  # localconnIndex, key  # localobj nil, innerList
    #
    #     key = $2
    #     # if self._target_manager.cellDistributor.pnm.myid == 0:
    #     #     print "find ", $2, "->", $1, " amongst ", self._connections.count(), "items"
    #     #}
    #
    #     # search through list, using binary search to find if this target exists
    #     binsrch_low = 0
    #     binsrch_high = self._connections.count()
    #
    #     while binsrch_low < binsrch_high:
    #         binsrch_mid = int(( binsrch_low+binsrch_high)*0.5 )
    #
    #         #if self._target_manager.cellDistributor.pnm.myid == 0:
    #         #    print key, " vs ", self._connections.o(binsrch_mid).o(0).tgid
    #
    #         if key < self._connections.o(binsrch_mid).o(0).tgid: # guess again, lower
    #             binsrch_low = binsrch_mid+1
    #         else:
    #             binsrch_high = binsrch_mid
    #         #}
    #
    #         # if self._target_manager.cellDistributor.pnm.myid == 0:
    #         #     print "new range: ", binsrch_low, "..", binsrch_high
    #     #}
    #
    #     if binsrch_low<self._connections.count():
    #         if self._connections.o(binsrch_low).o(0).tgid == key:
    #             # found it!
    #             innerList = self._connections.o(binsrch_low)
    #         else:
    #             # no inner list for this sgid, so we can return nil
    #             return nil
    #         #}
    #     else:  # not found, return nil
    #         return nil
    #     #}
    #
    #     # if we reach here, then we have found a pre-existing inner list that we now must search
    #     binsrch_low = 0
    #     binsrch_high = innerList.count()
    #     key = $1
    #
    #     while binsrch_low < binsrch_high:
    #         binsrch_mid = int(( binsrch_low+binsrch_high)*0.5 )
    #
    #         if key < innerList.o(binsrch_mid).sgid: # guess again, lower
    #             binsrch_low = binsrch_mid+1
    #         else:
    #             binsrch_high = binsrch_mid
    #         #}
    #     #}
    #
    #     if binsrch_low<innerList.count() ) and ( innerList.o(binsrch_low).sgid == key:  # found
    #         return innerList.o(binsrch_low)
    #     #}
    #
    #     return nil
    # #}


    #
    def storeConnection(self, conn):
        """When we have created a new connection (sgid->tgid), determine where to store it in our arrangement
        and store it for faster retrieval later

        Args:
            conn: The connection object to be stored
        """
        # local binsrch_low, binsrch_mid, binsrch_high, key, innerList
        logging.debug("store %d -> %d amongst %d items", conn.tgid, conn.sgid, " amongst ", len(self._connections))

        cell_conns = self._connections[conn.tgid]
        if len(cell_conns) == 0:
            cell_conns.append(conn)
            return

        # if we reach here, then we have found a pre-existing inner list that we now must search
        binsrch_low = 0
        binsrch_high = len(cell_conns)
        key = conn.sgid

        while binsrch_low < binsrch_high:
            binsrch_mid = int(( binsrch_low+binsrch_high)*0.5 )
            if key < cell_conns[binsrch_mid].sgid:
                binsrch_low = binsrch_mid+1
            else:
                binsrch_high = binsrch_mid

        if binsrch_low < len(cell_conns):
            if cell_conns[binsrch_low].sgid == key:
                logging.warning("Attempting to store a connection twice: %d->%d", conn.sgid, conn.tgid)
            else:
                # put Connection obj here
                cell_conns.insert(binsrch_low, conn)
        else:
            # append Connection obj to end list
            cell_conns.append(conn)

    # -
    def _iter_synapses(self):
        for conns in self._connections.values():
            for conn in conns:
                n_synapses = int(conn.count())
                for i in range(n_synapses):
                    yield conn, conn.o[i]

    # -
    def finalizeGapJunctions(self):
        """All GapJunctions should be placed, all weight scalars should have their final values.
        Now we can create the netcons
        # local innerIndex, connIndex, spgid, baseSeed, cell, connectObj, pc
        """
        for conn, synapse in self._iter_synapses():
            cell = self._target_manager.cellDistributor.getCell(conn.tgid)
            synapse.finalizeGapJunctions(self._target_manager.cellDistributor.pnm, cell,
                                         self._gj_offsets[conn.tgid-1], self._gj_offsets[conn.sgid-1])

    # -
    def updateConductance(self, new_conductance):
        for _, synapse in self._iter_synapses():
            synapse.updateConductance(new_conductance)

    # -
    def loadSynapseParameters(self, gid):
        # localgid, ret, nrow, synIndex, synParamsList, activeSynParams, tmpParams, cellName
        """Access the specified dataset from the nrn.h5 file to get all synapse parameters for a post-synaptic cell

        Args:
            gid: The gid of the cell whose parameters are required

        Returns: A list containing the parameters (SynapseParameters objects) of each synapse
        """
        if gid in self._syn_params:
            return self._syn_params[gid]  # Cached

        self._syn_params[gid] = syn_params_list = []
        params = [0]*11
        cell_name = "a%d" % gid

        if self._n_synapse_files > 1:
            ret = self._synapse_reader.loadData(gid)
        else:
            ret = self._synapse_reader.loadData(cell_name)

        if ret < 0:
            logging.warning("No synapses for %s. Skipping", cell_name)
            return []

        nrow = int(self._synapse_reader.numberofrows(cell_name))

        for i in range(nrow):
            params[0] = self._synapse_reader.getData(cell_name, i, 0)   # sgid
            params[1] = self._synapse_reader.getData(cell_name, i, 1)   # delay
            params[2] = self._synapse_reader.getData(cell_name, i, 2)   # isec
            params[3] = self._synapse_reader.getData(cell_name, i, 3)   # ipt
            params[4] = self._synapse_reader.getData(cell_name, i, 4)   # offset
            params[5] = self._synapse_reader.getData(cell_name, i, 8)   # weight
            params[6] = self._synapse_reader.getData(cell_name, i, 9)   # U
            params[7] = self._synapse_reader.getData(cell_name, i, 10)  # D
            params[8] = self._synapse_reader.getData(cell_name, i, 11)  # F
            params[9] = self._synapse_reader.getData(cell_name, i, 12)  # DTC
            params[10] = self._synapse_reader.getData(cell_name, i, 13)  # isynType
            # compensate for minor floating point inaccuracies in the delay
            dt = Neuron.h.dt
            params[1] = int(params[1]/dt + 1e-5)*dt

            syn_params_list.append(Neuron.h.SynapseParameters(params))

        return syn_params_list
