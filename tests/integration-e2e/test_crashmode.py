

def test_crash_test_loading(SIM_DIR, tmp_path):
    from neurodamus import Node
    from neurodamus.cell_distributor import CellDistributor
    from neurodamus.metype import PointCell
    from neuron import nrn
    sim_dir = SIM_DIR / "v5_sonata"
    sim_config_path = sim_dir / "simulation_config_mini.json"

    n = Node(str(sim_config_path), {"crash_test": True})
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
