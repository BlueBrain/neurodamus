from mpi4py import MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
print("I am node {}".format(rank))

from neurodamus.node import Node
node = Node("/home/leite/dev/TestData/build/circuitBuilding_1000neurons/BlueConfig")
node.loadTargets()
node.computeLB()
node.createCells()
node.executeNeuronConfigures()

print("Create connections")
node.createSynapses()
node.createGapJunctions()

print("Enable Stimulus")
node.enableStimulus()

print("Enable Modifications")
node.enableModifications()

print("Enable Reports")
node.enableReports()

print("Run")
node.prun(True)

print("\nsimulation finished. Gather spikes then clean up.")
node.spike2file("out.dat")
node.cleanup()
