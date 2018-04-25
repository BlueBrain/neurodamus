from __future__ import absolute_import
from lazy_property import LazyProperty
import logging
from.utils import classproperty
from .commands import GlobalConfig
from . import _neuron


class Cell(_neuron.HocEntity):
    # We must override the basic tpl definition
    # Since the morphology parser expects several arrays
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

    proc exec_within_context() {{
        execute($s1)
    }}

endtemplate {cls_name}"""

    _section_lists = ('all', 'somatic', 'axonal', 'basal', 'apical')
    _section_arrays = ('soma', 'axon', 'dend', 'apic', 'myelin')

    def __init__(self, gid=0, morpho=None):
        # type: (int, str) -> None
        h = _neuron.get_init()
        self.gid = gid
        self._soma = None
        # Sections
        if morpho is not None:
            self.load_morphology(morpho)

    def load_morphology(self, morpho_path):
        # type: (str) -> None
        h = _neuron.get_init("import3d.hoc")
        # try and determine format
        if morpho_path.endswith(('hoc', 'HOC')):
            h.load_file(1, morpho_path)
        else:
            if morpho_path.endswith(('asc', 'ASC')):
                imp = h.Import3d_Neurolucida3()
                if not GlobalConfig.verbosity:
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
            except:
                raise Exception("Error loading morphology. Verify Neuron outputs")

            imprt.instantiate(self.h)
            self._soma = self.h.soma[0]

    @LazyProperty
    def all(self):
        return SectionList(self.h.all)

    @property
    def soma(self):
        return self._soma

    # Other properties use neuron structures as source
    # So that we don't need to handle sync issues

    @LazyProperty
    def axons(self):
        return SectionList(self.h.axonal, self.h.axon)

    @LazyProperty
    def dendrites(self):
        return SectionList(self.h.basal, self.h.basal)

    @LazyProperty
    def apical_dendrites(self):
        return SectionList(self.h.apical, self.h.aic)

    @staticmethod
    def show_topology():
        h = _neuron.get_init()
        h.topology()

    class Builder:
        """Enables building a cell from soma/axon blocks"""
        # Cell Section builder
        class Section:
            def __init__(self, name, length, n_segments=None, **params):
                # type: (str, float, int, dict) -> None
                """Creates a new section
                Args:
                    name: Section name
                    **params: Additional properties to be set on the hoc object
                """
                h = _neuron.get_init()
                self.parent = None
                self.this = h.Section(name=name)
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
                sec = self.get_root()
                if sec.parent is None:
                    raise RuntimeError("Disconnected subtree. Attach to a CellBuilder root node")
                assert sec.parent is True, "Unable to find Cell root"
                c = Cell()
                c.h.all.wholetree(sec.this)
                c._soma = sec.this
                # This requires further init to fill axonal, apical... etc
                return c

        @classmethod
        def add_root(cls, name, diam, **params):
            root = cls.Section(name, length=diam, diam=diam, **params)
            root.parent = True  # this is root
            return root


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
