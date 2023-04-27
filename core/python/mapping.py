from neuron import h

pc = h.ParallelContext()
nhost = int(pc.nhost())
rank = int(pc.id())

def getNodeID(sectionID, nSeg):
    '''
    Since hoc has no interface to access section node info (node_index),
    provide a python interface.
    '''
    sec = h.cas()

    for seg in sec:
        h.secvec.append( sectionID )
        h.segvec.append( seg.node_index() )
        nSeg += 1

    return nSeg
