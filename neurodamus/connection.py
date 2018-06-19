from __future__ import absolute_import
import logging
import numpy as np
from .core import NeuronDamus as ND
from .utils import compat
from six.moves import zip


# SynapseParameters = namedtuple("SynapseParameters", _synapse_fields)
# SynapseParameters.__new__.__defaults__ = (None, 0.5)  # defaults to last 2 optional params
class SynapseParameters(object):
    """Synapse parameters, internally implemented as numpy record
    """
    _synapse_fields = ("sgid", "delay", "isec", "ipt", "offset", "weight", "U", "D", "F", "DTC",
                       "synType", "nrrp", "location")  # total: 13
    _dtype = np.dtype({"names": _synapse_fields,
                       "formats": ["f8"] * len(_synapse_fields)})

    def __new__(cls, params):
        npa = np.empty(1, cls._dtype)
        npa["location"] = 0.5
        # Return record object
        return npa.view(np.recarray)[0]

    @classmethod
    def create_array(cls, length):
        npa = np.empty(length, cls._dtype)
        npa["location"] = 0.5
        return npa.view(np.recarray)


class SynapseMode:
    # Note, these are constants provided for other objects (like SynapseRuleManager)
    AMPA_ONLY = 1
    DUAL_SYNS = 2
    default = DUAL_SYNS

    @classmethod
    def from_str(cls, str_repr):
        if str_repr.lower().startswith("ampa"):
            return cls.AMPA_ONLY
        elif str_repr.lower().startswith("dual"):
            return cls.DUAL_SYNS
        raise ValueError("Invalid synapse mode: " + str_repr +
                         ". Possible values are Ampa% and Dual%")


class STDPMode:
    """Values for each STDP rule. Add more here as more rules are implemented
    """
    NO_STDP = 0
    DOUBLET_STDP = 1
    TRIPLET_STDP = 2

    _str_val = {
        "stdpoff": NO_STDP,
        "doublet": DOUBLET_STDP,
        "triplet": TRIPLET_STDP
    }

    @classmethod
    def from_str(cls, str_repr):
        try:
            return cls._str_val[str_repr.lower()]
        except KeyError:
            raise ValueError("Invalid STDP mode: " + str_repr +
                             ". Possible values are STDPoff, Doublet and Triplet")

    @classmethod
    def validate(cls, value):
        if value is None:
            return cls.NO_STDP
        if value not in cls._str_val.values():
            raise ValueError("Invalid STDP value: " + value)
        return value


