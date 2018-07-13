"""
Module defining cell mechanisms
"""
from __future__ import absolute_import
from ._neuron import Neuron
from ..utils import ConfigT


class Mechanism(ConfigT):
    _mec_name = None

    # Declare the subtypes
    HH = None   # type: HH
    PAS = None  # type: PAS

    def __new__(cls, **opts):
        if cls is Mechanism:
            raise TypeError("Mechanisms is abstract. Instantiate a specific Mechanism")
        return object.__new__(cls)

    def _apply_f(self, section, opts_dict):
        section.insert(self._mec_name)
        for key, val in opts_dict.items():
            setattr(section, "{}_{}".format(key, self._mec_name), val)

    def apply(self, obj_or_list, **kw):
        if not isinstance(obj_or_list, Neuron.Section):
            if hasattr(obj_or_list, "__iter__"):
                obj_or_list = tuple(iter(obj_or_list))
            else:
                raise TypeError("Object {} cant be assigned Mechanism properties")
        ConfigT.apply(self, obj_or_list)


class HH(Mechanism):
    _mec_name = "hh"
    gnabar = None  # 0.120 mho/cm2   Maximum specific sodium channel conductance
    gkbar  = None  # 0.036 mho/cm2   Maximum potassium channel conductance
    gl     = None  # 0.0003 mho/cm2  Leakage conductance
    el     = None  # -54.3 mV        Leakage reversal potential
    m      = None  # ?               sodium activation state variable
    h      = None  # ?               sodium inactivation state variable
    n      = None  # ?               potassium activation state variable
    ina    = None  # mA/cm2          sodium current through the hh channels
    ik     = None  # mA/cm2          potassium current through the hh channels


class PAS(Mechanism):
    _mec_name = "pas"
    g = None  # mho/cm2      conductance
    e = None  # mV           reversal potential
    i = None  # mA/cm2       non-specific current


Mechanism.HH = HH
Mechanism.PAS = PAS
