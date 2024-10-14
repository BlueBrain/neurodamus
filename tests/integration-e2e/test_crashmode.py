import json
import os


def test_crash_test_loading(SIM_DIR, tmp_path):
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
    config["node_set"] = "L4_SP"
    config["network"] = str(SIM_DIR / "v5_sonata"/ "sub_L4_SP" / "circuit_config.json")
    with open(new_config_path, "w") as new_config:
        json.dump(config, new_config)

    n = Node(str(new_config_path), {"crash_test": True})
    n.load_targets()
    n.create_cells()

    cell_manager: CellDistributor = n.circuits.get_node_manager("default")
    assert len(cell_manager.cells) == 7687
    cell0 = next(iter(cell_manager.cells))
    assert isinstance(cell0, PointCell)
    assert isinstance(cell0.soma, list)
    assert len(cell0.soma) == 1
    assert isinstance(cell0.soma[0], nrn.Section)

    n.create_synapses()
    syn_manager = n.circuits.get_edge_manager("default", "default")
    assert syn_manager.connection_count == 7681
