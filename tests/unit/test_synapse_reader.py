import numpy as np
import numpy.testing as npt
from pathlib import Path
from unittest.mock import Mock

SIM_DIR = Path(__file__).parent.parent.absolute() / "simulations"


def test_gapjunction_sonata_reader():
    from neurodamus.gap_junction import GapJunctionSynapseReader
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

    full_counts = reader.get_counts(np.array([1, 2, 3], dtype=int))
    assert len(full_counts) == 3  # dataset has only two but the count=0 must be set
    assert full_counts[1] == 2
    assert full_counts[2] == 2
    assert full_counts[3] == 0

    conn_counts = reader.get_conn_counts([1])
    assert len(conn_counts) == 1
    assert conn_counts[1] == {2: 2}

    # Will reuse cache
    conn_counts = reader.get_conn_counts([1, 2])
    assert len(conn_counts) == 2
    assert conn_counts[1] == {2: 2}  # [1->0] 2 synapses
    assert conn_counts[2] == {1: 2}  # [0->1] 2 synapses

    # Fully from cache
    conn_counts = reader.get_conn_counts([2])
    assert len(conn_counts) == 1
    assert conn_counts[2] == {1: 2}  # [0->1] 2 synapses


def test_conn_manager_syn_stats():
    """Test _get_conn_stats in isolation using a mocked instance of SynapseRuleManager
    """
    from neurodamus.connection_manager import SynapseRuleManager
    from neurodamus.core.nodeset import NodeSet
    from neurodamus.io.synapse_reader import SonataReader
    from neurodamus.target_manager import NodesetTarget

    sonata_file = str(SIM_DIR / "usecase3/local_edges_A.h5")
    reader = SonataReader(sonata_file, "NodeA__NodeA__chemical")

    manager_mock = Mock(SynapseRuleManager)
    manager_mock._synapse_reader = reader
    manager_mock._cell_manager = Mock()
    manager_mock._cell_manager.population_name = "pop-A"
    manager_mock._dry_run_stats = Mock()
    manager_mock._dry_run_stats.metype_gids = {"pop-A": {"metype-x": [0, 1], "metype-y": [2]}}
    manager_mock._dry_run_conns = set()  # cache obj
    manager_mock._dry_run_stats.average_syns_per_cell = {}  # for output

    target_ns = NodesetTarget("nodeset1", [NodeSet([0, 1, 2, 3])], [NodeSet([0, 1])])
    total_synapses = SynapseRuleManager._get_conn_stats(manager_mock, target_ns)
    assert total_synapses == 2
    assert manager_mock._dry_run_stats.average_syns_per_cell["metype-x"] == 1

    target_ns = NodesetTarget("nodeset1", [NodeSet([0, 1, 2, 3])], [NodeSet([0, 1, 2, 3])])
    total_synapses = SynapseRuleManager._get_conn_stats(manager_mock, target_ns)
    assert total_synapses == 4
    assert manager_mock._dry_run_stats.average_syns_per_cell["metype-x"] == 1
    assert manager_mock._dry_run_stats.average_syns_per_cell["metype-y"] == 2
