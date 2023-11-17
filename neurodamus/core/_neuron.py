"""
Internal module which defines several wrapper classes for Hoc entities.
They are then available as singletons objects in neurodamus.core package
"""
from __future__ import absolute_import
import logging
import os.path
from contextlib import contextmanager
from .configuration import NeuronStdrunDefaults
from .configuration import GlobalConfig
from .configuration import SimConfig
from ..utils import classproperty


#
# Singleton, instantiated right below
#
class _Neuron(object):
    """A wrapper over the neuron simulator.
    """
    __name__ = "_Neuron"
    _h = None  # We dont import it at module-level to avoid starting neuron
    _hocs_loaded = set()

    # No new attributes. __setattr__ can rely on it
    __slots__ = ()

    @classproperty
    def h(cls):
        """The neuron hoc interpreter, initializing if needed.
        """
        return cls._h or cls._init()

    @classmethod
    def _init(cls, mpi=False):
        """Initializes the Neuron simulator.
        """
        if cls._h is not None:
            return cls._h
        if mpi:
            GlobalConfig.set_mpi()

        from neuron import h
        from neuron import nrn
        cls.__cache = {}
        cls._h = h
        cls.Section = nrn.Section
        cls.Segment = nrn.Segment
        h.load_file("stdrun.hoc")
        h("objref nil")
        h.init()
        return h

    @classmethod
    def load_hoc(cls, mod_name):
        """Loads a hoc module, available in the path.
        """
        if mod_name in cls._hocs_loaded:
            return
        h = (cls._h or cls._init())
        mod_filename = mod_name + ".hoc"
        if not h.load_file(mod_filename):
            raise RuntimeError("Cant load HOC library {}. Consider checking HOC_LIBRARY_PATH"
                               .format(mod_filename))
        cls._hocs_loaded.add(mod_name)

    @classmethod
    def require(cls, *hoc_mods):
        """Load a set of hoc mods by name.
        """
        for mod in hoc_mods:
            cls.load_hoc(mod)
        return cls._h

    @classmethod
    def load_dll(cls, dll_path):
        """Loads a Neuron mod file (typically an .so file in linux).
        """
        h = (cls._h or cls._init())
        rc = h.nrn_load_dll(dll_path)
        if rc == 0:
            raise RuntimeError("Cant load MOD dll {}. Please check LD path and dependencies"
                               .format(dll_path))

    @contextmanager
    def section_in_stack(self, sec):
        """A contect manager to push and pop a section to the Neuron stack.
        """
        sec.push()
        yield
        self.h.pop_section()

    @classmethod
    def run_sim(cls, t_stop, *monitored_sections, **params):
        """A helper to run the simulation, recording the Voltage in the specified cell sections.

        Args:
            t_stop: Stop time
            *monitored_sections: Cell sections to be probed.
            **params: Custom simulation parameters

        Returns: A simulation object
        """
        cls._h or cls._init()
        sim = Simulation(**params)
        for sec in monitored_sections:
            sim.record_activity(sec)
        sim.run(t_stop)
        return sim

    # Properties that are not found here are get / set
    # directly in neuron.h
    def __getattr__(self, item):
        # We use a cache since going down to hoc costs at least 10us
        # Cache is not expected to grow very large. Unbounded for the moment
        if item.startswith("__"):
            return object.__getattribute__(self, item)
        self._h or self._init()
        cache = self.__class__.__cache
        obj = cache.get(item)
        if obj is None:
            obj = getattr(self._h, item)
            if type(obj) is not float:
                cache[item] = obj
        return obj

    def __setattr__(self, key, value):
        try:
            object.__setattr__(self, key, value)
        except AttributeError:
            setattr(self.h, key, value)

    # public shortcuts
    HocEntity = None   # type: HocEntity
    Simulation = None  # type: Simulation
    LoadBalance = None  # type: type
    Section = None
    Segment = None


Neuron = _Neuron()
"""A singleton wrapper for the Neuron library"""


class HocEntity(object):
    _hoc_cls = None
    _hoc_obj = None
    _hoc_cldef = """
begintemplate {cls_name}
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


class Simulation(object):
    # Some defaults from stdrun
    v_init = NeuronStdrunDefaults.v_init  # -65V

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
        if isinstance(section, Neuron.Segment):
            segment = section
            name = str(segment.sec)
        else:
            segment = section(rel_pos)
            name = section.name()

        rec_vec = Neuron.h.Vector()
        rec_vec.record(segment._ref_v)
        self.recordings[name] = rec_vec

    def get_voltages_at(self, section):
        return self.recordings[section.name()]

    def plot(self):
        try:
            from matplotlib import pyplot
        except Exception:
            logging.error("Matplotlib is not installed. Please install pyneurodamus[full]")
            return None
        if len(self.recordings) == 0:
            logging.error("No recording sections defined")
            return None
        if not self.t_vec:
            logging.error("No Simulation data. Please run it first.")
            return None

        fig = pyplot.figure()
        ax = fig.add_subplot(1, 1, 1)  # (nrows, ncols, axnum)
        for name, y in self.recordings.items():
            ax.plot(self.t_vec, y, label=name)
        ax.legend()
        fig.show()


class MComplexLoadBalancer(object):
    """Wrapper of the load balance Hoc Module with mcomplex.
    """
    def __init__(self, force_regenerate=False):
        # Can we use an existing mcomplex.dat?
        if force_regenerate or not os.path.isfile("mcomplex.dat"):
            logging.info("Generating mcomplex.dat...")
            self._create_mcomplex()
        else:
            logging.info("Using existing mcomplex.dat")
        self._lb = Neuron.h.LoadBalance()
        self._lb.read_mcomplex()

    @staticmethod
    def _create_mcomplex():
        # Save the dt of the simulation and set the dt for calculating the ExperimentalMechComplex
        # to the default value of 0.025
        prev_dt = Neuron.h.dt
        Neuron.h.dt = SimConfig.default_neuron_dt
        # ExperimentalMechComplex is a complex routine changing many state vars, and cant be reused
        # Therefore here we create a temporary LoadBalance obj
        lb = Neuron.h.LoadBalance()
        lb.ExperimentalMechComplex("StdpWA", "extracel", "HDF5", "Report", "Memory", "ASCII")
        # Revert dt to the old value
        Neuron.h.dt = prev_dt
        # mcomplex changes neuron state and results get different. We re-init
        Neuron.h.init()

    def __getattr__(self, item):
        return getattr(self._lb, item)


# shortcuts
_Neuron.HocEntity = HocEntity
_Neuron.Simulation = Simulation
_Neuron.MComplexLoadBalancer = MComplexLoadBalancer
