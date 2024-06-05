"""
Py Wrappers for the HOC RNGs
"""
from __future__ import absolute_import
from . import Neuron


# NOTE: These are pure wrappers, in the sense they don't create Python objects. Instead
#       Neuron objects are returned (using __new__)


class RNG(object):
    def __new__(cls, **kw):
        """Creates a default RNG (Random123 with ids of 0,1,2)"""
        seed = kw.get("seed", 0)
        return Random123(0, 1, 2, seed)

    @classmethod
    def create(cls, ids, seed=None):
        # type: (tuple, object) -> RNG
        assert len(ids) == 3, "Random123 requires three ids (as a tuple)"
        obj = Random123(ids[0], ids[1], ids[2], seed)

        return obj


class Random123(RNG):
    def __new__(cls, id1, id2, id3, seed=None):
        rng = Neuron.h.Random() if seed is None else Neuron.h.Random(seed)
        if seed is not None:
            rng.Random123_globalindex(seed)
        rng.Random123(id1, id2, id3)
        return rng


# Gamma-distributed sample generator (not available in NEURON)
def gamma(rng, a, b, N=1):
    """
    Sample N variates from a gamma distribution with parameters shape = a, scale = b
    using the NEURON random number generator rng.
    Uses the algorithm by Marsaglia and Tsang 2001.
    """
    from math import log, sqrt

    if a < 1:
        rng.uniform(0, 1)
        w = Neuron.h.Vector(N)
        w.setrand(rng)
        w.pow(1 / a)
        return gamma(rng, 1 + a, b, N).mul(w)

    d = a - 1 / 3
    c = 1 / 3 / sqrt(d)

    vec = Neuron.h.Vector(N)
    for i in range(0, N):
        while True:
            x = rng.normal(0, 1)
            v = 1 + c * x
            if v > 0:
                v = v * v * v
                u = rng.uniform(0, 1)
                if u < 1 - 0.0331 * x * x * x * x:
                    vec.x[i] = b * d * v
                    break
                if log(u) < 0.5 * x * x + d * (1 - v + log(v)):
                    vec.x[i] = b * d * v
                    break

    return vec
