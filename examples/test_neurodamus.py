from __future__ import print_function
from neurodamus import Node
from neurodamus.core import NeuronDamus as Nd
from neurodamus.utils import setup_logging
import logging

DEBUG = True
"""WIll dump extensive logging information"""


def test_node_run():
    setup_logging(2)
    if DEBUG:
        logging.root.setLevel(5)

    node = Node("/home/leite/dev/TestData/build/circuitBuilding_1000neurons/BlueConfig")
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

    if DEBUG:
        logging.info("Dumping config")
        Nd.stdinit()
        node.dump_circuit_config("")

    logging.info("Enable Reports")
    node.enable_reports()

    logging.info("Run")
    node.prun(True)

    logging.info("Simulation finished. Gather spikes then clean up.")
    node.spike2file("out.dat")
    node.cleanup()


if __name__ == "__main__":
    test_node_run()
