"""
Neurodamus is a software for handling neuronal simulation using neuron.

Copyright (c) 2018 Blue Brain Project, EPFL.
All rights reserved
"""
from neurodamus import Neurodamus
from neurodamus.cell_distributor import CellDistributor
from neurodamus.connection_manager import _ConnectionManagerBase
from neurodamus.connection import Connection
from line_profiler import LineProfiler
from neurodamus.core import MPI
# import cProfile

if __name__ == "__main__":
    if MPI.rank > 0:
        Neurodamus('BlueConfig')
    else:
        # Neurodamus('BlueConfig').run()
        # cProfile.run("nd = Neurodamus('BlueConfig')")
        lp = LineProfiler()
        lp.add_function(CellDistributor._setup)
        lp.add_function(CellDistributor.finalize)
        lp.add_function(Connection._create_synapse)
        lp.add_function(Connection.apply_configuration)
        lp.add_function(Connection.finalize)
        lp.add_function(_ConnectionManagerBase.group_connect)
        lp.add_function(_ConnectionManagerBase.get_synapse_parameters)
        with lp:
            Neurodamus('BlueConfig')
        lp.print_stats(open("line_stats.txt", "w"))
