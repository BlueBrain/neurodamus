"""
TimeIt - Helper class for measuring Neuron Execution time
"""
import logging
from neuron import h


class Timer:
    _timers = {}

    @classmethod
    def init(cls, parallel_ctx):
        cls._pc = parallel_ctx

    def __init__(self, name, ):
        self.name = name
        self.t_start = None
        self.t_accum = 0
        self._timers[name] = self

    def start(self):
        self.t_start = h.startsw()

    def split(self):
        self.t_accum += h.startsw() - self.t_start
        logging.info("(Timer %30s) Accum: %g", self.name, self.t_accum)
        return self.t_accum
    # Compat
    add = split

    @classmethod
    def events(cls, name):
        return cls._timers[name]
