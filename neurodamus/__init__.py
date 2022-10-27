# flake8: noqa
"""
    neurodamus
    ----------

    The neurodamus package implements the instantiation of simulations in Neuron
    based on a configuration file, a.k.a. BlueConfigs
    It is deeply based on the HOC implementation, therefore providing python modules like
    `node`, `cell_distributor`, etc; and still depends on several low-level HOC files at runtime.
"""
from __future__ import absolute_import
import pkg_resources
try:
    __version__ = pkg_resources.get_distribution(__name__).version
except Exception:
    __version__ = 'devel'

__author__ = "Fernando Pereira <fernando.pereira@epfl.ch>"
__copyright__ = "2018 Blue Brain Project, EPFL"

# Neurodamus node for setting up a neurodamus execution
from .node import Node, Neurodamus
from .metype import Cell_V5, Cell_V6


__all__ = ["Node", "Neurodamus"]
