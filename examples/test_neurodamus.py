from neurodamus.node import Node
from neurodamus.utils import setup_logging
import logging


def test_node_run():
    setup_logging(2)
    node = Node("/home/leite/dev/TestData/build/circuitBuilding_1000neurons/BlueConfig")
    node.loadTargets()
    node.computeLB()
    node.createCells()
    node.executeNeuronConfigures()

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


if __name__ == "__main__":
    test_node_run()
