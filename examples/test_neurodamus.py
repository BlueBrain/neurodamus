from neurodamus.node import Node
node = Node("/home/leite/dev/TestData/build/circuitBuilding_1000neurons/BlueConfig")
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
