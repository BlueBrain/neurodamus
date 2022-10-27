from neurodamus.core import Cell
from neurodamus.core import CurrentSource
from neurodamus.core import Neuron
from neurodamus.core import mechanisms
from neurodamus import Cell_V6
from neurodamus.core.stimuli import RealElectrode, ConstantEfield, PointSourceElectrode
from neuron import h
import numpy as np

import pdb; pdb.set_trace()

class CircuitConfig():
    _name = None
    Engine = None
    CircuitPath = None
    nrnPath = None
    CellLibraryFile = None
    MEComboInfoFile = None
    METypePath = '/gpfs/bbp.cscs.ch/project/proj45/scratch/S1full/hocAxons/'
    #METypePath = '/gpfs/bbp.cscs.ch/project/proj45/scratch/S1full/hocAxons/cADpyr_L5TPC.hoc'
    MorphologyType = None
    MorphologyPath = '/gpfs/bbp.cscs.ch/project/proj68/home/arnaudon/mm_new_axon/selected_morphologies/C080501B2.asc'
    CircuitTarget = None
    PopulationID = 0
    
class MEInfo():
    morph_name = 'C080501B2'
    morph_extension = 'asc'
    threshold_current = 0
    holding_current = 0
    exc_mini_frequency = 0
    inh_mini_frequency = 0
    local_to_global_matrix = np.eye(3)
    emodel = 'cADpyr_L5TPC'
    
if __name__=='__main__':
    
    circ = CircuitConfig()
    inf = MEInfo()
    c = Cell_V6(0,inf,circ)