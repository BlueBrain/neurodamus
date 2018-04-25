from __future__ import absolute_import
from . import _neuron


class StimuliSource(object):
    def __init__(self):
        h = _neuron.get_init()
        self.stim_vec = h.Vector()
        self.time_vec = h.Vector()
        self._cur_t = 0

    def attach_to(self, section, position=0.5):
        h = _neuron.get_init()
        clamp = h.IClamp(position, sec=section)
        self.stim_vec.play(clamp.amp, self.time_vec, 1)

    def reset(self):
        self.stim_vec.resize(0)
        self.time_vec.resize(0)

    def _add_point(self, amp):
        """Appends a single point to the time-voltage source.
        Note: It doesnt advance time, not supposed to be called directly
        """
        self.time_vec.append(self._cur_t)
        self.stim_vec.append(amp)

    def delay(self, duration):
        """Increments the ref time so that the next created signal is delayed
        """
        self._cur_t += duration

    def add_segment(self, amp, duration, amp2=None):
        """Sets a linear voltage for a certain duration
        If amp2 is None (default) then we have constant voltage
        """
        self._add_point(amp)
        self.delay(duration)
        self._add_point(amp if amp2 is None else amp2)

    def add_pulse(self, max_amp, duration, base_amp=.0):
        """Adds a pulse.
        A pulse is characterized by raising from a base voltage, default 0, for a certain duration.
        """
        self._add_point(base_amp)
        self.add_segment(max_amp, duration)
        self._add_point(base_amp)

    def add_ramp(self, amp1, amp2, duration, base_amp=.0):
        """Adds a ramp.
        A ramp is characterized by a pulse whose peak changes uniformly during its length.
        """
        self._add_point(base_amp)
        self.add_segment(amp1, duration, amp2)
        self._add_point(base_amp)

    def add_train(self, amp, frequency, pulse_duration, total_duration, base_amp=.0):
        """Stimulus with repeated pulse injections at a specified frequency.
        Args:
          amp: the amplitude of a each pulse
          frequency: determines the number of pulses per second (hz)
          pulse_duration: the duration of a single pulse (peak time) (ms)
          total_duration: duration of the whole train (ms)
          base_amp: The base amplitude
        """
        tau = 1000 // frequency
        delay = tau - pulse_duration
        number_pulses = total_duration // tau
        for _ in range(number_pulses):
            self.add_pulse(amp, pulse_duration, base_amp)
            self.delay(delay)

        # Add extra pulse if fits
        remaining_time = total_duration % tau
        if pulse_duration <= remaining_time:
            self.add_pulse(amp, pulse_duration, base_amp)
            self.delay(min(delay, remaining_time - pulse_duration))
        # Last point
        self._add_point(base_amp)

    def add_sin(self, amp, total_duration, freq, step=0.025):
        """ Builds a sinusoidal signal
        Args:
            amp: The max amplitude of the wave
            total_duration: Total duration, in ms
            freq: The wave frequency, in Hz
            step: The step, in ms (default: 0.025)
        """
        h = _neuron.get_init()
        n_steps = total_duration // step + 1

        t_vec = h.Vector(n_steps)
        t_vec.indgen(step)
        self.time_vec.append(t_vec)

        v_vec = h.Vector(n_steps)
        v_vec.sin(freq, .0, step)
        v_vec.mul(amp)
        self.stim_vec.append(v_vec)

    def add_sinspec(self, start, dur):
        raise NotImplementedError()

    def add_pulses(self, pulse_duration, amp, *more_amps, **kw):
        """Appends a set of voltages without returning to zero
           Each voltage is applied 'dur' time\
        Args:
          pulse_duration: The duration of each pulse
          amp: The amplitude of the first pulse
          *more_amps: 2nd, 3rd, ... pulse amplitudes
          **kw: Additional params:
            - base_amp [default: 0]
        """
        # First and last are base_amp
        base_amp = kw.get("base_amp", .0)
        self._add_point(base_amp)
        self.add_segment(amp, pulse_duration)
        for amp in more_amps:
            self.add_segment(amp, pulse_duration)
        self._add_point(base_amp)

    def add_noise(self, rand_source, mean, variance, duration, dt=0.5):
        rand_source.normal(mean, variance)

    @classmethod
    def infinite_noise_source_attach(cls, rand_source, mean, variance, dt=0.5):
        return



# EStim class is a derivative of TStim for stimuli with an extracelular electrode. The main
# difference is that it collects all elementary stimuli pulses and converts them using a
# VirtualElectrode object before it injects anything
#
# The stimulus is defined on the hoc level by using the addpoint function for every (step) change
# in extracellular electrode voltage. At this stage only step changes can be used. Gradual,
# i.e. sinusoidal changes will be implemented in the future
# After every step has been defined, you have to call initElec() to perform the frequency dependent
# transformation. This transformation turns e_electrode into e_extracellular at distance d=1 micron
# from the electrode. After the transformation is complete, NO MORE STEPS CAN BE ADDED!
# You can then use inject() to first scale e_extracellular down by a distance dependent factor
# and then vector.play() it into the currently accessed compartment
#
# TODO: 1. more stimulus primitives than step. 2. a dt of 0.1 ms is hardcoded. make this flexible!
