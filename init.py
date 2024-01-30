"""
Neurodamus is a software for handling neuronal simulation using neuron.

Copyright (c) 2018 Blue Brain Project, EPFL.
All rights reserved
"""
import sys
from neurodamus import commands
from neuron import h
import logging


def extract_arguments(args):
    """Get the options for neurodamus and launch it.

    We can't use positional arguments with special so we look for
    --configFile=FILE, which defaults to simulation_config.json
    """
    config_file = "simulation_config.json"
    for i, arg in enumerate(args[1:]):
        if not arg.startswith("-"):
            raise ValueError("Positional arguments are not supported")
        elif arg.startswith("--configFile="):
            config_file = arg.split('=')[1]
            break
    args = [config_file] + [x for x in args[1:] if not x.startswith("--configFile=")]
    return args


def main():
    args = []
    try:
        args = extract_arguments(sys.argv)
    except ValueError:
        logging.error("Positional arguments are not supported by init.py; please specify --configFile=<config> "
                      "to run this script (or leave empty to use the default, ./simulation_config.json).")
        h.quit(1)

    return commands.neurodamus(args)


if __name__ == "__main__":
    # Returns exit code and calls MPI.Finalize
    h.quit(main())
