from neurodamus.core import Cell
from neurodamus.core import CurrentSource
from neurodamus.core import Neuron
from neurodamus.core import mechanisms
from neurodamus.core.stimuli import RealElectrode, ConstantEfield, PointSourceElectrode
from neuron import h
import numpy as np

import pdb; pdb.set_trace()


# Change v_init globally
# Alternatively v_init can be configured per simulation in run_sim(**kw)
Neuron.Simulation.v_init = -70


def test_tut1(offset, quick=True):
    
    
    c = Cell(0,'/gpfs/bbp.cscs.ch/project/proj68/home/arnaudon/mm_new_axon/selected_morphologies/C080501B2.asc')
    hh = Cell.Mechanisms.HH(gkbar=0.01, gnabar=0.2, el=-70)
    for sec in c.all:
        hh.apply(sec)

        

    stim = ConstantEfield('Extracellular', 100, 'Pulse',
                          100, [.001], None, [100], None, None, 0.025, 0,0,np.array([offset,0,0]),'x',[0,0,0])
    
    for sec in c.all:
        for seg in sec:
            stim.attach_to(sec, seg.x)

        
    sim = Neuron.run_sim(200, c.soma)
    
    return sim

if __name__ == "__main__":

    r1 = test_tut1(1, True)