"""
Neurodamus is a software for handling neuronal simulation using neuron.

Copyright (c) 2018 Blue Brain Project, EPFL.
All rights reserved
"""
import sys
from neurodamus import Neurodamus
from neurodamus.core.configuration import GlobalConfig

if __name__ == "__main__":
    GlobalConfig.verbosity = 3
    Neurodamus("BlueConfig").dump_circuit_config()

