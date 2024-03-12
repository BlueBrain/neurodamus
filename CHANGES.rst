==========
Change Log
==========

Version 3.1.1
=============
**12 Mar 2024**

*Bug Fixes*
  * Fix fetching error in GH workflow triggered by tag


Version 3.1.0
=============
**12 Mar 2024**

*New Features*
  * [BBPBGLIB-1102] (Part two) Load memory balance from file (#129)
  * [BBPBGLIB-1102] Add memory load balance export based on dry run estimate (#111)

*Bug Fixes*
  * StrEnum not working with older python versions (#125)
  * Fix unit tests (#119)

*Improvements*
  * [BBPBGLIB-1125] GH forkflow for building a wheel (#121)
  * On --debug install a hook for NGV to show neuro-glial "spikes" (#137)
  * [BBPBGLIB-1132] Replace StimulusManager.hoc with the python classes (#132)
  * [BBPBGLIB-1134] Move ShowProgress.hoc to python (#131)
  * [BBPBGLIB-1135] Move CompartmentMapping to python (#133)
  * [BBPBGLIB-1133] Remove ElectrodeManager.hoc and LookupTableV2.mod (#128)
  * [BBPBGLIB-1121] Remove BlueConfig parser (#127)
  * Use actions/checkout@v4 to use Node 20 (#126)
  * [BBPBGLIB-1127] Remove SpikeWriter.mod and out.dat (#123)
  * [BBPBGLIB-1110] Error now raised when executeConfigure is returned with errors (#120)
  * Remove SynapseReader.mod and SynReaderNRN (#122)
  * [BBPBGLIB-1124] Remove hoc targets related code (#118)
  * [BBPBGLIB-1120] Remove node loaders for MVD3 and NCS (#117)


Version 3.0.0
=============
**31 Jan 2024**

*New Features*
  * Deprecate BlueConfig part-1: Raise errors for BlueConfig configuration files (#101)
  * Read synapse parameters in a collective safe manner. (#85)

*Bug Fixes*
  * [BBPBGLIB-1115] Fix issue with summation reports and cell target in NEURON (#114)
  * [BBPBGLIB-1114] Apply offset to the gids before reading node file (#113)

*Improvements*
  * [BBPBGLIB-1111] Raise a proper error when missing "--configFile=" (#115)
  * Remove dependency on mvdtool (#112)
  * Transform setup.py to pyproject.toml (#110)


Version 2.17.0
==============
**22 Dec 2023**

*New Features*
  * Fast & lightweight dry run (#91)
  * Implement chunking mechanism for loading synapses in dryrun mode (#88)
*Bug Fixes*
  * CoreConfig: write_report_count() should always create a new report.conf (#107)
  * Fix netstim_inhpoisson.mod for CoreNEURON direct mode (#94)
  * Fix memory usage reporting on MacOS (#105)
  * Fix call to `trim_memory` on non-GNU C libraries (#106)
  * Fix unit test: new morphology test file to fulfil MorphIO change (#104)
  * [BBPBGLIB-1027] Fix: Load Balance with multi-populations (#92)
  * CI fix for `python setup.py egg_info` error (#95)
  * Build recipe: remove shallow clone to meet the version requirement of latest setuptools (#90)
  * Fix bug with duplicate count of synapses (#87)
  * Fix docs (#84)
*Improvements*
  * [BBPBGLIB-1093] Move scientific tests from blueconfigs (#103)
  * Update documentation for new synapse estimate algorithm (#99)
  * Modernize the setup infractructure slightly. (#98)
  * [BBPBGLIB-1092] Add unit tests for CLI options (#86)
  * [BBPBGLIB-1097] Reorganization of unit/integration tests (#83)
  * Update build_neurodamus.sh with `--only-neuron` (#89)


Version 2.16.6
==============
**17 Nov 2023**

*Bug Fixes*
  * Use default dt value of NEURON in WholeCell load balancing (#81)
  * Fix conversion from sonata parameter to neurodamus internal key : amp_cv -> AmpCV (#79)
*Improvements*
  * CI and container improvements
  * Protect numpy.concatenate empty tuple in get_local_gids (#53)
  * [BBPP134-1022] Handling exceptions from NEURON during emodel loading (#80)


Version 2.16.5
==============
**1 Nov 2023**

*New Features*
  * [BBPBGLIB-1069] Dry-run node allocation suggestions (#64)
  * [BBPBGLIB-1067] Implement 'node_sets_file' resolution order (#55)
*Bug Fixes*
  * [BBPBGLIB-1076] Fix NGV offsetting with Sonata circuits (#69)
  * [BBPBGLIB-1055] Support "<NONE>" as nrnPath (#65)
*Improvements*
  * [BBPBGLIB-1044] Use libsonata to read the spikes (#70)
  * [HPCTM-1824] Introducing a temporary set for faster lookup in the src_target gids (#63)
  * [BBPBGLIB-556] Dry-run improvements, fixes with projections (#56, #60)
  * [REP-68] Add report dt to the logging (#59)
  * Remove ranks-cpus warning as can be inaccurate (#66)


Version 2.16.4
==============
**9 Oct 2023**

*New Features*
  * [BBPBGLIB-556] Full estimate of memory consumption (#32)
*Bug Fixes*
  * [BBPBGLIB-1042] GapJunctionManager: filter source target by population (#42)
  * [BBPBGLIB-1061] SONATA conf: Dont map to internal connectivity
*Improvements*
  * Modernize ALU (#48)
  * [HPCTM-1793] Add a Dockerfile for building Neurodamus


Version 2.16.3
==============
**21 Sep 2023**

*New Features*
  * Share GluSynapseHelper.hoc with public users (#47)
  * Read 'electrodes_file' field from libsonata (#23)
  * [BBPBGLIB-1060] Remove CoreConfig.mod and enable CoreNEURON execution via NEURON Python API (#41)


Version 2.16.2
==============
**1 Sep 2023**

*Bug fixes*
  * Use 0-based gid for reading GlioVascular sonata edges file
  * import h5py in the function call to filter numpy warnings
  * Propagate the log level correctly from the CLI option to Neurodamus class
  * Skip CORENEURON unit tests pending for a fix from NEURON (#38)


Version 2.16.1
==============
**25 Aug 2023**

*New Features*
  * [BBPBGLIB-1044] Sonata Replay
  * [BBPBGLIB-712] Estimate memory usage for synapse and connection
*Improvements*
  * Update CoreConfig.mod for latest CoreNEURON changes
  * [BBPBGLIB-1030] Reject .sonata extenson for nodes and edges file
  * Breaking enable_reports code into pieces
  * [BBPBGLIB-851]Warning on cao_CR syn variable if not the same as extracellular_calcium
  * Use libsonata API to read report secton keys in the sonata config file


Version 2.16.0
==============
**26 July 2023**

*New Features*
  * [BBPBGLIB-1036] Pure SONATA reader for gap junctions
  * [BBPBGLIB-984] Option to keep Cell axon during init

*Improvements*
  * [BBPBGLIB-1035] Drop Synapsetool. Migrate all synapses loading to libsonata (no syn2 support)


Version 2.15.3
===============
**14 July 2023**

*Improvements*
  * Replace sys.exit with h.quit to fix issue with MPI_Finalize


Version 2.15.2
===============
**13 July 2023**

*New Features*
  * [BBPBGLIB-1027] Enable load balance for Sonata config simulations
  * [NRN-152] MorphIO API: morphio_read
  * Support HDF5 morphology containers via MorphIO
  * hocify: file mode
  * [BBPBGLIB-711] Dry run for cells instantiation
*Improvements*
  * [BBPBGLIB-795] Added documentation for how to install/develop/use a custom neurodamus-py
  * Ncs with sonata
  * [NSETM-1948] Log warning on SonataError from libsonata.NodeSets materialization
  * Replace BlueConfig with SONATA config in ngv test


Version 2.15.1
===============
**13 June 2023**

*New Features*
  * [BBPBGLIB-706] Make all core mod files compatible with CoreNEURON/NMODL
*Improvements*
  * Docs for the open source repo
  * All `usecase3` circuit files now are contained in neurodamus-py
  * [HPCTM-1755] one morphio_wrapper.py in neurodamus
*Bug fixes*
  * Fixed unit tests due to changes in `common` MOD files


Version 2.15.0
===============
**11 May 2023**

*New Features*
  * [BBPBGLIB-1008] Unify/Drop core submodule
*Improvements*
  * [BBPBGLIB-988] Migrate to libsonata node reader
  * [BBPBGLIB-1009] Remove utility.mod and replace checkDirectory with python function
*Bug fixes*
  * [BBPBGLIB-1016] Read connection_overrides list insteamd of dict from libsonata
  * CI dont rely on common submodule, Clone. Small fixes


Version 2.14.0
===============
**6 Apr 2023**

*New Features*
  * [BBPBGLIB-983] Remove Bin reports
  * [BBPBGLIB-995] [BBPBGLIB-996] [BBPBGLIB-997] SONATA config: read "log_file" and report "file_name"
  * Add support for on-line LFP calculations
  * [BBPBGLIB-908] API to restrict features and populations
*Improvements*
  * [BBPBGLIB-908] Scientific tests - Multi-population
  * Control numpy subnormal flush to zero warnings
  * Add test for projections connectivity
  * [BBPBGLIB-908] Add spont-minis test
  * [BBPP40-291] Improve Sonata configurations for ngv simulations
*Bug fixes*
  * Force dtype during numpy.concatenate recarrays
  * [HPCTM-1687]: fix error of checking np.recarray None or empty


Version 2.13.2
===============
**1 Mar 2023**

*Bug fixes*
  * Updates on sonata parsing to adapt changes from libsonata
  * Don't handle SpikeLocation from Sonata conditions


Version 2.13.1
===============
**14 Feb 2023**

*Bug fixes*
  * Fix potential issues with freeing the NEURON event queues

Version 2.13.0
===============
**8 Feb 2023**

*New Features*
  * [BBPP40-275] Set endfeet R0pas based on `vasculature.h5`
  * [BBPBGLIB-748]: neuromodulation with coreneuron

*Improvements*
  * [BBPBGLIB-959] Clear bbss objects and SpontMini's random123 objects
  * [BBPBGLIB-899] Improved Synapse instantiation memory and time
  * Better warnings when synapses cannot be placed

*Bug fixes*
  * [BBPBGLIB-964] load additional cell properties to work when using Sonata nodesets
  * [BBPBGLIB-964] Fix replay with virtual populations during coreneuron restore
  * Fix CoreNeuron cleanup for re-running the same campaign with bbp-worfklow


Version 2.12.11
===============
**20 Dec 2022**

*Improvements*
  * [BBPBGLIB-954] Don't create hoc obj for nodeset targets
  * [BBPBGLIB-937] Reduce memory consumption in Connection class
  * [BBPBGLIB-954] Avoid flattening nodesets

*Bug fixes*
  * Fix SHM File Transfer safety checks on large simulations
  * Fix CI as tox got updated
  * [BBPBGLIB-962] Fix and workaround for ngv test


Version 2.12.10
===============
**25 Nov 2022**

*New Features*
  * [BBPBGLIB-957] Added RSS printing in multiple places

*Improvements*
  * Avoid writing --report-conf to the sim.conf if reports are disabled
  * Load balancing improvements for multiple populations

*Bug fixes*
  * Clear the model after calling savestate()


Version 2.12.9
==============
**09 Nov 2022**

*New Features*
  * [BBPBGLIB-938] Clean Random123 objects in synapses
  * [BBPBGLIB-950] Call malloc_trim to return free pages back to the OS when clearing up the model
  * Shrink NEURON ArrayPools and call Python garbage collect when clearing up the model


Version 2.12.8
==============
**07 Nov 2022**

*New Features*
  * [NRN-111] Add support for incoming Datum changes in 9.0.0


Version 2.12.7
==============
**04 Nov 2022**

*Improvements*
  * [BBPP134-14] Support node files with '.sonata' extension

*Bug fixes*
  * [BBPBGLIB-945] Properly display the exception messages when the simulation crashes


Version 2.12.6
==============
**21 Oct 2022**

*New Features*
  * Enable model stats printing in CoreNEURON
  * Read new sonata keys from libsonata

    * [BBPBGLIB-885] neuromodulation_dtc and neuromodulation_strength in connection_overrides
    * [BBPBGLIB-915] deprecate minis_single_vesicle key from conditions
    * [BBPBGLIB-913] deprecate forward_skip key
    * [BBPBGLIB-920] add keys in run for additional seedings: stimulus_seed, ionchannel_seed, minis_seed, synapse_seed
    * [BBPBGLIB-921] add series_resistance key in seclamp
    * [BBPBGLIB-919] parse modifications

*Improvements*
  * [BBPBGLIB-934] LoadBalance refactoring for multiple circuits
  * Enable reading sonata circuit config with empty edge

*Bug fixes*
  * [BBPBGLIB-933] Fix coreneuron multi-cycle model building for multiple circuits
  * Fix for conflict with SHM File Transfer and --keep-build


Version 2.12.5
==============
**07 Oct 2022**

*Improvements*
  * Add a GapJunction unit test to showcase how it could be tested
  * Improved Cell Managers API with `get_cell` (python cell) and `get_cellref` (hoc cellref)
  * Make Load balancer use the TargetManager Python class
  * [HPCTM-1600] Set SHM File Transfer by default + Improve model memory consumption estimates


Version 2.12.4
==============
**23 Sep 2022**

*Improvements*
  * Add test for point to detailed neuron connectivity and vice versa
  * [BBPBGLIB-904] Pytests refactoring and coverage + Have mini simulations run directly under pytest
  * Add zero amplitude at start of new noise stimuli to allow stacking over time

*Bug fixes*
  * [BBPBGLIB-888] Save populations_offset.dat in output directory to resolve issue in restore
  * coreneuron restore: link populations_offset.dat only in rank0 and hold the other ranks
  * [HPCTM-1584] Fix deletion of SHM coredat files when '--enable-shm' is not set



Version 2.12.3
==============
**29 Aug 2022**

*New Features*
  * Bump submodule past hpc/sim/neurodamus-core!12

*Bug fixes*
  * [BBPBGLIB-887] Protect synapse reading: n_rrp_vesicles is required for SONATA circuits
  * [REP-80] Call hoc in report initialization for synapse reports in CoreNEURON
  * [BBPBGLIB-901] Fix corenrn input dir w sonata


Version 2.12.2
==============
**17 Aug 2022**

*Improvements*
  * CoreNEURON: Skip report initialization after creating report.conf in save/restore
  * Improve report initialization time with CoreNEURON

*Bug fixes*
  * Fix for race-condition when reading sim.conf
  * [BBPBGLIB-894] Fix spike train handling


Version 2.12.1
==============
**28 Jul 2022**

*New Features*
  * Add support for SHM file transfer in CoreNEURON


Version 2.12.0
==============
**15 Jul 2022**

*New Features*
  * [BBPBGLIB-816] Complete Baseline support for SONATA configuration
  * New CLI options for save-restore, run mode and dump cell state
  * Documentation for running a SONATA simulation

*Improvements*
  * Avoid creating out.dat when running simulations with SONATA config file
  * Read sonata config parameters from libsonata parser
  * Replace calculation of U scale_factors calculation by a single function

*Bug fixes*
  * Resolve nodes and edges paths according to circuit_config.json location
  * [BBPBGLIB-856] Fixes for hoc targets w offset and nodes extra properties
  * Expect same behavior when connection delay is not present and when is 0


Version 2.11.3
==============
**25 May 2022**

*New Features*
 * Load extended cell properties from SONATA [BBPBGLIB-806]

*Improvements*
 * Core mods compatibility across Nrn8.0..9.x
 * Added synapses test [BBPBGLIB-826]


Version 2.11.2
==============
**12 May 2022**

*Improvements*
 * Improved target intersection for nodesets addressed in BBPBGLIB-823


Version 2.11.1
==============
**2 May 2022**

*Improvements*
 * Use libsonata API parser for sonata config


Version 2.11.0
==============
**28 Apr 2022**

*Improvements*
 * No eager caching of synaptic parameters
 * Sonata nodesets to be able to cross multiple populations
 * Adding test with patched delays after ModOverride


Version 2.10.3
==============
**30 Mar 2022**

*New Features*
 * Support sonata configurations for ngv

*Improvements*
 * BBPBGLIB-805 Allow independent scaling fields
 * Configurable scaling between I_thresh and invRin

*Bug fixes*
 * Summation report fixes


Version 2.10.2
==============
**4 Mar 2022**

*New Features*
 * Suport multi-population compartment report
 * Suport sonata configuration and sonata NodeSetTarget
 * Implement RelativeOrnsteinUhlenbeck stimulus
 * New-gen stimuli injected as Current or Conductance
 * Implement StochasticConductance stimulus
 * Implement ConductanceSource(SignalSource) using an SEClamp
 * Implement Ornstein-Uhlenbeck process signal generation

*Improvements*
 * Control display of unhandled exceptions

*Bug fixes*
 * Store reference to rs-driving signal (fix CELLS-79)


Version 2.8.0
=============
**October 21, 2021**

*New Features*
 * Addition of PointNeuron Engine for supporting Point neuron simulations
 * Reading extra parameters for GluSynapses ffrom SONATA edges file
 * Allow ConfigureAllSections modifications

*Improvements*
 * Handle reports for multiple populations adapting new features of libsonata-report
 * Add warning when synapse targets invalid point
 * Refactoring Targets for Nodeset compat
 * Differenciate between cell target and section soma
 * NGV endpoint id: Fallback to global synapse id

*Bug fixes*
 * Fix stims for new target API. Make API compat old usage\
 * Fix regression: pass nodesets file as BC TargetFile
 * Offset fixes for replay with multiple circuits
 * Fix bug with SynConfigure and multipopulation


Version 2.7.0
=============
**July 7, 2021**

*New Features*
 * Initial Framework for Python modifications + TTX
 * Implement python helpers for common stim
 * V6 cells provide API (local_to_global_coord_mapping) to move cell points to absolute position

*Improvements*
 * BBPBGLIB-675 Neurodamus to re-launch using special
 * MorphIO lazy loading to avoid issue #316
 * Validation of report configuration
 * [NGVDISS-89] glia_2013 superseded by mcd

*Bug fixes*
 * local_nodes to handle case of 0 count


Version 2.6.0
=============
**May 11, 2021**

*New Features*
 * NGV

   * [NGVDISS-1] Astrocyte Endoplasmic Reticulum
   * [NGVDISS-73] Astrocyte perimeters & cross-sectional areas
   * [NGVDISS-74] Endfeet handling
   * [NGVDISS-229] Spec update for neuroglial synapse parameters

 * SONATA reports node_ids offsetting
 * post-stdinit callback support in Node

*Improvements*
 * Checks for non-negative config params
 * Don't raise exception if replay file is empty


Version 2.5.3
=============

*Fixes*
 * Attach source netconns in additional populations and CoreNeuron [critical c/53194]
 * Type field in StimulusInject to select the proper cell manager


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
