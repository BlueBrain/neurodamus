"""
Module which defines and handles Glia Cells and connectivity
"""
import libsonata
import logging
import numpy as np
import os.path

from .cell_distributor import CellDistributor
from .metype import BaseCell
from .connection import Connection
from .connection_manager import ConnectionManagerBase
from .core import EngineBase
from .core import NeurodamusCore as Nd, MPI
from .core.configuration import GlobalConfig, LogLevel
from .io.sonata_config import ConnectionTypes
from .io.synapse_reader import SynapseParameters, SonataReader
from .utils import bin_search
from .utils.logging import log_verbose
from .utils.pyutils import append_recarray
from .morphio_wrapper import MorphIOWrapper


class Astrocyte(BaseCell):
    __slots__ = ('_glut_list', '_secidx2names', '_nseg_warning')

    def __init__(self, gid, meinfos, circuit_conf):
        """Instantiate a new Cell from node info."""
        super().__init__(gid, meinfos, None)
        morpho_path = circuit_conf.MorphologyPath
        morph_filename = meinfos.morph_name + "." + circuit_conf.MorphologyType
        morph_file = os.path.join(morpho_path, morph_filename)
        self._cellref, self._glut_list, self._secidx2names, self._nseg_warning \
            = self._init_cell(gid, morph_file)
        self._cellref.gid = gid

    gid = property(lambda self: int(self._cellref.gid),
                   lambda self, val: setattr(self._cellref, 'gid', val))

    endfeet = property(lambda self: self._cellref.endfeet)

    def create_endfeet(self, size):
        """
            Create endfeet sections in the cell's context.
            :param size: number of sections to create
        """
        self._cellref.execute_commands(['create endfoot[{}]'.format(size),
                                        'endfeet = new SectionList()',
                                        'forsec "endfoot" endfeet.append'])

    @staticmethod
    def _er_as_hoc(morph_wrap):
        """
            Create hoc commands for Endoplasmic Reticulum data.
            :param morph_wrap: MorphIOWrapper object holding MorphIO morphology object
        """

        '''
            For example:
                dend[0] { er_area_mcd = 0.21 er_vol_mcd = 0.4 }
                dend[1] { er_area_mcd = 0.56 er_vol_mcd = 0.23 }
                dend[2] { er_area_mcd = 1.3 er_vol_mcd = 0.78 }
                dend[3] { er_area_mcd = 0.98 er_vol_mcd = 1.1 }
        '''
        cmds = []
        cmds.extend(("{} {{ er_area_mcd = {:g} er_volume_mcd = {:g} }}".format(
            morph_wrap.section_index2name_dict[sec_index],
            er_area,
            er_vol)
            for sec_index, er_area, er_vol in zip(
            morph_wrap.morph.endoplasmic_reticulum.section_indices,
            morph_wrap.morph.endoplasmic_reticulum.surface_areas,
            morph_wrap.morph.endoplasmic_reticulum.volumes)))
        return cmds

    @staticmethod
    def _truncated_cone_surface_areas(perimeters, seg_lengths):
        radii = perimeters / (2. * np.pi)
        radii_starts = radii[:-1]
        radii_ends = radii[1:]
        slant_heights = np.sqrt(seg_lengths ** 2 + (radii_ends - radii_starts) ** 2)
        return np.pi * (radii_starts + radii_ends) * slant_heights

    @staticmethod
    def _truncated_cone_volumes(diameters, seg_lengths):
        r_begs = 0.5 * diameters[:-1]
        r_ends = 0.5 * diameters[1:]
        return (1. / 3.) * np.pi * (r_begs ** 2 + r_begs * r_ends + r_ends ** 2) * seg_lengths

    @staticmethod
    def _mcd_section_parameters(section):
        points = section.points
        diameters = section.diameters
        perimeters = section.perimeters

        segment_lengths = np.linalg.norm(points[1:] - points[:-1], axis=1)
        segment_volumes = Astrocyte._truncated_cone_volumes(diameters, segment_lengths)
        segment_surface_areas = Astrocyte._truncated_cone_surface_areas(perimeters, segment_lengths)

        total_length = segment_lengths.sum()

        # representing the entire section as a single cylinder
        perimeter = segment_surface_areas.sum() / total_length
        cross_sectional_area = segment_volumes.sum() / total_length

        return section.id, perimeter, cross_sectional_area

    @staticmethod
    def _secparams_as_hoc(morph_wrap):
        """
            Create hoc commands for section parameters (perimeters & cross-sectional area)
            :param morph_wrap: MorphIOWrapper object holding MorphIO morphology object

            For example:
                dend[0] { perimeter_mcd = 32 cross_sectional_area_mcd = 33}
        """
        cmds = []
        cmds.extend(("{} {{ perimeter_mcd = {:g} cross_sectional_area_mcd = {:g} }}".format(
            morph_wrap.section_index2name_dict[morph_sec_index + 1],
            sec_perimeter,
            sec_xsect_area)
            for morph_sec_index, sec_perimeter, sec_xsect_area in
            (Astrocyte._mcd_section_parameters(sec) for sec in morph_wrap.morph.sections)))
        return cmds

    @staticmethod
    def _init_cell(gid, morph_file):
        c = Nd.Cell(gid)
        m = MorphIOWrapper(morph_file)
        c.AddHocMorph(m.morph_as_hoc())

        glut_list = []
        c.geom_nseg_fixed()
        c.geom_nsec()  # To recount all sections

        # Insert mechanisms and populate holder lists
        logging.debug("Instantiating NGV cell gid=%d", gid)
        nseg_reduce_instance = 0  # temporary field until proper handling of nseg > 1 implemented

        for sec in c.all:
            if sec.nseg > 1:
                nseg_reduce_instance = 1
                sec.nseg = 1
            sec.insert("mcd")
            glut = Nd.GlutReceive(sec(0.5), sec=sec)
            Nd.setpointer(glut._ref_glut, 'glu2', sec(0.5).mcd)
            glut_list.append(glut)

        # Endoplasmic reticulum
        c.execute_commands(Astrocyte._er_as_hoc(m))

        # Section parameters (perimeters & cross-sectional area)
        c.execute_commands(Astrocyte._secparams_as_hoc(m))

        # Print out mcd section parameters
        # for sec in c.all:
        #     self._show_mcd()

        # Soma receiver must be last element in the glut_list
        soma = c.soma[0]
        soma.insert("mcd")
        glut = Nd.GlutReceiveSoma(soma(0.5), sec=soma)
        Nd.setpointer(glut._ref_glut, 'glu2', soma(0.5).mcd)
        glut_list.append(glut)
        return c, glut_list, m.section_index2name_dict, nseg_reduce_instance

    def _show_mcd(sec):
        if not hasattr(sec(0.5), 'mcd'):
            logging.info("No mcd mechanism found")
            return
        logging.info("{}: \tP={:.4g}\tX-Area={:.4g}\tER[area={:.4g}\tvol={:.4g}]".format(
            sec,
            sec(0.5).mcd.perimeter,
            sec(0.5).mcd.cross_sectional_area,
            sec(0.5).mcd.er_area,
            sec(0.5).mcd.er_volume)
        )

    def set_pointers(self):
        glut_list = self._glut_list
        c = self._cellref
        index = 0

        for sec in c.all:
            glut = glut_list[index]
            index += 1
            Nd.setpointer(glut._ref_glut, 'glu2', sec(0.5).mcd)
        soma = c.soma[0]
        glut = glut_list[index]
        Nd.setpointer(glut._ref_glut, 'glu2', soma(0.5).mcd)

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
    # the same Node formats and Cell morphologies.
    # The difference lies only in the Cell Type
    CellType = Astrocyte
    _sonata_with_extra_attrs = False

    def post_stdinit(self):
        nseg_warning = 0
        for cell in self.cells:
            cell.set_pointers()
            nseg_warning += cell._nseg_warning

        MPI.allreduce(nseg_warning, MPI.SUM)
        if nseg_warning:
            logging.warning("Astrocyte sections with multiple compartments not yet supported."
                            "Reducing %d to 1", nseg_warning)


