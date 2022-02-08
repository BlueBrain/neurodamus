import logging
import numpy as np

from .connection_manager import SynapseRuleManager
from .connection import Connection, NetConType, ReplayMode
from .core.configuration import GlobalConfig
from .io.synapse_reader import SynapseParameters, SynReaderSynTool
from .utils.logging import log_all


class NeuroModulationConnection(Connection):
    def finalize(self, cell, base_seed=0, *,
                 skip_disabled=False,
                 replay_mode=ReplayMode.AS_REQUIRED,
                 base_manager=None, **_kwargs):
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
            if self._replay is not None:
                nc = self._replay.create_on(self, sec, syn_obj, syn_params)
                nc.weight[0] = int(self.weight_factor > 0)  # weight is binary 1/0, default 1
                nc.weight[1] = syn_params.neuromod_strength if np.isnan(self.neuromod_strength) \
                    else self.neuromod_strength
                nc.weight[2] = syn_params.neuromod_dtc if np.isnan(self.neuromod_dtc) \
                    else self.neuromod_dtc
                self.netcon_set_type(nc, syn_obj, NetConType.NC_NEUROMODULATOR)
                if GlobalConfig.debug_conn == [self.tgid]:
                    log_all(logging.DEBUG, "Neuromodulatory event on tgid: %d, " +
                            "weights: [%f, %f, %f], nc_type: %d", self.tgid,
                            nc.weight[0], nc.weight[1], nc.weight[2], NetConType.NC_NEUROMODULATOR)

            # Delayed connections
            if self._delay_vec is not None:
                syn_obj.setup_delay_vecs(self._delay_vec, self._delayweight_vec)
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
    # Attribute names of synapse parameters
    _synapse_fields = ("sgid", "delay", "isec", "ipt", "offset", "weight", "synType",
                       "neuromod_strength", "neuromod_dtc", "location")
    # Data fields to read from edges file
    _data_fields = ("connected_neurons_pre", "delay", "morpho_section_id_post",
                    "morpho_segment_id_post", "morpho_offset_segment_post", "conductance",
                    "syn_type_id", "neuromod_strength", "neuromod_dtc")


class NeuroModulationSynapseReader(SynReaderSynTool):
    def _load_reader(self, gid, reader):
        """ Override the function from base case.
            Call loadSynapseCustom to read customized fields rather than the default fields
            in SynapseReader.mod
        """
        requested_fields = ModulationConnParameters._data_fields
        nrow = int(reader.loadSynapseCustom(gid, ",".join(requested_fields)))
        if nrow < 1:
            return nrow, 0, 0, ModulationConnParameters.empty

        record_size = len(requested_fields)
        conn_syn_params = ModulationConnParameters.create_array(nrow)
        supported_nfields = len(conn_syn_params.dtype) - 1  # location is not read from data
        return nrow, record_size, supported_nfields, conn_syn_params


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
