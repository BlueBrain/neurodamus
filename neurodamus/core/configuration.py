"""
Runtime configuration
"""
from __future__ import absolute_import
from enum import Enum
import os
from neurodamus.utils import ConfigT


class GlobalConfig:
    verbosity = 1
    debug_conn = os.getenv('ND_DEBUG_CONN', [])
    if debug_conn:
        debug_conn = [int(gid) for gid in os.getenv('ND_DEBUG_CONN', '').split(',')]
        verbosity = 3

    @classmethod
    def set_mpi(cls):
        os.environ["NEURON_INIT_MPI"] = "1"


class RNGConfig(ConfigT):
    Modes = Enum("Mode", "COMPATIBILITY RANDOM123 UPMCELLRAN4")
    mode = Modes.COMPATIBILITY
    global_seed = None
    IonChannelSeed = None
    StimulusSeed = None
    MinisSeed = None
    SynapseSeed = None

    @classmethod
    def init(cls, config_map):
        # type: (dict) -> None
        mode = config_map.get('RNGMode')
        if mode is not None:
            if hasattr(cls.Modes, mode):
                cls.rng_mode = cls.Modes[mode]
                config_map.pop("RNGMode")
        cls.global_init(**config_map)


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
