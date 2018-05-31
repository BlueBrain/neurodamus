from __future__ import absolute_import
import logging
from collections import defaultdict
from itertools import chain
from os import path
from .core import Neuron
from .utils import ArrayCompat, bin_search
from .connection import SynapseParameters, Connection, SYNAPSE_MODE, STDP_MODE


class _ConnectionManagerBase(object):
    """
    An abstract base class common to Synaptic connections and GapJunctions
    """
    DATA_FILENAME = "nrn.h5"
    # Synapses dont require circuit_target but GapJunctions do
    # so the generic insertion validates against target.sgid if defined
    _circuit_target = None
    # Connection parameters which might not be used by all Managers
    _synapse_mode = SYNAPSE_MODE.default

    def __init__(self, circuit_path, target_manager, n_synapse_files):
        self._target_manager = target_manager
        self._n_synapse_files = n_synapse_files
        # The map of the parameters (original name: loadedMap)
        self._syn_params = {}
        # Connections indexed by post-gid, then ordered by pre-gid
        self._connections = defaultdict(list)
        self.creationMode = 1

        synapse_file = path.join(circuit_path, self.DATA_FILENAME)
        self._synapse_reader = self._init_synapse_reader(
            target_manager, synapse_file, n_synapse_files)

    @staticmethod
    def _init_synapse_reader(target_manager, synapse_file, n_synapse_files):
        time_id = Neuron.h.timeit_register("file read")
        Neuron.h.timeit_start(time_id)
        _syn_reader = Neuron.h.HDF5Reader(synapse_file, n_synapse_files)
        Neuron.h.timeit_add(time_id)

        if n_synapse_files > 1:
            timeID = Neuron.h.timeit_register("syn exchange")
            Neuron.h.timeit_start(timeID)
            _syn_reader.exchangeSynapseLocations(
                target_manager.cellDistributor.getGidListForProcessor())
            Neuron.h.timeit_add(timeID)
        return _syn_reader

    # -
    def connectAll(self, gidvec, weight_factor=1):
        """For every gid access its synapse parameters and instantiate all synapses.

        Args:
            gidvec: The array of local gids
            weight: (Optional) factor to scale all synapse / neetcon weights
        """
        logging.debug("iterate %d cells", len(gidvec))
        for tgid in gidvec:
            synapses_params = self.loadSynapseParameters(tgid)
            cur_conn = None

            logging.debug("connecting to post neuron a%d - %d items", tgid, len(synapses_params))
            for i, syn_params in enumerate(synapses_params):
                sgid = syn_params.sgid
                logging.debug("connect pre a%d to post a%d", sgid, tgid)
                if self._circuit_target and not self._circuit_target.completeContains(sgid):
                    continue
                # should still need to check that the other side of the gap junction will
                # be there by ensuring that other gid is in the circuit target
                # Note: The sgids in any given dataset from nrn.h5 will come in sorted order,
                # low to high. This code therefore doesn't search or sort on its own.
                # If the nrn.h5 file changes in the future we must update the code accordingly
                if cur_conn is None or cur_conn.sgid != sgid:
                    cur_conn = Connection(sgid, tgid, None, "STDPoff", 0, self._synapse_mode,
                                          weight_factor)
                    self.storeConnection(cur_conn)

                # placeSynapses( activeConnection, synParamsList.o(synIndex), synIndex+1 )
                point = self._target_manager.locationToPoint(tgid, syn_params.isec,
                                                             syn_params.ipt, syn_params.offset)
                cur_conn.append(point, syn_params, i)


    # -
    def groupConnect(self, src_target, dst_target, gidvec, weight=None, configuration=None,
                     stdp_mode="STDPoff",
                     spont_mini_rate=0, synapse_type_id_restrict=None):
        """ Given some gidlists, connect those gids in the source list to those in the dest list
            Note: the cells in the source list are not limited by what is on this cpu whereas
            the dest list requires the cells be local

        Args:
            src_target: Name of Source Target
            dst_target: Name of Destination Target
            gidvec: Vector of gids on the local cpu
            weight: (optional) Scaling weight to apply to the synapses
            configuration: (optional) SynapseConfiguration string
            stdp_mode: (optional) Which STDP to use (Default: STDPoff)
            spont_mini_rate: (optional) For spontaneous minis trigger rate (default: 0)
            synapse_type_id_restrict: (optional) to further restrict when the weight is applied
        """
        # unlike connectAll, we must look through self._connections to see if sgid->tgid exists
        # because it may be getting weights updated.
        # Note: it is better to get the whole target over just the gid vector since then we can use
        # utility functions like 'contains'
        src_target = self._target_manager.getTarget(src_target)
        dst_target = self._target_manager.getTarget(dst_target)
        stdp = STDP_MODE.from_str(stdp_mode)

        for tgid in gidvec:
            if not dst_target.contains(tgid):  # if tgid not in dst_target:
                continue

            # this cpu owns some or all of the destination gid
            syns_params = self.loadSynapseParameters(tgid)

            old_sgid = -1
            pend_conn = None
            for i, syn_params in enumerate(syns_params):
                sgid = int(syn_params.sgid)

                # if this gid in the source target?
                if not src_target.completeContains(sgid):
                    continue

                # is this gid in the self._circuit_target (if defined)
                if self._circuit_target is not None and self._circuit_target.completeContains(sgid):
                    continue

                # to reach here, 'source' target includes a cell that sends to the tgid and sgid
                # should exist somewhere in the simulation - on or off node.  Don't care

                # are we on a different sgid than the previous iteration?
                if sgid != old_sgid:
                    # if we were putting things in a pending object, we can store that away now
                    if pend_conn is not None:
                        self.storeConnection(pend_conn)
                    old_sgid = sgid

                    # determine what we will do with the new sgid:
                    # update weights if seen before, or prep for pending connections
                    existing_conn = self.findConnection(sgid, tgid)
                    if existing_conn is not None:
                        # Known pathway/connection -> just update the weights
                        if weight is not None:
                            existing_conn.setWeightScalar(weight)
                            existing_conn.appendSynapseConfiguration(configuration)
                        pend_conn = None
                    else:
                        if self.creationMode == 1:
                            # What should happen if the initial group connect is given -1?
                            # I would think is is an error.  For now, emit a warning
                            if weight is None:
                                logging.warning("Invalid weight value for initial connection "
                                                "creation")
                            pend_conn = Connection(sgid, tgid, configuration, stdp,spont_mini_rate,
                                                   self._synapse_mode)

                # if we are using an object for a pending connection, then it is new
                # and requires we place the synapse(s) for the current index
                if pend_conn is not None:
                    point = self._target_manager.locationToPoint(tgid, syn_params.isec,
                                                                 syn_params.ipt, syn_params.offset)
                    pend_conn.append(point, syn_params, i)

            # if we have a pending connection, make sure we store it
            if pend_conn is not None:
                self.storeConnection(pend_conn)



    # -
    def loadSynapseParameters(self, gid):
        """Access the specified dataset from the nrn.h5 file to get all synapse parameters for
        a post-synaptic cell

        Args:
            gid: The gid of the cell whose parameters are required

        Returns: A list containing the parameters (SynapseParameters objects) of each synapse
        """
        if gid in self._syn_params:
            return self._syn_params[gid]  # Cached

        cell_name = "a%d" % gid
        if self._n_synapse_files > 1:
            ret = self._synapse_reader.loadData(gid)
        else:
            ret = self._synapse_reader.loadData(cell_name)

        if ret < 0:
            logging.warning("No synapses for %s. Skipping", cell_name)
            return []

        dt = Neuron.h.dt
        reader = self._synapse_reader
        nrn_version = reader.checkVersion()
        nrow = int(reader.numberofrows(cell_name))
        conn_syn_params = SynapseParameters.create_array(nrow)
        self._syn_params[gid] = conn_syn_params

        for i in range(nrow):
            params = conn_syn_params[i]
            params[0] = reader.getData(cell_name, i, 0)   # sgid
            params[1] = reader.getData(cell_name, i, 1)   # delay
            params[2] = reader.getData(cell_name, i, 2)   # isec
            params[3] = reader.getData(cell_name, i, 3)   # ipt
            params[4] = reader.getData(cell_name, i, 4)   # offset
            params[5] = reader.getData(cell_name, i, 8)   # weight
            params[6] = reader.getData(cell_name, i, 9)   # U
            params[7] = reader.getData(cell_name, i, 10)  # D
            params[8] = reader.getData(cell_name, i, 11)  # F
            params[9] = reader.getData(cell_name, i, 12)  # DTC
            params[10] = reader.getData(cell_name, i, 13)  # isynType
            if nrn_version > 4:
                params[11] = reader.getData(cell_name, i, 17)  # nrrp
            else:
                params[11] = -1
            # compensate for minor floating point inaccuracies in the delay
            params[1] = int(params[1] / dt + 1e-5) * dt

        return conn_syn_params

    # -----------------------------------------------------------------------------
    # THESE METHODS ARE HELPERS FOR HANDLING OBJECTS IN THE INTERNAL STRUCTURES
    # -----------------------------------------------------------------------------
    def _find_connection(self, sgid, tgid, exact=True):
        """Finds a connection, given its source and destination gids.
        Returns: None if it doesnt exist, or (when exact is False) the possible insertion index
        """
        cell_conns = self._connections[tgid]
        if not cell_conns:
            return cell_conns, None
        pos = bin_search(cell_conns, sgid, lambda x: x.sgid)
        if pos == len(cell_conns):
            # Not found and pos index is invalid
            return cell_conns, None
        if exact and cell_conns[pos].sgid != sgid:
            return cell_conns, None
        return cell_conns, pos

    # -
    def findConnection(self, sgid, tgid):
        """Retrieves a connection from the pre and post gids.
        Returns: A connection object if it exists. None otherwise.
        """
        conn_lst, idx = self._find_connection(sgid, tgid)
        if idx is None:
            return None
        return conn_lst[idx]

    # -
    def storeConnection(self, conn):
        """When we have created a new connection (sgid->tgid), determine where to store it
        in our arrangement and store it for faster retrieval later

        Args:
            conn: The connection object to be stored
        """
        logging.debug("store %d->%d amongst %d items", conn.tgid, conn.sgid,
                      len(self._connections))
        cell_conns, pos = self._find_connection(conn.sgid, conn.tgid, exact=False)
        if pos is not None:
            if cell_conns[pos].sgid == conn.sgid:
                logging.warning("Attempting to store a connection twice: %d->%d",
                                conn.sgid, conn.tgid)
            else:
                cell_conns.insert(pos, conn)
        else:
            cell_conns.append(conn)

    # -
    def _iter_synapses(self):
        """Iterator over all the connections synapses, yielding (conn, synapse) pairs
        """
        for conns in self._connections.values():
            for conn in conns:
                n_synapses = int(conn.count())
                for i in range(n_synapses):
                    yield conn, conn.o[i]

    # -
    def getSynapseDataForGID(self, target_gid):
        conns = self._connections[target_gid]
        return chain.from_iterable(c.synapseParamsList for c in conns)


