from neurodamus.core.nodeset import NodeSet
from neurodamus.target_manager import _HocTarget, NodesetTarget, TargetSpec
import numpy as np

null_target_spec = TargetSpec("")


def test_targetspec_overlap_name():
    assert null_target_spec.overlap_byname(null_target_spec)
    t1_spec = TargetSpec("t1")
    assert t1_spec.overlap_byname(null_target_spec)
    assert null_target_spec.overlap_byname(t1_spec)
    assert not t1_spec.overlap_byname(TargetSpec("t2"))
    assert not t1_spec.overlap_byname(TargetSpec("another:t2"))
    # With populations, should ignore
    assert TargetSpec("popx:t1").overlap_byname(TargetSpec("popy:t1"))
    assert not TargetSpec("popx:t1").overlap_byname(TargetSpec("popy:t2"))


def test_populations_disjoint():
    """We test for disjoint since population doesnt say much about intersection,
    it can simply help identifying when they are disjoint for sure
    """
    assert not null_target_spec.disjoint_populations(null_target_spec)
    assert TargetSpec("pop1:").disjoint_populations(TargetSpec("pop2:"))
    assert not TargetSpec("pop1:").disjoint_populations(TargetSpec("pop1:"))


def test_targetspec_overlap():
    assert null_target_spec.overlap(null_target_spec)
    assert not TargetSpec("pop1:x").overlap(null_target_spec)  # we cant be sure -> false
    assert not TargetSpec("pop1:target1").overlap(TargetSpec("target2"))
    assert not TargetSpec("pop1:").overlap(TargetSpec("pop2:"))  # disjoint pop
    assert TargetSpec("pop1:").overlap(TargetSpec("pop1:ahh"))
    assert not TargetSpec("pop1:t1").overlap(TargetSpec("pop1:t2"))


def test_hoc_target_intersect():
    ht1 = _HocTarget("t1", None, pop_name=None)
    ht2 = _HocTarget("t2", None, pop_name=None)
    ht1_pop1 = _HocTarget("t1", None, pop_name="pop1")
    ht1_pop2 = _HocTarget("t1", None, pop_name="pop2")

    # different population is short circuited -> gids aren't necessary to see they dont intersect
    assert not ht1_pop1.intersects(ht1_pop2)
    # We override the internal gid cache to avoid creating hoc targets
    ht1._raw_gids = np.array([1, 2], dtype=int)
    ht2._raw_gids = np.array([1, 2], dtype=int)
    assert ht1.intersects(ht2)
    ht2._raw_gids = np.array([2, 3], dtype=int)
    assert ht1.intersects(ht2)
    ht2._raw_gids = np.array([3, 4], dtype=int)
    assert not ht1.intersects(ht2)


def test_nodeset_target_intersect():
    nodes_popA = NodeSet([1, 2]).register_global("pop_A")
    nodes2_popA = NodeSet([2, 3]).register_global("pop_A")
    nodes3_popA = NodeSet([11, 12]).register_global("pop_A")
    nodes_popB = NodeSet([1, 2]).register_global("pop_B")

    t1 = NodesetTarget("t1", [nodes_popA])
    t2 = NodesetTarget("t2", [nodes_popB])
    assert not t1.intersects(t2)
    t2.nodesets = [nodes_popB, nodes_popA]
    assert t1.intersects(t2)
    t2.nodesets = [nodes_popB, nodes2_popA]
    assert t1.intersects(t2)
    t2.nodesets = [nodes3_popA]
    assert not t1.intersects(t2)
    t2.nodesets = [nodes_popB, nodes3_popA]
    assert not t1.intersects(t2)


if __name__ == "__main__":
    test_targetspec_overlap_name()
    test_populations_disjoint()
    test_targetspec_overlap()
    test_hoc_target_intersect()
    test_nodeset_target_intersect()
    print("tests passed")
