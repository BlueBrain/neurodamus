import os
import pytest
from neurodamus.core.nodeset import NodeSet, _ranges_overlap, _ranges_vec_overlap
import numpy
import json


@pytest.mark.forked
def test_NodeSet_base():
    # No registration, just plain gid sets
    set1 = NodeSet([1, 2, 3])
    assert set1.offset == 0
    assert set1.max_gid == 3

    set2 = NodeSet()
    assert set2.offset == 0
    assert set2.max_gid == 0
    set2.add_gids([1, 2, 3])
    assert set2.offset == 0
    assert set2.max_gid == 3


@pytest.mark.forked
def test_NodeSet_add():
    set_mid = NodeSet([1, 2, 3, 1000]).register_global("pop2")
    assert set_mid.offset == 0
    assert set_mid.max_gid == 1000

    # Append to right
    set_right = NodeSet([1, 2, 3, 4]).register_global("pop3")
    assert set_right.offset == 1000
    assert set_right.max_gid == 4

    # Append to left (occupies two blocks of 1000)
    set_left = NodeSet([1, 2, 3, 4, 1001]).register_global("pop1")
    assert set_left.offset == 0
    assert set_left.max_gid == 1001
    assert set_mid.offset == 2000
    assert set_right.offset == 3000

    # Extend middle to also occupy two blocks (rare)
    set_mid.add_gids([1002])
    assert set_mid.max_gid == 1002
    assert set_right.offset == 4000


@pytest.mark.parametrize(("ranges1", "ranges2", "expected"), [
    ([(0, 10), (20, 30)], [(8, 23), (28, 35)], numpy.array([8, 9, 20, 21, 22, 28, 29])),
    ([(0, 10), (20, 30)], [(10, 20)], []),
    ([(5, 10), (20, 30)], [(0, 10)], numpy.arange(5, 10)),
    ([(5, 10), (20, 30)], [(25, 35)], numpy.arange(25, 30)),
    ([], [], []),
    ([], [(5, 25)], []),
    ([(0, 10), (20, 30)], [], []),
])
def test_ranges_overlap(ranges1, ranges2, expected):
    out = _ranges_overlap(ranges1, ranges2, flattened_out=True)
    numpy.testing.assert_array_equal(out, expected)


@pytest.mark.parametrize(("ranges1", "vec", "expected"), [
    ([(0, 10), (20, 30)], [1, 2, 11, 12, 19, 20, 21, 29, 30], [1, 2, 20, 21, 29]),
    ([(0, 10), (20, 30)], [11, 12], []),
    ([], [], []),
    ([], [1, 2, 3], []),
    ([(0, 10), (20, 30)], [], []),
])
def test_ranges_vec_overlap(ranges1, vec, expected):
    out = _ranges_vec_overlap(ranges1, vec)
    numpy.testing.assert_array_equal(out, expected)


@pytest.fixture
def nodeset_files(tmpdir):
    """
    Generates example nodeset files
    """
    # Define nodesets
    config_nodeset_file = {
        "Mosaic": {
            "population": "default"
        },
        "Layer1": {
            "layer": 1
        },
    }

    simulation_nodesets_file = {
        "Mosaic": {
            "population": "All"
        },
        "Layer2": {
            "layer": 2
        },
    }

    # Create the test JSON files with nodesets
    config_nodeset = tmpdir.join("node_sets_circuit.json")
    with open(config_nodeset, 'w') as f:
        json.dump(config_nodeset_file, f)

    simulation_nodeset = tmpdir.join("node_sets_simulation.json")
    with open(simulation_nodeset, 'w') as f:
        json.dump(simulation_nodesets_file, f)

    yield config_nodeset, simulation_nodeset

    # Delete the files after they're used
    os.unlink(config_nodeset)
    os.unlink(simulation_nodeset)


def test_read_nodesets_from_file(nodeset_files):
    from neurodamus.target_manager import NodeSetReader

    ns_reader = NodeSetReader(*nodeset_files)
    assert ns_reader.names == {'Mosaic', 'Layer1', 'Layer2'}
    assert ns_reader.read_nodeset("Mosaic") is not None
    assert ns_reader.read_nodeset("Layer3") is None
    expected_output = {
        "Layer1": {"layer": [1]},
        "Layer2": {"layer": [2]},
        "Mosaic": {"population": ["All"]}
    }
    assert json.loads(ns_reader.nodesets.toJSON()) == json.loads(json.dumps(expected_output))
