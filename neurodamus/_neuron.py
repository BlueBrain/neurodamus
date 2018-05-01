from __future__ import absolute_import
from .utils import classproperty
from .definitions import Neuron_Stdrun_Defaults


class Neuron:
    """
    A wrapper over the neuron simulator.
    """
    # The neuron hoc interpreter
    # Is it a global var since only one can exist and thus can be imported anywhere
    # We dont import it at module-level to avoid starting neuron
    _h = None
    """The Neuron hoc interpreter.
    Be sure to use after having called init() before.
    """
    _mods_loaded = []
    """A list of modules already loaded"""

    @classproperty
    def h(cls):
        """Initializes neuron and its hoc interpreter which is returned
        """
        return cls._h or cls._init()

    @classmethod
    def _init(cls):
        """Initializes the Neuron simulator"""
        from neuron import h
        cls._h = h
        h.load_file("stdrun.hoc")
        h.init()
        return h

    @classmethod
    def _load_mod(cls, mod_name):
        if mod_name in cls._mods_loaded:
            return
        cls.h.load_file(mod_name)
        cls._mods_loaded.append(mod_name)

    @classmethod
    def with_mods(cls, *hoc_mods):
        for mod in hoc_mods:
            cls._load_mod(mod)
        return cls._h

    @classmethod
    def run_sim(cls, t_stop, *monitored_sections, **params):
        sim = Simulation(**params)
        for sec in monitored_sections:
            sim.record_activity(sec)
        sim.run(t_stop)
        return sim

    HocEntity = None   # type: HocEntity
    Simulation = None  # type: Simulation


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
        if cls is HocEntity:
            raise TypeError("HocEntity must be subclassed")
        if cls._hoc_cls is None:
            h = Neuron.h
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


class Simulation:
    # Some defaults from stdrun
    v_init = Neuron_Stdrun_Defaults.v_init  # -65V

    def __init__(self, **args):
        args.setdefault("v_init", self.v_init)
        self.args = args
        self.t_vec = None
        self.recordings = {}

    def run(self, t_stop):
        h = Neuron.h
        self.t_vec = h.Vector()  # Time stamp vector
        self.t_vec.record(h._ref_t)

        Neuron.h.tstop = t_stop
        for key, val in self.args.items():
            setattr(Neuron.h, key, val)
        Neuron.h.run()

    def run_continue(self, t_stop):
        Neuron.h.continuerun(t_stop)

    def record_activity(self, section, rel_pos=0.5):
        rec_vec = Neuron.h.Vector()
        rec_vec.record(section(rel_pos)._ref_v)
        self.recordings[section.name()] = rec_vec

    def get_voltages_at(self, section):
        return self.recordings[section.name()]

    def plot(self):
        try:
            from matplotlib import pyplot
        except Exception:
            print("Matplotlib is not installed. Please install pyneurodamus[full]")
            return None
        if len(self.recordings) == 0:
            print("No recording sections defined")
            return None
        if not self.t_vec:
            print("No Simulation data. Please run it first.")
            return None

        fig = pyplot.figure()
        ax = fig.add_subplot(1, 1, 1)  # (nrows, ncols, axnum)
        for name, y in self.recordings.items():
            ax.plot(self.t_vec, y, label=name)
        ax.legend()
        fig.show()


# shortcuts
Neuron.HocEntity = HocEntity
Neuron.Simulation = Simulation