class NeuroGliaConnParameters(SynapseParameters):
    _synapse_fields = (
        "tgid",
        "synapse_id",
        "astrocyte_section_id",
        "astrocyte_segment_id",
        "astrocyte_segment_offset"
    )


class NeuroGlialSynapseReader(SonataReader):
    LOOKUP_BY_TARGET_IDS = False
    Parameters = NeuroGliaConnParameters
    custom_parameters = set()


USE_COMPAT_SYNAPSE_ID = True
"""
Compat Synapse ID means the id is taken directly as the virtual gid, without any gap
optimization. This is still required when nrank > 1
"""


class NeuroGlialConnection(Connection):
    neurons_not_found = set()
    neurons_attached = set()

    def add_synapse(self, syn_tpoints, params_obj, syn_id=None):
        # Only store params. Glia have mechanisms pre-created
        self._synapse_params = append_recarray(self._synapse_params, params_obj)

    def finalize(self, astrocyte, base_Seed, *, base_connections=None, **kw):
        """
        Bind each glia connection to synapses in connections target cells via
        the assigned unique gid.
        """

        # TODO: Currently it receives the base_connections object to look (bin search)
        # for the sinapse to attach to. However since target cells and Glia might be
        # distributed differently across MPI ranks, this is bound to work in a single rank.
        # For the moment we fallback to using the original synapse id.

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
            if USE_COMPAT_SYNAPSE_ID:
                syn_gid = 1_000_000 + syn_params.synapse_id
            else:
                tgid_conns = base_connections.get(syn_params.connected_neurons_post)
                syn_gid = self._find_neuron_endpoint_id(syn_params, tgid_conns)
                if syn_gid is None:
                    continue

            glut_obj = glut_list[int(syn_params.astrocyte_section_id)]
            netcon = pc.gid_connect(syn_gid, glut_obj)
            netcon.delay = 0.05
            self._netcons.append(netcon)

            # Soma netcon (last glut_list)
            logging.debug("[NGV] Conn %s linking synapse id %d to Astrocyte", self, syn_gid)
            netcon = pc.gid_connect(syn_gid, glut_list[-1])
            netcon.delay = 0.05
            self._netcons.append(netcon)

            n_bindings += 1
        return n_bindings

    def _find_neuron_endpoint_id(self, syn_params, conns):
        """
        Gets the endpoint id on the neuronal synapse.
        To avoid gaps, the optimized version has to search along the existing connections
        for the given synapse id.

        """
        if not conns:
            self.neurons_not_found.add(self.sgid)
            return None

        if conns[0].synapses_offset > syn_params.synapse_id:
            logging.error("Data Error: TGID %d syn offset (%d) is larger than syn gid %d",
                          conns[0].tgid, conns[0].synapses_offset, syn_params.synapse_id)
            return None

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
        return syn_gid


