from __future__ import absolute_import
from . import nrn


class StimuliSource(object):
    def __init__(self):
        h = nrn.get_init()
        self.stim_vec = h.Vector()
        self.time_vec = h.Vector()
        self._cur_t = 0

    def attach_to(self, section, position=0.5):
        h = nrn.get_init()
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

    def _add_delay(self, duration):
        """Increments the ref time so that the next created signal is delayed
        """
        self._cur_t += duration

    def add_segment(self, amp, duration, amp2=None):
        """Sets a linear voltage for a certain duration
        If amp2 is None (default) then we have constant voltage
        """
        self._add_point(amp)
        self._add_delay(duration)
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

    def add_train(self, amp, frequency, pulse_duration, dur, base_amp=.0):
        """Stimulus with repeated pulse injections at a specified frequency.
        Args:
          amp: the amplitude of a each pulse
          frequency: determines the number of pulses per second (hz)
          pulse_duration: the duration of a single pulse (peak time)
          dur: duration of the whole train
          base_amp: The base amplitude
        """
        tau = 1000 / frequency
        delay = tau - pulse_duration
        number_pulses = dur // tau
        for _ in number_pulses:
            self.add_pulse(amp, pulse_duration, base_amp)
            self._add_delay(delay)
        # Last point of the last cycle
        self._add_point(base_amp)

    def add_sin(self, amp, dur, freq, step=0.025):
        h = nrn.get_init()
        n_steps = dur // step + 1

        t_vec = h.Vector(n_steps)
        t_vec.indgen(step)
        self.time_vec.append(t_vec)

        v_vec = h.Vector(n_steps)
        v_vec.sin(freq, .0, step)
        v_vec.mul(amp)
        self.stim_vec.append(v_vec)

    def add_sinspec(self, start, dur):
        raise NotImplementedError()

    def add_pulses(self, dur, amp, *more_amps):
        """Appends a set of voltages without returning to zero
           Each voltage is applied 'dur' time
        """
        # First and last are 0
        self._add_point(.0)
        self.add_segment(amp, dur)
        for amp in more_amps:
            self.add_segment(amp, dur)
        self._add_point(.0)

    def add_noise(self, start, dur, mean, var, dt=0.5):
        raise NotImplementedError()


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
