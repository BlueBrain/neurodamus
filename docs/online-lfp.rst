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

1. Produce a compartment report from a target including the cells that will be used for the LFP calculation. Instructions for this step are found elsewhere in this repository.

2. Create a csv file containing information about the electrodes. Each row of the file contains information about one electrode contact. The scripts writeEEGToCSV.py and writeNeuropixelsToCSV.py are provided to create this file for a two-contact EEG system and a Neuropixels probe, respectively. The latter can be launched with WriteNP2CSV.sh. The format of the csv file is defined as follows:

- The header is *,x,y,z,layer,region*
- The first column is the name of the electrode contact. It is either a string or an integer
- The second through fourth columns are the x, y, and z coordinates of the contact in Cartesian space. They are floats.
- The fifth column is the cortical layer in which the electrode is located. It is a string in the format L*N*, where *N* is an integer.
    + If the electrode is outside of the brain, the value in the column is the strign *Outside*
    + If the electrode is in a region without laminar oraginzation, the value in the column is the string *NA*
- The sixth column is the brain region in which the electrode is located. It is a string.
    + If the electrode is outside the brain, the value in the column is the strong *Outside* 

3. Run the file getPositions.py, using the bash script GetPositions.sh. This loads the compartment report produced in step 1, and will create a folder containing pickle files listing the (x,y,z) position of each segment in each cell in the target.

4. Run the file writeH5_MPI_prelim.py, using the bash script WriteH5Prelim.sh. This loads the compartment report produced in step 1 and the csv file produced in step 2, and will create the electrodes file, populating all coefficients with 1s.

5. Run the file writeH5_MPI.py, using the bash script WriteH5.sh. This loads the position files created in step 3 and the electrode file created in step 4, populates the electrode file with the correct coefficients. This step requires the use of a version of h5py built with MPI support. This two-step procedure is used because the calculation of the LFP coefficients is not feasible without parallelization, but MPI cannot be used when H5 files are created.


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

By keeping these considerations in mind, you can ensure a smooth and successful usage of the online LFP calculation feature.

Conclusion
----------

This comprehensive documentation provides step-by-step instructions and considerations for the online LFP calculation feature. Follow the guidelines provided to understand, set up, and effectively utilize the feature in your Neurodamus simulations.
