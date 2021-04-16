# https://bbpteam.epfl.ch/project/spaces/display/BGLIB/Neurodamus
# Copyright 2005-2021 Blue Brain Project, EPFL. All rights reserved.
"""
    Implements coupling artificial stimulus into simulation

    New Stimulus classes must be registered, using the appropriate decorator.
    Also, when instantiated by the framework, __init__ is passed three arguments
    (1) target (2) stim_info: dict (3) cell_manager. Example

    >>> @StimulusManager.register_type
    >>> class ShotNoise:
    >>>
    >>> def __init__(self, target, stim_info: dict, cell_manager):
    >>>     tpoints = target.getPointList(cell_manager)
    >>>     for point in tpoints:
    >>>         gid = point.gid
    >>>         cell = cell_manager.getMEType(gid)

"""

import logging
from .core import NeurodamusCore as Nd
from .utils.logging import log_verbose
from .core.configuration import SimConfig
from .core.stimuli import CurrentSource
from .core import random


class StimulusManager:

    """
    A manager for synaptic artificial Stimulus.
    Old stimulus resort to hoc implementation
    """

    _stim_types = {}  # stimulus handled in Python

    def __init__(self, target_manager, elec_manager=None, *args):
        self._hoc = Nd.StimulusManager(target_manager.hoc, elec_manager, *args)
        self._target_manager = target_manager
        self._stimulus = []
        self.reset_helpers()  # reset helpers for multi-cycle builds

    def interpret(self, target_spec, stim_info):
        stim_t = self._stim_types.get(stim_info["Pattern"])
        if stim_t:  # New style Stim, in Python
            log_verbose("Using new-gen stimulus")
            target = self._target_manager.get_target(target_spec.name)
            cell_manager = self._target_manager.hoc.cellDistributor
            stim = stim_t(target, stim_info, cell_manager)
            self._stimulus.append(stim)
        else:
            # Fallback to hoc stim manager
            self._hoc.interpret(target_spec.name, stim_info.hoc_map)

    def interpret_extracellulars(self, injects, stimuli):
        """Hoc only implementation for extra-cellulars"""
        self._hoc.interpretExtracellulars(injects.hoc_map, stimuli.hoc_map)

    def __getattr__(self, item):
        logging.debug("Pass unknown method request to Hoc")
        return getattr(self._hoc, item)

    def reset_helpers(self):
        ShotNoise.stimCount = 0

    @classmethod
    def register_type(cls, stim_class):
        """ Registers a new class as a handler for a new stim type """
        cls._stim_types[stim_class.__name__] = stim_class
        return stim_class


