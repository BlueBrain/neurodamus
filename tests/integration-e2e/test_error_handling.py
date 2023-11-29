import pytest


def test_handling_neuron_exceptions(USECASE3):
    SONATA_CONF_FILE = str(USECASE3 / "simulation_sonata.json")
    from neurodamus import Node
    n = Node(SONATA_CONF_FILE)
    n.load_targets()
    n._extra_circuits['NodeA'].MorphologyPath = str(USECASE3 / "dummy_err_dir")
    with pytest.raises(RuntimeError,
                       match="Error from NEURON when loading Gid .: emodel: .*, Morphology: .*: "
                             "hocobj_call error: hoc_execerror: .*:file is not open"):
        n.create_cells()
