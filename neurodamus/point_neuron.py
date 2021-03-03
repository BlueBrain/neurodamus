"""
Module which defines and handles Point Neurons
"""

import logging
import numpy as np
from os import path as ospath

from .cell_distributor import CellManagerBase
from .connection_manager import SynapseRuleManager, ConnectionSet
from .io.cell_readers import TargetSpec, split_round_robin
from .core import EngineBase
from .core.configuration import GlobalConfig
from .connection import ConnectionBase
from .core import NeurodamusCore as Nd
from .core import ProgressBarRank0 as ProgressBar, MPI
from .metype import BaseCell
from .utils import compat
from .utils.logging import log_verbose, log_all
from .utils.timeit import timeit


class PointCell(BaseCell):
    """
    Class representing a PointType. Will instantiate a Hoc-level cell as well
    """

    def __init__(self, gid, point_type_info, circuit_conf):
        """Instantiate a new Point Neuron from mvd/node info

        Args:
            gid: Cell gid
        """
        self._gid = gid
        self._section = None
        self._cellref = None
        self._ccell = None
        self._netcons = []
        self._synapses = []
        self._instantiate_cell(point_type_info)

    # Read-only properties
    section = property(lambda self: self._section)
    section_ref = property(lambda self: self._section_ref)
    gid = property(lambda self: int(self._gid),
                   lambda self, val: setattr(self, '_gid', val))
    excitatory = property(lambda self: self._excitatory)
    synapses = property(lambda self: self._synapses)

    def _instantiate_cell(self, point_type_info):
        """Instantiates an AdEx cell
        """
        self._section = Nd.Section()
        self._section_ref = Nd.SectionRef(sec=self._section)
        AdEx_cell = Nd.AdEx(self._section(0.5))
        AdEx_cell.C_m = point_type_info[0]
        AdEx_cell.E_L = point_type_info[1]
        AdEx_cell.g_L = point_type_info[2]
        AdEx_cell.V_reset = point_type_info[3]
        AdEx_cell.V_th = point_type_info[4]
        AdEx_cell.V_peak = point_type_info[5]
        AdEx_cell.Delta_T = point_type_info[6]
        AdEx_cell.a = point_type_info[7]
        AdEx_cell.b = point_type_info[8]
        AdEx_cell.tau_w = point_type_info[9]
        AdEx_cell.t_ref = point_type_info[10]
        nb_receptors_size = int(point_type_info[11])
        E_rev = Nd.Vector(point_type_info[12][0:nb_receptors_size])
        tau_decay = Nd.Vector(point_type_info[13][0:nb_receptors_size])
        tau_rise = Nd.Vector(point_type_info[14][0:nb_receptors_size])
        AdEx_cell.setPostsyn(E_rev, tau_rise, tau_decay)

        self._excitatory = point_type_info[15]
        self._ccell = AdEx_cell
        self._cellref = self._section_ref

    def connect2target(self, target_pp):
        """ Connects MEtype cell to target

        Args:
            target_pp: target point process

        Returns: NetCon obj
        """
        netcon = Nd.NetCon(self.CCell._ref_spike, target_pp, sec=self._section)
        netcon.threshold = 1
        self._synapses.append(netcon)
        return netcon


