SONATA FAQ
----------

This is a list of Frequently Asked Questions about the NEURODAMUS support of SONATA format.


How do I convert my old BlueConfig to SONATA configuration?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Right now it is a manual process, however we are studying the viability of
an automatic converter in this `ticket
<https://bbpteam.epfl.ch/project/issues/browse/BBPBGLIB-891>`__

For more info regarding the corresponding keys between BlueConfig and SONATA
you could check this spreadsheet.

There are also some examples where given a BlueConfig, we show the corresponding
SONATA config file. The examples can be found `here
<https://bbpgitlab.epfl.ch/hpc/sim/neurodamus-py/-/blob/doc/sonata/docs/sonata-simulation.rst>`__


How do I know if my new SONATA configuration is valid?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can load your simulation_config.json file with libsonata and it will tell
you if there are any issues with the file.

.. code-block:: bash

    $  module load unstable py-libsonata/0.1.14
    $  python
    $  >>> import libsonata
    $  >>> libsonata.SimulationConfig.from_file('simulation_config.json')
    File "read_simconfig.py", line 3, in <module>
    libsonata.SimulationConfig.from_file('simulation_config.json')
    libsonata._libsonata.SonataError: Invalid value: '"compartment"' for key 'type'

More info about the sections and valid values in the simulation config can be found `here
<https://github.com/BlueBrain/sonata-extension/blob/master/source/sonata_simulation.rst>`__


And how do I convert my spikes (out.dat) and binary reports (.bbp) to SONATA format?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are 2 options:

- If you want to convert also the BlueConfig to SONATA, then rerun the simulation with the new simulation config file that you converted.

- If you only need the reports, then we have a proof of concept converter.
  More info can be found in this `ticket <https://bbpteam.epfl.ch/project/issues/browse/REP-77>`__


How do I run a SONATA simulation?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Basically the same way than before.

First, neurodamus modules need to be loaded

- py-neurodamus: should be at least 2.12.0 for base SONATA support

- neurodamus-xxx: load the neurodamus model needed for your simulation

.. code-block:: console

    $ module load unstable py-neurodamus/2.12.0 neurodamus-neocortex

Finally `special` is called with the --configFile CLI option pointing to the sonata configuration file

.. code-block:: console

    $  srun special -mpi -python $NEURODAMUS_PYTHON/init.py --configFile=simulation_config.json