class NeuroGliaConnManager(ConnectionManagerBase):
    """A Connection Manager for Neuro-Glia connections

    NOTE: We assume the only kind of connections for Glia are Neuron-Glia
    If one day Astrocytes have connections among themselves a sub ConnectionManager
    must be used
    """

    CONNECTIONS_TYPE = ConnectionTypes.NeuroGlial
    conn_factory = NeuroGlialConnection
    SynapseReader = NeuroGlialSynapseReader

    def __init__(self, circuit_conf, target_manager, cell_manager, src_cell_manager=None, **kw):
        kw.pop("load_offsets")
        super().__init__(circuit_conf, target_manager, cell_manager, src_cell_manager, **kw)

    def _add_synapses(self, cur_conn, syns_params, syn_type_restrict=None, base_id=0):
        for syn_params in syns_params:
            cur_conn.add_synapse(None, syn_params)

    def finalize(self, base_Seed=0, *_):
        """
        Instantiate connections to the simulator.

        This is a two-step process:
        First we create netcons to listen events on target synapses.Ustate,
        and assign them a virtual gid.
        Second, as part of NeuroGlialConnection.finalize(), we attach netcons to
        the target glia cell, listening for "signals" from the virtual gids.
        """
        logging.info("Creating virtual cells on target Neurons for coupling to GLIA...")
        base_manager = next(self._src_cell_manager.connection_managers.values())

        if USE_COMPAT_SYNAPSE_ID:
            total_created = self._create_synapse_ustate_endpoints(base_manager)
        else:
            total_created = self._create_synapse_ustate_endpoints_optimized(base_manager)

        logging.info("(RANK 0) Created %d Virtual GIDs for synapses.", total_created)

        super().finalize(base_Seed,
                         base_connections=base_manager.get_population(0),
                         conn_type="NeuronGlia connections")

        if not USE_COMPAT_SYNAPSE_ID:
            logging.info("Target cells coupled to: %s", NeuroGlialConnection.neurons_attached)

        if NeuroGlialConnection.neurons_not_found:
            logging.warning("Missing cells to couple Glia to: %d",
                            len(NeuroGlialConnection.neurons_not_found))

    def _create_synapse_ustate_endpoints(self, base_manager):
        """
        Creating an endpoint netcon to listen for events in synapse.Ustate
        Netcon ids are directly the synapse id (hence we are limited in number space)
        """
        pc = Nd.pc
        syn_gid_base = 1_000_000  # Below 1M is reserved for cell ids
        total_created = 0

        def ustate_event_handler(tgid, syn_gid):
            return lambda: print(f"[gid={tgid}] Ustate netcon event. Spiking via v-gid:", syn_gid)

        for conn in base_manager.all_connections():
            syn_objs = conn.synapses
            tgid_syn_offset = syn_gid_base + conn.synapses_offset
            logging.debug("Tgid: %d, Base syn offset: %d", conn.tgid, tgid_syn_offset)

            for param_i, sec in conn.sections_with_synapses:
                if conn.synapse_params[param_i].synType >= 100:  # Only Excitatory
                    synapse_gid = tgid_syn_offset + param_i
                    pc.set_gid2node(synapse_gid, MPI.rank)
                    netcon = Nd.NetCon(syn_objs[param_i]._ref_Ustate, None, 0, 0, 1.1, sec=sec)
                    pc.cell(synapse_gid, netcon)
                    if GlobalConfig.verbosity >= LogLevel.DEBUG:
                        netcon.record(ustate_event_handler(conn.tgid, synapse_gid))

                    conn._netcons.append(netcon)
                    total_created += 1

        return total_created

    def _create_synapse_ustate_endpoints_optimized(self, base_manager):
        # This is an optimized version to avoid using the global synapse id
        # as the virtual gid, which would strongly limit the size of the circuits.
        pc = Nd.pc
        syn_gid_base = 100_000_000  # Below 100M is reserved for cell ids

        # Get the total amount of synapses per rank and compute the base
        # synapse_gid (sum synapse count in all previous ranks)
        syn_counts = Nd.Vector(MPI.size)
        local_syn_count = sum(len(conn.synapses) for conn in base_manager.all_connections())
        MPI.allgather(local_syn_count, syn_counts)
        if MPI.rank > 0:
            syn_gid_base += syn_counts.sum(0, MPI.rank - 1)

        for conn in base_manager.all_connections():
            # Conn objects have a placeholder (syn_gid_base) for storing the id
            # for its first synapse. This enables getting to the synapse directly
            conn.syn_gid_base = syn_gid_base

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

            # Next base is incremented number of synapses (last syn_i + 1)
            if syn_i is not None:
                syn_gid_base += syn_i + 1

        return syn_gid_base - 100_000_000  # total created


