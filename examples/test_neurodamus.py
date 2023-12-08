#!/usr/bin/env python
"""
An example on how node can be used to mimick neurodamus behavior
"""
from __future__ import print_function
from neurodamus import Node, Neurodamus
from neurodamus.core import NeurodamusCore as Nd
from neurodamus.utils.logging import setup_logging
import sys
import logging
from os import path as Path

RECIPE_FILE = Path.expanduser("~/dev/TestData/build/circuitBuilding_1000neurons/BlueConfig")
DEFAULT_LOG_LEVEL = 2
TRACE_LOG_LEVEL = 5


def test_run():
    """A Neurodamus typical run can be quickly setup and run using the Neurodamus class
    """
    Neurodamus(RECIPE_FILE).run()


def test_node_run(trace=False):
    """Node is more of a low-level class, where all initialization steps are manual
    """
    setup_logging(DEFAULT_LOG_LEVEL)
    if trace:
        # Some additional logging is available at special level 5
        print("TRACE mode is ON")
        logging.root.setLevel(TRACE_LOG_LEVEL)

    node = Node(RECIPE_FILE)
    node.load_targets()
    node.compute_load_balance()
    node.create_cells()
    node.execute_neuron_configures()

    logging.info("Create connections")
    node.create_synapses()
    node.create_gap_junctions()

    logging.info("Enable Stimulus")
    node.enable_stimulus()

    logging.info("Enable Modifications")
    node.enable_modifications()

    if trace:
        logging.info("Dumping config")
        Nd.stdinit()
        node.dump_circuit_config("")

    logging.info("Enable Reports")
    node.enable_reports()

    logging.info("Run")
    node.run(True)

    logging.info("Simulation finished. Gather spikes then clean up.")
    node.spike2file("out.dat")
    node.cleanup()


if __name__ == "__main__":
    test_node_run("trace" in sys.argv)
