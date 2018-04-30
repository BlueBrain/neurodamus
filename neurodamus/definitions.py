from __future__ import absolute_import

from cycler import concat

from .utils import ConfigT, classproperty
from enum import Enum


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
