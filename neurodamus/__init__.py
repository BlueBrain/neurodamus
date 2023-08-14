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

# Control matched warning to display once in rank 0.
# "special" binaries built with %intel build_type=Release,RelWithDebInfo flushes
# denormal results to zero, which triggers the numpy warning for subnormal in every rank
# after "import h5py". Reduce this type of warning displayed once in rank0.
# Note: "special" with build_type = FastDebug/Debug or calling the simulation process
#     in python (built with gcc) does not have such flush-to-zero warning.
from .utils import warnings_once
warnings_once(message="The value of the smallest subnormal for .* type is zero.",
              category=UserWarning, module="numpy")

# Neurodamus node for setting up a neurodamus execution
from .node import Node, Neurodamus


__all__ = ["Node", "Neurodamus"]