class GlioVascularManager(ConnectionManagerBase):
    CONNECTIONS_TYPE = ConnectionTypes.GlioVascular
    InnerConnectivityCls = None  # No synapses

    def __init__(self, circuit_conf, target_manager, cell_manager, src_cell_manager=None, **kw):

        if cell_manager.circuit_target is None:
            raise Exception(
                "Circuit target is required for GlioVascular projections")
        if "Path" not in circuit_conf:
            raise Exception("Missing GlioVascular Sonata file via 'Path' configuration")

        if "VasculaturePath" not in circuit_conf:
            logging.warning("Missing Vasculature Sonata file via 'VasculaturePath' configuration")

        super().__init__(circuit_conf, target_manager, cell_manager, src_cell_manager, **kw)
        self._astro_ids = self._cell_manager.local_nodes.raw_gids()
        self._gid_offset = self._cell_manager.local_nodes.offset

    def open_edge_location(self, sonata_source, circuit_conf, **__):
        logging.info("GlioVascular sonata file %s", sonata_source)
        # sonata files can have multiple populations. In building we only use one
        # per file, hence this two lines below to access the first and only pop in
        # the file
        edge_file, *pop = sonata_source.split(":")
        storage = libsonata.EdgeStorage(edge_file)
        pop_name = pop[0] if pop else list(storage.population_names)[0]
        self._gliovascular = storage.open_population(pop_name)

        if "VasculaturePath" in circuit_conf:
            storage = libsonata.NodeStorage(circuit_conf["VasculaturePath"])
            pop_name = list(storage.population_names)[0]
            self._vasculature = storage.open_population(pop_name)

    def create_connections(self, *_, **__):
        logging.info("Creating GlioVascular virtual connections")
        # Retrieve endfeet selections for GLIA gids on the current processor
        for astro_id in self._astro_ids:
            self._connect_endfeet(astro_id)

    def _connect_endfeet(self, astro_id):

        endfeet = self._gliovascular.afferent_edges(astro_id-1)  # 0-based for libsonata API
        if endfeet.flat_size > 0:
            # Get endfeet input
            parent_section_ids = self._gliovascular.get_attribute('astrocyte_section_id', endfeet)
            lengths = self._gliovascular.get_attribute('endfoot_compartment_length', endfeet)
            diameters = self._gliovascular.get_attribute('endfoot_compartment_diameter', endfeet)
            perimeters = self._gliovascular.get_attribute('endfoot_compartment_perimeter', endfeet)

            # Retrieve instantiated astrocyte
            astrocyte = self._cell_manager.gid2cell[astro_id + self._gid_offset]

            # Create endfeet SectionList
            astrocyte.create_endfeet(parent_section_ids.size)

            # Iterate through endfeet: insert mechanisms, set values and connect to parent section
            for sec, parent_section_id, l, d, p in zip(astrocyte.endfeet,
                                                       parent_section_ids,
                                                       lengths,
                                                       diameters,
                                                       perimeters):
                sec.L = l
                sec.diam = d
                # here we just insert the mechanism. Population comes after
                sec.insert('vascouplingB')
                sec.insert('mcd')
                sec(0.5).mcd.perimeter = p
                glut = Nd.GlutReceive(sec(0.5), sec=sec)
                Nd.setpointer(glut._ref_glut, 'glu2', sec(0.5).mcd)
                # because soma glut must be the last
                astrocyte._glut_list.insert(len(astrocyte._glut_list)-1, glut)
                exec('parent_sec = astrocyte.CellRef.{}; sec.connect(parent_sec)'.format(
                    astrocyte._secidx2names[parent_section_id + 1]))
                # astrocyte.CellRef.all.append(sec)
            # Some useful debug lines:
            # cell = astrocyte.CellRef
            # logging.warn(str(cell.endfeet.printnames()))  # print endfeet section list names
            # logging.warn(str(cell.all.printnames())) #  print astrocyte names for "all" sections
            # logging.warn(str(Nd.h.topology()))  # print astrocyte topology
            # Nd.h('forall psection()')

            assert self._gliovascular.source == "vasculature"
            if hasattr(self, "_vasculature"):

                vasc_node_ids = libsonata.Selection(self._gliovascular.source_nodes(endfeet))
                assert vasc_node_ids.flat_size == len(list(astrocyte.endfeet))
                d_vessel_starts = self._vasculature.get_attribute("start_diameter", vasc_node_ids)
                d_vessel_ends = self._vasculature.get_attribute("end_diameter", vasc_node_ids)

                for sec, d_vessel_start, d_vessel_end in zip(
                        astrocyte.endfeet, d_vessel_starts, d_vessel_ends
                ):
                    # /4 is because we have an average of diameters and the output is a radius
                    sec(0.5).vascouplingB.R0pas = (d_vessel_start + d_vessel_end) / 4

    def finalize(self, *_, **__):
        pass  # No synpases/netcons


class NGVEngine(EngineBase):
    CellManagerCls = AstrocyteManager
    ConnectionTypes = {
        ConnectionTypes.NeuroGlial: NeuroGliaConnManager,
        ConnectionTypes.GlioVascular: GlioVascularManager
    }
