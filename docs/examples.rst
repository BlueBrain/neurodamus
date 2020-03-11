Examples
========

Basic Usage
-----------

Neurodamus, as an application, is very similar to the hoc version in the sense that it can
be fully unmanned guided by the BlueConfig. However a python launcher script is
provided which accepts options.
Once installed, you should be able to find `neurodamus` in your path:

.. code-block::

  $ neurodamus
    Usage:
        neurodamus <BlueConfig> [options]
        neurodamus --help

Among the options you will find flags to tune run behavior, which was not possible in HOC.

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