from __future__ import absolute_import
from . import nrn


class StimuliSource(object):
    def __init__(self):
        h = nrn.get_init()
        self.stim_vec = h.Vector()
        self.time_vec = h.Vector()

    def attach_to(self, section, position=0.5):
        h = nrn.get_init()
        clamp = h.IClamp(position, sec=section)
        self.stim_vec.play(clamp.amp, self.time_vec, 1)

    def reset(self):
        self.stim_vec.resize(0)
        self.time_vec.resize(0)

    def pulse(self, start, dur, max_amp, min_amp=None):
        pass



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
