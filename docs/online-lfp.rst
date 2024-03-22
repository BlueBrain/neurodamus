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

The electrodes file can be generated using specific steps and considerations. Follow the instructions below to generate the file:

1. Produce a compartment report from a target including the cells that will be used for the LFP calculation.

2. Run the file getPositions.py, using the bash script GetPositions.sh. This will create a folder containing pickle files listing the (x,y,z) position of each segment in each cell in the target.

3. Run the file writeH5_MPI_prelim.py, using the bash script WriteH5Prelim.sh. This will create the weights file, populating all coefficients with 1s. The script writeH5_MPI_prelim.py will have to be modified depending on the desired electrode array; it currently creates the weights file for a Neuropixels probe.

4. Run the file writeH5_MPI.py, using the bash script WriteH5.sh. This populates the weights file with the correct coefficients. This step requires the use of a version of h5py built with MPI support. This two-step procedure is used because the calculation of the LFP coefficients is not feasible without parallelization, but MPI cannot be used when H5 files are created.

The files mentioned can be found `here <https://github.com/joseph-tharayil/create_lfp_weights_for_neurodamus>`_

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

- **Stimulus Electrode Compatibility**: A common use case is that current will be injected into a population to account for synaptic inputs from neural populations that are not modeled. In this case, it is neccessary that total current over the neuron sums to zero in order to produce valid extracellular recording results. For IClamp electrodes, this is always the case. However, the Neuron SEClamp class does not fulfill this criterion due to numerical issues. We have created a new point process, `new_conductance_source`, available in `neurodamus-neocortex`, which does fulfill the criterion. Therefore, If an SEClamp source is present in the simulation config file, and `new_conductance_source` is compiled, this will be used instead of the SEClamp mechanism. If `new_conductance_source` is not available, SEClamp will be used, and extracellular recording results should not be trusted.    

By keeping these considerations in mind, you can ensure a smooth and successful usage of the online LFP calculation feature.

Conclusion
----------

This comprehensive documentation provides step-by-step instructions and considerations for the online LFP calculation feature. Follow the guidelines provided to understand, set up, and effectively utilize the feature in your Neurodamus simulations.
