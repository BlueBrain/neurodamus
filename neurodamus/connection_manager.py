"""
Main module for handling and instantiating synaptical connections and gap-junctions
"""
from __future__ import absolute_import, print_function
import logging
from itertools import chain
from collections import defaultdict
from os import path as ospath

from .core import NeurodamusCore as Nd
from .core import ProgressBarRank0 as ProgressBar, MPI
from .core.configuration import GlobalConfig, ConfigurationError
from .connection import Connection, SynapseMode
from .synapse_reader import SynapseReader
from .utils import compat, bin_search, OrderedDefaultDict, dict_filter_map
from .utils.logging import log_verbose


class _ConnectionManagerBase(object):
    """
    An abstract base class common to Synaptic connections and GapJunctions
    """

    CIRCUIT_FILENAMES = None
    """The possible circuit filenames specificed in search order"""
    CONNECTIONS_TYPE = None
    """The type of connections subclasses handle"""

    # We declare class variables which might be used in subclass methods
    # Synapses dont require circuit_target but GapJunctions do
    # so the generic insertion validates against target.sgid if defined
    _circuit_target = None
    _synapse_mode = SynapseMode.default
    _local_gids = None

    # -
    def __init__(self, circuit_path, target_manager, cell_distributor, n_synapse_files=None):
        """Base class c-tor for connections (Synapses & Gap-Junctions) manager
        """
        self._target_manager = target_manager
        self._cell_distibutor = cell_distributor

        # Multipopulation support
        self._population_connections = defaultdict(OrderedDefaultDict)
        self._cur_population_ids = None

        # Connections indexed by post-gid, then ordered by pre-gid
        self._connections_map = None  # initialized by select_population
        self._disabled_conns = OrderedDefaultDict()
        self._synapse_reader = None
        self._local_gids = cell_distributor.getGidListForProcessor()

        if ospath.isdir(circuit_path):
            circuit_path = self._find_circuit_file(circuit_path)
        assert ospath.isfile(circuit_path), "Circuit path doesnt contain valid circuit files"

        self.open_synapse_file(circuit_path, n_synapse_files)
        self.__created_conns = 0

        if GlobalConfig.debug_conn:
            logging.info("Debugging activated for cell/conn %s", GlobalConfig.debug_conn)

    # -
    def open_synapse_file(self, synapse_file, n_synapse_files=None, population_id=0):
        """Initializes a reader for Synapses
        """
        logging.info("Opening Synapse file %s", synapse_file)
        self._synapse_reader = SynapseReader.create(
            synapse_file, self.CONNECTIONS_TYPE, self._local_gids, n_synapse_files)
        self.select_populations(population_id, 0)
        self._unlock_all_connections()  # Allow appending synapses from new sources

    # -
    def select_populations(self, src_id, dst_id):
        """Set different populations IDs for different seeding with multiple projections
        """
        if src_id or dst_id:
            log_verbose("  * Appending to population id %d-%d", src_id, dst_id)
        self._cur_population_ids = (src_id, dst_id)
        self._connections_map = self.get_population(src_id, dst_id)

    # -
    def get_population(self, src_id, dst_id=0):
        return self._population_connections[(src_id, dst_id)]

    # -
    def _get_or_create_connection(self, sgid, tgid, *conn_params, **kwargs):
        cur_conn = self.get_connection(sgid, tgid)
        if cur_conn is not None:
            return cur_conn
        cur_conn = Connection(sgid, tgid, *conn_params, **kwargs)
        self.store_connection(cur_conn)  # Store immediately
        self.__created_conns += 1
        return cur_conn

    # -
    def connect_all(self, weight_factor=1):
        """For every gid access its synapse parameters and instantiate all synapses.

        Args:
            gidvec: The array of local gids
            weight_factor: (Optional) factor to scale all netcon weights
        """
        conn_options = {'weight_factor': weight_factor,
                        'synapse_mode': self._synapse_mode}
        _dbg_conn = GlobalConfig.debug_conn
        total_created_conns = 0

        for tgid in ProgressBar.iter(self._local_gids):
            synapses_params = self._synapse_reader.get_synapse_parameters(tgid)
            cur_conn = None
            logging.debug("Connecting post neuron a%d: %d synapses", tgid, len(synapses_params))
            self.__created_conns = 0

            if len(_dbg_conn) == 1 and _dbg_conn[0] == tgid:
                print("[ DEBUG ] -> Tgid={} Params: {}".format(tgid, synapses_params))

            for i, syn_params in enumerate(synapses_params):
                # sgids expected to come sorted
                sgid = int(syn_params.sgid)

                # Only applicable to GAP-Junctions
                if self._circuit_target and not self._circuit_target.completeContains(sgid):
                    continue

                # Do we need to change/create connection? (or append to existing?)
                # When tgid changes cur_conn is also set no None
                if cur_conn is None or cur_conn.sgid != sgid:
                    cur_conn = self._get_or_create_connection(sgid, tgid, *self._cur_population_ids,
                                                              **conn_options)
                # placeSynapses() called from connection.finalize
                # NOTE: Here we dont need to lock since the whole file is consumed at once
                point = self._target_manager.locationToPoint(
                    tgid, syn_params.isec, syn_params.ipt, syn_params.offset)
                cur_conn.add_synapse(point, syn_params, i)

                if _dbg_conn == [tgid, sgid]:
                    print("[ DEBUG ] -> Tgid={} Sgid={} Params: {}".format(tgid, sgid, syn_params))

            if self.__created_conns  > 0:
                total_created_conns += self.__created_conns
                logging.debug("[post-gid %d] 0: Created %d connections",
                              tgid, self.__created_conns)

        return total_created_conns

    # -
    def connect_group(self, src_target_name, dst_target_name, synapse_type_restrict=None):
        src_target = self._target_manager.getTarget(src_target_name)
        dst_target = self._target_manager.getTarget(dst_target_name)
        conn_kwargs = {'synapse_mode': self._synapse_mode}

        _dbg_conn = GlobalConfig.debug_conn
        self.__created_conns = 0
        cur_conn = None

        for tgid in self._local_gids:
            if not dst_target.contains(tgid):
                continue

            # this cpu owns some or all of the destination gid
            syns_params = self._synapse_reader.get_synapse_parameters(tgid)
            prev_sgid = None

            if len(_dbg_conn) == 1 and _dbg_conn[0] == tgid:
                print("[ DEBUG ] -> Tgid={} Params: {}".format(tgid, syns_params))

            for i, syn_params in enumerate(syns_params):
                sgid = int(syn_params.sgid)
                if synapse_type_restrict and syn_params.synType != synapse_type_restrict:
                    continue

                if sgid != prev_sgid:
                    if not src_target.completeContains(sgid):
                        continue
                    prev_sgid = sgid
                    if cur_conn:
                        cur_conn.locked = True

                    cur_conn = self._get_or_create_connection(sgid, tgid, *self._cur_population_ids,
                                                              **conn_kwargs)
                if cur_conn.locked:
                    continue

                point = self._target_manager.locationToPoint(
                    tgid, syn_params.isec, syn_params.ipt, syn_params.offset)
                cur_conn.add_synapse(point, syn_params, i)

        if cur_conn:
            cur_conn.locked = True  # Lock last conn

        return self.__created_conns

    # -
    def _get_target_connections(self, src_target_name, dst_target_name,
                                      gidvec=None, population_id=None):
        src_target = self._target_manager.getTarget(src_target_name)
        dst_target = self._target_manager.getTarget(dst_target_name)
        gidvec = self._local_gids if gidvec is None else gidvec
        if isinstance(population_id, int):
            populations = (self.get_population(population_id),)
        elif isinstance(population_id, tuple):
            populations = (self.get_population(*population_id),)
        elif population_id is None:
            populations = self._population_connections.values()
        else:
            raise ValueError("Invalid population id: %s" % str(population_id))

        for population in populations:
            for tgid in gidvec:
                if not dst_target.contains(tgid) or tgid not in population:
                    continue
                for conn in population[tgid]:
                    sgid = conn.sgid
                    if not src_target.completeContains(sgid):
                        continue
                    yield conn

    # -
    def configure_group(self, conn_config, gidvec=None, population=None):
        """Configure connections according to a BlueConfig Connection block

        Args:
            conn_config: The connection configuration dict
            populations(optional): A tuple of populations' connections. Defaul: all
        """
        src_target = conn_config["Source"]
        dst_target = conn_config["Destination"]
        _properties = {
            "Weight": "weight_factor",
            "SpontMinis": "minis_spont_rate",
        }
        syn_params = dict_filter_map(conn_config, _properties)

        # Load eventual mod override helper
        if "ModOverride" in conn_config:
            logging.info("   => Overriding mod: %s", conn_config["ModOverride"])
            override_helper = conn_config["ModOverride"] + "Helper"
            Nd.load_hoc(override_helper)
            assert hasattr(Nd.h, override_helper), \
                "ModOverride helper doesn't define expected hoc template: " + override_helper

        for conn in self._get_target_connections(src_target, dst_target, gidvec, population):
            for key, val in syn_params.items():
                setattr(conn, key, val)
            if "ModOverride" in conn_config:
                conn.override_mod(conn_config['_hoc'])
            if "SynapseConfigure" in conn_config:
                conn.add_synapse_configuration(conn_config["SynapseConfigure"])

    # -
    def configure_group_delayed(self, conn_config, gidvec=None, population=None):
        """Update existing connections with info from delayed Connections blocks
        """
        self.update_connections(
            conn_config["Source"], conn_config["Destination"], gidvec, population,
            conn_config.get("SynapseConfigure"), conn_config.get("Weight")
        )

    # Live connections update Helpers
    # -------------------------------
    def update_connections(self, src_target, dst_target, gidvec=None, population=None,
                                 syn_configure=None, weight=None, **syn_params):
        """ Given some gidlists, recover the connection objects for those gids involved and
        adjust params.
        NOTE: Keyword arguments override the same-name properties in the provided hoc configuration

        Args:
            src_target: Name of Source Target
            dst_target: Name of Destination Target
            gidvec: (optional) A list of gids to apply configuration. Default: all cells
            configuration: (optional) A hoc configuration str to be executed over synapse objects
            weight: (optional) new weights for the netcons
            **syn_params: Keyword arguments of synapse properties to be changed, e.g. conductance(g)
        """
        if syn_configure is None and weight is None and not syn_params:
            logging.warning("No synpases parameters being updated for Targets %s->%s",
                            src_target, dst_target)
            return
        for conn in self._get_target_connections(src_target, dst_target, gidvec, population):
            if weight is not None:
                conn.update_weights(weight)
            if syn_configure is not None:
                conn.configure_synapses(syn_configure)
            if syn_params:
                conn.update_synpase_parameters(**syn_params)

    # -----------------------------------------------------------------------------
    # THESE METHODS ARE HELPERS FOR HANDLING OBJECTS IN THE INTERNAL STRUCTURES
    # -----------------------------------------------------------------------------
    def _find_connection(self, sgid, tgid, exact=True):
        """Finds a connection, given its source and destination gids.

        Returns:
            tuple: connection list and index. If the element doesnt exist, index depends on the
            exact flag: None if exact=True, otherwise the possible insertion index.
        """
        cell_conns = self._connections_map[tgid]
        pos = 0
        if cell_conns:
            pos = bin_search(cell_conns, sgid, lambda x: x.sgid)
        if exact and (pos == len(cell_conns) or cell_conns[pos].sgid != sgid):
            # Not found
            return cell_conns, None
        return cell_conns, pos

    # -
    def get_connection(self, sgid, tgid):
        """Retrieves a connection from the pre and post gids.

        Returns:
            Connection: A connection object if it exists. None otherwise.
        """
        conn_lst, idx = self._find_connection(sgid, tgid)
        return None if idx is None else conn_lst[idx]

    # -
    def store_connection(self, conn):
        """When we have created a new connection (sgid->tgid), store it in order in
        our structure for faster retrieval later

        Args:
            conn: The connection object to be stored
        """
        cell_conns, pos = self._find_connection(conn.sgid, conn.tgid, exact=False)
        if pos < len(cell_conns) and cell_conns[pos].sgid == conn.sgid:
            logging.error("Attempt to store existing connection: %d->%d", conn.sgid, conn.tgid)
            return
        cell_conns.insert(pos, conn)

    def all_connections(self, conn_map=None):
        """Get an iterator over all the connections.
        """
        conn_map = conn_map or self._connections_map
        return chain.from_iterable(conn_map.values())

    def get_connections(self, target_gid):
        """Get an iterator over all the connections of a target cell.
        """
        return self._connections_map[target_gid]

    def get_synapse_params_gid(self, target_gid):
        """Get an iterator over all the synapse parameters of a target cell connections.
        """
        conns = self._connections_map[target_gid]
        return chain.from_iterable(c.synapse_params for c in conns)

    # -----------------------------------------------------------------------------
    # Delete, Disable / Enable
    # -----------------------------------------------------------------------------
    def delete(self, sgid, tgid):
        """Deletes a connection given source and target gids.

        This action can't be undone. To have the connection again it must be recreated.
        For temporarily ignoring a connection see disable()
        NOTE: Contrary to disable(), deleting a connection will effectively remove them
        from the model, saving computational resources during simulation.
        """
        conn_lst, idx = self._find_connection(sgid, tgid)
        if idx is None:
            logging.warning("Non-existing connection to disable: %d->%d", sgid, tgid)
            return
        del conn_lst[idx]

    def disable(self, sgid, tgid, also_zero_conductance=False):
        """Disable a connection, all of its netcons and optionally synapses.

        Args:
            sgid: The pre-gid of the cell
            tgid: The post-gid of the cell
            also_zero_conductance: (bool) Besides deactivating the netcon, will set synapses'
                conductances to zero. Default: False
        """
        conn_lst, idx = self._find_connection(sgid, tgid)
        if idx is None:
            logging.warning("Non-existing connection to disable: %d->%d", sgid, tgid)
        else:
            c = conn_lst.pop(idx)  # type: Connection
            self._disabled_conns[tgid].append(c)
            c.disable(also_zero_conductance)

    def enable(self, sgid, tgid):
        """(Re)enable a connection
        """
        tgid_conns = self._disabled_conns[tgid]
        for i, c in enumerate(tgid_conns):  # type: Connection
            if c.sgid == sgid:
                self.store_connection(c)
                del tgid_conns[i]
                c.enable()
                break
        else:
            logging.warning("Non-existing connection to enable: %d->%d", sgid, tgid)

    def delete_group(self, post_gids, pre_gids=None):
        """Delete a number of connections given lists of pre and post gids.
           Note: None is neutral and will match all gids.

        Args:
            post_gids: The target gids of the connections to be disabled. None for all
            pre_gids: idem for pre-gids. [Default: None -> all)
        """
        for _, lst, idx in self._find_group_in(self._connections_map, post_gids, pre_gids):
            del lst[idx]

    def disable_group(self, post_gids, pre_gids=None, also_zero_conductance=False):
        """Disable a number of connections given lists of pre and post gids.
        Note: None will match all gids.
              Should be called before Neurodamus.init() for CORENEURON

        Args:
            post_gids: The target gids of the connections to be disabled. None for all
            pre_gids: idem for pre-gids. [Default: None -> all)
            also_zero_conductance: Besides disabling the netcon, sets synapse conductance to 0
        """
        for conn, lst, idx in self._find_group_in(self._connections_map, post_gids, pre_gids):
            self._disabled_conns[conn.tgid].append(lst.pop(idx))
            conn.disable(also_zero_conductance)

    def enable_group(self, post_gids, pre_gids=None):
        """Enable a number of connections given lists of pre and post gids.
        Note: None will match all gids.
        """
        for conn, lst, idx in self._find_group_in(self._disabled_conns, post_gids, pre_gids):
            self.store_connection(lst.pop(idx))
            conn.enable()

    def all_disabled(self):
        return chain.from_iterable(self._disabled_conns.values())

    def get_disabled(self, post_gid):
        return self._disabled_conns[post_gid]

    @staticmethod
    def _find_group_in(conn_map, post_gids, pre_gids=None):
        # type: (dict, list, list) -> []
        for tgid, conns in conn_map.items():
            if post_gids is not None and tgid not in post_gids:
                continue
            for i, c in enumerate(conns):  # type: Connection
                if pre_gids is not None and c.sgid not in pre_gids:
                    continue
                yield c, conns, i

    @classmethod
    def _find_circuit_file(cls, location):
        """Attempts to find a circuit file given any directory or file, and reader"""
        compat_file = cls.CIRCUIT_FILENAMES[-1]  # last is the nrn.h5 format
        files_avail = [f for f in cls.CIRCUIT_FILENAMES
                       if ospath.isfile(ospath.join(location, f))]
        if not files_avail:
            raise ConfigurationError(
                "nrnPath is not a file and could not find any synapse file within.")
        if not SynapseReader.is_syntool_enabled() and compat_file not in files_avail:
            raise ConfigurationError(
                "Found synapse file requires synapsetool, which is not available")
        if len(files_avail) > 1:
            logging.warning("DEPRECATION: Found several synapse file formats in nrnPath. "
                            "Auto-select is deprecated and will be removed")
            if not SynapseReader.is_syntool_enabled():
                files_avail[0] = compat_file
        return ospath.join(location, files_avail[0])

    def _unlock_all_connections(self):
        """Unlock all, mainly when we load a new connectivity source"""
        for conn_map in self._population_connections.values():
            for conns in conn_map.values():
                for conn in conns:
                    conn.locked = False


