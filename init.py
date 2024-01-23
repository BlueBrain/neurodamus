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
    first_argument_pos = 1
    config_file = "simulation_config.json"

    for i, arg in enumerate(sys.argv):
        if arg.endswith("init.py"):
            first_argument_pos = i + 1
        elif arg.startswith("--configFile="):
            config_file = arg.split('=')[1]
            first_argument_pos = i + 1
            break

    args = [config_file] + sys.argv[first_argument_pos:]

    return commands.neurodamus(args)


if __name__ == "__main__":
    # Returns exit code and calls MPI.Finalize
    h.quit(main())
