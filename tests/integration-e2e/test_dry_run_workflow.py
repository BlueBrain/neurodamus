from pathlib import Path
import numpy as np
from neurodamus.utils.memory import import_allocation_stats, export_allocation_stats
from test_multicycle_runs import _create_tmpconfig_coreneuron
from neurodamus.core.configuration import GlobalConfig, LogLevel

SIM_DIR = Path(__file__).parent.parent.absolute() / "simulations"


def convert_to_standard_types(obj):
    """Converts an object containing defaultdicts or dictionaries with NumPy arrays to standard
    Python types."""
    result = {}
    for node, vectors in obj.items():
        result[node] = {}
        for key, vector in vectors.items():
            if isinstance(vector, np.ndarray):
                result[node][key] = vector.tolist()
            elif isinstance(vector, dict):
                result[node][key] = {
                    k: v.tolist() if isinstance(v, np.ndarray) else v for k, v in vector.items()
                }
            else:
                result[node][key] = vector
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
        dry_run=True
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
    rank_allocation, _, cell_memory_usage = nd._dry_run_stats.distribute_cells(2, 1, 1)
    export_allocation_stats(rank_allocation,
                            USECASE3 / "allocation.pkl.gz",
                            cell_memory_usage,
                            USECASE3 / "memory_per_metype.json")
    rank_allocation = import_allocation_stats(USECASE3 / "allocation.pkl.gz")
    rank_allocation_standard = convert_to_standard_types(rank_allocation)

    expected_items = {
        'NodeA': {(0, 0): [1], (1, 0): [2, 3]},
        'NodeB': {(0, 0): [1], (1, 0): [2]}
    }

    assert rank_allocation_standard == expected_items

    # Test that the allocation works and can be saved and loaded
    # and generate allocation.pkl.gz for 1 rank
    rank_allocation, _, cell_memory_usage = nd._dry_run_stats.distribute_cells(1, 1, 1)
    export_allocation_stats(rank_allocation,
                            USECASE3 / "allocation.pkl.gz",
                            cell_memory_usage,
                            USECASE3 / "memory_per_metype.json")
    rank_allocation = import_allocation_stats(USECASE3 / "allocation.pkl.gz")
    rank_allocation_standard = convert_to_standard_types(rank_allocation)

    expected_items = {
        'NodeA': {(0, 0): [1, 2, 3]},
        'NodeB': {(0, 0): [1, 2]}
    }

    assert rank_allocation_standard == expected_items

    # Clean up
    Path(("cell_memory_usage.json")).unlink(missing_ok=True)


def test_dry_run_workflow_multi():
    """
    Test that the dry run mode works in multicycle mode
    """

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

    rank_allocation, _, cell_memory_usage = nd._dry_run_stats.distribute_cells(2)
    export_allocation_stats(rank_allocation,
                            SIM_DIR / "allocation_multi.pkl.gz",
                            cell_memory_usage,
                            SIM_DIR / "memory_per_metype.json")
    rank_allocation = import_allocation_stats(SIM_DIR / "allocation_multi.pkl.gz")
    rank_allocation_standard = convert_to_standard_types(rank_allocation)

    expected_items = {
        'default': {
            (0, 0): [
                62798, 62946, 63257, 63699, 64164, 64862, 65916, 65952, 66069, 66106,
                69840, 63623, 64234, 64666, 64788, 64936, 69878, 65821, 67078, 68856
            ],
            (1, 0): [
                66141, 66497, 66872, 67667, 68224, 68354, 68533, 68581, 68942, 69531
            ]
        }
    }
    assert rank_allocation_standard == expected_items

# Temporarily disabled since it requires a rework of the
# memory load balance workflow to be compatible with the new
# memory allocation stats

# def test_memory_load_balance_workflow(USECASE3):
#     """
#     Test that the memory load balance works
#     """

#     from neurodamus import Neurodamus
#     nd = Neurodamus(
#         str(USECASE3 / "simulation_sonata.json"),
#         lb_mode="Memory",
#     )

#     nd.run()
