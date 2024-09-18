from pathlib import Path
from neurodamus.utils.memory import import_allocation_stats, export_allocation_stats
from neurodamus.utils.memory import export_metype_memory_usage
from test_multicycle_runs import _create_tmpconfig_coreneuron
from neurodamus.core.configuration import GlobalConfig, LogLevel

SIM_DIR = Path(__file__).parent.parent.absolute() / "simulations"


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

    # Make sure no old cell_memory_usage is used
    Path(("cell_memory_usage.json")).unlink(missing_ok=True)

    from neurodamus import Neurodamus
    GlobalConfig.verbosity = LogLevel.DEBUG
    nd = Neurodamus(
        str(USECASE3 / "simulation_sonata.json"),
        dry_run=True,
        num_target_ranks=2
    )

    nd.run()

    assert 20.0 <= nd._dry_run_stats.cell_memory_total <= 30.0
    assert 0.0 <= nd._dry_run_stats.synapse_memory_total <= 1.0
    assert 70.0 <= nd._dry_run_stats.base_memory <= 120.0
    expected_items = {
        'L4_PC-dSTUT': 2,
        'L4_MC-dSTUT': 1,
        'L4_MC-dNAC': 1,
        'L5_PC-dSTUT': 1
    }
    assert nd._dry_run_stats.metype_counts == expected_items
    assert nd._dry_run_stats.suggest_nodes(0.3) > 0

    # Test that the allocation works and can be saved and loaded
    rank_alloc, _, cell_mem_use = nd._dry_run_stats.distribute_cells_with_validation(2, 1, None)
    export_allocation_stats(rank_alloc,
                            USECASE3 / "allocation", 2, 1)
    export_metype_memory_usage(cell_mem_use, USECASE3 / "memory_per_metype.json")

    rank_alloc = import_allocation_stats(USECASE3 / "allocation_r2_c1.pkl.gz", 0)
    rank_allocation_standard = convert_to_standard_types(rank_alloc)

    expected_items = {
        'NodeA': {(0, 0): [1]},
        'NodeB': {(0, 0): [1]}
    }

    assert rank_allocation_standard == expected_items

    # Test that the allocation works and can be saved and loaded
    # and generate allocation file for 1 rank
    rank_alloc, _, cell_mem_use = nd._dry_run_stats.distribute_cells_with_validation(1, 1, None)
    export_metype_memory_usage(cell_mem_use, USECASE3 / "memory_per_metype.json")
    rank_allocation_standard = convert_to_standard_types(rank_alloc)

    expected_items = {
        'NodeA': {(0, 0): [1, 2, 3]},
        'NodeB': {(0, 0): [1, 2]}
    }

    assert rank_allocation_standard == expected_items


def test_dry_run_workflow_multi():
    """
    Test that the dry run mode works in multicycle mode
    """

    # Make sure no old cell_memory_usage is used
    Path(("cell_memory_usage.json")).unlink(missing_ok=True)

    from neurodamus import Neurodamus

    config_file = str(SIM_DIR / "v5_sonata" / "simulation_config.json")
    output_dir = str(SIM_DIR / "v5_sonata" / "output_coreneuron")
    tmp_file = _create_tmpconfig_coreneuron(config_file)
    GlobalConfig.verbosity = LogLevel.DEBUG

    nd = Neurodamus(tmp_file.name,
                    output_path=output_dir,
                    modelbuilding_steps=3,
                    dry_run=True)
    nd.run()

    rank_allocation, _, cell_memory_usage = nd._dry_run_stats.distribute_cells_with_validation(2)
    export_allocation_stats(rank_allocation,
                            SIM_DIR / "allocation", 2, 1)
    export_metype_memory_usage(cell_memory_usage, SIM_DIR / "memory_per_metype.json")
    rank_allocation = import_allocation_stats(SIM_DIR / "allocation_r2_c1.pkl.gz", 0, True)
    rank_allocation_standard = convert_to_standard_types(rank_allocation)

    expected_items = {
        'default': {
            (0, 0): [
                62798, 63257, 64164, 65916, 66069, 66141, 66872, 68224,
                68533, 68942, 69840, 64234, 69878, 67078
                ]
            }
        }

    assert rank_allocation_standard == expected_items
