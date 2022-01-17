"""
Main module for handling and instantiating synaptical connections
"""
from __future__ import absolute_import
import logging
import numpy as np
from os import path as ospath

from .connection_manager import ConnectionManagerBase
from .core.configuration import ConfigurationError
from .io.synapse_reader import SynapseReader, SynReaderSynTool, SynReaderNRN, SynapseParameters,\
    SynToolNotAvail
from .utils import compat
from .utils.logging import log_verbose


class GapJunctionConnParameters(SynapseParameters):
    # Attribute names of synapse parameters, consistent with the normal synapses
    _synapse_fields = ("sgid", "isec", "offset", "weight", "D", "F", "ipt", "location")

    # Actual fields to read from conectivity files
    _gj_v1_fields = [
        "connected_neurons_pre",
        "morpho_section_id_post",
        "morpho_offset_segment_post",
        "conductance",
        "junction_id_pre",
        "junction_id_post",
        "morpho_segment_id_post",

    ]
    _gj_v2_fields = [
        "connected_neurons_pre",
        "morpho_section_id_post",
        "morpho_section_fraction_post",  # v2 field
        "conductance",
        "junction_id_pre",
        "junction_id_post"
    ]
    # SONATA fields, see conversion map in spykfunc/schema.py and
    # synapse-tool Naming::get_property_mapping
    _gj_sonata_fields = [
        "connected_neurons_pre",
        "morpho_section_id_post",
        "morpho_section_fraction_post",
        "conductance",
        "efferent_junction_id",
        "afferent_junction_id"
    ]

    @classmethod
    def create_array(cls, length):
        npa = np.recarray(length, cls.dtype)
        npa.ipt = -1
        npa.location = 0.5
        return npa


class GapJunctionSynToolReader(SynReaderSynTool):

    def _get_gapjunction_fields(self):
        """ Determine data fields to adapt to different versions of edges files """
        if self.has_property("afferent_junction_id") and self.has_property("efferent_junction_id"):
            return GapJunctionConnParameters._gj_sonata_fields
        elif self.has_property("morpho_section_fraction_post"):
            return GapJunctionConnParameters._gj_v2_fields
        else:
            return GapJunctionConnParameters._gj_v1_fields

    def _load_reader(self, gid, reader):
        """ Override the function from base case.
            Call loadSynapseCustom to read customized fields rather than the default fields
            in SynapseReader.mod
        """
        requested_fields = self._get_gapjunction_fields()
        nrow = int(reader.loadSynapseCustom(gid, ",".join(requested_fields)))
        if nrow < 1:
            return nrow, 0, 0, GapJunctionConnParameters.empty

        record_size = len(requested_fields)
        conn_syn_params = GapJunctionConnParameters.create_array(nrow)
        supported_nfields = len(conn_syn_params.dtype) - 1  # location is not read from data
        return nrow, record_size, supported_nfields, conn_syn_params


class GapJunctionSynapseReader(SynapseReader):
    """ Derived from SynapseReader, used for reading GapJunction synapses.
        Factory create() will attempt to instantiate GapJunctionSynToolReader,
        followed by SynReaderNRN.
    """

    @classmethod
    def create(cls, syn_src, conn_type, population=None, *args, **kw):
        """Instantiates a synapse reader, giving preference to GapJunctionSynToolReader
        """
        if cls.is_syntool_enabled():
            log_verbose("[GapJunctionSynReader] Using new-gen SynapseReader.")
            return GapJunctionSynToolReader(syn_src, conn_type, population, **kw)
        else:
            if not ospath.isdir(syn_src) and not syn_src.endswith(".h5"):
                raise SynToolNotAvail(
                    "Can't load new synapse formats without syntool. File: {}".format(syn_src))
            logging.info("[GapJunctionSynReader] Attempting legacy hdf5 reader.")
            return SynReaderNRN(syn_src, conn_type, None, *args, **kw)


class GapJunctionManager(ConnectionManagerBase):
    """
    The GapJunctionManager is similar to the SynapseRuleManager. It will
    open dedicated connectivity files which will have the locations and
    conductance strengths of gap junctions detected in the circuit.
    The user will have the capacity to scale the conductance weights.
    """

    CONNECTIONS_TYPE = SynapseReader.GAP_JUNCTIONS
    _gj_offsets = None
    SynapseReader = GapJunctionSynapseReader

    def __init__(self, gj_conf, target_manager, cell_manager, src_cell_manager=None, **kw):
        """Initialize GapJunctionManager, opening the specified GJ
        connectivity file.

        Args:
            gj_conf: The gaps junctions configuration block / dict
            target_manager: The TargetManager which will be used to query
                targets and translate locations to points
            cell_manager: The cell manager of the target population
            src_cell_manager: The cell manager of the source population
        """
        if cell_manager.circuit_target is None:
            raise ConfigurationError(
                "No circuit target. Required when initializing GapJunctionManager")
        if "Path" not in gj_conf:
            raise ConfigurationError("Missing GapJunction 'Path' configuration")

        super().__init__(gj_conf, target_manager, cell_manager, src_cell_manager, **kw)
        self._src_target_filter = target_manager.get_target(cell_manager.circuit_target)

    def open_synapse_file(self, synapse_file, *args, **kw):
        super().open_synapse_file(synapse_file, *args, **kw)
        src_is_dir = ospath.isdir(synapse_file)
        if src_is_dir or synapse_file.endswith("nrn_gj.h5"):
            gj_dir = synapse_file if src_is_dir else ospath.dirname(synapse_file)
            self._gj_offsets = self._compute_gj_offsets(gj_dir)

    def _compute_gj_offsets(self, gj_dir):
        log_verbose("Computing gap-junction offsets from gjinfo.txt")
        gjfname = ospath.join(gj_dir, "gjinfo.txt")
        assert ospath.isfile(gjfname), "Nrn-format GapJunctions require gjinfo.txt: %s" % gj_dir
        gj_offsets = compat.Vector("I")
        gj_sum = 0

        for line in open(gjfname):
            gj_offsets.append(gj_sum)  # fist gid has no offset. the final total is not used
            gid, offset = map(int, line.strip().split())
            gj_sum += 2 * offset

        return gj_offsets

    def create_connections(self, *_, **_kw):
        """Gap Junctions dont use connection blocks, connect all belonging to target"""
        self.connect_all()

    def configure_connections(self, conn_conf):
        """Gap Junctions dont configure_connections"""
        pass

    def finalize(self, *_, **_kw):
        super().finalize(conn_type="Gap-Junctions")

    def _finalize_conns(self, final_tgid, conns, *_, **_kw):
        metype = self._cell_manager.getMEType(final_tgid)

        if self._gj_offsets is None:
            for conn in reversed(conns):
                conn.finalize_gap_junctions(metype, 0, 0)
        else:
            raw_tgid_0base = final_tgid - self.target_pop_offset - 1
            src_pop_offset = self.src_pop_offset
            t_gj_offset = self._gj_offsets[raw_tgid_0base]   # Old nrn_gj uses offsets
            for conn in reversed(conns):
                raw_sgid_0base = conn.sgid - src_pop_offset - 1
                conn.finalize_gap_junctions(metype, t_gj_offset, self._gj_offsets[raw_sgid_0base])
        return len(conns)
