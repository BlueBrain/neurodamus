=============
Neurodamus-py
=============

Neurodamus is a BBP Simulation Control application for Neuron.

The Python implementation offers a comprehensive Python API for fine tunning of the simulation, initially defined by a BlueConfig file.


Description
===========

Neurodamus is the BBP in-house developed application for setting up large-scale neuronal simulations.
It has traditionally been implemented as a set of extensions to Neuron, in the form of .hoc and .mod files.
The parameters of the simulation are loaded from a configuration file, by default BlueConfig.

To address several limitations of the Hoc implementation, including development effort, the
high-level layers of Neurodamus have been reimplemented in Python.
Such implementation effectively makes available to the user a Python module with a comprehensive
API, suitable to fine control simulation aspects, as well as inspect and eventually adapt the
simulations as intended.

Main classes
------------

At the top level the user may instantiate a `Neurodamus<neurodamus.Neurodamus>` object, which will instantiate the whole simulation according to the provided BlueConfig, but stop before launching it.
**Note**: For finer level of control of the initialization, the user may opt for instantiating a `Node<neurodamus.Node>` object, where he is responsible for every phase.
*This is not recommended since the initialization phases cannot be arbitrarily interchanged.*

Once the simulation has been initialized, `Node<neurodamus.Node>` provides several data structures which can be inspected and manipulated, namely:

* `synapse_manager`: an instance of `SynapseRuleManager<neurodamus.connection_manager.SynapseRuleManager>`
* `gj_manager`: an instance of `GapJunctionManager<neurodamus.connection_manager.GapJunctionManager>`
* `cells`: a list of cell instances (`METype<neurodamus.metype.METype>`)
