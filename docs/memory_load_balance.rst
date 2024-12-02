============================
Memory Load Balance Tutorial
============================

Introduction
------------
When using neurodamus on a very big circuit one might incur into issues and OOMs due
to the sheer size of the circuit and imbalance in the memory distribution of gids
during the simulation.
In order to mitigate (or solve) these issues, we have implemented a memory balancing
mechanism in neurodamus that uses the estimation data collected in the dry run mode
to balance the memory usage across all the nodes.
The usage, at the moment, needs multiple steps: first a neurodamus dry run,
then a neurodamus model instantiation with no simulation, a rebalance and then finally simulation.

Dry Run
-------
.. code-block:: bash

    $ neurodamus ... --dry-run

This will run the simulation in dry-run mode and collect the memory usage data for
each gid, for both cells and synapses.
The data will be stored in the `memory_per_metype.json`, `cell_memory_usage,json` and
`allocation_rx_cy.pkl.gz` files in the cwd directory where x and y are respectively the number of
ranks and cycles the simulation was balanced for.
By default, the balance distribution will happen on the amount of nodes/ranks that the dry run suggests.
However you can manually specify the amount of ranks you want to distribute on by using the `--num-target-ranks`` option.
So, for example, let's say you want to distribute over 100 ranks, you can run neurodamus with:

.. code-block:: bash

    $ neurodamus ... --configFile=simulation_config.json --dry-run --num-target-ranks=100


Model Instantiation
-------------------
.. code-block:: bash

    $ neurodamus ... --lb-mode=Memory --simulate-model=OFF

Once the allocation files have been created, we need to instantiate the model without running the simulation.
This is obtained using the `--simulate-model=OFF` option and the `--lb-mode=Memory` option to specify that
we want to use the memory load balancing for this step, even without simulating.
This will create the model in the specified output folder and will be used for the rebalance step.
The model will be saved in the output folder specified using the `--output-path` option.

.. code-block:: bash

    $ neurodamus ... --lb-mode=Memory --configFile=simulation_config.json --simulate-model=OFF --output-path=/path/to/output

Rebalance
---------
Balancing for CoreNeuron, especially using multi-cycle, can distribute gids unoptimally for a single machine.
In order to mitigate these issues we have implemented a post processing rebalance step that will redistribute the gids
evenly across the machines, based on the data collected in the previous phases.
You will find the `rebalance-corenrn-data.py` script in the `neurodamus/tools` folder and you can run it with:

.. code-block:: bash

    $ python3 rebalance-corenrn-data.py input_file.dat n_machines --output-file rebalanced_file.dat

where `input_file.dat` is the file containing the data collected during the dry run and `n_machines` is the number
of target machines.
The script will output a new file `rebalanced_file.dat` that will contain the rebalanced data.
The script offers more options so please consult the help message for more information.

Another script `rebalance-stats.py` in the `neurodamus/tools` folder can be used to check the distribution of the gids
across the machines to make sure the distribution is even.

Simulation
----------

Finally we can run the simulation with the rebalanced data using coreneuron.

.. code-block:: bash

    $ special-core -d /path/to/coreneuron_input -f /path/to/rebalanced_file.dat

This will run the simulation using the rebalanced data and should distribute the memory usage more evenly across the machines.
