from __future__ import print_function
from neurodamus import Node, Neurodamus
from neurodamus.core import NeuronDamus as Nd
from neurodamus.utils import setup_logging
import sys
import logging
from os import path as osp

RECIPE_FILE = osp.expanduser("~/dev/TestData/build/circuitBuilding_1000neurons/BlueConfig")


def test_run():
    """A Neurodamus typical run can be quickly setup and run using the Neurodamus class
    """
    Neurodamus(RECIPE_FILE).run()


def test_node_run(trace=False):
    """Node is more of a low-level class, where all initialization steps are manual
    """
    setup_logging(2)
    if trace:
        # Some additional logging is available at special level 5
        print("TRACE mode is ON")
        logging.root.setLevel(5)

    node = Node(RECIPE_FILE)
    node.load_targets()
    node.compute_loadbal()
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
