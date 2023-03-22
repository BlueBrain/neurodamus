import pytest
import h5py


@pytest.fixture
def test_file(tmpdir):
    """
    Generates example weights file
    """
    # Create a test HDF5 file with sample data
    test_file = h5py.File(tmpdir.join("test_file.h5"), 'w')
    test_file.create_group("electrodes")
    test_file["electrodes"].create_group("electrode_grid")
    test_file["electrodes"]["electrode_grid"].create_dataset("0", data=[[0.1, 0.2], [0.3, 0.4]])
    test_file["electrodes"]["electrode_grid"].create_dataset("1", data=[[0.5, 0.6], [0.7, 0.8]])
    test_file.create_group("sec_ids")
    test_file["sec_ids"].create_dataset("0", data=[0, 1])
    test_file["sec_ids"].create_dataset("1", data=[2, 3])
    neuron_ids = test_file.create_dataset("neuron_ids", data=[0, 1])
    neuron_ids.attrs["circuit"] = "test_circuit.h5"
    yield test_file


def test_load_lfp_config(tmpdir, test_file):
    """
    Test that the 'load_lfp_config' function opens and loads correctly
    the LFP weights file and checks its format
    """
    from neurodamus.cell_distributor import LFPManager
    from neurodamus.core.configuration import ConfigurationError

    # Test loading LFP config file from invalid circuit
    lfp_invalid = LFPManager()
    lfp_weights_file = tmpdir.join("test_file.h5")
    circuit_list_invalid = ["invalid_circuit.h5"]
    lfp_invalid.load_lfp_config(lfp_weights_file, circuit_list_invalid)
    # File is closed
    assert not lfp_invalid._lfp_file

    # Create an instance of the class
    lfp = LFPManager()
    circuit_list = ["test_circuit2.h5", "test_circuit.h5"]

    # Test loading LFP configuration from file
    lfp.load_lfp_config(lfp_weights_file, circuit_list)
    assert lfp._lfp_file
    assert isinstance(lfp._lfp_file, h5py.File)
    assert "electrodes" in lfp._lfp_file
    assert "neuron_ids" in lfp._lfp_file
    assert "sec_ids" in lfp._lfp_file
    assert lfp._lfp_file["neuron_ids"].attrs['circuit'] == "test_circuit.h5"

    # Test loading LFP configuration from file with wrong format
    del lfp._lfp_file["neuron_ids"].attrs['circuit']
    with pytest.raises(ConfigurationError):
        lfp.load_lfp_config(lfp_weights_file, circuit_list)

    del lfp._lfp_file["neuron_ids"]
    with pytest.raises(ConfigurationError):
        lfp.load_lfp_config(lfp_weights_file, circuit_list)

    # Test loading LFP configuration from invalid file
    lfp_weights_invalid_file = "./invalid_file.h5"
    with pytest.raises(ConfigurationError):
        lfp.load_lfp_config(lfp_weights_invalid_file, circuit_list)


def test_read_lfp_factors(test_file):
    """
    Test that the 'read_lfp_factors' function correctly extracts the LFP factors
    for the specified gid and section ids from the weights file
    """
    from neurodamus.cell_distributor import LFPManager
    # Create an instance of the class
    lfp = LFPManager()
    lfp._lfp_file = test_file
    # Test the function with valid input
    gid = 0
    section_ids = [1, 2]
    result = lfp.read_lfp_factors(gid, section_ids).to_python()
    expected_result = [0.3, 0.4]
    assert result == expected_result, f'Expected {expected_result}, but got {result}'

    # Test the function with invalid input (non-existent gid)
    gid = 2
    section_ids = [0, 1]
    result = lfp.read_lfp_factors(gid, section_ids).to_python()
    expected_result = []
    assert result == expected_result, f'Expected {expected_result}, but got {result}'


def test_number_electrodes(test_file):
    """
    Test that the 'get_number_electrodes' function correctly extracts the number of
    electrodes in the weights file for a certain gid
    """
    from neurodamus.cell_distributor import LFPManager
    # Create an instance of the class
    lfp = LFPManager()
    lfp._lfp_file = test_file
    # Test the function with valid input
    gid = 0
    result = lfp.get_number_electrodes(gid)
    expected_result = 2
    assert result == expected_result, f'Expected {expected_result}, but got {result}'

    # Test the function with invalid input (non-existent gid)
    gid = 2
    result = lfp.get_number_electrodes(gid)
    expected_result = 0
    assert result == expected_result, f'Expected {expected_result}, but got {result}'
