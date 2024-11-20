import pytest
import os
from pathlib import Path
from unittest.mock import patch
from neurodamus.utils.memory import DryRunStats
from neurodamus.core.configuration import GlobalConfig, LogLevel

SIM_DIR = Path(__file__).parent.parent.absolute() / "simulations"


@pytest.fixture
def neurodamus_instance(request: pytest.FixtureRequest, USECASE3: Path):
    from neurodamus import Neurodamus

    params = request.param
    dry_run = params.get('dry_run', True)
    num_target_ranks = params.get('num_target_ranks', '1')
    modelbuilding_steps = params.get('modelbuilding_steps', '1')
    config_file = os.path.basename(params.get('config_file', "simulation_sonata.json"))
    path_to_config = params.get('path_to_config', USECASE3)
    lb_mode = params.get('lb_mode', "")

    GlobalConfig.verbosity = LogLevel.DEBUG
    nd = Neurodamus(
        str(path_to_config / config_file),
        dry_run=dry_run,
        num_target_ranks=num_target_ranks,
        modelbuilding_steps=modelbuilding_steps,
        lb_mode=lb_mode
    )
    yield nd

    nd = None


def convert_to_standard_types(obj):
    """Converts an object containing defaultdicts of Vectors to standard Python types."""
    result = {}
    for node, vectors in obj.items():
        result[node] = {key: list(vector) for key, vector in vectors.items()}
    return result


@pytest.mark.parametrize("neurodamus_instance", [
    {
        'dry_run': True,
        'num_target_ranks': 2,
        'config_file': "simulation_sonata.json",
        'path_to_config': SIM_DIR / "usecase3",
        'lb_mode': ""
    }
], indirect=True)
def test_dry_run_workflow(neurodamus_instance, USECASE3):
    """
    Test that the dry run mode works

    """
    from neurodamus.utils.memory import export_allocation_stats
    from neurodamus.utils.memory import export_metype_memory_usage

    GlobalConfig.verbosity = LogLevel.DEBUG
    nd = neurodamus_instance

    nd.run()

    assert 20.0 <= nd._dry_run_stats.cell_memory_total <= 30.0
    assert 0.0 <= nd._dry_run_stats.synapse_memory_total <= 1.0
    assert 60.0 <= nd._dry_run_stats.base_memory <= 120.0
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

    rank_alloc = nd._dry_run_stats.import_allocation_stats(USECASE3 / "allocation_r2_c1.pkl.gz", 0)
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

    Path(("allocation_r1_c1.pkl.gz")).unlink(missing_ok=True)
    Path(("allocation_r2_c1.pkl.gz")).unlink(missing_ok=True)


@pytest.mark.parametrize("neurodamus_instance", [
    {
        'dry_run': False,
        'config_file': "simulation_sonata.json",
        'path_to_config': SIM_DIR / "usecase3",
        'lb_mode': "Memory"
    }
], indirect=True)
def test_dynamic_distribute(neurodamus_instance):
    """
    Test that the dynamic distribution of cells works properly.
    The test deletes any old allocation file before running and uses
    the memory_per_metype.json generated in the previous test to
    redistribute the cells. Then checks if the new allocation is correct.
    """

    nd = neurodamus_instance

    rank_allocation, _, _ = nd._dry_run_stats.distribute_cells_with_validation(2, 1)
    rank_allocation_standard = convert_to_standard_types(rank_allocation)

    expected_items = {
        'NodeA': {
            (0, 0): [1],
            (1, 0): [2, 3]
        }
    }

    for key, sub_value in rank_allocation_standard['NodeA'].items():
        assert set(sub_value) == set(expected_items['NodeA'][key])


@pytest.fixture
def fixed_memory_measurements():
    with patch('neurodamus.utils.memory.get_mem_usage_kb', return_value=100):
        with patch('neurodamus.utils.memory.SynapseMemoryUsage.get_memory_usage', return_value=10):
            yield


def test_distribute_cells_multi_pop_multi_cycle(fixed_memory_measurements):
    """
    Test that the distribute_cells_with_validation function works with multiple pops and cycles
    """

    stats = DryRunStats()

    # Mock data for testing
    stats.metype_memory = {
        'L4_PC-dSTUT': 50,
        'L4_MC-dSTUT': 30,
        'L4_MC-dNAC': 20,
        'L5_PC-dSTUT': 40
    }
    stats.metype_cell_syn_average = {
        'L4_PC-dSTUT': 5,
        'L4_MC-dSTUT': 3,
        'L4_MC-dNAC': 2,
        'L5_PC-dSTUT': 4
    }
    stats.pop_metype_gids = {
        'NodeA': {
            'L4_PC-dSTUT': [1, 2, 3],
            'L4_MC-dSTUT': [4, 5],
            'L4_MC-dNAC': [6],
            'L5_PC-dSTUT': [7, 8]
        },
        'NodeB': {
            'L4_PC-dSTUT': [9],
            'L4_MC-dSTUT': [10, 11],
            'L4_MC-dNAC': [12, 13],
            'L5_PC-dSTUT': [14]
        }
    }

    # Run the distribute_cells_with_validation function
    bucket_allocation, bucket_memory, metype_memory_usage = stats.distribute_cells_with_validation(
        num_ranks=2,
        cycles=2
    )
    rank_allocation_standard = convert_to_standard_types(bucket_allocation)

    expected_allocation = {
        'NodeA': {
            (0, 0): [1, 6],
            (1, 0): [3, 8],
            (0, 1): [2, 7],
            (1, 1): [4, 5]
        },
        'NodeB': {
            (0, 0): [9],
            (1, 0): [11],
            (0, 1): [10, 14],
            (1, 1): [12, 13]
        }
    }
    expected_memory = {
        'NodeA': {
            (0, 0): 90,
            (1, 0): 110,
            (0, 1): 110,
            (1, 1): 80
        },
        'NodeB': {
            (0, 0): 60,
            (1, 0): 40,
            (0, 1): 90,
            (1, 1): 60
        }
    }

    # Assert that the results match the expected values
    assert rank_allocation_standard == expected_allocation
    assert bucket_memory == expected_memory
