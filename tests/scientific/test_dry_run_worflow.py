import os
import pytest
from pathlib import Path
from collections import Counter

USECASE3 = Path(__file__).parent.absolute() / "usecase3"


@pytest.mark.skipif(
    not os.environ.get("NEURODAMUS_NEOCORTEX_ROOT"),
    reason="Test requires loading a neocortex model to run"
)
def test_dry_run_workflow():
    """
    Test that the dry run mode works
    """

    from neurodamus import Neurodamus
    nd = Neurodamus(
        str(USECASE3 / "simulation_sonata.json"),
        dry_run=True
    )

    nd.run()

    assert 20.0 <= nd._dry_run_stats.cell_memory_total <= 30.0
    assert 0.0 <= nd._dry_run_stats.synapse_memory_total <= 1.0
    assert 90.0 <= nd._dry_run_stats.base_memory <= 120.0
    expected_items = Counter([('L4_PC-dSTUT', 2),
                              ('L4_MC-dSTUT', 1),
                              ('L4_MC-dNAC', 1),
                              ('L5_PC-dSTUT', 1)])
    assert set(nd._dry_run_stats.metype_counts.items()) == set(expected_items)
    assert nd._dry_run_stats.suggest_nodes(0.3) > 0