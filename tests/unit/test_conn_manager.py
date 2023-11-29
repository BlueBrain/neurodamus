import pytest
from unittest import mock

from neurodamus.connection_manager import ConnectionSet


class _FakeConn:
    def __init__(self, sgid, tgid):
        self.sgid = sgid
        self.tgid = tgid


def _create_population(src_dst_pairs):
    pop = ConnectionSet(0, 0)
    for src, dst in src_dst_pairs:
        pop.store_connection(_FakeConn(src, dst))
    return pop


@pytest.fixture
def population():
    pop = ConnectionSet(0, 0)
    for i in range(10):
        pop.store_connection(_FakeConn(i + 1, i))
        pop.store_connection(_FakeConn(i + 2, i))
        pop.store_connection(_FakeConn(i - 1, i))
    assert pop.count() == 30
    return pop


def test_population_get(population):
    conn = population.get_connection(1, 2)
    assert conn.sgid == 1
    assert conn.tgid == 2
    assert population.get_connection(2, 2) is None


def test_population_store_order():
    # Independently of insertion order, they get ordered
    pop = _create_population([(1, 0), (1, 2), (1, 1), (0, 0), (0, 1)])
    expected_sgids = {
        0: [0, 1],
        1: [0, 1],
        2: [1],
    }
    for tgid, conns in pop.items():
        assert expected_sgids[tgid] == [c.sgid for c in conns]


def test_population_get_create_conn(population):
    total = population.count()
    replacement_conn = mock.Mock()  # Replace connection
    population._conn_factory = replacement_conn

    conn = population.get_or_create_connection(1, 2)
    assert isinstance(conn, _FakeConn)
    assert population.count() == total

    population.get_or_create_connection(2, 2)
    assert replacement_conn.call_args == ((2, 2, 0, 0),)
    assert population.count() == total + 1
    conns2 = population[2]
    expected_types = [_FakeConn, mock.Mock, _FakeConn, _FakeConn]
    checks = [isinstance(c, expected_types[i]) for i, c in enumerate(conns2)]
    assert all(checks)


def test_population_all_conns():
    pop = _create_population([(1, 0), (1, 2), (1, 1), (0, 0), (0, 1)])
    expected = [(0, 0), (1, 0), (1, 2), (0, 1), (1, 1)]  # ordered sgids
    for i, conn in enumerate(pop.all_connections()):
        assert expected[i] == (conn.sgid, conn.tgid)


@pytest.mark.parametrize(("test_input", "expected"), [
    ((1,), [(0, 1), (1, 1)]),
    (([1],), [(0, 1), (1, 1)]),
    (([1, 2],), [(0, 1), (1, 1), (1, 2)]),
    (([1, 0],), [(0, 1), (1, 1), (0, 0), (1, 0)]),
    ((1, 1), [(1, 1)]),
    (([1], 1), [(1, 1)]),
    ((1, [1]), [(1, 1)]),
    (([1], [1]), [(1, 1)]),
    (([1, 2], [1]), [(1, 1), (1, 2)]),
    (([1], [0, 1]), [(0, 1), (1, 1)]),
    (([0, 1], [0, 1]), [(0, 0), (1, 0), (0, 1), (1, 1)]),
])
def test_population_get_connections(test_input, expected):
    pop = _create_population([(1, 0), (1, 2), (1, 1), (0, 0), (0, 1)])
    conns = list(pop.get_connections(*test_input))
    assert len(conns) == len(expected)
    for i, conn in enumerate(conns):
        assert expected[i] == (conn.sgid, conn.tgid)


def test_population_delete():
    pop = _create_population([(1, 0), (1, 2), (1, 1), (0, 0), (0, 1)])
    expected = [(0, 0), (1, 0), (1, 2), (1, 1)]  # ordered sgids
    pop.delete(0, 1)
    for i, conn in enumerate(pop.all_connections()):
        assert expected[i] == (conn.sgid, conn.tgid)


@pytest.mark.parametrize(("test_input", "expected"), [
    ((1,), [(0, 0), (1, 0), (1, 2)]),
    (([1],), [(0, 0), (1, 0), (1, 2)]),
    (([1, 2],), [(0, 0), (1, 0)]),
    (([1, 0],), [(1, 2)]),
    ((1, 1), [(0, 0), (1, 0), (1, 2), (0, 1)]),
    (([1], 1), [(0, 0), (1, 0), (1, 2), (0, 1)]),
    ((1, [1]), [(0, 0), (1, 0), (1, 2), (0, 1)]),
    (([1], [1]), [(0, 0), (1, 0), (1, 2), (0, 1)]),
    (([1, 2], [1]), [(0, 0), (1, 0), (0, 1)]),
    (([1], [0, 1]), [(0, 0), (1, 0), (1, 2)]),
    (([0, 1], [0, 1]), [(1, 2)]),
])
def test_population_delete_group(test_input, expected):
    pop = _create_population([(1, 0), (1, 2), (1, 1), (0, 0), (0, 1)])
    pop.delete_group(*test_input)
    result = [(conn.sgid, conn.tgid) for conn in pop.all_connections()]
    assert expected == result


def test_population_ids_match():
    pop = _create_population([])
    assert pop.ids_match(0)
    assert pop.ids_match(0, 0)
    assert pop.ids_match((0, 0))
    assert pop.ids_match(None)
    assert pop.ids_match(0, None)
    assert pop.ids_match(None, 0)
    assert pop.ids_match(None, None)

    assert not pop.ids_match(1)
    assert not pop.ids_match(1, 0)
    assert not pop.ids_match((0, 1))
    assert not pop.ids_match(1, 1)
    assert not pop.ids_match(1, None)
    assert not pop.ids_match(None, 1)
