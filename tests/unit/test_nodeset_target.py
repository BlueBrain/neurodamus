import numpy
import pytest


@pytest.mark.forked
def test_get_local_gids():

    from neurodamus.core.nodeset import NodeSet, PopulationNodes
    from neurodamus.target_manager import NodesetTarget
    PopulationNodes.reset()
    nodes_popA = NodeSet([1, 2]).register_global("pop_A")
    nodes_popB = NodeSet([1, 2]).register_global("pop_B")
    local_gids = [NodeSet([1]).register_global("pop_A"), NodeSet([2]).register_global("pop_B")]
    t1 = NodesetTarget("t1", [nodes_popA], local_gids)
    t2 = NodesetTarget("t2", [nodes_popB], local_gids)
    t_empty = NodesetTarget("t_empty", [], local_gids)
    numpy.testing.assert_array_equal(t1.get_local_gids(), [1])
    numpy.testing.assert_array_equal(t1.get_local_gids(raw_gids=True), [1])
    numpy.testing.assert_array_equal(t2.get_local_gids(), [1002])
    numpy.testing.assert_array_equal(t2.get_local_gids(raw_gids=True), [2])
    numpy.testing.assert_array_equal(t_empty.get_local_gids(), [])
