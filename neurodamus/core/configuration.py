"""
Runtime configuration
"""
from __future__ import absolute_import
from enum import Enum
import os
from neurodamus.utils import ConfigT


class LogLevel:
    ERROR_ONLY = 0
    DEFAULT = 1
    VERBOSE = 2
    DEBUG = 3


class GlobalConfig:
    verbosity = LogLevel.DEFAULT
    debug_conn = os.getenv('ND_DEBUG_CONN', [])
    if debug_conn:
        debug_conn = [int(gid) for gid in os.getenv('ND_DEBUG_CONN', '').split(',')]
        verbosity = 3

    @classmethod
    def set_mpi(cls):
        os.environ["NEURON_INIT_MPI"] = "1"


class RunOptions(ConfigT):
    build_model = None
    simulate_model = True
    model_path = None  # Currently is output-path
    output_path = None
    keep_build = False
    modelbuilding_steps = None


class _SimConfig(object):
    """
    A class initializing several HOC config objects and proxying to simConfig
    """
    _sim_conf = None
    rng_info = None
    core_config = None
    delete_corenrn_data = False
    buffer_time = 25
    # Dont duplicate data, forward calls
    use_coreneuron = property(lambda self: self._simconf.coreNeuronUsed())
    use_neuron = property(lambda self: self._simconf.runNeuron())
    coreneuron_datadir = property(lambda self: self._simconf.getCoreneuronDataDir().s)
    coreneuron_ouputdir = property(lambda self: self._simconf.getCoreneuronOutputDir().s)

    @classmethod
    def init(cls, h, run_conf):
        parsed_run = run_conf['_hoc']
        cls._simconf = h.simConfig
        cls._simconf.interpret(parsed_run)

        cls.rng_info = h.RNGSettings()
        cls.rng_info.interpret(parsed_run)

        if cls._simconf.coreNeuronUsed():
            cls.core_config = h.CoreConfig(run_conf["OutputRoot"])

        cls.buffer_time = 25 * run_conf.get("FlushBufferScalar", 1)

    def __getattr__(self, item):
        return getattr(self._simconf, item)


SimConfig = _SimConfig()


class RNGConfig(ConfigT):
    Modes = Enum("Mode", "COMPATIBILITY RANDOM123 UPMCELLRAN4")
    mode = Modes.COMPATIBILITY
    global_seed = None
    IonChannelSeed = None
    StimulusSeed = None
    MinisSeed = None
    SynapseSeed = None


class NeuronStdrunDefaults:
    """Neuron stdrun default (src: share/lib/hoc/stdrun.hoc"""
    using_cvode_ = 0
    stdrun_quiet = 0
    realtime = 0
    tstop = 5
    stoprun = 0
    steps_per_ms = 1 / .025
    nstep_steprun = 1
    global_ra = 35.4
    v_init = -65


class ConfigurationError(Exception):
    """Error due to invalid settings in BlueConfig"""
    pass
