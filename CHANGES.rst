==========
Change Log
==========

Version 2.5.2
=============
**Apr. 20, 2021**

*Fixes*
  * Reset ShotNoise.stimCount for multi-cycle builds
  * Enable getting target from hoc via TargetManager
  * Initialization improvements. Always NEURON_INIT_MPI


Version 2.5.1
=============

*Improvements*
  * Summation reports support for CoreNeuron
  * Prepend /scatter to out.dat after CoreNEURON simulation
  * Local to global transformation in METype
  * ShotNoise and RelativeShotNoise stimuli


Version 2.5.0
=============
**Mar. 26, 2021**

*New Features*
  * Support for Multi-Circuit
  * Connection configurations override checks
  * NGV Engine

*Improvements*
  * reading src/dst population from edges meta
  * Support for Sonata Edges with mvd3 nodes
  * Detection of node file type: support for arbitrary mvd3


Version 2.4.0
=============
**Feb. 2, 2021**

*New features*
  * Read additional attributes from new emodel hoc template and pass to metype constructor
  * New key SynDelayOverride in Connection block to modify synaptic delays
  * New key SYNAPSES__init_depleted in Conditions block to initialize synapses in depleted state

*Improvements*
  * Read CoreNeuron data version dynamically than hard coded number in case of more ranks than cells
  * Full debug logging only for src-dst
  * Fixes related to Engines
  * Refactoring Node and Engine for multi-circuit
  * Pass population ids to override_helper


Version 2.3.1
=============
**Jan. 29, 2021**

*Fixes*
  * Issue when launching CoreNEURON sim with more ranks than cells


Version 2.3.0
=============
**Dec. 22, 2020**

*New features*
  * Implement global options block in BlueConfig

*Improvements*
  * Attach to src cell when not offset and CoreNeuron
  * Save load balance data to folder sim_conf


Version 2.2.1
=============
**Dec. 10, 2020**

*New features*
  * Support for Section target reports

*Improvements*
  * Completely drop hoc ParallelNetManager
  * Refactoring cell distribution: explicit V5 and V6 cells, gid offset, unified finalize
  * Refactoring Sim-Config: New config validation framework


Version 2.1.2
=============
**Nov. 27, 2020**

*New Features*
  * Support for MinisSingleVesicle BlueConfig option (BBPBGLIB-660)
  * Added options for setting SpikeLocation, SpikeThreshold, temperature and initial voltage

*Fixes*
  * Fixing call to write sim config
  * Flush SONATA reports at the end of the simulation
  * Documentation: launch notes
  * Throw error when report tstart > tend

*Improvements*
  * CellDistributor: Refactoring cell loading


Version 2.0.2
=============
**Oct. 28, 2020**

*Fixes*
  * Fix skipping synapse creation when weight is 0 (BBPBGLIB-673)
  * Fix deadlock when an exception is thrown from NEURON (BBPBGLIB-678)
  * Ensure data dir when skipping model build
  * SONATA: Replay to work with multiple populations
  * Logging colors only for terminal devices


Vesion 2.0.0
============

*New Features*
  * Full delayed connection implementation mechanisms.
  * SONATA: Computig PopulationIDs from Edge population names
  * SONATA: Connection blocks to handle target populations
  * Support for setting SecondOrder in BlueConfig

*Improvements*
  * Improved delayed connections, setup before finalize
  * New behavior of relative paths. Set CurrentDir

*Fixes*
  * Fix spike with negative time (BBPBGLIB-367)
  * CoreNeuron processes with 0-cells
  * Single spike in SynapseReplay (BBPBGLIB-661)
  * Fixing replay to work with multiple populations


Version 1.3.1
=============
**Aug. 26, 2020**

*Improvements*
  * Calcium scaling via new BlueConfig key "ExtracellularCalcium"
  * Pass Baseseed to Coreneuron

*Fixes*
  * GJ Offset calculation only for nrn
  * Fix for nrn when sgids are not ascending


Version 1.2.1
=============
**July 27, 2020**

*New features*
  * Support for multipopulation edge files, for circuit and projections
  * Support for SONATA reports
  * Support for nodes "exc_mini_frequency" and "inh_mini_frequency"


Version 1.1.0
=============
**May 28, 2020**

*New features*
  * BBPBGLIB-618 Add Time Measurements featuring support for nested routines
  * BBPBGLIB-555 Heuristic to auto select the Load Balance mode

*Improvements*
  * Simplify cell loaders API/implementation using numpy exclusively

*Bug fixes*
  * Delayed connections: Handle simultaneous events. Avoid last delayed connection from
    overriding previous ones (late binding issue)


Version 1.0.0
=============
**Apr 21, 2020**

*New features / Major changes*
  * Add xopen morphology generation and loading feature
  * Reusing previously calculated LoadBalance
  * Dropped Python 2.x support (simplified deps)

*Improvements*
  * Refactoring of ConnectionManager wrt instantiation of SpontMinis and Replay
  * Make SimConfig global singleton
  * Refactoring CellDistributor


Version 0.9.0
=============
**Feb 27, 2020**

*New features*
  * New loader to support Sonata nodes
  * Initial support for Sonata node populations, specified via the target pop:target_name
  * Added CLI option --modelbuilding-steps to set the number of steps for the model building
  * BBPBGLIB-567 Filter Instantiated projections

*Improvements*
  * Refactoring replay for compat with save-restore and CoreNeuron
  * Refactoring connection_manager for dedicated ConnectionSet structure


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
