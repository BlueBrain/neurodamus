from pathlib import Path

USECASE3 = Path(__file__).parent.absolute() / "usecase3"


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
    assert 100.0 <= nd._dry_run_stats.base_memory <= 120.0
