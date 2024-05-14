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


def test_syn_read_counts():
    from neurodamus.io.synapse_reader import SonataReader
    sonata_file = str(SIM_DIR / "usecase3/local_edges_A.h5")
    reader = SonataReader(sonata_file, "NodeA__NodeA__chemical")

    full_counts = reader.get_counts(np.arange(3, dtype=int))
    assert len(full_counts) == 3 # dataset has only two but the count=0 must be set
    assert full_counts[0] == 2
    assert full_counts[1] == 2
    assert full_counts[2] == 0

    conn_counts = reader.get_conn_counts([0])
    assert len(conn_counts) == 1
    assert conn_counts[0] == {1: 2}

    # Will reuse cache
    conn_counts = reader.get_conn_counts([0, 1])
    assert len(conn_counts) == 2
    assert conn_counts[0] == {1: 2}  # [1->0] 2 synapses
    assert conn_counts[1] == {0: 2}  # [0->1] 2 synapses

    # Fully from cache
    conn_counts = reader.get_conn_counts([1])
    assert len(conn_counts) == 1
    assert conn_counts[1] == {0: 2}  # [0->1] 2 synapses
