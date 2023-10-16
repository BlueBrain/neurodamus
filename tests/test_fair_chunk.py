from neurodamus.io.cell_readers import split_fair_chunks

def test_split_fair_chunk_from_gids():
    gids = list(range(1, 8))

    assert split_fair_chunks(gids, n_chunks=3, k_chunk=0) == [1, 2, 3]
    assert split_fair_chunks(gids, n_chunks=3, k_chunk=1) == [4, 5]
    assert split_fair_chunks(gids, n_chunks=3, k_chunk=2) == [6, 7]

def test_split_fair_chunk_total():
    gids = None

    assert list(split_fair_chunks(gids, n_chunks=3, k_chunk=0, total_cells=7)) == [0, 1, 2]
    assert list(split_fair_chunks(gids, n_chunks=3, k_chunk=1, total_cells=7)) == [3, 4]
    assert list(split_fair_chunks(gids, n_chunks=3, k_chunk=2, total_cells=7)) == [5, 6]

def test_split_fair_chunk_from_almost_empty_gids():
    gids = [0, 1]

    assert split_fair_chunks(gids, n_chunks=3, k_chunk=0) == [0]
    assert split_fair_chunks(gids, n_chunks=3, k_chunk=1) == [1]
    assert split_fair_chunks(gids, n_chunks=3, k_chunk=2) == []

def test_split_fair_chunk_from_two():
    gids = None

    assert list(split_fair_chunks(gids, n_chunks=3, k_chunk=0, total_cells=2)) == [0]
    assert list(split_fair_chunks(gids, n_chunks=3, k_chunk=1, total_cells=2)) == [1]
    assert list(split_fair_chunks(gids, n_chunks=3, k_chunk=2, total_cells=2)) == []

def test_split_fair_chunk_from_empty_gids():
    gids = []
    for k in range(3):
        assert split_fair_chunks(gids, n_chunks=3, k_chunk=k) == []

def test_split_fair_chunk_from_zero():
    gids = None
    for k in range(3):
        assert list(split_fair_chunks(gids, n_chunks=3, k_chunk=k, total_cells=0)) == []
