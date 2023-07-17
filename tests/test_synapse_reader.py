import numpy as np
import numpy.testing as npt
import os
import pytest
from neurodamus.gap_junction import GapJunctionSynapseReader
from pathlib import Path


pytestmark = [
    pytest.mark.forked,
    pytest.mark.skipif(
        not os.environ.get("NEURODAMUS_NEOCORTEX_ROOT"),
        reason="Test requires loading a neocortex model to run"
    )
]


def test_gapjunction_synreaderNRN():
    nrn_file = "/gpfs/bbp.cscs.ch/project/proj12/jenkins/cellular/circuit-scx-v5-gapjunctions/gap_junctions/nrn_gj.h5" # noqa
    nrn_reader = GapJunctionSynapseReader.create(nrn_file, 1)
    syn_params_nrn = nrn_reader._load_synapse_parameters(100124)
    # check reading of sgid, junction_id_pre and junction_id_post
    ref_sgids = np.array([94669., 94723., 95634., 95823., 96581.,
                          97338., 97455., 98139., 98432., 100725.,
                          101360., 101506., 101696., 101696., 191567.])
    ref_junction_id_pre = np.array([735., 736., 29., 36., 51.,
                                    77., 744., 134., 148., 286.,
                                    322., 337., 355., 356., 681.])
    ref_junction_id_post = np.array([1251., 1259., 617., 1354., 1002.,
                                     1756., 1027., 924., 709., 624.,
                                     1050., 521., 592., 593., 590.])
    npt.assert_allclose(syn_params_nrn.sgid, ref_sgids)
    npt.assert_allclose(syn_params_nrn.D, ref_junction_id_pre)
    npt.assert_allclose(syn_params_nrn.F, ref_junction_id_post)


def test_gapjunction_sonata_reader():
    SIM_DIR = Path(__file__).parent.absolute() / "simulations"
    sonata_file = str(SIM_DIR / "mini_thalamus_sonata/gapjunction/edges.h5")
    sonata_reader = GapJunctionSynapseReader.create(sonata_file, 1)
    syn_params_sonata = sonata_reader._load_synapse_parameters(1)
    ref_junction_id_pre = np.array([10257., 43930., 226003., 298841., 324744.,
                                    1094745., 1167632., 1172523., 1260104.])
    ref_junction_id_post = np.array([14., 52., 71., 76., 78., 84., 89., 90., 93.])
    ref_weight = np.array([0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2])
    npt.assert_allclose(syn_params_sonata.D, ref_junction_id_pre)
    npt.assert_allclose(syn_params_sonata.F, ref_junction_id_post)
    npt.assert_allclose(syn_params_sonata.weight, ref_weight)