class PointNeuronManager(CellManagerBase):
    CellType = PointCell

    @staticmethod
    def _node_loader(circuit_conf, gidvec, stride=1, stride_offset=0):
        """Load point neuron cells from SONATA file

        This function is used by the load_nodes function from CellManagerBase to load the nodes
        information from the CellLibraryFile.
        """
        logging.info("Load Cells from SONATA file")
        import h5py  # Can be heavy so loaded on demand
        pth = ospath.join(circuit_conf["CircuitPath"], circuit_conf["CellLibraryFile"])
        sonata_point_nodes = h5py.File(pth, 'r')

        sonata_gidvec = sonata_point_nodes["/nodes/default/node_id"][:]
        total_point_cells = len(sonata_gidvec)

        original_gidvec = np.frombuffer(sonata_gidvec, dtype="uint32")

        # convert 0-based sonata gids to 1-based for neurodamus
        original_gidvec += 1
        # find which gids are in target to simulate
        target_gidvec = original_gidvec[np.in1d(original_gidvec, gidvec)]

        target_gidvec = split_round_robin(target_gidvec, stride, stride_offset, total_point_cells)

        # create filter for loading the nodes info
        filter_local_gids = np.in1d(original_gidvec, target_gidvec)
        local_point_cells = len(target_gidvec)
        if not len(gidvec):
            # Not enough cells to give this rank a few
            return compat.Vector('I'), {}, total_point_cells

        properties = np.array([
            sonata_point_nodes["/nodes/default/0/dynamics_params/C_m"][filter_local_gids],
            sonata_point_nodes["/nodes/default/0/dynamics_params/E_L"][filter_local_gids],
            sonata_point_nodes["/nodes/default/0/dynamics_params/g_L"][filter_local_gids],
            sonata_point_nodes["/nodes/default/0/dynamics_params/V_reset"][filter_local_gids],
            sonata_point_nodes["/nodes/default/0/dynamics_params/V_th"][filter_local_gids],
            sonata_point_nodes["/nodes/default/0/dynamics_params/V_peak"][filter_local_gids],
            sonata_point_nodes["/nodes/default/0/dynamics_params/Delta_T"][filter_local_gids],
            sonata_point_nodes["/nodes/default/0/dynamics_params/a"][filter_local_gids],
            sonata_point_nodes["/nodes/default/0/dynamics_params/b"][filter_local_gids],
            sonata_point_nodes["/nodes/default/0/dynamics_params/tau_w"][filter_local_gids],
            ([5.0]*local_point_cells
             if "t_ref" not in sonata_point_nodes["/nodes/default/0/dynamics_params"].keys()
             else sonata_point_nodes["/nodes/default/0/dynamics_params/t_ref"][filter_local_gids]),
            sonata_point_nodes["/nodes/default/0/dynamics_params/nb_receptors"][filter_local_gids],
            sonata_point_nodes["/nodes/default/0/dynamics_params/E_rev"][:][
                filter_local_gids
            ].tolist(),
            sonata_point_nodes["/nodes/default/0/dynamics_params/tau_decay"][:][
                filter_local_gids
            ].tolist(),
            sonata_point_nodes["/nodes/default/0/dynamics_params/tau_rise"][:][
                filter_local_gids
            ].tolist(),
            sonata_point_nodes["/nodes/default/0/excitatory"][filter_local_gids]],
            dtype=object
        )
        pointinfo = dict(zip(target_gidvec, np.transpose(properties)))
        return target_gidvec, pointinfo, total_point_cells

    def enable_report(self, report_conf, target_spec, use_coreneuron):
        """Add custom PointReport for the PointNeuron Engine

        Args:
            report_conf: The dict containing the report configuration
            target_name: The target of the report
            use_coreneuron: Whether the simulator is CoreNeuron
        """
        gids = self.target_manager.get_target(target_spec).get_gids()
        for gid in gids:
            if gid in self.gid2cell:
                report_conf.addPointReport(self.gid2cell[gid].section_ref, gid, use_coreneuron)


