"""
Neurodamus execution main class
"""
from __future__ import absolute_import
from .node import Node
from .utils import setup_logging


def init(recipe_file):
    from . import GlobalConfig
    setup_logging(GlobalConfig.verbosity)
    node = Node(recipe_file)
    node.loadTargets()
    node.computeLB()
    node.createCells()
    node.executeNeuronConfigures()

    node.log("Create connections")
    node.createSynapses()
    node.createGapJunctions()

    node.log("Enable Stimulus")
    node.enableStimulus()

    node.log("Enable Modifications")
    node.enableModifications()

    node.log("Enable Reports")
    node.enableReports()

    node.log("Run")
    node.prun(True)

    node.log("\nsimulation finished. Gather spikes then clean up.")
    node.spike2file("out.dat")
    node.cleanup()
