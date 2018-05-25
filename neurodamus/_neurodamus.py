"""
Neurodamus execution main class
"""
from __future__ import absolute_import
from .node import Node
from .utils import logging, setup_logging
from .core.configuration import GlobalConfig


def init_node(recipe_file):
    setup_logging(GlobalConfig.verbosity)
    node = Node(recipe_file)
    node.loadTargets()
    node.computeLB()
    node.createCells()
    node.executeNeuronConfigures()
    return node


def run(recipe_file):
    node = init_node(recipe_file)
    logging.info("Create connections")
    node.createSynapses()
    node.createGapJunctions()

    logging.info("Enable Stimulus")
    node.enableStimulus()

    logging.info("Enable Modifications")
    node.enableModifications()

    logging.info("Enable Reports")
    node.enableReports()

    logging.info("Run")
    node.prun(True)

    logging.info("\nsimulation finished. Gather spikes then clean up.")
    node.spike2file("out.dat")
    node.cleanup()