class PointNeuronConnection(ConnectionBase):
    """
    Connection object that gets all the synapses for a target cells and
    sets the connections
    """

    def __init__(self, sgids, tgid, src_pop_id=0, dst_pop_id=0, **kw):
        super().__init__(None, tgid, src_pop_id, dst_pop_id, **kw)
        self.sgids = sgids
        self._synapses = []
        self._synapse_ids = {}
        self._conn_params = None

        self._replay_tvec = {}  # Dict that the replay tvecs for the VecStims are saved in
        self._vecstims = {}  # VecStims VCells

    def filter_sgids(self, sgids):
        self._conn_params.filter_sgids(sgids)

    def add_point_synapses(self, params_obj):
        """Adds a synapse in given location to this Connection.

        Args:
            params_obj: Parameters object for the Synapse to be placed
        """
        if self._conn_params is None:
            self._conn_params = params_obj
        else:
            self._conn_params.append_synapse_parameters(params_obj)

    def finalize(self, cell_distributor, cell):
        """Finalize synapses. Set's the receptors values, creates the point synapses,
        edits their parameters based on the excitatory and inhibitory cells and creates
        more synapses.

        Args:
            cell_distributor: Get the cell distributor which includes all the cells, to be able
                              to access the references of all the cells
            cell: The PointType object which is the target of this connection
        """
        return self._create_point_synapse(cell_distributor, cell, self._conn_params)

    def _create_point_synapse(self, cell_distributor, target_neuron, syn_params):
        """Actually create the Netcons of the point synapses and also connect the VecStims to the
           cells

        Args:
            cell_distributor: Needed to access the references to all the cells of the CircuitTarget
            target_neuron: The reference to the PointType
            syn_params: The synapse parameters of the connection (passed as argument as they might
                        be passed changed)
        """
        nb_synapses_ = len(syn_params)
        target_cell = target_neuron.CCell
        id_syn = target_cell.initSynapse(nb_synapses_)
        netconns_numbers = 0
        gid_offset = cell_distributor.local_nodes.offset
        for i in range(nb_synapses_):
            base_sgid = syn_params.sgid[i]
            source_gid = base_sgid + gid_offset
            if source_gid in self.sgids:
                weight = syn_params.weight[i] if syn_params.weight[i] > 1e-9 else 0.
                target_cell.addSynapse(id_syn + i, weight, syn_params.tau_rec[i],
                                       syn_params.tau_fac[i], syn_params.U[i],
                                       syn_params.delay[i],  # used for last_spike to match Nest
                                       syn_params.x[i], syn_params.u[i])
                if base_sgid in self._vecstims:
                    connection = Nd.NetCon(self._vecstims[base_sgid], target_cell)
                else:
                    connection = cell_distributor.pc.gid_connect(source_gid, target_cell)
                connection.weight[0] = id_syn + i
                connection.weight[1] = syn_params.receptor_type[i] - 1
                connection.delay = syn_params.delay[i] + Nd.dt
                netconns_numbers += 1
                self._synapse_ids[source_gid] = id_syn + i
                self._synapses.append(connection)

        return netconns_numbers

    def replay(self, sgid, tvec, vstim, start_delay=.0):
        """ The synapses connecting these gids are to be activated using
        predetermined timings.

        Args:
            sgid: VecStim "cell" gid
            tvec: time for spike events from the sgid
            start_delay: When the events may start to be delivered
        """
        if vstim is None:
            tvec = tvec[tvec >= start_delay]
            tvec = tvec[tvec <= Nd.tstop]
            if len(tvec) == 0:
                return None
            hoc_tvec = Nd.Vector(tvec)
            logging.debug("Replaying %d spikes on %d", hoc_tvec.size(), sgid)
            logging.debug(" > First replay event for connection at %f", hoc_tvec.x[0])

            if sgid not in self._replay_tvec:
                self._replay_tvec[sgid] = hoc_tvec
            else:
                self._replay_tvec[sgid].append(
                    hoc_tvec)
            self._replay_tvec[sgid].sort()

            vstim = Nd.VecStim()
            vstim.play(self._replay_tvec[sgid], sgid)

        self._vecstims[sgid] = vstim

        return vstim


class PointNeuronConnSet(ConnectionSet):
    """A ConnectionSet specialized for PointNeurons.

    Unlike detailed Neurons, there is a single connection object per tgid which
    contains all (single) synapses from src neurons.
    """

    def get_or_create_point_connection(self, sgids, tgid, **kwargs):
        """Returns a connection by pre-post gid, creating if required."""
        conns = self._connections_map[tgid]
        if conns:
            conn = conns[0]
            # add the sgids of one tgid in the same connection
            conn.sgids = np.concatenate((conn.sgids, sgids))
            return conn

        # Not found. Create & insert
        cur_conn = PointNeuronConnection(sgids, tgid, self.src_id, self.dst_id, **kwargs)
        self._connections_map[tgid] = [cur_conn]
        self._conn_count += 1
        return cur_conn


