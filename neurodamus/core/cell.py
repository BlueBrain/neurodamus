"""
A module implementing a high-level interface to Neuron cells.
"""
from __future__ import absolute_import
import logging
from collections import defaultdict
from .configuration import GlobalConfig
from .mechanisms import Mechanism
from .synapses import _SpikeSource
from . import Neuron

__all__ = ["Cell"]


class Cell(Neuron.HocEntity, _SpikeSource):
    """
    A Cell abstraction. It allows users to instantiate Cells from morphologies or
    create them from scratch using the Cell.Builder
    """
    # We must override the basic tpl definition
    # Since the morphology parser expects several arrays
    __name__ = "Cell"
    _hoc_cldef = """
begintemplate {cls_name}
    public init, exec_within_context
    public soma, dend, apic, axon, myelin
    public synlist, all, apical, basal, somatic, axonal
    objref synlist, all, apical, basal, somatic, axonal, this
    create soma[1], dend[1], apic[1], axon[1], myelin[1]

    proc init() {{
        all     = new SectionList()
        somatic = new SectionList()
        basal   = new SectionList()
        apical  = new SectionList()
        axonal  = new SectionList()
        forall delete_section()
    }}
endtemplate {cls_name}"""

    _section_lists = ('all', 'somatic', 'axonal', 'basal', 'apical')
    _section_arrays = ('soma', 'axon', 'dend', 'apic', 'myelin')

    def __init__(self, gid=0, morpho=None):
        # type: (int, str) -> None
        self.gid = gid
        self._soma = None
        self._axon = None
        self._dend = None
        self._apic = None

        # first indexed by sec_name, then synapse_obj. Leaves are list of NetCon
        # Synapses are relative to receptor cells
        self._synapses = defaultdict(lambda: defaultdict(list))

        self._builder = None  # type: Cell.Builder.Section
        if morpho is not None:
            self.load_morphology(morpho)

    # ---
    def load_morphology(self, morpho_path, export_commands=False):
        """ Creates the cell compartments according to the given morphology
        """
        h = Neuron.require("import3d", "MorphIO")
        # try and determine format
        if morpho_path.endswith(('h5', 'H5')):
            if(export_commands):
                from neurodamus.morphio_wrapper import MorphIOWrapper
                self._commands = MorphIOWrapper(morpho_path).morph_as_hoc()
            h.morphio_read(self.h, morpho_path)
            self._soma = self.h.soma[0]

        elif morpho_path.endswith(('hoc', 'HOC')):
            h.load_file(1, morpho_path)
        else:
            if morpho_path.endswith(('asc', 'ASC')):
                imp = h.Import3d_Neurolucida3()
                if not GlobalConfig.verbosity or export_commands:
                    imp.quiet = 1
            elif morpho_path.endswith(('swc', 'SWC')):
                imp = h.Import3d_SWC_read()
            elif morpho_path.endswith(('xml', 'XML')):
                imp = h.Import3d_MorphML()
            else:
                raise ValueError(
                    "{} is not a recognised morphology file format".format(morpho_path) +
                    "Should be either .hoc, .asc, .swc, .xml!")
            try:
                imp.input(morpho_path)
                imprt = h.Import3d_GUI(imp, 0)
            except Exception:
                raise Exception("Error loading morphology. Verify Neuron outputs")

            if export_commands:
                imprt.instantiate(self.h, 1)
            else:
                imprt.instantiate(self.h)
            # Create shortcuts. Hoc arrays are fine, no need to convert
            self._soma = self.h.soma[0]
            self._dend = self.h.dend
            self._apic = self.h.apic
            self._axon = self.h.axon

            if export_commands:
                self._commands = imprt.commands

    @property
    def all(self):
        return SectionList(self.h.all)

    @property
    def soma(self):
        return self._soma

    # Other properties use neuron structures as source
    # So that we don't need to handle sync issues
    @property
    def axons(self):
        return self._axon or SectionList(self.h.axonal, self.h.axon)

    @property
    def dendrites(self):
        return self._dend or SectionList(self.h.basal, self.h.dend)

    @property
    def apical_dendrites(self):
        return self._apic or SectionList(self.h.apical, self.h.apic)

    @staticmethod
    def show_topology():
        Neuron.h.topology()

    def section_info(self, section):
        c = self.all[section] if isinstance(section, int) else section
        return ("|lenght: {} um\n".format(c.L) +
                "|diameter: {} um\n".format(c.diam) +
                "|N_segments: {}\n".format(c.nseg) +
                "|axial resistance: {} ohm.cm\n".format(c.Ra))

    # ---
    class Builder:
        """Enables building a cell from soma/axon blocks
        """
        class Section:
            SOMA = 0
            DENDRITE = 1
            APICAL_DENDRITE = 2
            AXON = 3

            def __init__(self, name, length, n_segments=None, sec_type=None, **params):
                # type: (str, float, int, int, dict) -> None
                """Creates a new section
                Args:
                    name: Section name
                    **params: Additional properties to be set on the hoc object
                """
                self.parent = None
                self.sec_type = sec_type
                self.this = Neuron.h.Section(name=name)
                self.this.L = length
                if n_segments:
                    self.this.nseg = n_segments
                for param, value in params.items():
                    setattr(self.this, param, value)
                self.sub_nodes = []

            def add(self, name, length, n_segments, **params):
                """Creates a new section as a child of the current section"""
                self.attach(self.__class__(name, length, nseg=n_segments, **params))
                return self

            def add_dendrite(self, name, length, n_segments, apical=False, **params):
                """Creates the first section of a dendrite"""
                self._ensure_soma()
                t = self.APICAL_DENDRITE if apical else self.DENDRITE
                return self.add(name, length, n_segments, sec_type=t, **params)

            def add_axon(self, name, length, n_segments, **params):
                """Creates the first section of an axon"""
                self._ensure_soma()
                return self.add(name, length, n_segments, sec_type=self.AXON, **params)

            def attach(self, *nodes):
                """Adds the given sections as children of the current"""
                for n in nodes:
                    self.sub_nodes.append(n)
                    n.set_parent(self)
                return self

            def append(self, name, length, n_segments, **params):
                """Creates a new section as a child and returns it"""
                newnode = self.__class__(name, length, nseg=n_segments, **params)
                self.attach(newnode)
                return newnode

            def append_dendrite(self, name, length, n_segments, apical=False, **params):
                """Creates the first section of an axon"""
                self._ensure_soma()
                t = self.APICAL_DENDRITE if apical else self.DENDRITE
                return self.append(name, length, n_segments, sec_type=t, **params)

            def append_axon(self, name, length, n_segments, **params):
                """Creates the first section of an axon"""
                self._ensure_soma()
                return self.append(name, length, n_segments, sec_type=self.AXON, **params)

            def chain(self, *nodes):
                """Chain given nodes in parent-child relations, and make it child of the current"""
                parent = self
                for n in nodes:
                    n.set_parent(parent)
                    parent = n
                return parent

            def set_parent(self, parent):
                """Sets the parent of the given section"""
                self.parent = parent
                self.this.connect(parent.this)
                return self

            def get_root(self):
                """Finds the root section by crawling parents up"""
                sec = self
                while isinstance(sec.parent, self.__class__):
                    sec = sec.parent
                return sec

            def create(self):
                """Builds the cell the current section belongs to.
                If no root is found (e.g. disconnected branch) an exception is raised
                """
                sec = self.get_root()  # type: self.__class__
                if sec.parent is None:
                    raise CellCreationError("Disconnected subtree. Attach to a CellBuilder root "
                                            "node")
                # If parent is True we must create the cell. Otherwise use it
                c = Cell() if sec.parent is True else sec.parent
                c.h.all.wholetree(sec=sec.this)

                for branch_sec in sec.sub_nodes:
                    node = branch_sec.this
                    t = branch_sec.sec_type
                    if t == self.SOMA:
                        c.h.somatic.subtree(sec=node)
                        print("Somas: I got", list(c.h.somatic))
                    elif t == self.DENDRITE:
                        c.h.basal.subtree(sec=node)
                        c._dend = list(c.h.basal)
                    elif t == self.APICAL_DENDRITE:
                        c.h.apical.subtree(sec=node)
                        c._apic = list(c.h.apical)
                    elif t == self.AXON:
                        c.h.axonal.subtree(sec=node)
                        c._axon = list(c.h.axonal)
                    else:
                        logging.warning("Branch starting at %s doesnt have a type", node)
                c._soma = sec.this
                c._builder = sec
                return c

            def _ensure_soma(self):
                if self.sec_type is not self.SOMA:
                    raise CellCreationError("Dendrites must start on the soma")

        class DendriteSection(Section):
            def __init__(self, name, length, n_segments=None, apical=False, **params):
                Cell.Builder.Section.__init__(
                    self, name, length, n_segments,
                    sec_type=self.APICAL_DENDRITE if apical else self.DENDRITE,
                    **params)

        class AxonSection(Section):
            def __init__(self, name, length, n_segments=None, **params):
                Cell.Builder.Section.__init__(self, name, length, n_segments, **params)

        @classmethod
        def add_soma(cls, diam, name="soma", **params):
            root = cls.Section(name, length=diam, diam=diam, sec_type=cls.Section.SOMA, **params)
            root.parent = True  # this is root
            return root

    # ---
    def init_soma(self, diam, name="soma", **params):
        """Creates a soma and returns the section builder
        NOTE: you must call create at the end so that the new sections are added to the cell
        """
        soma = self.Builder.add_soma(diam, name, **params)
        soma.parent = self
        return soma

    @property
    def builder(self):
        """Returns the Section builder object, to build additional axon/dendrites"""
        if self._builder is None:
            raise RuntimeError("When the cell is void start creating it with init_soma()")
        return self._builder

    # --------
    # Synapses
    # --------

    def add_synapse(self, src_seg, target_seg, syn_props_obj, **conn_options):
        # type: (Neuron.nrn.Segment, Neuron.nrn.Segment, object, **dict) -> object
        """Adds an incoming synapse from another cell, according to the options."""
        synapse = self.add_synaptic_receptor(syn_props_obj, target_seg)
        netcon = self._add_connection(src_seg, synapse, **conn_options)
        self._synapses[target_seg.sec.name()][synapse].append(netcon)
        return netcon

    def add_synaptic_receptor(self, target_seg, syn_props_obj, **custom):
        """Creates a raw neuron Synapse"""
        synapse = getattr(Neuron.h, type(syn_props_obj).__name__)(target_seg)
        # Applies specific properties
        syn_props_obj.apply(synapse, **custom)
        # Save in the cell synapse dict
        self._synapses[target_seg.sec.name()][synapse] = []
        return synapse

    def connect_to(self, synapse_receptor, threshold=None, delay=None, weight=None):
        """Creates a synapse between the current cell soma extremity and a given synapse receptor
        Notes: This is a relatively low-level f, there is no automatic registration of the netcon
        """
        return self._add_connection(self.soma(1), synapse_receptor,
                                    threshold=threshold, delay=delay, weight=weight)

    @staticmethod
    def _add_connection(src_segment, synapse_receptor, **props):
        nc = Neuron.h.NetCon(src_segment._ref_v, synapse_receptor, sec=src_segment.sec)
        return _SpikeSource._setup_netcon(nc, **props)

    # Declare shortcut
    Mechanisms = Mechanism


class SectionList(object):
    """A SectionList wrapper providing convenience methods, inc len(),
       and consolidating SectionList and hoc section arrays
    """
    __slots__ = ('_hlist', '_harray')

    def __init__(self, hoc_section_list, hoc_section_array=None):
        self._hlist = hoc_section_list
        self._harray = hoc_section_array

    def __len__(self):
        return sum(1 for _ in self._hlist)

    def __getattr__(self, item):
        return object.__getattribute__(self._hlist, item)

    def __getitem__(self, item):
        if self._harray is not None:
            return self._harray[item]
        else:
            logging.info("Indexing list without array. This might be inneficient")
            for i, elem in enumerate(self._hlist):
                if i == item:
                    return elem
            return None

    def __iter__(self):
        return iter(self._hlist)


class CellCreationError(Exception):
    """ An exception for errors in instantiating a cell
    """
