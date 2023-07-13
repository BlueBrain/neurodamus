import logging

from .connection_manager import SynapseRuleManager
from .connection import Connection, NetConType, ReplayMode
from .core.configuration import GlobalConfig, SimConfig
from .io.synapse_reader import SynapseParameters, SonataReader
from .utils.logging import log_all


class NeuroModulationConnection(Connection):
    __slots__ = ("_neuromod_strength", "_neuromod_dtc")

    def __init__(self,
                 sgid, tgid, src_pop_id=0, dst_pop_id=0,
                 weight_factor=1.0,
                 minis_spont_rate=None,
                 configuration=None,
                 mod_override=None,
                 **kwargs):
        self._neuromod_strength = None
        self._neuromod_dtc = None
        super().__init__(sgid, tgid, src_pop_id, dst_pop_id,
                         weight_factor, minis_spont_rate, configuration, mod_override, **kwargs)

    neuromod_strength = property(
        lambda self: self._neuromod_strength,
        lambda self, val: setattr(self, '_neuromod_strength', val)
    )
    neuromod_dtc = property(
        lambda self: self._neuromod_dtc,
        lambda self, val: setattr(self, '_neuromod_dtc', val)
    )

    def finalize(self, cell, base_seed=0, *,
                 skip_disabled=False,
                 replay_mode=ReplayMode.AS_REQUIRED,
                 base_manager=None, attach_src_cell=True, **_kwargs):
        """ Override the finalize process from the base class.
            NeuroModulatory events do not create synapses but link to existing cell synapses.
            A neuromodulatory connection from projections with match to the closest cell synapse.
            A spike coming from the neuromodulatory event (SynapseReplay) will trigger the
            NET_RECEIVE of the existing synapse, with the weight (binary 1/0), neuromod_strength,
            neuromod_dtc, and nc_type NC_MODULATOR
        """
        logging.debug("Finalize neuromodulation connection")
        if skip_disabled and self._disabled:
            return 0

        self._netcons = []
        # Initialize member lists
        self._init_artificial_stims(cell, replay_mode)

        for syn_i, sec in self.sections_with_synapses:
            syn_params = self._synapse_params[syn_i]
            # We need to get all connections since we dont know the sgid
            # TODO: improve this by extracting all the relative distances only once
            base_conns = base_manager.get_connections(self.tgid)
            syn_obj = self._find_closest_cell_synapse(syn_params, base_conns)
            if syn_obj is None:
                logging.warning("No cell synapse associated to the neuromodulatory event")
                return 0
            nc = None
            # For coreneuron, create NetCon attached to the (virtual) source gid for replay
            # For neuron, create NetCon with source from replay stim
            if SimConfig.use_coreneuron:
                nc = self._pc.gid_connect(self.sgid, syn_obj)
                nc.delay = syn_params.delay
                self._netcons.append(nc)
            elif self._replay is not None:
                nc = self._replay.create_on(self, sec, syn_obj, syn_params)
            if nc:
                nc.weight[0] = int(self.weight_factor > 0)  # weight is binary 1/0, default 1
                nc.weight[1] = self.neuromod_strength or syn_params.neuromod_strength
                nc.weight[2] = self.neuromod_dtc or syn_params.neuromod_dtc
                self.netcon_set_type(nc, syn_obj, NetConType.NC_NEUROMODULATOR)
                if GlobalConfig.debug_conn == [self.tgid]:
                    log_all(logging.DEBUG, "Neuromodulatory event on tgid: %d, " +
                            "weights: [%f, %f, %f], nc_type: %d", self.tgid,
                            nc.weight[0], nc.weight[1], nc.weight[2], NetConType.NC_NEUROMODULATOR)

        return 1

    def _find_closest_cell_synapse(self, syn_params, base_conns):
        """ Find the closest cell synapse by the location parameter
        """
        if not base_conns:
            return None
        section_i = syn_params.isec
        location_i = syn_params.location
        min_diff = 0.05
        syn_obj = None
        for base_conn in base_conns:
            for syn_j, _ in base_conn.sections_with_synapses:
                params_j = base_conn._synapse_params[syn_j]
                if params_j.isec != section_i:
                    continue
                diff = abs(params_j.location - location_i)
                if diff < min_diff:
                    syn_obj = base_conn._synapses[syn_j]
                    min_diff = diff
        return syn_obj


class ModulationConnParameters(SynapseParameters):
    # Attribute names of synapse parameters,
    # For consistancy with standard synapses, location is computed with hoc function
    # TargetManager.locationToPoint using isec, offset, ipt
    # ipt is not read from data but -1, so that locationToPoint will set location = offset .
    # weight is a placeholder for replaystim, default to 1. and overwritten by connection weight.
    _synapse_fields = ("sgid", "delay", "isec", "offset", "neuromod_strength", "neuromod_dtc",
                       "ipt", "location", "weight")


class NeuroModulationSynapseReader(SonataReader):
    Parameters = ModulationConnParameters
    custom_parameters = {"isec", "ipt", "offset", "weight"}

    def _load_params_custom(self, _populate, _read):
        super()._load_params_custom(_populate, _read)
        _populate("weight", 1)


class NeuroModulationManager(SynapseRuleManager):
    conn_factory = NeuroModulationConnection
    SynapseReader = NeuroModulationSynapseReader

    def _finalize_conns(self, tgid, conns, base_seed, sim_corenrn, **kwargs):
        """ Override the function from the base class.
            Retrieve the base synapse connections with the same tgid.
            Pass the base connections to the finalize process of superclass,
            to be processed by NeuroModulationConnection.
        """
        base_manager = next(self.cell_manager.connection_managers.values())
        return super()._finalize_conns(tgid, conns, base_seed, sim_corenrn,
                                       base_manager=base_manager,
                                       **kwargs)
