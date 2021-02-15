"""
Module which defines and handles Glia Cells and connectivity
"""
import logging
import os.path

from .cell_distributor import CellDistributor
from .metype import BaseCell
from .connection import Connection
from .connection_manager import ConnectionManagerBase
from .core import EngineBase
from .core import NeurodamusCore as Nd, MPI
from .core.configuration import GlobalConfig
from .io.synapse_reader import SynapseParameters, SynReaderSynTool
from .utils import bin_search
from .utils.logging import log_verbose


class Astrocyte(BaseCell):
    __slots__ = ('_glut_list',)

    def __init__(self, gid, meinfos, circuit_conf):
        """Instantiate a new Cell from mvd/node info."""
        super().__init__(gid, meinfos, None)
        morpho_path = circuit_conf.MorphologyPath
        morph_filename = meinfos.morph_name + "." + circuit_conf.MorphologyType
        morph_file = os.path.join(morpho_path, morph_filename)
        self._cellref, self._glut_list = self._init_cell(gid, morph_file)
        self._cellref.gid = gid

    gid = property(lambda self: int(self._cellref.gid),
                   lambda self, val: setattr(self._cellref, 'gid', val))

    @staticmethod
    def _init_cell(gid, morph_file):
        c = Nd.Cell(gid, morph_file)
        glut_list = []
        c.geom_nseg_fixed()
        c.geom_nsec()  # To recount all sections

        # Insert mechanisms and populate holder lists
        logging.debug("Instantiating NGV cell gid=%d", gid)
        for sec in c.all:
            sec.insert("mcd")
            glut = Nd.GlutReceive(sec(0.5), sec=sec)
            Nd.setpointer(glut._ref_glut, 'glu2', sec(0.5).mcd)
            glut_list.append(glut)

        soma = c.soma[0]
        soma.insert("glia_2013")
        glut = Nd.GlutReceiveSoma(soma(0.5), sec=soma)
        Nd.setpointer(glut._ref_glut, 'glu2', soma(0.5).glia_2013)
        glut_list.append(glut)
        return c, glut_list

    @property
    def glut_list(self) -> list:
        return self._glut_list

    def connect2target(self, target_pp=None):
        return Nd.NetCon(self._cellref.soma[0](1)._ref_v, target_pp,
                         sec=self._cellref.soma[0])

    @staticmethod
    def getThreshold():
        return 0.114648

    @staticmethod
    def getVersion():
        return 99


class AstrocyteManager(CellDistributor):
    # Cell Manager is the same as CellDistributor, so it's able to handle
    # the same Node formats (mvd, ...) and Cell morphologies.
    # The difference lies only in the Cell Type
    CellType = Astrocyte
    _sonata_with_extra_attrs = False


class NeuroGliaConnParameters(SynapseParameters):
    _synapse_fields = [
        "connected_neurons_post",
        "synapse_id",
        "morpho_section_id_pre",
        "morpho_segment_id_pre",
        "morpho_offset_segment_pre"
    ]


class NeuroGlialSynapseReader(SynReaderSynTool):

    def _load_synapse_parameters(self, glia_gid):
        reader = self._syn_reader
        req_fields_str = ", ".join(NeuroGliaConnParameters._synapse_fields)
        nrow = int(reader.loadSynapseCustom(glia_gid, req_fields_str, True))
        log_verbose("Edges for glia gid %d: %d", glia_gid, nrow)
        if nrow < 1:
            return NeuroGliaConnParameters.empty

        conn_syn_params = NeuroGliaConnParameters.create_array(nrow)
        syn_params_mtx = conn_syn_params.view(('f8', len(conn_syn_params.dtype)))
        tmpParams = Nd.Vector(len(conn_syn_params.dtype))

        for syn_i in range(nrow):
            reader.getSynapse(syn_i, tmpParams)
            syn_params_mtx[syn_i] = tmpParams.as_numpy()

        return conn_syn_params

    def get_synapse_parameters(self, glia_gid):
        """Returns NeuroGlia synapses parameters for a given astrocyte
        """
        # Direct load and return. Cache is not worth being used
        # NOTE: thanks to _gid_offset, glia gid here is already offset
        return self._load_synapse_parameters(glia_gid)