# ################################################################################################
# SynapseRuleManager
# ################################################################################################
class SynapseRuleManager(_ConnectionManagerBase):
    """
    The SynapseRuleManager is designed to encapsulate the creation of synapses for BlueBrain
    simulations, handling the data coming from the circuit file. If the BlueConfig file provides any
    Connection Rules, those override which synapses are created.

    Note that the Connection rules are processed with the assumption that they come in the config
    file from more general to more specific. E.g.: A column->column connection should come before
    layer 4 -> layer 2 which should come before L4PC -> L2PC.

    Once all synapses are preped with final weights, the netcons can be created.
    """

    CIRCUIT_FILENAMES = ('edges.sonata', 'edges.h5', 'circuit.syn2', 'nrn.h5')
    CONNECTIONS_TYPE = SynapseReader.SYNAPSES

    def __init__(self, circuit_path, target_manager, cell_dist, n_synapse_files, synapse_mode=None):
        """ Constructor for SynapseRuleManager, checks that the nrn.h5 synapse file is available
        for reading

        Args:
            circuit_path: Circuit path, typically a folder with circuit.syn2 or nrn.h5
            target_manager: The TargetManager which will be used to query targets and translate
                locations to points
            n_synapse_files: How many nrn.h5 files to expect (Nrn only, typically 1)
            synapse_mode: str dictating modifiers to what synapses are placed based on synType
                (AmpaOnly vs DualSyns). Default: DualSyns
        """
        _ConnectionManagerBase.__init__(self, circuit_path, target_manager, cell_dist,
                                        n_synapse_files)

        self._synapse_mode = SynapseMode.from_str(synapse_mode) \
            if synapse_mode is not None else SynapseMode.default

        #  self._rng_list = []
        self._replay_list = []

    # -
    def finalize(self, base_seed=0, use_corenrn=False):
        """Create the actual synapses and netcons.
        All weight scalars should have their final values.

        Args:
            base_seed: optional argument to adjust synapse RNGs (default=0)
        """
        logging.info("Instantiating synapses...")
        cell_distributor = self._cell_distibutor
        n_created_conns = 0
        for popid, population in self._population_connections.items():
            for tgid, conns in ProgressBar.iteritems(population, name="Pop:" + str(popid)):
                metype = cell_distributor.getMEType(tgid)
                spgid = cell_distributor.getSpGid(tgid)
                # NOTE: neurodamus hoc keeps connections in reversed order.
                # To exactly replicate results we temporarily finalize conns in reversed order
                for conn in reversed(conns):  # type: Connection
                    conn.finalize(cell_distributor.pnm, metype, base_seed, spgid)
                # logging.debug("Created %d connections on post-gid %d", len(conns), tgid)
                n_created_conns += len(conns)

        # When the simulator is CoreNeuron there is no 'disable' conn state so we dont
        # instantiate. This is ok since there is no chance the user to reenable them later
        if not use_corenrn:
            for tgid, conns in self._disabled_conns.items():
                for conn in reversed(conns):
                    if conn._netcons is not None:
                        continue
                    metype = cell_distributor.getMEType(tgid)
                    spgid = cell_distributor.getSpGid(tgid)
                    conn.finalize(cell_distributor.pnm, metype, base_seed, spgid)
                    conn.disable()
                    n_created_conns += 1

        MPI.check_no_errors()
        all_ranks_total = MPI.allreduce(n_created_conns, MPI.SUM)
        logging.info(" => Created %d connections", all_ranks_total)

    finalizeSynapses = finalize  # compat

    # -
    def replay(self, spike_manager, target_name, start_delay=.0):
        """ After all synapses have been placed, we can create special netcons to trigger
        events on those synapses

        Args:
            target_name: Target name whose gids should be replayed
            spike_manager: map of gids (pre-synaptic) with spike times
            start_delay: Dont deliver events before t=start_delay
        """
        log_verbose("Applying replay map with %d src cells...", len(spike_manager))
        target = self._target_manager.getTarget(target_name)
        replay_count = 0

        for tgid, conns in ProgressBar.iteritems(self._connections_map):
            if not target.contains(tgid):
                continue

            for conn in conns:
                if conn.sgid in spike_manager:
                    replay_count += conn.replay(spike_manager[conn.sgid], start_delay)
                    self._replay_list.append(conn)

        total_replays = MPI.allreduce(replay_count, MPI.SUM)
        if MPI.rank == 0:
            if total_replays == 0:
                logging.warning("No cells were injected replay stimulus")
            else:
                logging.info(" => Replaying total %d stimulus", total_replays)
        return total_replays