class PointSynapseParameters(object):
    """Point Synapses parameters based on whole_brain_model_SONATA.h5
    """
    _synapse_fields = ("sgid", "delay", "tau_rec", "tau_fac", "U", "u", "x", "weight",
                       "receptor_type", "isec", "ipt", "offset", "weight_factor")

    def __init__(self):
        self.sgid = []
        self.delay = []
        self.tau_rec = []
        self.tau_fac = []
        self.U = []
        self.u = []
        self.x = []
        self.weight = []
        self.receptor_type = []
        self.isec = []
        self.ipt = []
        self.offset = []
        self.weight_factor = []

    def __len__(self):
        return len(self.sgid)

    def filter_sgids(self, sgids):
        filter_disregarded_sgids = np.in1d(self.sgid, sgids)
        self.sgid = self.sgid[filter_disregarded_sgids]
        self.delay = self.delay[filter_disregarded_sgids]
        self.tau_rec = self.tau_rec[filter_disregarded_sgids]
        self.tau_fac = self.tau_fac[filter_disregarded_sgids]
        self.U = self.U[filter_disregarded_sgids]
        self.u = self.u[filter_disregarded_sgids]
        self.x = self.x[filter_disregarded_sgids]
        self.weight = self.weight[filter_disregarded_sgids]
        self.receptor_type = self.receptor_type[filter_disregarded_sgids]

    def append_synapse_parameters(self, point_synapse_params):
        self.sgid = np.concatenate((self.sgid, point_synapse_params.sgid))
        self.delay = np.concatenate((self.delay, point_synapse_params.delay))
        self.tau_rec = np.concatenate((self.tau_rec, point_synapse_params.tau_rec))
        self.tau_fac = np.concatenate((self.tau_fac, point_synapse_params.tau_fac))
        self.U = np.concatenate((self.U, point_synapse_params.U))
        self.u = np.concatenate((self.u, point_synapse_params.u))
        self.x = np.concatenate((self.x, point_synapse_params.x))
        self.weight = np.concatenate((self.weight, point_synapse_params.weight))
        self.receptor_type = np.concatenate((self.receptor_type,
                                             point_synapse_params.receptor_type))


class CustomPointSynFileReader(object):
    def __init__(self, syn_h5file):
        import h5py  # Can be heavy so loaded on demand
        self.syn_h5file = h5py.File(syn_h5file, 'r')
        self.tgids = self.syn_h5file["/edges/default/target_node_id"][:] + 1
        self.sgids = self.syn_h5file["/edges/default/source_node_id"][:] + 1
        self.delay = self.syn_h5file["/edges/default/0/delay"][:]
        self.tau_rec = self.syn_h5file["/edges/default/0/tau_rec"][:]
        self.tau_fac = self.syn_h5file["/edges/default/0/tau_fac"][:]
        self.U = self.syn_h5file["/edges/default/0/U"][:]
        self.weight = self.syn_h5file["/edges/default/0/weight"][:]
        self.receptor_type = self.syn_h5file["/edges/default/0/receptor"][:]
        self.node_ids = self.syn_h5file["/nodes/default/node_id"][:] + 1
        self.excitatory = self.syn_h5file["/nodes/default/0/excitatory"][:]

    def read_synapses(self, tgid):
        indexes_mask = np.in1d(self.tgids, tgid)
        conn_syn_params = PointSynapseParameters()

        # Those should take care of the correct population instead of 0
        conn_syn_params.sgid = self.sgids[indexes_mask]
        conn_syn_params.delay = self.delay[indexes_mask]
        conn_syn_params.tau_rec = self.tau_rec[indexes_mask]
        conn_syn_params.tau_fac = self.tau_fac[indexes_mask]
        conn_syn_params.U = self.U[indexes_mask]
        conn_syn_params.u = 0.5 * np.ones(len(conn_syn_params.sgid), np.float64)
        conn_syn_params.x = 0.5 * np.ones(len(conn_syn_params.sgid), np.float64)
        conn_syn_params.weight = self.weight[indexes_mask]
        conn_syn_params.receptor_type = self.receptor_type[indexes_mask]

        return conn_syn_params


