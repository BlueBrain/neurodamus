"""
Implementation of the core Connection classes
"""
from __future__ import absolute_import
import logging
import numpy as np
from enum import Enum
from six.moves import zip
from .core import NeurodamusCore as Nd
from .utils import compat


class SynapseParameters(object):
    """Synapse parameters, internally implemented as numpy record
    """
    _synapse_fields = ("sgid", "delay", "isec", "ipt", "offset", "weight", "U", "D", "F",
                       "DTC", "synType", "nrrp", "maskValue", "location")  # total: 13
    _dtype = np.dtype({"names": _synapse_fields,
                       "formats": ["f8"] * len(_synapse_fields)})

    empty = np.recarray(0, _dtype)

    def __new__(cls, params):
        raise NotImplementedError()

    @classmethod
    def create_array(cls, length):
        npa = np.recarray(length, cls._dtype)
        npa.maskValue = -1
        npa.location = 0.5
        return npa


class SynapseMode:
    """Synapse Modes, as req. by SynapseRuleManager
    """
    AMPA_ONLY = 1
    DUAL_SYNS = 2
    default = DUAL_SYNS

    @classmethod
    def from_str(cls, str_repr):
        if str_repr.lower().startswith("ampa"):
            return cls.AMPA_ONLY
        elif str_repr.lower().startswith("dual"):
            return cls.DUAL_SYNS
        raise ValueError("Invalid synapse mode: " + str_repr + ". "
                         "Possible values are Ampa* and Dual*")


class ReplayMode(Enum):
    """Replay instantiation mode.
    """
    NONE = 0
    """INstantiate no replay NetCons"""

    AS_REQUIRED = 1
    """Instantiate Replay netcons as required for this run.
    Subsequent Save-Restore may not work"""

    COMPLETE = 2
    """Instantiate Replay Netcons on all Connections so that
    users may add arbitrary new replays in Restore phases"""


