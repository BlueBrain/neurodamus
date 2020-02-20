==========
Change Log
==========


Version 0.8.1
=============
**Feb 20, 2020**

*Improvements*
  * Refactoring for ConnectionSet class
  * Documentation

*Bug fixes*
  * Cached Hoc values were not being updated
  * Resume w CoreNeuron: dont init circuit


Version 0.8.0
=============
**Jan. 14, 2020**

*New features*
  * Allow selecting which phases to run with --build-model --simulate-model --output-path
  * Will delete intermediate CoreNeuron files, unless --keep-build option is set
  * Ability to load multiple mod libraries. NRNMECH_LIBRARY_PATH should point to a
    library containing at least the neurodamus aux mods. Libraries of cell mechanisms
    alone shall go into BGLIBPY_MOD_LIBRARY_PATH (multiple accepted)

*Bug Fixes*
  * BBPBGLIB-554 Finalize connections only at init() time


Version 0.7.2
=============
**Dec. 19, 2019**

*Improvements*
  * Support loading of several mech lib (: separated)
  * Fixed & cleanup options to detect build model


Version 0.7.1
=============
**Nov. 22, 2019**

*Improvements*
  * Adding option to initialize later
  * Refactor for Single configure step, allowing for split-file conections


Version 0.7.0
=============
**Nov. 19, 2019**

*New Features*
  * Multi-Cycle model building
  * src- dst- seed popuplation IDs
  * New circuit paths (start.target and edges location)

*Bug Fixes*
  * Spont minis was not being updated correctly (c/46614)

*Improvements*
  * MPI auto-detection
  * targets printCellCounts()
  * Automatic project version & documentation


Version 0.6.0
=============
**Aug. 15, 2019**

*New Features*
  * Support to launch with CoreNeuron with Reports and Replay
  * Support mixed projection file types
  * Nice API for Step-by-step run
  * Replay like in save-state, support for delay and shift

*Bug Fixes*
  * MultiSplit fixed

*Improvements*
  * SpontMiniRate independent of the Connection definition order
  * General improvements after MG review
  * Refactoring on connection.py
  * Refactored LoadBalance
  * Refactored neurodamus.prepare_run()
  * Cell Readers spinned off cell distributor.
  * PEP8 / doctrings...
  * Better integration with SynapseTool
  * Deployment improv for pip-install compat
  * Documentation


Version 0.5.0
=============
**Nov. 3, 2018**

*Bug Fixes*
  * Instantiate synapses/GJs in reverse, mimicking HOC
  * Always Instantiate ElectrodeManager
  * More GJ fixes
  * OSError lock err for MVD3 file

*Improvements*
  * Detection of circuit file types
  * Enabling other configFiles via --configFile=


Version 0.4.0
=============
**Oct. 1, 2018**

*New Features*
  * Support of SynapseTool for Syn2/SONATA

*fixes*
  * GapJunctions
  * Progressbar for streams


Version 0.3.0
=============
**Aug. 14, 2018**

*New Features*
  * Synapse Replay and Projections

*Improvements*
  * connection_configure implemented in a fast hoc routine
  * Pep8


Version 0.2.2
=============
**July 31, 2018**

*New Features*
  * Added init.py
  * V6 circuit loading
  * V6 circuit stim apply

*Improvements*
  * Sync Hoc files with latest neurodamus master
  * Better output for multi-cpu runs


Version 0.2.1
=============
**July 26, 2018**

*New Python API*
  * ConnectionManager
  * GapJuntionsManager
  * METype
  * Enable/Disable connections

*Improvements*
  * Replays using a new OrderedMap structure
  * Cleaned and Refactored: Creation of .core subpackage
  * Refactoring CellDistributor
  * Remove mpi4y dependency


Version 0.1.0
=============
**June 5, 2018**

*New Features*
  * Initial version of Neurodamus Python
  * Node.hoc API 100% in Python
  * High-Level Neuron implementation

    - Neuron Bridge, Cell, Stimuli
    - Examples on how to implement Neuron full tutorials in a few lines