class PointSynReader(object):
    """ Synapse Reader for AdEx Point Neurons' Synapses based on whole_brain_model_SONATA.h5
    """
    def __init__(self, syn_source):
        self.syn_source = syn_source
        self._syn_reader = CustomPointSynFileReader(syn_source)

    def get_synapse_parameters(self, gid):
        """Obtains the synapse parameters record for a given gid.
        """
        syn_params = self._load_synapse_parameters(gid)
        return syn_params

    def _load_synapse_parameters(self, gid):
        """Load synapses parameters from whole_brain_model_SONATA.h5
        """
        return self._syn_reader.read_synapses(gid)


class PointNeuronSynapseManager(SynapseRuleManager):
    ConnectionSet = PointNeuronConnSet
    vecstims = {}

    def open_synapse_file(self, synapse_file, edge_population, n_files=1, load_offsets=False, *,
                          src_pop_id=None, src_name=None, **_kw):
        """Initializes a reader for Synapses"""
        logging.info("Opening Synapse file %s with PointSynReader", synapse_file)
        self._synapse_reader = PointSynReader(synapse_file)
        self._init_conn_population(None, src_pop_id)
        self._unlock_all_connections()  # Allow appending synapses from new sources

    def connect_all(self, weight_factor=1, only_gids=None, **kwargs):
        pop = self._cur_population
        created_conns_0 = pop.count()
        for sgids, tgid, syns_params in self._iterate_conn_params(None, None, only_gids, True):
            cur_conn = pop.get_or_create_point_connection(sgids, tgid)
            cur_conn.add_point_synapses(syns_params)
        return pop.count() - created_conns_0

    def connect_group(self, conn_source, conn_destination, synapse_type_restrict=None,
                      mod_override=None):
        """Instantiates pathway connections & synapses given src-dst

                Args:
                   conn_source (str): The target name of the source cells
                   conn_destination (str): The target of the destination cells
                   synapse_type_restrict(int): Create only given synType synapses
                   mod_override (str): ModOverride given for this connection group
                """
        pop = self._cur_population
        logging.debug("Connecting group %s -> %s", conn_source, conn_destination)
        src_tname = TargetSpec(conn_source).name
        dst_tname = TargetSpec(conn_destination).name
        src_target = src_tname and self._target_manager.getTarget(src_tname)
        dst_target = dst_tname and self._target_manager.getTarget(dst_tname)

        for sgids, tgid, syns_params in self._iterate_conn_params(src_target, dst_target):
            cur_conn = pop.get_or_create_point_connection(sgids, tgid)
            cur_conn.add_point_synapses(syns_params)

    def _iterate_conn_params(self, src_target, dst_target, gids=None, show_progress=False):
        """A generator which loads synapse data and yields tuples(sgid, tgid, synapses)

        Args:
            src_target: the target to filter the source cells, or None
            dst_target: the target to filter the destination cells, or None
            gids: Use given gids, instead of the circuit target cells. Default: None
            show_progress: Display a progress bar as tgids are processed
        """
        if gids is None:
            gids = self._raw_gids
        if show_progress:
            gids = ProgressBar.iter(gids)
        created_conns = 0

        sgid_offset, tgid_offset = self.get_updated_population_offsets(src_target, dst_target)
        for base_tgid in gids:
            tgid = base_tgid + tgid_offset
            if dst_target is not None and not dst_target.contains(tgid):
                continue

            # Retrieve all synapses for base_tgid
            syns_params = self._synapse_reader.get_synapse_parameters(base_tgid)
            base_sgids = []
            sgids = []
            yielded_src_gids = compat.Vector("i")

            for base_sgid in syns_params.sgid:
                sgid = base_sgid + sgid_offset
                if src_target is None or src_target.completeContains(sgid):
                    sgids.append(sgid)
                    base_sgids.append(base_sgid)
            syns_params.filter_sgids(base_sgids)
            if not sgids:
                continue
            yield sgids, tgid, syns_params
            yielded_conns = len(sgids)

            for base_sgid in base_sgids:
                if GlobalConfig.debug_conn == [base_tgid]:
                    yielded_src_gids.append(base_sgid)
                elif GlobalConfig.debug_conn == [base_sgid, base_tgid]:
                    log_all(logging.DEBUG, "Connection (%d-%d). Params:\n%s", base_sgid, base_tgid,
                            syns_params)

            created_conns += yielded_conns
            if yielded_src_gids:
                log_all(logging.DEBUG, "Source GIDs for debug cell: %s", yielded_src_gids)
        self._total_connections += created_conns

        if created_conns:
            pathway_repr = "[ALL]"
            if src_target and dst_target:
                pathway_repr = "Pathway {} -> {}".format(src_target.name, dst_target.name)
            logging.info(" * %s. [Rank 0]: Created %d connections",
                         pathway_repr, created_conns)

    # -
    def configure_group(self, conn_config, gidvec=None):
        logging.info("Avoid configuring group for point neurons")
        return

    # -
    def get_target_connections(self, src_target_name,
                               dst_target_name,
                               gidvec=None,
                               conn_population=None):
        """Retrives the connections between src-dst cell targets

        Optional gidvec (post) / conn_population restrict the set of
        connections to be returned
        """
        src_target_spec = TargetSpec(src_target_name)
        dst_target_spec = TargetSpec(dst_target_name)
        src_target = self._target_manager.getTarget(src_target_spec.name)
        dst_target = self._target_manager.getTarget(dst_target_spec.name)
        gidvec = self._raw_gids if gidvec is None else gidvec
        _, tgid_offset = self.get_updated_population_offsets(src_target, dst_target)

        populations = (conn_population,) if conn_population is not None \
            else self._populations.values()

        for population in populations:
            log_verbose("Connections from population %s", population)
            for base_tgid in gidvec:
                tgid = base_tgid + tgid_offset
                if not dst_target.contains(tgid) or tgid not in population:
                    continue
                for conn in population[tgid]:
                    yield conn

    @timeit(name="Replay inject")
    def replay(self, spike_manager, src_target_name, dst_target_name, start_delay=.0):
        """Create special netcons to trigger timed spikes on those synapses.

        Args:
            spike_manager: map of gids (pre-synaptic) with spike times
            src_target_name: Source population:target of the replay connections
            dst_target_name: Target whose gids should be replayed
            start_delay: Dont deliver events before t=start_delay
        """
        log_verbose("Applying replay map with %d src cells...", len(spike_manager))

        # Dont deliver events in the past
        if Nd.t > start_delay:
            start_delay = Nd.t
            log_verbose("Restore: Delivering events only after t=%.4f", start_delay)

        src_pop_offset = self.src_pop_offset
        for conn in self.get_target_connections(src_target_name, dst_target_name):
            for sgid in conn.sgids:
                base_sgid = sgid - src_pop_offset
                if base_sgid in spike_manager:
                    if base_sgid not in self.vecstims:
                        self.vecstims[base_sgid] = conn.replay(base_sgid, spike_manager[base_sgid],
                                                               None, start_delay)
                    else:
                        conn.replay(base_sgid, spike_manager[base_sgid], self.vecstims[base_sgid],
                                    start_delay)

        replayed_count = len(self.vecstims)
        logging.info("total unique sgids replayed: {}".format(len(self.vecstims)))
        total_replays = MPI.allreduce(replayed_count, MPI.SUM)
        if MPI.rank == 0:
            if total_replays == 0:
                logging.warning("No connections were injected replay stimulus")
            else:
                logging.info(" => Replaying on %d connections", total_replays)
        return total_replays

    def _finalize_conns(self, tgid, conns, base_seed, sim_corenrn, **kwargs):
        cell_distributor = self._cell_manager
        cell = cell_distributor.gid2cell[tgid]
        n_created_conns = 0

        # Note: (Compat) neurodamus hoc keeps connections in reversed order.
        for conn in reversed(conns):  # type of conn: Connection
            # Skip disabled if we are running with core-neuron
            n_created_conns += conn.finalize(cell_distributor, cell)
        return n_created_conns


class PointNeuronEngine(EngineBase):
    CellManagerCls = PointNeuronManager
    InnerConnectivityCls = PointNeuronSynapseManager
    ConnectionTypes = {
        "Point": PointNeuronSynapseManager
    }
