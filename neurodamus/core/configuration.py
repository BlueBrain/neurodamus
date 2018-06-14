"""
Runtime configuration
"""
from __future__ import absolute_import
from enum import Enum
from neurodamus.utils import ConfigT


class GlobalConfig:
    verbosity = 1
    use_mpi = True


class MPInfo:
    cpu_count = 1
    rank = 0
    comm = None  # type: MPI.Comm


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


class Neuron_Stdrun_Defaults:
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
