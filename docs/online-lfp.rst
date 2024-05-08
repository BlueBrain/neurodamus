:orphan:

=======================================
Online LFP Calculation Documentation
=======================================

Electrodes Input File
---------------------

Required Format
~~~~~~~~~~~~~~~~

To perform online LFP calculation, a weights file is required. The weights file should follow a specific format to ensure proper functioning.
More information about this file can be found in the `SONATA Simulation Specification <https://github.com/BlueBrain/sonata-extension/blob/master/source/sonata_tech.rst#format-of-the-electrodes_file>`_

Generating the Electrodes File
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The electrodes file can be generated using specific steps and considerations. Code and instructions to generate these files can be found `here <https://github.com/BlueBrain/BlueRecording>`_

Generating the LFP report
--------------------------

Before we proceed with the next steps, it's important to note that the online LFP calculation feature is **exclusively supported in CoreNEURON**. Therefore, ensure that you switch to CoreNEURON as your simulator before proceeding further.

Now that we have an electrode file for our simulation, the next steps will vary depending on whether you have a BlueConfig or SONATA simulation. Follow the instructions below based on your simulation setup:

BlueConfig Simulation
~~~~~~~~~~~~~~~~~~~~~~

1. Open your BlueConfig.

2. Locate the "Run Default" section.

3. Add the following key-value pair, providing the correct path to your electrodes file:

.. code-block::

    Run Default
    {
        ...
        LFPWeightsPath /path/to/electrodes_file.h5
        ...
    }

4. Create a report of type 'lfp':

.. code-block::

    Report lfp_report
    {
        Target AllCompartments
        Type lfp
        ReportOn v
        Unit mV
        Format SONATA
        Dt .1
        StartTime 0
        EndTime 110000
    }

.. note::
    Support for lfp reports with BlueConfig will be deprecated. All new features will be developed for SONATA simulations. It is recommended to migrate to SONATA simulations for future updates and enhancements.

SONATA Simulation
~~~~~~~~~~~~~~~~~~

To utilize the online LFP calculation feature, follow these steps:

1. Open your simulation configuration file.

2. Locate the "run" section in the configuration file.

3. Add the following key-value pair to the "run" section, providing the correct path to your electrodes file:

.. code-block::

    "run": {
        "tstart": 0,
        "tstop": 1,
        "dt": 0.025,
        "random_seed": 767740,
        "run_mode" : "WholeCell",
        "electrodes_file": "/path/to/electrodes_file.h5"
    }

Replace "/path/to/electrodes_file.h5" with the actual path to your electrodes file.

4. Create a report of type 'lfp' in the reports section:

.. code-block::

    "reports": {
        "lfp_report": {
            "type": "lfp",
            "cells": "Mosaic",
            "variable_name": "v",
            "dt": 0.1,
            "start_time": 0.0,
            "end_time": 40.0
        }
    }

Modify the rest of the parameters according to your requirements.

Key considerations
------------------

It is crucial to take note of the following considerations, some of which have been mentioned earlier:

- **Simulator Compatibility**: The online LFP calculation feature is exclusively supported in CoreNEURON. Therefore, ensure that you switch to CoreNEURON as your simulator if you want to be able to generate LFP reports. Failure to do so will result in a WARNING message:

.. code-block::

    [WARNING] Online LFP supported only with CoreNEURON.

Subsequently, an ERROR will be encountered when instantiating the LFP report:

.. code-block::

    [ERROR] (rank 0) LFP reports are disabled. Electrodes file might be missing or simulator is not CoreNEURON

- **BlueConfig Deprecation**: It's important to be aware that support for LFP reports with BlueConfig will be deprecated. Going forward, all new features and enhancements will be developed exclusively for SONATA simulations. It is recommended to migrate to SONATA simulations to take advantage of the latest advancements and ensure long-term compatibility.

- **Electrodes File Compatibility**: It is important to note that using an electrodes file intended for a different circuit than the one being used in your simulation will result in a warning and the most likely absence of an LFP report since the node_ids and sections won't match. There will be several WARNING messages displayed as follows:

.. code-block::

    [WARNING] Node id X not found in the electrodes file

To ensure accurate and valid LFP reports, make sure that the electrodes file corresponds to the circuit being used in your simulation.

- **Stimulus Electrode Compatibility**: A common use case is that current will be injected into a population to account for synaptic inputs from neural populations that are not modeled. In this case,the injected current should be considered a membrane current rather than an electrode current, and it is neccessary that total current over the neuron sums to zero in order to produce valid extracellular recording results. The Neuron SEClamp class does not fulfill these criteria due to numerical issues. We have created a new point process, `ConductanceSource`, available in `neurodamus-neocortex`, which does fulfill the criteria. If an conductance source stimulus is present in the simulation config file, `ConductanceSource` will be used by default instead of the SEClamp mechanism. The injected current will be reported as part of the `i_membrane` variable, rather than as an electrode current. 

However, it may be the case that the user wishes to model a physical electrode, rather than missing synaptic input, using the conductance source mechanism. In this case, the total current over the neuron is nonzero, and the injected current should not be considered a membrane current. For this reason, we have added the key `represents_phsyical_electrode` to the stimulus block. With the key-value pair `represents_physical_electrode:true`, SEClamp will be used rather than ConductanceSource.

Similarly, current sources may also be used to model the effects of missing synaptic inputs. We have created a new point process, `MembraneCurrentSource`, which is used instead of IClamp if the key `represents_phsyical_electrode` is set to false or is not set. `MembraneCurrentSource` behaves identically to IClamp, but is considered a membrane current, and is therefore accounted for in the calculation of the extracellular signal. It is not reported on as an electrode current. Setting `represents_physical_electrode:true` will result in using IClamp instead of `MembraneCurrentSource` 

By keeping these considerations in mind, you can ensure a smooth and successful usage of the online LFP calculation feature.

Conclusion
----------

This comprehensive documentation provides step-by-step instructions and considerations for the online LFP calculation feature. Follow the guidelines provided to understand, set up, and effectively utilize the feature in your Neurodamus simulations.
