# flake8: noqa
"""
    neurodamus
    ----------

    The neurodamus package implements the instantiation of simulations in Neuron
    based on a configuration file, a.k.a. simulation_config.json
    It is deeply based on the HOC implementation, therefore providing python modules like
    `node`, `cell_distributor`, etc; and still depends on several low-level HOC files at runtime.
"""
from __future__ import absolute_import
import importlib.metadata
try:
    __version__ = importlib.metadata.version(__name__)
except Exception:
    __version__ = 'devel'

__author__ = "Fernando Pereira <fernando.pereira@epfl.ch>"
__copyright__ = "2018 Blue Brain Project, EPFL"

# Neurodamus node for setting up a neurodamus execution
from .node import Node, Neurodamus


__all__ = ["Node", "Neurodamus"]