class Connection(object):
    """
    A Connection object serves as a container for synapses formed from a presynaptic and a
    postsynaptic gid, including Points where those synapses are placed (stored in TPointList)
    """
    __slots__ = ("sgid", "tgid", "weight_factor", "__dict__")

    def __init__(self, sgid, tgid, configuration=None,
                 stdp=None,
                 minis_spont_rate=0,
                 synapse_mode=SynapseMode.DUAL_SYNS,
                 weight_factor=1):
        """Creates a connection object

        Args:
            sgid: presynaptic gid
            tgid: postsynaptic gid
            configuration: Any synapse configurations that should be applied when the synapses
                are instatiated (or nil for none)
            stdp (str): STDP settings
            minis_spont_rate: rate for spontaneous minis
            synapse_mode: (optional) synapse mode. Default: DUAL_SYNS
        """
        h = ND.h
        self.sgid = sgid
        self.tgid = tgid
        self.synapse_mode = synapse_mode
        self.doneReplayRegister = 0
        self.synOverride = None
        self.weight_factor = weight_factor
        self._stdp = STDPMode.validate(stdp)
        self._minis_spont_rate = minis_spont_rate
        self._tpoint_man = h.TPointList(tgid, 1)
        self._synapse_params = []
        self._synapse_ids = compat.Vector("i")
        self._configurations = [configuration] \
            if configuration is not None else []
        # Lists defined in finalize
        self._netcons = None
        self._synapses = None
        self._conductances_bk = None  # Store conductances for re-ebaling
        self._replay_netcons = None
        self._minis_netcons = None
        self._minis_RNGs = None
        # Used for replay
        self._tvecs = []

    synapse_params = property(lambda self: self._synapse_params)

    def _set_stdp(self, stdp):
        self._stdp = STDPMode.validate(stdp)
    stdp = property(lambda self: self._stdp, _set_stdp)

    # -
    def add_synapse(self, syn_tpoints, params_obj, syn_id=None):
        """Adds a location and synapse to this Connection so that netcons can later be generated

        Args:
            syn_tpoints: TPointList with one point on the tgid where the associated synapse exists
            params_obj: Parameters object for the Synapse to be placed
            syn_id: Optional id for the synapse to be used for seeding rng if applicable
        """
        self._tpoint_man.append(syn_tpoints)
        self._synapse_params.append(params_obj)

        # copy the location from the pointlist into the param item for easier debugging access
        params_obj.location = syn_tpoints.x[0]

        if syn_id is not None:
            self._synapse_ids.append(syn_id)
        else:
            self._synapse_ids.append(self._tpoint_man.count())

    # -
    def add_synapse_configuration(self, configuration):
        """Add a synapse configuration command to the list.
        All commands are executed on synapse creation
        """
        if configuration is not None:
            self._configurations.append(configuration)

    # -
    def place_synapses(self, cell, params_obj, x, syn_id, base_seed):
        """Create one or more synapses, updating the self._synapses and TPointList in the supplied
        Connection object. This is dependant on the location existing on the cpu.

        Args:
            cell: The cell object
            params_obj: SynapseParameters object for the synapse to be placed at a single location
            x: distance into the currently accessed section (cas)
            syn_id: Synapse id (determined by row number in the nrn.h5 dataset)
            base_seed: base seed to adjust synapse RNG - added to MCellRan4's low index parameter

        """
        if self.synOverride is not None:
            # there should be a 'Helper' for that syntype in the hoc path.
            override_helper = self.synOverride.get("ModOverride") + "Helper"
            ND.load_hoc(override_helper)
            try:
                helper_cls = getattr(ND.h, override_helper)
            except AttributeError:
                raise RuntimeError("Failed to load override helper " + override_helper)
        else:
            helper_cls = ND.GABAABHelper if params_obj.synType < 100 \
                else ND.AMPANMDAHelper

        syn_helper = helper_cls(self.tgid, params_obj, x, syn_id, base_seed, self.synOverride)
        cell.CellRef.synHelperList.append(syn_helper)
        cell.CellRef.synlist.append(syn_helper.synapse)

    # -
    def finalize(self, pnm, cell, base_seed=None, tgid_override=None):
        """ When all parameters are set, create synapses and netcons

        Args:
            pnm: parallelNetManager object which manages cells (& netcons) for NEURON
            cell: cell provided directly rather than via pnm to avoid loadbalance issues
            base_seed: base seed value (leave default None in case no adjustment is needed)
            tgid_override: optional argument which overrides the tgid in the event of loadbalancing

        """
        tgid = tgid_override if tgid_override is not None else self.tgid
        weight_adjusts = []
        wa_netcon_pre = []
        wa_netcon_post = []
        rng_info = ND.RNGSettings()
        tbins_vec = ND.Vector(1)
        tbins_vec.x[0] = 0.0
        rate_vec = ND.Vector(1)

        # Initialize member lists
        self._synapses = []
        self._netcons = []
        self._minis_netcons = []
        self._minis_RNGs = []

        # Note that synapseLocation.SPLIT = 1
        # All locations, on and off node should be in this list, but only synapses/netcons on-node
        # should get instantiated
        for syn_i, sc in enumerate(self._tpoint_man.sclst):
            if not sc.exists():
                continue
            # Put the section in the stack, so generic hoc instructions apply to the right section
            sc.sec.push()

            x = self._tpoint_man.x[syn_i]
            active_params = self._synapse_params[syn_i]
            self.place_synapses(cell, active_params, x, self._synapse_ids[syn_i], base_seed)
            cell_syn_list = cell.CellRef.synlist
            syn_obj = cell_syn_list.o(cell_syn_list.count()-1)
            self._synapses.append(syn_obj)

            # see also pc.gid_connect
            # if sgid exists (i.e. both gids are local), makes netcon connection (c/c++) immediately
            # if sgid not exist, creates an input PreSyn to receive spikes transited over the net.
            # PreSyn is the source to the NetCon, cannot ask netcon about the preloc, but srcgid ok

            nc_index = pnm.nc_append(self.sgid, tgid, cell_syn_list.count()-1, active_params.delay,
                                     active_params.weight)
            nc = pnm.nclist.object(nc_index)  # Netcon object
            nc.delay = active_params.delay
            nc.weight[0] = active_params.weight * self.weight_factor
            nc.threshold = -30

            # If the config has UseSTDP, do STDP stuff (can add more options later
            #   here and in Connection.init). Instantiates the appropriate StdpWA mod file
            if self._stdp:
                if self._stdp == STDPMode.DOUBLET_STDP:
                    weight_adjuster = ND.StdpWADoublet(x)
                elif self._stdp == STDPMode.TRIPLET_STDP:
                    weight_adjuster = ND.StdpWATriplet(x)
                else:
                    raise ValueError("Invalid STDP config")

                # The synapse ID is useful for synapse reporting
                weight_adjuster.synapseID = syn_obj.synapseID

                # Create netcons for the pre and post synaptic cells
                #   with weights of 1 and -1, respectively
                nc_wa_pre = pnm.pc.gid_connect(self.sgid, weight_adjuster)
                nc_wa_pre.threshold = -30
                nc_wa_pre.weight[0] = 1
                nc_wa_pre.delay = active_params.delay

                nc_wa_post = pnm.pc.gid_connect(tgid, weight_adjuster)
                nc_wa_post.threshold = -30
                nc_wa_post.weight[0] = -1
                nc_wa_post.delay = active_params.delay

                # Set the pointer to the synapse netcon weight
                ND.setpointer(nc._ref_weight, "wsyn", weight_adjuster)

                weight_adjusts.append(weight_adjuster)
                wa_netcon_pre.append(nc_wa_pre)
                wa_netcon_post.append(nc_wa_post)

            if self._minis_spont_rate > 0.0:
                ips = ND.InhPoissonStim(x)
                # netconMini = pnm.pc.gid_connect(ips, finalgid)

                # A simple NetCon will do, as the synapse and cell are local.
                netcon_m = ND.NetCon(ips, syn_obj)
                netcon_m.delay = 0.1
                # TODO: better solution here to get the desired behaviour during
                # delayed connection blocks
                # Right now spontaneous minis should be unaffected by delays
                netcon_m.weight[0] = active_params.weight * self.weight_factor
                self._minis_netcons.append(netcon_m)
                if rng_info.getRNGMode() == rng_info.RANDOM123:
                    ips.setRNGs(syn_obj.synapseID+200, tgid+250, rng_info.getMinisSeed()+300,
                                syn_obj.synapseID+200, tgid+250, rng_info.getMinisSeed()+350)
                else:
                    exprng = ND.Random()
                    if rng_info.getRNGMode() == rng_info.COMPATIBILITY:
                        exprng.MCellRan4(syn_obj.synapseID*100000 + 200,
                                         tgid + 250 + base_seed + rng_info.getMinisSeed())
                    else:  # if ( rngIndo.getRNGMode()== rng_info.UPMCELLRAN4 ):
                        exprng.MCellRan4(syn_obj.synapseID*1000 + 200,
                                         tgid + 250 + base_seed + rng_info.getMinisSeed())

                    exprng.negexp(1)
                    uniformrng = ND.Random()
                    if rng_info.getRNGMode() == rng_info.COMPATIBILITY:
                        uniformrng.MCellRan4(syn_obj.synapseID*100000 + 300,
                                             tgid + 250 + base_seed + rng_info.getMinisSeed())
                    else:  # if ( rngIndo.getRNGMode()== rng_info.UPMCELLRAN4 ):
                        uniformrng.MCellRan4(syn_obj.synapseID*1000 + 300,
                                             tgid + 250 + base_seed + rng_info.getMinisSeed())

                    uniformrng.uniform(0.0, 1.0)
                    ips.setRNGs(exprng, uniformrng)

                    # keep variables so they don't get deleted
                    self._minis_RNGs.append(exprng)
                    self._minis_RNGs.append(uniformrng)

                # we never use this list, so I can put the ips in here too
                self._minis_RNGs.append(ips)
                self._minis_RNGs.append(tbins_vec)
                self._minis_RNGs.append(rate_vec)

                # set the rate of the ips
                rate_vec.x[0] = self._minis_spont_rate
                ips.setTbins(tbins_vec)
                ips.setRate(rate_vec)

            self._netcons.append(nc)
            ND.pop_section()  # clear selection

        self._configure_cell(cell)

    # -
    def finalize_gap_junctions(self, pnm, cell, offset, end_offset):
        """ When all parameters are set, create synapses and netcons

        Args:
            pnm: parallelNetManager object which manages cells (& netcons) for NEURON
            cell: cell provided directly rather than via pnm to avoid loadbalance issues
            offset: offset for this cell's gap junctions
            end_offset: offset for the other cell's gap junctions

        """
        self._synapses = []
        self._netcons = []

        # Note that synapseLocation.SPLIT = 1
        # All locations should be in this list, but only synapses/netcons on-node get instantiated
        for syn_i, sc in enumerate(self._tpoint_man.sclst):
            if not sc.exists():
                continue
            x = self._tpoint_man.x[syn_i]
            active_params = self._synapse_params[syn_i]
            gap_junction = ND.Gap(x)

            # Using computed offset
            logging.debug("connect %f to %f [D: %f + %f], [F: %f + %f] (weight: %f)",
                          self.tgid, self.sgid, offset, active_params.D,
                          end_offset, active_params.F, active_params.weight)
            pnm.pc.target_var(gap_junction, gap_junction._ref_vgap, (offset + active_params.D))
            pnm.pc.source_var(sc.sec._ref_v(x), (end_offset + active_params.F))
            gap_junction.g = active_params.weight
            self._synapses.append(gap_junction)
            self._configure_cell(cell)

    def update_conductance(self, new_g):
        """ Updates all synapses conductance
        """
        for syn in self._synapses:
            syn.g = new_g

    def update_synapse_params(self, **params):
        """A generic function to update several parameters of all synapses
        """
        for syn in self._synapses:
            for key, val in params:
                setattr(syn, key, val)

    @staticmethod
    def _apply_configuration(configuration, synapse, context=None):
        # In the future configurations should be Python functions?
        """ Executes a configuration against a (tuple of) synapse(s)

        Args:
            configuration: The configuration to be applied
            synapse: The synapse to be applied the configuration. If synapse is a tuple the
                configuration is applied to each element.
            context: The context in which the command shall be executed
        """
        synapses = synapse if isinstance(synapse, tuple) else (synapse,)
        ND.execute("objref _tmp")
        for syn in synapses:
            ND._tmp = syn
            hoc_cmd = configuration.s.replace("%s", "_tmp")
            try:
                ND.execute(hoc_cmd, context)
            except RuntimeError:
                logging.warning("Failed to apply configuration to synapse: %s", hoc_cmd)

    def _configure_cell(self, cell):
        """ Helper function to apply the SynapseConfigure statements on a given cell synapses
        """
        for config in self._configurations:
            self._apply_configuration(config, tuple(cell.CellRef.synlist), cell.CellRef)

    # -
    def apply_configuration(self, configuration):
        """ Helper function to execute a configuration command on all created synapses.
        """
        # NOTE: After the simulation has run for some time we can't assume that the last synapse
        # of the cell object is the target
        self._apply_configuration(configuration, tuple(self._synapses))

    # -
    def update_weights(self, weight, update_also_replay_netcons=False):
        """ Change the weights of the netcons generated when connecting the source and target gids
        represented in this connection

        Args:
            weight: The new weight
            update_also_replay_netcons: Whether weights shall be applied to replay netcons as well
        """
        for nc in self._netcons:
            nc.weight[0] = weight

        if update_also_replay_netcons and self._replay_netcons:
            for nc in self._replay_netcons:
                nc.weight[0] = weight

    # -
    def replay(self, tvec):
        """ The synapses connecting these gids are to be activated using predetermined timings
        Args:
            tvec: time for spike events from the sgid
        """
        self._tvecs.append(tvec)
        self._replay_netcons = []

        # Note that synapseLocation.SPLIT = 1
        # All locations, on and off node should be in this list, but only synapses/netcons on-node
        # will receive the events
        local_i = 0
        for syn_i, sc in enumerate(self._tpoint_man.sclst):
            if not sc.exists():
                continue
            active_params = self._synapse_params[syn_i]

            nc = ND.NetCon(None, self._synapses[local_i], 10, 1, active_params.weight)
            nc.weight[0] = active_params.weight  * self.weight_factor
            self._replay_netcons.append(nc)
            local_i += 1

    # -
    def register_events(self):
        # TODO: DEPRECATED: this callback is unusable in the current form. Please replace
        """For each time vector registered with this connection object, iterate the spike times
        and queue up an event. To be invoked by FInitializeHandler.
        """
        # only need to register events once per Connection
        if self.doneReplayRegister == 1:
            return
        self.doneReplayRegister = 1

        for tvec in self._tvecs:
            local_i = 0
            for syn_i, sc in enumerate(self._tpoint_man.sclst):
                if not sc.exists():
                    continue
                active_params = self._synapse_params[syn_i]
                nc = self._replay_netcons[local_i]

                for t in tvec:
                    # Note: just creating an nc.event here did not seem to work.  Presumably
                    # the queue is cleared when stdinit is called, hence we must use an
                    # FInitializeHandler
                    nc.event(t + active_params.delay)

                    # sprint(tstr,"%s.event(%f)", nc, tVec.x[timeIndex] + activeParams.delay )
                    logging.debug("%d->%d event at %f",
                                  self.sgid, self.tgid, t + active_params.delay)
                local_i += 1

    # -
    def disable(self, set_zero_conductance=False):
        """Deactivates a synapse by disabling the netcon. Additionally can also set conductance
        to zero so that the point process has no contribution whatsoever to the simulation.

        Args:
            set_zero_conductance: (bool) Sets synapses' conductance to zero [default: False]

        """
        for nc in self._netcons:
            nc.active(False)
        if set_zero_conductance:
            self._conductances_bk = compat.Vector("d", (syn.g for syn in self._synapses))
            self.update_conductance(.0)

    def enable(self):
        """(Re)enables connections. It will activate all netcons and restore conductance values
        had they been set to zero"""
        for nc in self._netcons:
            nc.active(True)
        if self._conductances_bk:
            for syn, cond in zip(self._synapses, self._conductances_bk):
                syn.g = cond
            self._conductances_bk = None
