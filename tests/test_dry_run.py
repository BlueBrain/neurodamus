import pytest
import numpy as np
import unittest.mock


@pytest.mark.forked
def test_dry_run_distribution():
    """Test the dry_run_distribution function.
    This test makes sure that the distribution for dry runs
    returns the inner lists of the gid_metype_bundle as a single list
    with round robin distribution on the inner lists.
    """
    from neurodamus.io.cell_readers import dry_run_distribution

    # Sample of a typical gid_metype_bundle
    gid_metype_bundle = [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10]]

    # Test with stride=1 (single rank)
    expected_output = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    assert np.array_equal(dry_run_distribution(gid_metype_bundle, stride=1), expected_output)

    # Test with stride=2 and stride_offset=0 (two ranks total, first rank)
    expected_output = np.array([1, 2, 3, 7, 8, 9])
    assert np.array_equal(dry_run_distribution(gid_metype_bundle, stride=2, stride_offset=0),
                          expected_output)

    # Test with stride=2 and stride_offset=1 (two ranks total, second rank)
    expected_output = np.array([4, 5, 6, 10])
    assert np.array_equal(dry_run_distribution(gid_metype_bundle, stride=2, stride_offset=1),
                          expected_output)


@pytest.mark.forked
def test_retrieve_unique_metypes():
    from neurodamus.io.cell_readers import _retrieve_unique_metypes

    # Define test inputs
    node_reader = DummyNodeReader()
    all_gids = [1, 2, 3, 4, 5]

    # Call the function
    with unittest.mock.patch('neurodamus.io.cell_readers.isinstance', return_value=True):
        result_list, result_int = _retrieve_unique_metypes(node_reader, all_gids)

    # Assertion checks
    assert isinstance(result_list, list)
    assert all(isinstance(lst, list) for lst in result_list)

    # Check the expected output based on the test inputs
    expected_result_list = [[1, 3, 5], [2, 4]]
    assert result_list == expected_result_list
    expected_result_int = {('emodel1', 'mtype1'): 3, ('emodel2', 'mtype2'): 2}
    assert result_int == expected_result_int


class DummyNodeReader:
    """ Fake dummy class to mock the NodeReader class
    for sonata readers.
    """
    def get_attribute(self, attr, selection):
        if attr == "etype":
            return ["emodel1", "emodel2", "emodel1", "emodel2", "emodel1"]
        elif attr == "mtype":
            return ["mtype1", "mtype2", "mtype1", "mtype2", "mtype1"]
        else:
            pytest.fail(f"Unsupported attribute: {attr}")
