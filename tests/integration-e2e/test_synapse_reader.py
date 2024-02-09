import numpy as np
import numpy.testing as npt
from neurodamus.gap_junction import GapJunctionSynapseReader
from pathlib import Path

SIM_DIR = Path(__file__).parent.parent.absolute() / "simulations"


def test_gapjunction_sonata_reader():
    sonata_file = str(SIM_DIR / "mini_thalamus_sonata/gapjunction/edges.h5")
    sonata_reader = GapJunctionSynapseReader.create(sonata_file)
    syn_params_sonata = sonata_reader._load_synapse_parameters(1)
    ref_junction_id_pre = np.array([10257., 43930., 226003., 298841., 324744.,
                                    1094745., 1167632., 1172523., 1260104.])
    ref_junction_id_post = np.array([14., 52., 71., 76., 78., 84., 89., 90., 93.])
    ref_weight = np.array([0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2])
    npt.assert_allclose(syn_params_sonata.D, ref_junction_id_pre)
    npt.assert_allclose(syn_params_sonata.F, ref_junction_id_post)
    npt.assert_allclose(syn_params_sonata.weight, ref_weight)
