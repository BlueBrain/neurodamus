# -*- coding: utf-8 -*-
# flake8: noqa
from __future__ import absolute_import
import pkg_resources
try:
    __version__ = pkg_resources.get_distribution(__name__).version
except Exception:
    __version__ = 'unknown'

__author__ = "Fernando Pereira <fernando.pereira@epfl.ch>"
__copyright__ = "2018 Blue Brain Project, EPFL"

# Neurodamus node for setting up a neurodamus execution
from .node import Node, Neurodamus
