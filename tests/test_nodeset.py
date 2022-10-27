import pytest
from neurodamus.core.nodeset import NodeSet


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