# ----------------------------------------------------------------------
# Connection class
# ----------------------------------------------------------------------
class Connection(object):
    """
    A Connection object serves as a container for synapses formed from
    a presynaptic and a postsynaptic gid, including Points where those
    synapses are placed (stored in TPointList)
    """
    __slots__ = ("sgid", "tgid", "locked", "_conn_params", "__dict__")
    _AMPAMDA_Helper = None
    _GABAAB_Helper = None
    ConnUtils = None  # Collection of hoc routines to speedup execution

    @classmethod
    def _init_hmod(cls):
        if cls._AMPAMDA_Helper is not None:
            return Nd.h
        h = Nd.require("AMPANMDAHelper", "GABAABHelper")
        cls._AMPAMDA_Helper = h.AMPANMDAHelper
        cls._GABAABHelper = h.GABAABHelper
        cls.ConnUtils = h.ConnectionUtils()
        return h

    # -
    def __init__(self,
                 sgid, tgid, src_pop_id=0, dst_pop_id=0,
                 weight_factor=1.0,
                 minis_spont_rate=.0,
                 configuration=None,
                 mod_override=None,
                 synapse_mode=SynapseMode.DUAL_SYNS):
        """Creates a connection object

        Args:
            sgid: presynaptic gid
            tgid: postsynaptic gid
            weight_factor: the weight factor to be applied to the connection. Default: 1
            configuration: Any synapse configurations that should be applied
                when the synapses are instantiated (or None)
            minis_spont_rate: rate for spontaneous minis. Default: 0
            mod_override: Alternative Synapse type. Default: None (use standard Inh/Exc)
            synapse_mode: synapse mode. Default: DUAL_SYNS

        """
        h = self._init_hmod()
        self.sgid = int(sgid)
        self.tgid = int(tgid)
        self._conn_params = np.recarray(1, dtype=dict(
            names=['weight_factor', 'src_pop_id', 'dst_pop_id'],
            formats=['f8', 'i4', 'i4']
        ))[0]
        self._conn_params.put(
            0, (weight_factor, src_pop_id, dst_pop_id))
        self._disabled = False
        self._synapse_mode = synapse_mode
        self._mod_override = mod_override
        self._synapse_points = h.TPointList(tgid, 1)
        self._synapse_params = []
        self._synapse_ids = compat.Vector("i")
        self._configurations = [configuration] if configuration is not None else []
        self.locked = False

        # Main lists (defined in finalize)
        self._netcons = None
        self._synapses = None
        self._conductances_bk = None  # Store for re-enabling
        # Artificial stimulus sources
        self._spont_minis = SpontMinis(minis_spont_rate)
        self._replay = ReplayStim()

    # read-only properties
    synapse_params = property(lambda self: self._synapse_params)
    synapse_mode = property(lambda self: self._synapse_mode)
    population_id = property(lambda self: (self._conn_params.src_pop_id,
                                           self._conn_params.dst_pop_id))
    # R/W properties
    weight_factor = property(
        lambda self: self._conn_params.weight_factor,
        lambda self, weight: self._conn_params.__setattr__('weight_factor', weight)
    )
    minis_spont_rate = property(
        lambda self: self._spont_minis.rate,
        lambda self, rate: self._spont_minis.__setattr__('rate', rate)
    )

    # -
    def add_synapse_configuration(self, configuration):
        """Add a synapse configuration command to the list.
        All commands are executed on synapse creation
        """
        if configuration is not None:
            self._configurations.append(configuration)

    def override_mod(self, mod_override):
        assert mod_override.exists("ModOverride"), "ModOverride requires hoc config obj"
        self._mod_override = mod_override

    @property
    def sections_with_netcons(self):
        """Generator over all sections containing netcons, yielding pairs
        (section_index, section)
        """
        for syn_i, sc in enumerate(self._synapse_points.sclst):
            # All locations, on and off node should be in this list, but
            # only synapses/netcons on-node should be returned
            if not sc.exists():
                continue
            yield syn_i, sc.sec

    # -
    def add_synapse(self, syn_tpoints, params_obj, syn_id=None):
        """Adds a synapse in given location to this Connection.

        Args:
            syn_tpoints: TPointList with one point on the tgid where the
                associated synapse exists
            params_obj: Parameters object for the Synapse to be placed
            syn_id: Optional id for the synapse to be used for seeding rng
        """
        self._synapse_points.append(syn_tpoints)
        self._synapse_params.append(params_obj)

        params_obj.location = syn_tpoints.x[0]  # helper

        if syn_id is not None:
            self._synapse_ids.append(syn_id)
        else:
            self._synapse_ids.append(self._synapse_points.count())

    def replay(self, tvec, start_delay=.0):
        """ The synapses connecting these gids are to be activated using
        predetermined timings.

        Args:
            tvec: time for spike events from the sgid
            start_delay: When the events may start to be delivered
        """
        assert self._netcons is None, "Replay must be setup prior to finalize()"
        hoc_tvec = Nd.Vector(tvec[tvec >= start_delay])
        logging.debug("Replaying %d spikes on %d", hoc_tvec.size(), self.sgid)
        logging.debug(" > First replay event for connection at %f", hoc_tvec.x[0])

        self._replay.add_spikes(hoc_tvec)
        return len(self._replay)

    # -
    def finalize(self,
                 pnm, cell, base_seed=0, spgid=None,
                 replay_mode=ReplayMode.AS_REQUIRED, skip_disabled=False):
        """ When all parameters are set, create synapses and netcons

        Args:
            pnm: parallelNetManager object which manages cells (& netcons)
            cell: The cell to create synapses and netcons on. Provided
                directly rather than via pnm to avoid loadbalance issues
            base_seed: base seed value (Default: None - no adjustment)
            spgid: Part id, required With multisplit
            replay_mode: Policy to initialize replay in this conection
            skip_disabled: Dont instantiate at all if conn was disabled. Mostly
                useful for CoreNeuron
        """
        if skip_disabled and self._disabled:
            return False
        target_spgid = spgid or self.tgid

        # Initialize member lists
        self._synapses = compat.List()  # Used by ConnUtils
        self._netcons = []

        shall_create_replay = replay_mode == ReplayMode.COMPLETE or \
            replay_mode == ReplayMode.AS_REQUIRED and self._replay.has_data()

        # Release objects if not needed
        if not shall_create_replay:
            self._replay = None
        if self._spont_minis.rate == 0:
            self._spont_minis = None

        for syn_i, sec in self.sections_with_netcons:
            x = self._synapse_points.x[syn_i]
            syn_params = self._synapse_params[syn_i]
            with Nd.section_in_stack(sec):
                syn_obj = self._create_synapse(
                    cell, syn_params, x, self._synapse_ids[syn_i], base_seed)
            cell_syn_list = cell.CellRef.synlist
            self._synapses.append(syn_obj)

            # see also pc.gid_connect
            # if sgid exists (i.e. both gids are local), makes netcon connection (c/c++) immediately
            # if sgid not exist, creates an input PreSyn to receive spikes transited over the net.
            # PreSyn is the source to the NetCon, cannot ask netcon about the preloc, but srcgid ok
            with Nd.section_in_stack(sec):
                nc_index = pnm.nc_append(self.sgid, target_spgid, cell_syn_list.count()-1,
                                         syn_params.delay, syn_params.weight)
            nc = pnm.nclist.object(nc_index)  # Netcon object
            nc.delay = syn_params.delay
            nc.weight[0] = syn_params.weight * self._conn_params.weight_factor
            nc.threshold = -30
            self._netcons.append(nc)

            if self._spont_minis is not None:
                self._spont_minis.create_on(self, sec, x, syn_obj, syn_params, base_seed)

            if shall_create_replay:
                self._replay.create_on(self, sec, syn_obj, syn_params)

        # Apply configurations to the synapses
        self._configure_synapses()
        return True

    # -
    def _create_synapse(self, cell, params_obj, x, syn_id, base_seed):
        """Create synapse (GABBAB inhibitory, AMPANMDA excitatory, etc)
        passing the creation helper the params.

        Created synapses are appended to the corresponding cell lists.
        Third-party Synapse types are supported via the synapse-override
        configuration.

        Args:
            cell: The cell object
            params_obj: SynapseParameters object for the synapse to be
                placed at a single location.
            x: distance into the currently accessed section (cas)
            syn_id: Synapse id (NRN: determined by row number)
            base_seed: base seed to adjust synapse RNG - added to
                MCellRan4's low index parameter

        """
        if self._mod_override is not None:
            override_helper = self._mod_override.get("ModOverride").s + "Helper"
            helper_cls = getattr(Nd.h, override_helper)
            add_params = (self._mod_override,)
        else:
            helper_cls = Nd.GABAABHelper if params_obj.synType < 100 \
                else Nd.AMPANMDAHelper  # excitatory
            add_params = (self._conn_params.src_pop_id, self._conn_params.dst_pop_id)

        syn_helper = helper_cls(self.tgid, params_obj, x, syn_id, base_seed, *add_params)
        cell.CellRef.synHelperList.append(syn_helper)
        cell.CellRef.synlist.append(syn_helper.synapse)
        return syn_helper.synapse

    # -
    def finalize_gap_junctions(self, pnm, cell, offset, end_offset):
        """ When all parameters are set, create synapses and netcons

        Args:
            pnm: parallelNetManager object which manages cells (& netcons)
            cell: The cell to create synapses and netcons on. Provided
                directly rather than via pnm to avoid loadbalance issues
            offset: offset for this cell's gap junctions
            end_offset: offset for the other cell's gap junctions

        """
        self._synapses = compat.List()
        self._netcons = []

        for syn_i, sec in self.sections_with_netcons:
            x = self._synapse_points.x[syn_i]
            active_params = self._synapse_params[syn_i]
            gap_junction = Nd.Gap(x, sec=sec)

            # Using computed offset
            logging.debug("connect %f to %f [D: %f + %f], [F: %f + %f] (weight: %f)",
                          self.tgid, self.sgid, offset, active_params.D,
                          end_offset, active_params.F, active_params.weight)
            with Nd.section_in_stack(sec):
                pnm.pc.target_var(
                    gap_junction, gap_junction._ref_vgap, (offset + active_params.D))
                pnm.pc.source_var(sec(x)._ref_v, (end_offset + active_params.F))
            gap_junction.g = active_params.weight
            self._synapses.append(gap_junction)
            self._configure_cell(cell)

    # ------------------------------------------------------------------
    # Parameters Live update / Configuration
    # ------------------------------------------------------------------
    def update_conductance(self, new_g):
        """ Updates all synapses conductance
        """
        for syn in self._synapses:
            syn.g = new_g

    def update_synapse_parameters(self, **params):
        """A generic function to update several parameters of all synapses
        """
        for syn in self._synapses:
            for key, val in params:
                setattr(syn, key, val)

    def update_weights(self, weight, update_also_replay_netcons=False):
        """ Change the weights of the netcons generated when connecting
        the source and target gids represented in this connection

        Args:
            weight: The new weight
            update_also_replay_netcons: Whether weights shall be applied to
                replay netcons as well
        """
        for nc in self._netcons:
            nc.weight[0] = weight

        if update_also_replay_netcons and self._replay is not None:
            for nc in self._replay.netcons:
                nc.weight[0] = weight

    def _configure_cell(self, cell):
        """ Internal helper to apply all the configuration statements on
        a given cell synapses
        """
        for config in self._configurations:
            self.ConnUtils.executeConfigure(cell.CellRef.synlist, config)

    def _configure_synapses(self):
        """ Internal helper to apply all the configuration statements to
        the created synapses
        """
        for config in self._configurations:
            self.configure_synapses(config)

    def configure_synapses(self, configuration):
        """ Helper function to execute a configuration statement (hoc)
        on all connection synapses.
        """
        self.ConnUtils.executeConfigure(self._synapses, configuration)

    def restart_events(self):
        """Restart the artificial events, coming from Replay or Spont Minis"""
        if self._spont_minis is not None:
            self._spont_minis.restart_events()
        if self._replay is not None:
            self._replay.restart_events()

    def disable(self, set_zero_conductance=False):
        """Deactivates a connection.

        The connection synapses are inhibited by disabling the netcons.
        Additionally can also set conductance to zero so that the point
        process has no contribution whatsoever to the simulation.

        Args:
            set_zero_conductance: (bool) Sets synapses' conductance
                to zero [default: False]
        """
        self._disabled = True
        if self._netcons is None:
            return
        for nc in self._netcons:
            nc.active(False)
        if set_zero_conductance:
            self._conductances_bk = compat.Vector("d", (syn.g for syn in self._synapses))
            self.update_conductance(.0)

    def enable(self):
        """(Re)enables connections. It will activate all netcons and restore
        conductance values had they been set to zero
        """
        self._disabled = False
        if self._netcons is None:
            return
        for nc in self._netcons:
            nc.active(True)
        if self._conductances_bk:
            for syn, cond in zip(self._synapses, self._conductances_bk):
                syn.g = cond
            self._conductances_bk = None