class NeuroGlialConnection(Connection):
    neurons_not_found = set()
    neurons_attached = set()

    def add_synapse(self, syn_tpoints, params_obj, syn_id=None):
        # Only store params. Glia have mechanisms pre-created
        self._synapse_params.append(params_obj)

    def finalize(self, astrocyte, base_Seed, *, base_connections=None, **kw):
        """Finalize binds each glia connection to synapses in
        connections target cells vi the assigned unique gid
        """
        self._netcons = []
        glut_list = astrocyte.glut_list
        n_bindings = 0
        pc = Nd.pc

        if GlobalConfig.debug_conn:
            if GlobalConfig.debug_conn == [self.tgid]:
                logging.debug("Finalizing conn %s. N params: %d", self, len(self._synapse_params))
            elif GlobalConfig.debug_conn == [self.sgid, self.tgid]:
                logging.debug("Finalizing conn %s. Params:\n%s", self, self._synapse_params)

        for syn_params in self._synapse_params:
            conns = base_connections.get(syn_params.connected_neurons_post)
            if not conns:
                # Target Neuron not instantiated. log to warn later?
                self.neurons_not_found.add(self.sgid)
                continue

            if conns[0].synapses_offset > syn_params.synapse_id:
                logging.error("Data Error: TGID %d syn offset (%d) is larger than syn gid %d",
                              conns[0].tgid, conns[0].synapses_offset, syn_params.synapse_id)
                continue

            c_i = bin_search(conns, syn_params.synapse_id, lambda c: c.synapses_offset)
            # non-exact matches are attached to the left conn (base offset)
            if len(conns) == c_i or syn_params.synapse_id < conns[c_i].synapses_offset:
                c_i -= 1
            conn = conns[c_i]
            self.neurons_attached.add(conn.tgid)

            # syn_gid: compute offset and add to the gid_base
            syn_offset = int(syn_params.synapse_id - conn.synapses_offset)
            assert syn_offset >= 0

            syn_gid = conn.syn_gid_base + syn_offset
            syn_id = conn.synapses[syn_offset].synapseID  # visible in the synapse events
            log_verbose("[GLIA ATTACH] id %d to syn Gid %d (conn %d-%d, SynID %d, syn offset %d)",
                        self.tgid, syn_gid, conn.sgid, conn.tgid, syn_id, syn_offset)

            glut_obj = glut_list[int(syn_params.morpho_section_id_pre)]
            netcon = pc.gid_connect(syn_gid, glut_obj)
            netcon.delay = 0.05
            self._netcons.append(netcon)

            # Second netcon (last glut_list)
            netcon = pc.gid_connect(syn_gid, glut_list[-1])
            netcon.delay = 0.05
            self._netcons.append(netcon)

            n_bindings += 1
        return n_bindings


class NeuroGliaConnManager(ConnectionManagerBase):
    """A Connection Manager for Neuro-Glia connections

    NOTE: We assume the only kind of connections for Glia are Neuron-Glia
    If one day Astrocytes have connections among themselves a sub ConnectionManager
    must be used
    """

    CONNECTIONS_TYPE = "NeuroGlial"
    conn_factory = NeuroGlialConnection
    SynapseReader = NeuroGlialSynapseReader

    def _add_synapses(self, cur_conn, syns_params, syn_type_restrict=None, base_id=0):
        for syn_params in syns_params:
            cur_conn.add_synapse(None, syn_params)

    def finalize(self, base_Seed=0, *_):
        pc = Nd.pc
        syn_gid_base = 100_000_000
        syn_counts = Nd.Vector(MPI.size)
        # Compute the base synapse_gid from how many synapses exist in all previous ranks
        base_manager = next(self._src_cell_manager.connection_managers.values())
        local_syn_count = sum(len(conn.synapses) for conn in base_manager.all_connections())
        MPI.allgather(local_syn_count, syn_counts)
        if MPI.rank > 0:
            syn_gid_base += syn_counts.sum(0, MPI.rank - 1)

        logging.info("Creating virtual cells on target Neurons for coupling to GLIA...")

        for conn in base_manager.all_connections():
            conn.syn_gid_base = syn_gid_base  # store this generated offset
            syn_objs = conn.synapses
            syn_i = None
            logging.debug("Tgid: %d, Base syn gid: %d, Base syn offset: %d",
                          conn.tgid, conn.syn_gid_base, conn.synapses_offset)

            for syn_i, (param_i, sec) in enumerate(conn.sections_with_synapses):
                if conn.synapse_params[param_i].synType >= 100:  # Only Excitatory
                    synapse_gid = syn_gid_base + syn_i
                    pc.set_gid2node(synapse_gid, MPI.rank)
                    netcon = Nd.NetCon(syn_objs[syn_i]._ref_Ustate, None, 0, 0, 1.1, sec=sec)
                    pc.cell(synapse_gid, netcon)
                    conn._netcons.append(netcon)
            if syn_i is not None:
                # Keep incrementing
                syn_gid_base += syn_i + 1

        logging.info("(RANK 0) Created %d Virtual GIDs for synapses.", syn_gid_base - 100_000_000)

        super().finalize(base_Seed,
                         base_connections=base_manager.get_population(0),
                         conn_type="NeuronGlia connections")

        logging.info("Target cells coupled to: %s", NeuroGlialConnection.neurons_attached)
        if NeuroGlialConnection.neurons_not_found:
            logging.warning("Missing cells to couple Glia to: %d",
                            len(NeuroGlialConnection.neurons_not_found))


class NGVEngine(EngineBase):
    CellManagerCls = AstrocyteManager
    ConnectionTypes = {
        "NeuroGlial": NeuroGliaConnManager
    }