# ################################################################################################
class SynapseRuleManager(_ConnectionManagerBase):
    """
    The SynapseRuleManager is designed to encapsulate the creation of synapses for BlueBrain
    simulations, handling the data coming from the nrn.h5 file. If the BlueConfig file provides any
    Connection Rules, those override which synapses are created.
    Note that the Connection rules are processed with the assumption that they come in the config
    file from more general to more specific. E.g.: A column->column connection should come before
    layer 4 -> layer 2 which should come before L4PC -> L2PC.
    Once all synapses are preped with final weights, the netcons can be created.
    """

    def __init__(self, circuit_path, target_manager, n_synapse_files, synapse_mode="DualSyns"):
        """ Constructor for SynapseRuleManager, checks that the nrn.h5 synapse file is available
        for reading

        Args:
            circuit_path: Circuit path ('ncsStructural_gp2/nrn.h5' is added by this function)
            target_manager: The TargetManager which will be used to query targets and translate
                locations to points
            n_synapse_files: How many nrn.h5 files to expect (typically 1)
            synapse_mode: str dictating modifiers to what synapses are placed based on synType
                (AmpaOnly vs DualSyns)
        """
        _ConnectionManagerBase.__init__(self, circuit_path, target_manager, n_synapse_files)

        # ! These two vars seem not used
        self._synapse_mode = SYNAPSE_MODE.from_str(synapse_mode)
        #  self._rng_list = []


