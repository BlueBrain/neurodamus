"""
Py Wrappers for the HOC RNGs

Copyright 2018 - Blue Brain Project, EPFL
"""
from __future__ import absolute_import
from . import Neuron
from neurodamus.core.configuration import RNGConfig


# NOTE: These are pure wrappers, in the sense they dont create Python objects. Instead
#       Neuron objects are returned (using __new__)


class RNG(object):
    def __new__(cls, *ids, **kw):
        """Creates a default RNG, currently based on ACG"""
        seed = kw.get("seed")
        return Neuron.h.Random() if seed is None else Neuron.h.Random(seed)

    @classmethod
    def create(cls, rng_mode, ids, seed=None):
        # type: (RNGConfig, tuple, object) -> RNG
        if rng_mode == RNGConfig.Modes.RANDOM123:
            assert len(ids) == 3, "Random123 requires three ids (as a tuple)"
            obj = Random123(ids[0], ids[1], ids[2], seed)
        elif rng_mode == RNGConfig.Modes.UPMCELLRAN4:
            assert len(ids) == 1
            obj = MCellRan4(ids[0], seed)
        else:
            obj = RNG(seed)

        return obj


class ACG(RNG):
    def __new__(cls, size=None, seed=None):
        rng = RNG(seed=seed)
        rng.ACG(seed=seed, size=size)
        return rng


class Random123(RNG):
    def __new__(cls, id1, id2, id3, seed=None):
        rng = RNG()
        if seed is not None:
            rng.Random123_globalindex(seed)
        rng.Random123(id1, id2, id3)
        return rng


class MCellRan4(RNG):
    def __new__(cls, high_i, seed=None):
        rng = RNG()
        rng.MCellRan4(high_i)
        return rng
