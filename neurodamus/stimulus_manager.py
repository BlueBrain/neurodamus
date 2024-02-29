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
    >>>         cell = cell_manager.get_cell(gid)

"""

import logging
from .core import NeurodamusCore as Nd
from .utils.logging import log_verbose
from .core.configuration import SimConfig, ConfigurationError
from .core.stimuli import CurrentSource, ConductanceSource
from .core import random


class StimulusManager:

    """
    A manager for synaptic artificial Stimulus.
    Old stimulus resort to hoc implementation
    """

    _stim_types = {}  # stimulus handled in Python

    def __init__(self, target_manager):
        self._target_manager = target_manager
        self._stim_seed = SimConfig.run_conf.get("StimulusSeed")
        self._stimulus = []
        self.reset_helpers()  # reset helpers for multi-cycle builds

    def interpret(self, target_spec, stim_info):
        stim_t = self._stim_types.get(stim_info["Pattern"])
        if not stim_t:
            raise ConfigurationError("No implementation for Stimulus %s " % stim_info["Pattern"])
        if self._stim_seed is None and getattr(stim_t, 'IsNoise', False):
            logging.warning("StimulusSeed unset (default %d), "
                            "set explicitly to vary noisy stimuli across runs",
                            SimConfig.rng_info.getStimulusSeed())
        target = self._target_manager.get_target(target_spec)
        log_verbose("Interpret stimulus")
        cell_manager = self._target_manager._cell_manager
        stim = stim_t(target, stim_info, cell_manager)
        self._stimulus.append(stim)

    def interpret_extracellulars(self, injects, stimuli):
        """Pending for BBPBGLIB-890"""
        raise ConfigurationError("input_type extracellular_stimulation is not implemented")

    def reset_helpers(self):
        ShotNoise.stimCount = 0
        Noise.stimCount = 0
        OrnsteinUhlenbeck.stimCount = 0

    @classmethod
    def register_type(cls, stim_class):
        """ Registers a new class as a handler for a new stim type """
        cls._stim_types[stim_class.__name__] = stim_class
        return stim_class

    def saveStatePreparation(self, ss_obj):
        for stim in self._stimulus:
            ss_obj.ignore(stim)


class BaseStim:
    """
    Barebones stimulus class
    """

    IsNoise = False

    def __init__(self, _target, stim_info: dict, _cell_manager):
        self.duration = float(stim_info["Duration"])  # duration [ms]
        self.delay = float(stim_info["Delay"])        # start time [ms]


@StimulusManager.register_type
class OrnsteinUhlenbeck(BaseStim):
    """
    Ornstein-Uhlenbeck process, injected as current or conductance
    """
    IsNoise = True
    stimCount = 0  # global count for seeding

    def __init__(self, target, stim_info: dict, cell_manager):
        super().__init__(target, stim_info, cell_manager)

        self.stimList = []  # sources go here

        if not self.parse_check_all_parameters(stim_info):
            return None  # nothing to do, stim is a no-op

        # setup random seeds
        seed1 = OrnsteinUhlenbeck.stimCount + 2997  # stimulus block seed
        seed2 = SimConfig.rng_info.getStimulusSeed() + 291204  # stimulus type seed
        seed3 = (lambda x: x + 123) if self.seed is None else (lambda x: self.seed)  # GID seed

        # apply stim to each point in target
        tpoints = target.getPointList(cell_manager)
        for tpoint_list in tpoints:
            gid = tpoint_list.gid
            cell = cell_manager.get_cell(gid)

            self.compute_parameters(cell)

            for sec_id, sc in enumerate(tpoint_list.sclst):
                # skip sections not in this split
                if not sc.exists():
                    continue

                rng = random.Random123(seed1, seed2, seed3(gid))  # setup RNG
                ou_args = (self.tau, self.sigma, self.mean, self.duration)
                ou_kwargs = {'dt': self.dt, 'delay': self.delay, 'rng': rng}
                # inject Ornstein-Uhlenbeck signal
                if stim_info["Mode"] == "Conductance":
                    cs = ConductanceSource.ornstein_uhlenbeck(*ou_args, **ou_kwargs,
                                                              base_amp=self.reversal)
                else:
                    cs = CurrentSource.ornstein_uhlenbeck(*ou_args, **ou_kwargs)
                # attach source to section
                cs.attach_to(sc.sec, tpoint_list.x[sec_id])
                self.stimList.append(cs)  # save source

        OrnsteinUhlenbeck.stimCount += 1  # increment global count

    def parse_check_all_parameters(self, stim_info: dict):
        self.dt = float(stim_info.get("Dt", 0.25))  # stimulus timestep [ms]
        if self.dt <= 0:
            raise Exception("%s time-step must be positive" % self.__class__.__name__)

        self.reversal = float(stim_info.get("Reversal", 0.0))  # reversal potential [mV]

        if stim_info["Mode"] not in ["Current", "Conductance"]:
            raise Exception("%s must be used with mode Current or Conductance"
                            % self.__class__.__name__)

        self.tau = float(stim_info["Tau"])  # relaxation time [ms]
        if self.tau < 0:
            raise Exception("%s relaxation time must be non-negative" % self.__class__.__name__)

        # parse and check stimulus-specific parameters
        if not self.parse_check_stim_parameters(stim_info):
            return False  # nothing to do, stim is a no-op

        self.seed = stim_info.get("Seed")  # random seed override
        if self.seed is not None:
            self.seed = int(self.seed)

        return True

    def parse_check_stim_parameters(self, stim_info):
        self.sigma = float(stim_info["Sigma"])  # signal stdev [uS]
        if self.sigma <= 0:
            raise Exception("%s standard deviation must be positive" % self.__class__.__name__)

        self.mean = float(stim_info["Mean"])    # signal mean [uS]
        if self.mean < 0 and abs(self.mean) > 2 * self.sigma:
            logging.warning("%s signal is mostly zero" % self.__class__.__name__)

        return True

    def compute_parameters(self, cell):
        # nothing to do
        pass


@StimulusManager.register_type
class RelativeOrnsteinUhlenbeck(OrnsteinUhlenbeck):
    """
    Ornstein-Uhlenbeck process, injected as current or conductance,
    relative to cell threshold current or inverse input resistance
    """
    IsNoise = True

    def __init__(self, target, stim_info: dict, cell_manager):
        super().__init__(target, stim_info, cell_manager)

    def parse_check_stim_parameters(self, stim_info):
        self.mean_perc = float(stim_info["MeanPercent"])
        self.sigma_perc = float(stim_info["SDPercent"])

        if stim_info["Mode"] == "Current":
            self.get_relative = lambda x: x.getThreshold()
        else:
            self.get_relative = lambda x: 1.0 / x.input_resistance

        return True

    def compute_parameters(self, cell):
        # threshold current [nA] or inverse input resistance [uS]
        rel_prop = self.get_relative(cell)

        self.sigma = (self.sigma_perc / 100) * rel_prop  # signal stdev [nA or uS]
        if self.sigma <= 0:
            raise Exception("%s standard deviation must be positive" % self.__class__.__name__)

        self.mean = (self.mean_perc / 100) * rel_prop    # signal mean [nA or uS]
        if self.mean < 0 and abs(self.mean) > 2 * self.sigma:
            logging.warning("%s signal is mostly zero" % self.__class__.__name__)

        return True


@StimulusManager.register_type
class ShotNoise(BaseStim):
    """
    ShotNoise stimulus handler implementing Poisson shot noise
    with bi-exponential response and gamma-distributed amplitudes
    """
    IsNoise = True
    stimCount = 0  # global count for seeding

    def __init__(self, target, stim_info: dict, cell_manager):
        super().__init__(target, stim_info, cell_manager)

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
            cell = cell_manager.get_cell(gid)

            self.compute_parameters(cell)

            for sec_id, sc in enumerate(tpoint_list.sclst):
                # skip sections not in this split
                if not sc.exists():
                    continue

                rng = random.Random123(seed1, seed2, seed3(gid))  # setup RNG
                shotnoise_args = (self.tau_D, self.tau_R, self.rate,
                                  self.amp_mean, self.amp_var, self.duration)
                shotnoise_kwargs = {'dt': self.dt, 'delay': self.delay, 'rng': rng}
                # generate shot noise current source
                if stim_info["Mode"] == "Conductance":
                    cs = ConductanceSource.shot_noise(*shotnoise_args, **shotnoise_kwargs,
                                                      base_amp=self.reversal)
                else:
                    cs = CurrentSource.shot_noise(*shotnoise_args, **shotnoise_kwargs)
                # attach current source to section
                cs.attach_to(sc.sec, tpoint_list.x[sec_id])
                self.stimList.append(cs)  # save CurrentSource

        ShotNoise.stimCount += 1  # increment global count

    def parse_check_all_parameters(self, stim_info: dict):
        if stim_info["Mode"] not in ["Current", "Conductance"]:
            raise Exception("%s must be used with mode Current or Conductance"
                            % self.__class__.__name__)

        self.reversal = float(stim_info.get("Reversal", 0.0))  # reversal potential [mV]

        # time parameters
        self.dt = float(stim_info.get("Dt", 0.25))    # stimulus timestep [ms]
        if self.dt <= 0:
            raise Exception("%s time-step must be positive" % self.__class__.__name__)

        ntstep = int(self.duration / self.dt)  # number of timesteps [1]
        if ntstep == 0:
            return False  # nothing to do, stim is a no-op

        # bi-exponential parameters
        self.tau_R = float(stim_info["RiseTime"])     # rise time [ms]
        self.tau_D = float(stim_info["DecayTime"])    # decay time [ms]
        if self.tau_R >= self.tau_D:
            raise Exception("%s bi-exponential rise time must be smaller than decay time"
                            % self.__class__.__name__)

        # parse and check stimulus-specific parameters
        if not self.parse_check_stim_parameters(stim_info):
            return False  # nothing to do, stim is a no-op

        # seed
        self.seed = stim_info.get("Seed")  # random seed override
        if self.seed is not None:
            self.seed = int(self.seed)

        return True

    def parse_check_stim_parameters(self, stim_info: dict):
        """
        Parse parameters for ShotNoise stimulus
        """
        # event rate of Poisson process [Hz]
        self.rate = float(stim_info["Rate"])

        # mean amplitude of shots [nA or uS]
        # when negative we invert the sign of the current
        self.amp_mean = float(stim_info["AmpMean"])
        if self.amp_mean == 0:
            raise Exception("%s amplitude mean must be non-zero" % self.__class__.__name__)

        # variance of amplitude of shots [nA^2 or uS^2]
        self.amp_var = float(stim_info["AmpVar"])
        if self.amp_var <= 0:
            raise Exception("%s amplitude variance must be positive" % self.__class__.__name__)

        return self.rate > 0  # no-op if rate == 0

    def compute_parameters(self, cell):
        # nothing to do
        pass

    def params_from_mean_var(self, mean, var):
        """
        Compute bi-exponential shot noise parameters from desired mean and variance of signal.

        Analytical result derived from a generalization of Campbell's theorem present in
        Rice, S.O., "Mathematical Analysis of Random Noise", BSTJ 23, 3 Jul 1944.
        """
        from math import exp, log

        # bi-exponential time to peak [ms]
        t_peak = log(self.tau_D / self.tau_R) / (1 / self.tau_R - 1 / self.tau_D)
        # bi-exponential peak height [1]
        x_peak = exp(-t_peak / self.tau_D) - exp(-t_peak / self.tau_R)

        rate_ms = (1 + self.cv_square) / 2 * (mean ** 2 / var) / (self.tau_D + self.tau_R)
        self.rate = rate_ms * 1000  # rate in 1 / s [Hz]
        self.amp_mean = mean * x_peak / rate_ms / (self.tau_D - self.tau_R)
        self.amp_var = self.cv_square * self.amp_mean ** 2


@StimulusManager.register_type
class RelativeShotNoise(ShotNoise):
    """
    RelativeShotNoise stimulus handler, same as ShotNoise
    but parameters relative to cell threshold current or inverse input resistance
    """
    IsNoise = True

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
            raise Exception("%s stdev percent must be positive" % self.__class__.__name__)
        if self.sd_perc < 1:
            logging.warning("%s stdev percent too small gives a very high event rate"
                            % self.__class__.__name__)

        # coefficient of variation of shot amplitudes [1]
        cv = float(stim_info["AmpCV"])
        if cv <= 0:
            raise Exception("%s amplitude CV must be positive" % self.__class__.__name__)
        self.cv_square = cv * cv

        if stim_info["Mode"] == "Current":
            self.get_relative = lambda x: x.getThreshold()
        else:
            self.get_relative = lambda x: 1.0 / x.input_resistance

        return self.mean_perc != 0  # no-op if mean_perc == 0

    def compute_parameters(self, cell):
        # threshold current [nA] or inverse input resistance [uS]
        rel_prop = self.get_relative(cell)
        mean = self.mean_perc / 100 * rel_prop  # desired mean [nA or uS]
        sd = self.sd_perc / 100 * rel_prop      # desired standard deviation [nA or uS]
        var = sd * sd                           # variance [nA^2 or uS^2]
        super().params_from_mean_var(mean, var)


@StimulusManager.register_type
class AbsoluteShotNoise(ShotNoise):
    """
    AbsoluteShotNoise stimulus handler, same as ShotNoise
    but parameters from given mean and std. dev.
    """
    IsNoise = True

    def __init__(self, target, stim_info: dict, cell_manager):
        super().__init__(target, stim_info, cell_manager)

    def parse_check_stim_parameters(self, stim_info: dict):
        """
        Parse parameters for AbsoluteShotNoise stimulus
        """
        # signal mean [nA]
        self.mean = float(stim_info["Mean"])

        # signal standard deviation [nA]
        self.sd = float(stim_info["Sigma"])
        if self.sd <= 0:
            raise Exception("%s stdev must be positive" % self.__class__.__name__)

        # coefficient of variation of shot amplitudes [1]
        cv = float(stim_info["AmpCV"])
        if cv <= 0:
            raise Exception("%s amplitude CV must be positive" % self.__class__.__name__)
        self.cv_square = cv * cv

        return True

    def compute_parameters(self, cell):
        super().params_from_mean_var(self.mean, self.sd * self.sd)


@StimulusManager.register_type
class Linear(BaseStim):
    """
    Injects a linear current ramp.
    """
    def __init__(self, target, stim_info: dict, cell_manager):
        super().__init__(target, stim_info, cell_manager)

        self.stimList = []  # CurrentSource's go here

        if not self.parse_check_all_parameters(stim_info):
            return None  # nothing to do, stim is a no-op

        # apply stim to each point in target
        tpoints = target.getPointList(cell_manager)
        for tpoint_list in tpoints:
            gid = tpoint_list.gid
            cell = cell_manager.get_cell(gid)

            self.compute_parameters(cell)

            for sec_id, sc in enumerate(tpoint_list.sclst):
                # skip sections not in this split
                if not sc.exists():
                    continue

                # generate ramp current source
                cs = CurrentSource.ramp(self.amp_start, self.amp_end, self.duration,
                                        delay=self.delay)
                # attach current source to section
                cs.attach_to(sc.sec, tpoint_list.x[sec_id])
                self.stimList.append(cs)  # save CurrentSource

    def parse_check_all_parameters(self, stim_info: dict):
        # Amplitude at start
        self.amp_start = float(stim_info["AmpStart"])

        # Amplitude at end (optional, else same as start)
        self.amp_end = float(stim_info.get("AmpEnd", self.amp_start))

        return self.amp_start != 0 or self.amp_end != 0  # no-op if both 0

    def compute_parameters(self, cell):
        pass  # nothing to do


@StimulusManager.register_type
class Hyperpolarizing(Linear):
    """
    Injects a constant step with a cell's hyperpolarizing current.
    """
    def __init__(self, target, stim_info: dict, cell_manager):
        super().__init__(target, stim_info, cell_manager)

    def parse_check_all_parameters(self, stim_info: dict):
        return True

    def compute_parameters(self, cell):
        hypamp = cell.getHypAmp()
        self.amp_start = hypamp
        self.amp_end = hypamp


@StimulusManager.register_type
class RelativeLinear(Linear):
    """
    Injects a linear current ramp relative to cell threshold.
    """
    def __init__(self, target, stim_info: dict, cell_manager):
        super().__init__(target, stim_info, cell_manager)

    def parse_check_all_parameters(self, stim_info: dict):
        # Amplitude at start as percent of threshold
        self.perc_start = float(stim_info["PercentStart"])

        # Amplitude at end as percent of threshold (optional, else same as start)
        self.perc_end = float(stim_info.get("PercentEnd", self.perc_start))

        return self.perc_start != 0 or self.perc_end != 0  # no-op if both 0

    def compute_parameters(self, cell):
        threshold = cell.getThreshold()
        # here we use parentheses to match HOC exactly
        self.amp_start = threshold * (self.perc_start / 100)
        self.amp_end = threshold * (self.perc_end / 100)


@StimulusManager.register_type
class SubThreshold(Linear):
    """
    Injects a current step at some percent below a cell's threshold.
    """
    def __init__(self, target, stim_info: dict, cell_manager):
        super().__init__(target, stim_info, cell_manager)

    def parse_check_all_parameters(self, stim_info: dict):
        # amplitude as percent below threshold = 100%
        self.perc_less = float(stim_info["PercentLess"])

        return True

    def compute_parameters(self, cell):
        threshold = cell.getThreshold()
        # here we use parentheses to match HOC exactly
        self.amp_start = threshold * (100 - self.perc_less) / 100
        self.amp_end = self.amp_start


@StimulusManager.register_type
class Noise(BaseStim):
    """
    Inject a noisy (gaussian) current step, relative to cell threshold or not.
    """
    IsNoise = True
    stimCount = 0  # global count for seeding

    def __init__(self, target, stim_info: dict, cell_manager):
        super().__init__(target, stim_info, cell_manager)

        self.stimList = []  # CurrentSource's go here

        self.parse_check_all_parameters(stim_info)

        sim_dt = float(SimConfig.run_conf["Dt"])  # simulation time-step [ms]
        rng_mode = SimConfig.rng_info.getRNGMode()  # simulation RNGMode

        # setup RNG
        if rng_mode == SimConfig.rng_info.RANDOM123:
            rand = lambda gid: random.Random123(Noise.stimCount + 100,
                                                SimConfig.rng_info.getStimulusSeed() + 500,
                                                gid + 300)
        else:
            raise Exception("rng_mod is not RANDOM123")

        # apply stim to each point in target
        tpoints = target.getPointList(cell_manager)
        for tpoint_list in tpoints:
            gid = tpoint_list.gid
            cell = cell_manager.get_cell(gid)

            self.compute_parameters(cell)

            rng = rand(gid)  # setup RNG
            # draw already used numbers
            if self.delay > 0:
                self.draw_already_used_numbers(rng, sim_dt)

            for sec_id, sc in enumerate(tpoint_list.sclst):
                # skip sections not in this split
                if not sc.exists():
                    continue

                # generate noise current source
                cs = CurrentSource.noise(self.mean, self.var, self.duration,
                                         dt=self.dt, delay=self.delay, rng=rng)
                # attach current source to section
                cs.attach_to(sc.sec, tpoint_list.x[sec_id])
                self.stimList.append(cs)  # save CurrentSource

        Noise.stimCount += 1  # increment global count

    def parse_check_all_parameters(self, stim_info: dict):
        self.dt = float(stim_info.get("Dt", 0.5))  # stimulus timestep [ms]
        if self.dt <= 0:
            raise Exception("%s time-step must be positive" % self.__class__.__name__)

        if "Mean" in stim_info:
            self.is_relative = False
            self.mean = float(stim_info["Mean"])  # noise current mean [nA]

            self.var = float(stim_info["Variance"])  # noise current variance [nA]
            if self.var <= 0:
                raise Exception("%s variance must be positive" % self.__class__.__name__)
        else:
            self.is_relative = True
            # noise current mean as percent of threshold
            self.mean_perc = float(stim_info["MeanPercent"])

            # noise current variance as percent of threshold
            self.var_perc = float(stim_info["Variance"])
            if self.var_perc <= 0:
                raise Exception("%s variance percent must be positive" % self.__class__.__name__)

        return True

    def compute_parameters(self, cell):
        if self.is_relative:
            threshold = cell.getThreshold()  # threshold current [nA]
            # here threshold MUST be first factor to match HOC exactly
            self.mean = threshold * self.mean_perc / 100
            # note that here variance has units of nA, not nA^2
            self.var = threshold * self.var_perc / 100

    def draw_already_used_numbers(self, rng, dt):
        prev_t = 0
        tstep = self.duration - dt

        while prev_t < self.delay - dt:
            if prev_t + tstep < self.delay - dt:
                next_t = prev_t + tstep
            else:
                next_t = self.delay - dt

            tvec = Nd.h.Vector()
            tvec.indgen(prev_t, next_t, self.dt)
            stim = Nd.h.Vector(len(tvec))
            stim.setrand(rng)

            prev_t = next_t + dt


@StimulusManager.register_type
class Pulse(BaseStim):
    """
    Inject a pulse train with given amplitude, frequency and width.
    """
    def __init__(self, target, stim_info: dict, cell_manager):
        super().__init__(target, stim_info, cell_manager)

        self.stimList = []  # CurrentSource's go here

        if not self.parse_check_all_parameters(stim_info):
            return None  # nothing to do, stim is a no-op

        # apply stim to each point in target
        tpoints = target.getPointList(cell_manager)
        for tpoint_list in tpoints:
            for sec_id, sc in enumerate(tpoint_list.sclst):
                # skip sections not in this split
                if not sc.exists():
                    continue

                # generate pulse train current source
                cs = CurrentSource.train(self.amp, self.freq, self.width,
                                         self.duration, delay=self.delay)
                # attach current source to section
                cs.attach_to(sc.sec, tpoint_list.x[sec_id])
                self.stimList.append(cs)  # save CurrentSource

    def parse_check_all_parameters(self, stim_info: dict):
        self.amp = float(stim_info["AmpStart"])  # amplitude [nA]
        self.freq = float(stim_info["Frequency"])  # frequency [Hz]
        self.width = float(stim_info["Width"])  # pulse width [ms]

        return self.freq > 0 and self.width > 0  # no-op if any is 0


@StimulusManager.register_type
class Sinusoidal(BaseStim):
    """
    Inject a sinusoidal current with given amplitude and frequency.
    """
    def __init__(self, target, stim_info: dict, cell_manager):
        super().__init__(target, stim_info, cell_manager)

        self.stimList = []  # CurrentSource's go here

        if not self.parse_check_all_parameters(stim_info):
            return None  # nothing to do, stim is a no-op

        # apply stim to each point in target
        tpoints = target.getPointList(cell_manager)
        for tpoint_list in tpoints:
            for sec_id, sc in enumerate(tpoint_list.sclst):
                # skip sections not in this split
                if not sc.exists():
                    continue

                # generate sinusoidal current source
                cs = CurrentSource.sin(self.amp, self.duration, self.freq,
                                       step=self.dt, delay=self.delay)
                # attach current source to section
                cs.attach_to(sc.sec, tpoint_list.x[sec_id])
                self.stimList.append(cs)  # save CurrentSource

    def parse_check_all_parameters(self, stim_info: dict):
        self.dt = float(stim_info.get("Dt", 0.025))  # stimulus timestep [ms]
        if self.dt <= 0:
            raise Exception("%s time-step must be positive" % self.__class__.__name__)

        self.amp = float(stim_info["AmpStart"])  # amplitude [nA]
        self.freq = float(stim_info["Frequency"])  # frequency [Hz]

        return self.freq > 0  # no-op if 0


@StimulusManager.register_type
class SEClamp(BaseStim):
    """
    Apply a single electrode voltage clamp.
    """
    def __init__(self, target, stim_info: dict, cell_manager):
        super().__init__(target, stim_info, cell_manager)

        self.stimList = []  # SEClamp's go here

        self.parse_check_all_parameters(stim_info)

        # apply stim to each point in target
        tpoints = target.getPointList(cell_manager)
        for tpoint_list in tpoints:
            for sec_id, sc in enumerate(tpoint_list.sclst):
                # skip sections not in this split
                if not sc.exists():
                    continue

                # create single electrode voltage clamp at location
                seclamp = Nd.h.SEClamp(tpoint_list.x[sec_id], sec=sc.sec)
                seclamp.rs = self.rs
                seclamp.dur1 = self.duration
                seclamp.amp1 = self.vhold
                self.stimList.append(seclamp)  # save SEClamp

    def parse_check_all_parameters(self, stim_info: dict):
        self.vhold = float(stim_info["Voltage"])  # holding voltage [mV]
        self.rs = float(stim_info.get("RS", 0.01))  # series resistance [MOhm]
        if self.delay > 0:
            logging.warning("%s ignores delay" % self.__class__.__name__)
