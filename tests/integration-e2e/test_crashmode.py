

def test_crash_test_loading(SIM_DIR, tmp_path):
    import json
    from neurodamus import Node
    from neurodamus.cell_distributor import CellDistributor
    from neurodamus.metype import PointCell
    from neuron import nrn
    sim_dir = SIM_DIR / "v5_sonata"
    config_file_mini = "simulation_config_mini.json"

    # Read the original config file
    sim_config_path = sim_dir / config_file_mini
    with open(sim_config_path, "r") as f:
        sim_config_data = json.load(f)

    # Update the network path in the config
    sim_config_data["network"] = str(sim_dir / "sub_mini5" / "circuit_config.json")

    # Write the modified config to the temporary directory
    temp_config_path = tmp_path / config_file_mini
    with open(temp_config_path, "w") as f:
        json.dump(sim_config_data, f, indent=2)

    n = Node(str(temp_config_path), {"crash_test": True})
    n.load_targets()
    n.create_cells()

    cell_manager: CellDistributor = n.circuits.get_node_manager("default")
    assert len(cell_manager.cells) == 5
    cell0 = next(iter(cell_manager.cells))
    assert isinstance(cell0, PointCell)
    assert isinstance(cell0.soma, list)
    assert len(cell0.soma) == 1
    assert isinstance(cell0.soma[0], nrn.Section)

    n.create_synapses()
    syn_manager = n.circuits.get_edge_manager("default", "default")
    assert syn_manager.connection_count == 2
