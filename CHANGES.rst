==========
Change Log
==========


Version 0.6.0
=============

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

*New Features*
  * Support of SynapseTool for Syn2/SONATA

*fixes*
  * GapJunctions
  * Progressbar for streams


Version 0.3.0
=============

*New Features*
  * Synapse Replay and Projections

*Improvements*
  * connection_configure implemented in a fast hoc routine
  * Pep8


Version 0.2.2
=============

*New Features*
  * Added init.py
  * V6 circuit loading
  * V6 circuit stim apply

*Improvements*
  * Sync Hoc files with latest neurodamus master
  * Better output for multi-cpu runs


Version 0.2.1
=============

*New Features*
  * | Largely extending Python API
    | - ConnectionManager
    | - GapJuntionsManager
    | - METype
    | - API to Enable/Disable connections
    | - Etc

*Improvements*
  * Replays using a new OrderedMap structure
  * Cleaned and Refactored: Creation of .core subpackage
  * Refactoring CellDistributor
  * Remove mpi4y dependency


Version 0.1.0
=============

*New Features*
  * Initial version of Neurodamus Python
  * Node.hoc API 100% in Python
  * | High-Level Neuron implementation featuring:
    | - Neuron Bridge
    | - Cell
    | - Stimuli
    | - Examples on how to implemnt Neuron full tutorials in a few lines