class ArtificialStim:
    """Base class for artificial Stims, namely Replay and Minis
    """

    _bbss = None
    """SaveState object. Initialized on first use"""

    def __init__(self):
        self.netstims = []
        self.netcons = []
        if ArtificialStim._bbss is None:
            ArtificialStim._bbss = Nd.BBSaveState()

    def _store(self, netstim, netcon):
        if netstim is not None:
            self._bbss.ignore(netstim)
            self.netstims.append(netstim)
        self.netcons.append(netcon)

    def restart_events(self):
        for stim in self.netstims:
            stim.restartEvent()


class SpontMinis(ArtificialStim):
    """A class creating/holding spont minis of a connection
    """

    def __init__(self, minis_spont_rate):
        super().__init__()
        self._rng_info = Nd.RNGSettings()
        self.tbins_vec = Nd.Vector(1)
        self.tbins_vec.x[0] = 0.0
        self.rate_vec = Nd.Vector(1)
        self.rate_vec.x[0] = minis_spont_rate
        self._keep_alive = []

    rate = property(
        lambda self: self.rate_vec.x[0],
        lambda self, rate: self.rate_vec.x.__setitem__(0, rate)
    )

    def create_on(self, conn, sec, position, syn_obj, syn_params, base_seed):
        """Inserts a SpontMini stim into the given synapse
        """
        ips = Nd.InhPoissonStim(position, sec=sec)
        ips.setTbins(self.tbins_vec)
        ips.setRate(self.rate_vec)
        # A simple NetCon will do, as the synapse and cell are local.
        netcon = Nd.NetCon(ips, syn_obj, sec=sec)
        netcon.delay = 0.1
        netcon.weight[0] = syn_params.weight * conn.weight_factor
        self._store(ips, netcon)

        src_pop_id, dst_pop_id = conn.population_id
        rng_mode = self._rng_info.getRNGMode()
        rng_seed = self._rng_info.getMinisSeed()
        tgid_seed = conn.tgid + 250

        if rng_mode == self._rng_info.RANDOM123:
            seed2 = (src_pop_id * 65536 + dst_pop_id + rng_seed)
            ips.setRNGs(syn_obj.synapseID + 200, tgid_seed, seed2 + 300,
                        syn_obj.synapseID + 200, tgid_seed, seed2 + 350)
        else:
            seed2 = src_pop_id * 16777216
            exprng = Nd.Random()
            if rng_mode == self._rng_info.COMPATIBILITY:
                exprng.MCellRan4(syn_obj.synapseID * 100000 + 200,
                                 tgid_seed + base_seed + rng_seed)
            else:  # if ( rngIndo.getRNGMode()== rng_info.UPMCELLRAN4 ):
                exprng.MCellRan4(syn_obj.synapseID * 1000 + 200,
                                 seed2 + tgid_seed + base_seed + rng_seed)

            exprng.negexp(1)
            uniformrng = Nd.Random()
            if rng_mode == self._rng_info.COMPATIBILITY:
                uniformrng.MCellRan4(syn_obj.synapseID * 100000 + 300,
                                     tgid_seed + base_seed + rng_seed)
            else:  # if ( rngIndo.getRNGMode()== rng_info.UPMCELLRAN4 ):
                uniformrng.MCellRan4(syn_obj.synapseID * 1000 + 300,
                                     seed2 + tgid_seed + base_seed + rng_seed)

            uniformrng.uniform(0.0, 1.0)
            ips.setRNGs(exprng, uniformrng)
            self._keep_alive += (exprng, uniformrng)


class ReplayStim(ArtificialStim):
    """A class creating/holding replays of a connection
    """

    def __init__(self):
        super().__init__()
        self.time_vec = None

    def create_on(self, conn, sec, syn_obj, syn_params):
        """Inserts a replay stim into the given synapse
        """
        vecstim = None
        if self.has_data():
            vecstim = Nd.VecStim(sec=sec)
            vecstim.play(self.time_vec)

        nc = Nd.NetCon(vecstim, syn_obj, 10, syn_params.delay, syn_params.weight, sec=sec)
        nc.weight[0] = syn_params.weight * conn.weight_factor
        self._store(vecstim, nc)

    def add_spikes(self, hoc_tvec):
        """Appends replay spikes from a time vector to the main replay vector
        """
        if self.time_vec is None:
            self.time_vec = hoc_tvec
        else:
            self.time_vec.append(hoc_tvec)
        self.time_vec.sort()

    def has_data(self):
        return self.time_vec is not None

    def __len__(self):
        return self.time_vec.size() if self.time_vec else -1