# ################################################################################################
# Gap Junctions
# ################################################################################################
class GapJunctionManager(_ConnectionManagerBase):
    """
    The GapJunctionManager is similar to the SynapseRuleManager. It will open special nrn.h5 files
    which will have the locations and conductance strengths of gap junctions detected in the
    circuit. The user will have the capacity to scale the conductance weights
    """

    CIRCUIT_FILENAMES = ("gj.sonata", "gj.syn2", "nrn_gj.h5")
    CONNECTIONS_TYPE = SynapseReader.GAP_JUNCTIONS

    def __init__(self, circuit_path, target_manager, cell_distributor,
                       n_synapse_files=None, circuit_target=None):
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
        _ConnectionManagerBase.__init__(self, circuit_path, target_manager, cell_distributor,
                                              n_synapse_files)
        self._circuit_target = circuit_target

        log_verbose("Computing gap-junction offsets from gjinfo.txt")
        self._gj_offsets = compat.Vector("I")
        gjfname = ospath.join(circuit_path, "gjinfo.txt")
        gj_sum = 0

        for line in open(gjfname):
            gid, offset = map(int, line.strip().split())
            # fist gid has no offset.  the final total is not used as an offset at all.
            self._gj_offsets.append(gj_sum)
            gj_sum += 2 * offset

    # -
    def finalize(self):
        """Creates the netcons for all GapJunctions.
        Connections must have been placed and all weight scalars should have their final values.
        """
        logging.info("Instantiating GapJuntions...")
        cell_distributor = self._cell_distibutor
        n_created_conns = 0

        for tgid, conns in ProgressBar.iteritems(self._connections_map):
            metype = cell_distributor.getMEType(tgid)
            t_gj_offset = self._gj_offsets[tgid-1]
            for conn in reversed(conns):
                conn.finalize_gap_junctions(
                    cell_distributor.pnm, metype, t_gj_offset, self._gj_offsets[conn.sgid-1])
            logging.debug("Created %d gap-junctions on post-gid %d", len(conns), tgid)
            n_created_conns += len(conns)

        all_ranks_total = MPI.allreduce(n_created_conns, MPI.SUM)
        logging.info(" => Created %d Gap-Junctions", all_ranks_total)

    finalizeGapJunctions = finalize  # Compat
