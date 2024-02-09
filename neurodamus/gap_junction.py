"""
Main module for handling and instantiating synaptical connections
"""
from __future__ import absolute_import
import numpy as np
from os import path as ospath

from .connection_manager import ConnectionManagerBase
from .core.configuration import ConfigurationError
from .io.sonata_config import ConnectionTypes
from .io.synapse_reader import SonataReader, SynapseParameters
from .utils import compat
from .utils.logging import log_verbose


class GapJunctionConnParameters(SynapseParameters):
    # Attribute names of synapse parameters, consistent with the normal synapses
    _synapse_fields = ("sgid", "isec", "offset", "weight", "D", "F", "ipt", "location")

    @classmethod
    def create_array(cls, length):
        npa = np.recarray(length, cls.dtype)
        npa.location = 0.5
        return npa


class GapJunctionSynapseReader(SonataReader):
    Parameters = GapJunctionConnParameters
    parameter_mapping = {
        "weight": "conductance",
        "D": "efferent_junction_id",
        "F": "afferent_junction_id",
    }
    # "isec", "ipt", "offset" are custom parameters as in base class


class GapJunctionManager(ConnectionManagerBase):
    """
    The GapJunctionManager is similar to the SynapseRuleManager. It will
    open dedicated connectivity files which will have the locations and
    conductance strengths of gap junctions detected in the circuit.
    The user will have the capacity to scale the conductance weights.
    """

    CONNECTIONS_TYPE = ConnectionTypes.GapJunction
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
        self._src_target_filter = target_manager.get_target(cell_manager.circuit_target,
                                                            src_cell_manager.population_name)

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
        gj_offsets = compat.Vector()
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
        metype = self._cell_manager.get_cell(final_tgid)

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
