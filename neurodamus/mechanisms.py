"""
Class defining cell mechanisms
"""
from __future__ import absolute_import
import logging
from neuron import nrn
from .utils import dict_filter


class Mechanism:
    _mec_name = None
    # Declare the subtypes
    HH = None   # type: HH
    PAS = None  # type: PAS

    def __new__(cls):
        if cls is Mechanism:
            raise TypeError("Mechanisms is abstract. Instantiate a specific Mechanism")
        return object.__new__(cls)

    def _init(self, **opts):
        for name, val in dict_filter(opts, lambda _name, _: not _name.startswith("_")):
            if hasattr(self, name):
                setattr(self, name, val)
            else:
                logging.warn("Warning: param %s not recognized for the mechanism", name)
        return self

    def _apply(self, section):
        section.insert(self._mec_name)
        for name, val in vars(self).items():
            if not name.startswith("_") and hasattr(self, name) and val is not None:
                setattr(section, "{}_{}".format(name, self._mec_name), val)

    def apply(self, section_or_sectionlist):
        # Single section - base neuron cells used
        if isinstance(section_or_sectionlist, nrn.Section):
            self._apply(section_or_sectionlist)
        else:
            for s in section_or_sectionlist:
                self._apply(s)

    mk_HH = classmethod(lambda cls, **opts: HH()._init(**opts))
    mk_PAS = classmethod(lambda cls, **opts: PAS()._init(**opts))


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

