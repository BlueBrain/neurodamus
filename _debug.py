"""
Neurodamus is a software for handling neuronal simulation using neuron.

Copyright (c) 2018 Blue Brain Project, EPFL.
All rights reserved
"""
from neurodamus import Neurodamus

if __name__ == "__main__":
    Neurodamus("BlueConfig", enable_reports=False, logging_level=3).dump_circuit_config()
