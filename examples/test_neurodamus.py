from neurodamus import Node
import logging


def test_node_run():
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

    logging.info("Simulation finished. Gather spikes then clean up.")
    node.spike2file("out.dat")
    node.cleanup()


if __name__ == "__main__":
    test_node_run()