# ################################################################################################
class GapJunctionManager(_ConnectionManagerBase):
    """
    The GapJunctionManager is similar to the SynapseRuleManager. It will open special nrn.h5 files
    which will have the locations and conductance strengths of gap junctions detected in the
    circuit. The user will have the capacity to scale the conductance weights
    """
    DATA_FILENAME = "nrn_gj.h5"

    # HOC member variables
    # --------------------
    # objref self._synapse_reader, self._target_manager, self._connections, self._syn_params, this
    # objref self._circuit_target, self._gj_offsets

    # Public HOC members
    # ------------------
    # public updateCond # Oren
    # public creationMode
    # public init, connectAll, groupConnect, finalizeSynapses, replay, groupDelayedWeightAdjust,
    # openSynapseFile, finalizeGapJunctions

    def __init__(self, circuit_path, target_manager, n_synapse_files, circuit_target=None):
        """Constructor for GapJunctionManager, checks that the nrn_gj.h5 synapse file is available
        for reading

        Args:
            circuit_path: Circuit path ('ncsStructural_gp2/nrn.h5' is added by this function)
            target_manager: The TargetManager which will be used to query targets and
                translate locations to points
            n_synapse_files: How many nrn.h5 files to expect (typically 1)
            circuit_target: (optional) Used to know if a given gid is being simulated,
                including off node. Default: full circuit
        """
        _ConnectionManagerBase.__init__(self, circuit_path, target_manager, n_synapse_files)

        self._circuit_target = circuit_target
        self._gj_offsets = ArrayCompat("d")
        gjfname = path.join(circuit_path, "gjinfo.txt")
        gj_sum = 0

        for line in open(gjfname):
            gid, offset = line.strip().split()
            self._gj_offsets.append(gj_sum)
            gj_sum += 2 * offset




    # -
    def groupDelayedWeightAdjust(self, src_target, dst_target, weight, gidvec):
        """ Given some gidlists, recover the connection objects for those gids involved and
        adjust the weights.

        Args:
            src_target: Name of Source Target
            dst_target: Name of Destination Target
            weight: Scaling weight to apply to the synapses
            gidvec: Vector of gids on the local cpu
        """
        # unlike connectAll, we must look through self._connections to see if sgid->tgid exists
        # because it may be getting weights updated. Note that it is better to get the whole target
        # over just the gid vector, since then we can use utility functions like 'contains'
        src_target = self._target_manager.getTarget(src_target)
        dst_target = self._target_manager.getTarget(dst_target)

        for tgid in gidvec:
            if not dst_target.contains(tgid):
                continue

            # is it better to iterate over the cell's presyn gids or the target's gids.
            sgids = src_target.completegids()
            for sgid in sgids:
                sgid = int(sgid)
                existing_conn = self.findConnection(sgid, tgid)
                if existing_conn is not None:
                    # change the weight for all those netcons
                    existing_conn.updateWeights(weight)


    # -
    def finalizeGapJunctions(self):
        """Creates the netcons for all GapJunctions.
        Connections must have been places and all weight scalars should have their final values.
        """
        for conn, synapse in self._iter_synapses():
            cell = self._target_manager.cellDistributor.getCell(conn.tgid)
            synapse.finalizeGapJunctions(self._target_manager.cellDistributor.pnm, cell,
                                         self._gj_offsets[conn.tgid-1],
                                         self._gj_offsets[conn.sgid-1])

    # -
    def updateConductance(self, new_conductance):
        """Updates all synapses for a certain conductance value.
        """
        for _, synapse in self._iter_synapses():
            synapse.updateConductance(new_conductance)
