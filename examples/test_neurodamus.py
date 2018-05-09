from mpi4py import MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
print("I am node {}".format(rank))

from neurodamus import node
n = node.Node("/home/leite/dev/TestData/build/circuitBuilding_1000neurons/BlueConfig")
n.loadTargets()
n.computeLB()

