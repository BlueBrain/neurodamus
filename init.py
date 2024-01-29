"""
Neurodamus is a software for handling neuronal simulation using neuron.

Copyright (c) 2018 Blue Brain Project, EPFL.
All rights reserved
"""
import sys
from neurodamus import commands
from neuron import h


def main():
    """Get the options for neurodamus and launch it.

    We can't use positional arguments with special so we look for
    --configFile=FILE, which defaults to simulation_config.json
    """
    config_file = "simulation_config.json"

    for i, arg in enumerate(sys.argv[1:]):
        if not arg.startswith("-"):
            print("Positional arguments are not supported by init.py. Please specify --configFile=<config file> to\n"
                  "run this script (or leave empty to use the default, ./simulation_config.json).", file=sys.stderr)
            sys.exit(1)
        elif arg.startswith("--configFile="):
            config_file = arg.split('=')[1]
            break

    args = [config_file] + [x for x in sys.argv[1:] if not x.startswith("--configFile=")]

    return commands.neurodamus(args)


if __name__ == "__main__":
    # Returns exit code and calls MPI.Finalize
    h.quit(main())
