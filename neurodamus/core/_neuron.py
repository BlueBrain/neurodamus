from __future__ import absolute_import
from ..utils import classproperty
from neurodamus.core.configuration import Neuron_Stdrun_Defaults
from .configuration import GlobalConfig
from six import add_metaclass


class _NeuronMeta(type):
    def __getattr__(self, item):
        return getattr(self.h, item)

    def __setattr__(self, key, value):
        if key in vars(self):
            dctr = self.__dict__[key]
            if hasattr(dctr, "__set__"):
                # By default type doesnt honour descriptors. We do
                dctr.__set__(self, value)
            type.__setattr__(self, key, value)
        else:
            setattr(self.h, key, value)


# TODO: Instead of using classmethods, this class can probably be changed to a normal singleton
@add_metaclass(_NeuronMeta)
class Neuron(object):
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
    _mods_loaded = set()
    """A list of modules already loaded"""

    @classproperty
    def h(cls):
        """Initializes neuron and its hoc interpreter which is returned
        """
        return cls._h or cls._init()

    @classmethod
    def _init(cls):
        """Initializes the Neuron simulator"""
        if cls._h is None:
            if GlobalConfig.use_mpi:
                _init_mpi()
            from neuron import h
            from neuron import nrn
            cls.Section = nrn.Section
            cls.Segment = nrn.Segment
            cls._h = h
            h.load_file("stdrun.hoc")
            h("objref nil")
            h.init()
        return cls._h

    @classmethod
    def load_hoc(cls, mod_name):
        """Loads a hoc module, available in the path.
        E.g.: Neuron.load_mod("loadbal")
        """
        if mod_name in cls._mods_loaded:
            return
        mod_filename = mod_name + ".hoc"
        rc = cls.h.load_file(mod_filename)
        cls._mods_loaded.add(mod_name)
        if rc == 0:
            raise RuntimeError("Cant load HOC library {}. Consider checking HOC_LIBRARY_PATH"
                               .format(mod_filename))

    @classmethod
    def require(cls, *hoc_mods):
        for mod in hoc_mods:
            cls.load_hoc(mod)
        return cls._h

    @classmethod
    def load_dll(cls, dll_path):
        """Loads a Neuron mod file (typically an .so file in linux)"""
        rc = cls._h.nrn_load_dll(dll_path)
        if rc == 0:
            raise RuntimeError("Cant load MOD dll {}. Please check LD path and dependencies"
                               .format(dll_path))

    @classmethod
    def run_sim(cls, t_stop, *monitored_sections, **params):
        """A helper to run the simulation, recording the Voltage in the specified cell sections.
        Args:
            t_stop: Stop time
            *monitored_sections: Cell sections to be probed.
            **params: Custom simulation parameters

        Returns: A simulation object
        """
        sim = Simulation(**params)
        for sec in monitored_sections:
            sim.record_activity(sec)
        sim.run(t_stop)
        return sim

    HocEntity = None   # type: HocEntity
    Simulation = None  # type: Simulation
    Section = None
    Segment = None
    # Datastucts coming from Neuron: Vector, List


def _init_mpi():
    # Override default excepthook so that exceptions terminate all ranks
    from mpi4py import MPI
    import sys
    sys_excepthook = sys.excepthook

    def mpi_excepthook(v, t, tb):
        sys_excepthook(v, t, tb)
        MPI.COMM_WORLD.Abort(1)

    sys.excepthook = mpi_excepthook


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


class LoadBalance(object):
    """Wrapper of the load balance Hoc Module.
    """
    def __init__(self):
        self._lb = Neuron.h.LoadBalance()

    def create_mcomplex(self):
        self._lb.ExperimentalMechComplex("StdpWA", "extracel", "HDF5", "Report", "Memory", "ASCII")

    def read_mcomplex(self):
        self._lb.read_mcomplex()

    def __getattr__(self, item):
        return object.__getattribute__(self._lb, item)


# shortcuts
Neuron.HocEntity = HocEntity
Neuron.Simulation = Simulation
