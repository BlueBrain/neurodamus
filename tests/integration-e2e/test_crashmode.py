import json
import os


def test_crash_test_cell_loading(SIM_DIR, tmp_path):
    from neurodamus import Node
    from neurodamus.cell_distributor import CellDistributor
    from neurodamus.metype import PointCell
    from neuron import nrn
    sim_dir = SIM_DIR / "v5_sonata"
    sim_config_path = sim_dir / "simulation_config.json"

    with open(sim_config_path) as config_fp:
        config = json.load(config_fp)

    # Replace target with a large one (18k cells)
    # Test runs in a single rank and its still fast in crash-test mode
    new_config_path = tmp_path / "simulation_config.json"
    config["node_set"] = "L4_PC"
    with open(new_config_path, "w") as new_config:
        json.dump(config, new_config)

    # Symlink aux files, searched in the same dir
    for filename in ("circuit_config.json", "node_sets.json"):
        os.symlink(sim_dir / filename, tmp_path / filename)

    n = Node(str(new_config_path), {"crash_test": True})
    n.load_targets()
    n.create_cells()
    n.create_synapses()

    cell_manager: CellDistributor = n.circuits.get_node_manager("default")
    assert len(cell_manager.cells) == 18750
    cell0 = next(iter(cell_manager.cells))
    assert isinstance(cell0, PointCell)
    assert isinstance(cell0.soma, list)
    assert len(cell0.soma) == 1
    assert isinstance(cell0.soma[0], nrn.Section)
