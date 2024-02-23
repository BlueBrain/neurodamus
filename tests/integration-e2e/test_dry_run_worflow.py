from neurodamus.utils.memory import import_allocation_stats, export_allocation_stats


def convert_to_standard_types(obj):
    """Converts an object containing defaultdicts of Vectors to standard Python types."""
    result = {}
    for node, vectors in obj.items():
        result[node] = {key: list(vector) for key, vector in vectors.items()}
    return result


def test_dry_run_workflow(USECASE3):
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
    assert 80.0 <= nd._dry_run_stats.base_memory <= 120.0
    expected_items = {
        'L4_PC-dSTUT': 2,
        'L4_MC-dSTUT': 1,
        'L4_MC-dNAC': 1,
        'L5_PC-dSTUT': 1
    }
    assert nd._dry_run_stats.metype_counts == expected_items
    assert nd._dry_run_stats.suggest_nodes(0.3) > 0

    # Test that the allocation works and can be saved and loaded
    rank_allocation, _ = nd._dry_run_stats.distribute_cells(2)
    export_allocation_stats(rank_allocation, USECASE3 / "allocation.pkl.gz")
    rank_allocation = import_allocation_stats(USECASE3 / "allocation.pkl.gz")
    rank_allocation_standard = convert_to_standard_types(rank_allocation)

    expected_items = {
        'NodeA': {0: [1, 2, 3]},
        'NodeB': {1: [1, 2]}
    }

    assert rank_allocation_standard == expected_items

    # Test that the allocation works and can be saved and loaded
    # and generate allocation.pkl.gz for 1 rank
    rank_allocation, _ = nd._dry_run_stats.distribute_cells(1)
    export_allocation_stats(rank_allocation, USECASE3 / "allocation.pkl.gz")
    rank_allocation = import_allocation_stats(USECASE3 / "allocation.pkl.gz")
    rank_allocation_standard = convert_to_standard_types(rank_allocation)

    expected_items = {
        'NodeA': {0: [1, 2, 3]},
        'NodeB': {0: [1, 2]}
    }

    assert rank_allocation_standard == expected_items


def test_memory_load_balance_workflow(USECASE3):
    """
    Test that the memory load balance works
    """

    from neurodamus import Neurodamus
    nd = Neurodamus(
        str(USECASE3 / "simulation_sonata.json"),
        lb_mode="Memory",
    )

    nd.run()
