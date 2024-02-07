Examples
========

Basic Usage
-----------

Neurodamus-py, as an application, is very similar to the HOC version, both
run a simulaton fully unmanned guided by the BlueConfig. However, neurodamus-py does
accept CLI options to define some parameters of the simulations.

Once installed, you should be able to find `neurodamus` in your path:

.. code-block::

  $ neurodamus
    Usage:
        neurodamus <BlueConfig> [options]
        neurodamus --help

Among the options you will find flags to tune run behavior, which was not possible in HOC.

Launching
~~~~~~~~~

Neurodamus-py explicitly depends on MPI libraries for parallel execution.
Therefore please use "srun" or "mpiexec" to launch it, according to your platform. If you
don't, complicated error messages may show up. Please remember it.

Even though a `neurodamus` launcher is provided, for production runs we suggest using
`special` instead. This way has proven to take advantage of optimized math libraries.
We hope to bring the same advantages to the launcher script soon.

.. code-block:: sh

 srun <srun params> special -mpi -python $NEURODAMUS_PYTHON/init.py <neurodamus params>

For detailed launching instructions on BB5, please visit the confluence page "Neurodamus"
section "Neurodamus-py".


Only build model, run later
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The user has the possibility of creating the model to CoreNeuron independently
of the run phase. Consider the case of a heavy simulation. It might be desirable
to create the model and later attempt to run it with different parameters in a
dedicated allocation.

Two options exist to control this behavior:
 - ``--build-model=[AUTO, ON, OFF]`` Defines whether the build phase should run. Default: AUTO

   - AUTO: build model if doesn't exist and simulator is CoreNeuron
   - ON: always build and eventually overwrite the model
   - OFF: Don't build the model. Simulation may fail to start

 - ``--simulate-model=[ON, OFF]`` Controls whether neurodamus will launch the
   simulation automatically. Default: ON

Resource estimation
-------------------

Calculations
~~~~~~~~~~~~
When running a simulation on bb5, the number of computing nodes needed depends on the number of
cells being simulated. A rough(1) estimation is:

 - Each neuron can take ~ 20 - 25 MB memory for simulation.
 - Each node has ~ 360 GB x 1024 MB/GB = 368640 MB of memory

Hence each node can accommodate ~ 368640 / 25 = 14745 neurons.

In order to simulate faster, users can increase the number of nodes provided. HPC recommends
~ 15 neurons/core x 40 cores/node = 600 neurons/node.
For example, for a circuit of 6000 cells, users can simulate it on a single node or 10 nodes.

The choice depends on the availability of nodes and how fast the results are expected,
taking into consideration that the maximum number of nodes to request for each job is 720.

[1] Basic connectivity being considered. Depending on the connectivity and cells
configurations (e.g. featuring heavier mechanisms) these figures can change significantly.
This issue is being followed in https://bbpteam.epfl.ch/project/issues/browse/BBPBGLIB-556
For now we advise users to test jobs on a small scale before submitting a full-scale one.

Dry run mode
~~~~~~~~~~~~
In order to obtain a more accurate estimation of the resources needed for a simulation,
users can also run Neurodamus in dry run mode. This functionality is only available
for SONATA circuits.

This mode will partially instantiate cells and synapses to get a statistical overview
of the memory used but won't run the actual simulation.
The user can then check the estimated memory usage of the simulation as it's printed on
the terminal at the end of the execution. In a future update we will also integrate
indications and suggestions on the number of tasks and nodes to use for that circuit
based on the amount of memory used during the dry run.

The mode also provides detailed information on the memory usage of each cell metype,
synapse type and the total estimated memory usage of the simulation, including the
memory overhead dictated by loading of libraries and data structures.

The information on the cell memory usage is also automatically saved in a file called
``memory_usage.json`` in the working directory. This json file contains a
dictionary with the memory usage of each cell metype in the circuit and is automatically
loaded in any further execution of Neurodamus in dry run mode, in order to speed up the execution.
In future we plan to also use this file to improve the load balance of actual simulations.

To run Neurodamus in dry run mode, the user can use the ``--dry-run`` flag when launching
Neurodamus. For example:

``neurodamus --configFile=BlueConfig --dry-run``


Neurodamus for Developers
-------------------------

Neurodamus was designed to provide an easy Pythonic API while keeping the same concepts.
Please see `Module Reference`

Disable / Enable connections during simulation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As an example, the user may want to enable and disable connections at different simulation
times. (NOTE: this is only possible using the NEURON simulator. CoreNeuron simulations
cannot be changed interactively).

.. code-block:: python

 from neurodamus import Neurodamus
 from neurodamus.utils.logging import log_stage, log_verbose

 nd = Neurodamus('BlueConfig')

 log_stage('Run simulation!')
 nd.solve(50)  # Until 50ms
 nd.synapse_manager.disable_group(62977, 62698)
 nd.solve()  # until end


Drop connections to not be simulated
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sometimes we may want to drop connections altogether. The user may completely
avoid them from being instantiated in the simulator (compatible with CoreNeuron)

.. code-block:: python

 from neurodamus import Neurodamus
 from neurodamus.utils.logging import log_stage, log_verbose

 nd = Neurodamus('BlueConfig_for_remove', auto_init=False)

 log_stage('Starting edge removal')
 nd.synapse_manager.delete_group(62977, 62698)

 nd.init()   # Initialize the simulator (needed because we set auto_init=False)
 nd.run()    # Run all


Neurodamus as a High-Level API for neuron
-----------------------------------------

A slightly different set of use cases is to provide users a powerful High-Level API for Neuron,
to ease the life of manually setting up neuron networks.
With this API, you can reduce the amount of code to setup models by as far as 5-fold
(based on the next tutorials translation)

Example 1 - Neuron Tutorial Basic
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Basic neuron usage on how to:

 - Build a single compartment neuron model
 - Add membrane mechanisms (such as ion currents)
 - Create stimuli and run simulations
 - Extend a single compartment model with dendrites

.. literalinclude:: ../examples/neuron_tut1.py

Example 2 - Neuron Tutorial synapses
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../examples/neuron_tut2.py
   :pyobject: test_tut2


Neurodamus advanced simulation example
--------------------------------------

This is a more advanced example that instantiates a Neurodamus simulation step by step for a simple
circuit.
It creates a Node object and it takes care of doing the following:

 - Loads targets
 - Computes Load Balancing
 - Instantiates cells
 - Instantiates synapses and gap junctions
 - Enables stimulus
 - Enables modifications
 - Enables reports
 - Runs simulation
 - Dumps spikes to files
 - Cleans up the simulated model

.. literalinclude:: ../examples/test_neurodamus.py
   :pyobject: test_node_run