@StimulusManager.register_type
class ShotNoise:
    """
    ShotNoise stimulus handler implementing Poisson shot noise
    with bi-exponential response and gamma-distributed amplitudes
    """
    stimCount = 0  # global count for seeding

    def __init__(self, target, stim_info: dict, cell_manager):
        self.stimList = []  # CurrentSource's go here

        if not self.parse_check_all_parameters(stim_info):
            return None  # nothing to do, stim is a no-op

        # setup random seeds
        seed1 = ShotNoise.stimCount + 2997  # stimulus block seed
        seed2 = SimConfig.rng_info.getStimulusSeed() + 19216  # stimulus type seed
        seed3 = (lambda x: x + 123) if self.seed is None else (lambda x: self.seed)  # GID seed

        # apply stim to each point in target
        tpoints = target.getPointList(cell_manager)
        for tpoint_list in tpoints:
            gid = tpoint_list.gid
            cell = cell_manager.getMEType(gid)

            self.compute_parameters(cell)

            for sec_id, sc in enumerate(tpoint_list.sclst):
                # skip non-existing sections, FIXME: is this necessary?
                if not sc.exists():
                    continue

                rng = random.Random123(seed1, seed2, seed3(gid))  # setup RNG
                # generate shot noise current source
                cs = CurrentSource.shot_noise(self.tau_D, self.tau_R, self.rate,
                                              self.amp_mean, self.amp_var, self.duration,
                                              dt=self.dt, delay=self.delay, rng=rng)
                # attach current source to section
                cs.attach_to(sc.sec, tpoint_list.x[sec_id])
                self.stimList.append(cs)  # save CurrentSource

        ShotNoise.stimCount += 1  # increment global count

    def parse_check_all_parameters(self, stim_info: dict):
        # time parameters
        self.dt = float(stim_info.get("Dt", 0.25))    # stimulus timestep [ms]
        if self.dt <= 0:
            raise Exception("Shot noise time-step must be positive")

        self.duration = float(stim_info["Duration"])  # duration [ms]
        if self.duration < 0:
            raise Exception("Shot noise duration must be non-negative")

        ntstep = int(self.duration / self.dt)  # number of timesteps [1]
        if ntstep == 0:
            return False  # nothing to do, stim is a no-op

        self.delay = float(stim_info["Delay"])        # start time [ms]
        if self.delay < 0:
            raise Exception("Shot noise delay must be non-negative")

        # bi-exponential parameters
        self.tau_R = float(stim_info["RiseTime"])     # rise time [ms]
        self.tau_D = float(stim_info["DecayTime"])    # decay time [ms]
        if self.tau_R >= self.tau_D:
            raise Exception("Shot noise bi-exponential rise time must be smaller than decay time")

        # parse and check stimulus-specific parameters
        if not self.parse_check_stim_parameters(stim_info):
            return False  # nothing to do, stim is a no-op

        # seed
        self.seed = stim_info.get("Seed")  # random seed override
        if self.seed is not None:
            self.seed = int(self.seed)
            if self.seed < 0:
                raise Exception("Shot noise random seed must be non-negative")

        return True

    def parse_check_stim_parameters(self, stim_info: dict):
        """
        Parse parameters for ShotNoise stimulus
        """
        # event rate of Poisson process [Hz]
        self.rate = float(stim_info["Rate"])
        if self.rate < 0:
            raise Exception("Shot noise event rate must be non-negative")

        # mean amplitude of shots [nA]
        # when negative we invert the sign of the current
        self.amp_mean = float(stim_info["AmpMean"])
        if self.amp_mean == 0:
            raise Exception("Shot noise amplitude mean must be non-zero")

        # variance of amplitude of shots [nA^2]
        self.amp_var = float(stim_info["AmpVar"])
        if self.amp_var <= 0:
            raise Exception("Shot noise amplitude variance must be positive")

        return self.rate == 0  # no-op if rate == 0

    def compute_parameters(self, cell):
        # nothing to do
        pass


@StimulusManager.register_type
class RelativeShotNoise(ShotNoise):
    """
    RelativeShotNoise stimulus handler, same as shotNoise
    but parameters relative to cell threshold
    """

    def __init__(self, target, stim_info: dict, cell_manager):
        super().__init__(target, stim_info, cell_manager)

    def parse_check_stim_parameters(self, stim_info: dict):
        """
        Parse parameters for RelativeShotNoise stimulus
        """
        # signal mean as percent of cell's threshold [1],
        # when negative we invert the sign of the current
        self.mean_perc = float(stim_info["MeanPercent"])

        # signal standard deviation as percent of cell's threshold [1]
        self.sd_perc = float(stim_info["SDPercent"])
        if self.sd_perc <= 0:
            raise Exception("Shot noise stdev percent must be positive")
        if self.sd_perc < 1:
            logging.warning("Shot noise stdev percent too small gives a very high event rate")

        # coefficient of variation of shot amplitudes [1]
        cv = float(stim_info["AmpCV"])
        if cv <= 0:
            raise Exception("Shot noise amplitude CV must be positive")
        self.cv_square = cv * cv

        return self.mean_perc != 0  # no-op if mean_perc == 0

    def compute_parameters(self, cell):
        """
        Compute bi-exponential shot noise parameters from desired mean and variance of signal.

        Analytical result derived from a generalization of Campbell's theorem present in
        Rice, S.O., "Mathematical Analysis of Random Noise", BSTJ 23, 3 Jul 1944.
        """
        from math import exp, log

        threshold = cell.getThreshold()          # cell threshold current [nA]
        mean = self.mean_perc / 100 * threshold  # desired mean [nA]
        sd = self.sd_perc / 100 * threshold      # desired standard deviation [nA]
        var = sd * sd                            # variance [nA^2]

        # bi-exponential time to peak [ms]
        t_peak = log(self.tau_D / self.tau_R) / (1 / self.tau_R - 1 / self.tau_D)
        # bi-exponential peak height [1]
        x_peak = exp(-t_peak / self.tau_D) - exp(-t_peak / self.tau_R)

        rate_ms = (1 + self.cv_square) / 2 * (mean ** 2 / var) / (self.tau_D + self.tau_R)
        self.rate = rate_ms * 1000  # rate in 1 / s [Hz]
        self.amp_mean = mean * x_peak / rate_ms / (self.tau_D - self.tau_R)
        self.amp_var = self.cv_square * self.amp_mean ** 2
