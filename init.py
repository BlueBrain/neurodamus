"""
Neurodamus is a software for handling neuronal simulation using neuron.

Copyright (c) 2018 Blue Brain Project, EPFL.
All rights reserved
"""
import sys
from neurodamus import commands
from neurodamus.utils.cli import extract_arguments
from neuron import h
import logging


def main():
    args = []
    try:
        args = extract_arguments(sys.argv)
    except ValueError:
        logging.error("Positional arguments are not supported by init.py; please specify --configFile=<config> "
                      "to run this script (or leave empty to use the default, ./simulation_config.json).")
        return 1

    return commands.neurodamus(args)


if __name__ == "__main__":
    # Returns exit code and calls MPI.Finalize
    h.quit(main())
