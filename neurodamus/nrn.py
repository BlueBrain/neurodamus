from __future__ import absolute_import
""" 
A wrapper over the neuron simulator.
"""

# The neuron hoc interpreter
# Is it a global var since only one can exist and thus can be imported anywhere
_h = None
"""The Neuron hoc interpreter.
Be sure to use after having called init() before.
"""
_mods_loaded = []
"""A list of modules already loaded"""


def get_init(hoc_mods=()):
    """Initializes neuron and its hoc interpreter which is returned
    """
    global _h
    if isinstance(hoc_mods, str):
        hoc_mods = (hoc_mods,)
    if _h is None:
        return _init(hoc_mods)
    for mod in hoc_mods:
        use_mod(mod)
    return _h


def _init(hoc_mods):
    global _h
    import neuron
    _h = neuron.h
    _h.load_file("stdrun.hoc")
    _h.stdinit()
    for mod in hoc_mods:
        use_mod(mod)
    return _h


def use_mod(mod_name):
    if mod_name in _mods_loaded:
        return
    _h.load_file(mod_name)
    _mods_loaded.append(mod_name)


class HocEntity(object):
    _hoc_cls = None
    # The hoc hook for executing code within our context
    _hoc_cldef = """ 
begintemplate {cls_name}
    proc exec_with_context() {{
        execute($s1)
    }}
endtemplate {cls_name}
"""

    def __new__(cls, *args, **kw):
        if not cls._hoc_cls:
            h = get_init()
            # Create a HOC template to be able to use as context
            h(cls._hoc_cldef.format(cls_name=cls.__name__))
            cls._hoc_cls = getattr(h, cls.__name__)

        o = object.__new__(cls)
        o._hoc_obj = cls._hoc_cls()
        return o

    @property
    def h(self):
        return self._hoc_obj

    def exec_within_context(self, hoc_cmd):
        self.h.exec_within_context(hoc_cmd)


class SectionList(object):
    """A SectionList wrapper providing convenience methods, inc len()
    """
    __slots__ = ('_hlist',)

    def __init__(self, hoc_section_list):
        self._hlist = hoc_section_list

    def __len__(self):
        return sum(1 for _ in self._hlist)

    def __getattr__(self, item):
        return object.__getattribute__(self._hlist, item)
