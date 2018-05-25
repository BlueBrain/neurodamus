"""
MComplex module

Copyright 2018 - Blue Brain Project, EPFL
"""
from __future__ import absolute_import
import logging
from .. import Neuron


def create_mcomplex():
    h = Neuron.require("loadbal")
    x = h.startsw()
    pc = h.ParallelContext()
    lb = h.LoadBalance()

    lb.ExperimentalMechComplex("StdpWA", "extracel", "HDF5", "Report", "Memory", "ASCII")
    if pc.id == 0:
        logging.info("Created mcomplex.dat %g", h.startsw() - x)


def read_complex(lbalance_obj):
    logging.info("Loading mcomplex.dat")
    lbalance_obj.read_mcomplex()
