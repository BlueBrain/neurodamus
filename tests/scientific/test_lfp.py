import pytest
import h5py
import os
import numpy as np
from pathlib import Path

SIM_DIR = Path(__file__).parent.parent.absolute() / "simulations"


@pytest.fixture
def test_file(tmpdir):
    """
    Generates example weights file
    """
    # Define populations and their GIDs
    populations = {
        "default": [42, 62797, 63698],
        "other_pop": [77777, 88888]
    }

    # Create a test HDF5 file with sample data
    test_file = h5py.File(tmpdir.join("test_file.h5"), 'w')

    for population, gids in populations.items():
        # Create population group
        population_group = test_file.create_group(population)

        # Create node_ids dataset
        population_group.create_dataset("node_ids", data=gids)

        # Create offsets dataset
        sec_ids_count = [2, 82, 140]
        total_segments = 224
        offsets = np.append(np.add.accumulate(sec_ids_count) - sec_ids_count, total_segments)
        population_group.create_dataset('offsets', data=offsets)

        # Create electrodes group and data dataset
        electrodes_group = test_file.create_group("electrodes/" + population)
        matrix = []
        # Fill first 2 rows
        matrix.append([0.1, 0.2])
        matrix.append([0.3, 0.4])

        # Fill the remaining rows up to total_segments
        incrementx = 0.0
        incrementy = 0.0
        for i in range(2, total_segments):
            value_x = 0.4 + incrementx
            value_y = 0.3 + incrementy
            matrix.append([value_x, value_y])
            incrementx += 0.001
            incrementy -= 0.0032
        electrodes_group.create_dataset("scaling_factors", dtype='f8', data=matrix)

    return test_file


def test_load_lfp_config(tmpdir, test_file):
    """
    Test that the 'load_lfp_config' function opens and loads correctly
    the LFP weights file and checks its format
    """
    from neurodamus.cell_distributor import LFPManager
    from neurodamus.core.configuration import ConfigurationError

    # Load the electrodes file
    lfp_weights_file = tmpdir.join("test_file.h5")

    # Create an instance of the class
    lfp = LFPManager()
    pop_list = ["wrong_pop", "default"]

    # Test loading LFP configuration from file
    lfp.load_lfp_config(lfp_weights_file, pop_list)
    assert lfp._lfp_file
    assert isinstance(lfp._lfp_file, h5py.File)
    assert "/electrodes/default" in lfp._lfp_file
    assert "/default/node_ids" in lfp._lfp_file

    del lfp._lfp_file["default"]["node_ids"]
    with pytest.raises(ConfigurationError):
        lfp.load_lfp_config(lfp_weights_file, pop_list)

    # Test loading LFP configuration from invalid file
    lfp_weights_invalid_file = "./invalid_file.h5"
    with pytest.raises(ConfigurationError):
        lfp.load_lfp_config(lfp_weights_invalid_file, pop_list)


def test_read_lfp_factors(test_file):
    """
    Test that the 'read_lfp_factors' function correctly extracts the LFP factors
    for the specified gid and section ids from the weights file
    """
    from neurodamus.cell_distributor import LFPManager
    # Create an instance of the class
    lfp = LFPManager()
    lfp._lfp_file = test_file
    # Test the function with valid input (node_id is 0 based, so expected 42 in the file)
    gid = 43
    result = lfp.read_lfp_factors(gid).to_python()
    expected_result = [0.1, 0.2, 0.3, 0.4]
    assert result == expected_result, f'Expected {expected_result}, but got {result}'

    # Test the function with invalid input (non-existent gid)
    gid = 2
    result = lfp.read_lfp_factors(gid).to_python()
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
    gid = 62798
    result = lfp.get_number_electrodes(gid)
    expected_result = 2
    assert result == expected_result, f'Expected {expected_result}, but got {result}'

    # Test the function with invalid input (non-existent gid)
    gid = 2
    result = lfp.get_number_electrodes(gid)
    expected_result = 0
    assert result == expected_result, f'Expected {expected_result}, but got {result}'


def _create_tmpconfig_lfp(config_file, lfp_file):
    import fileinput
    import shutil
    from tempfile import NamedTemporaryFile

    lfp_replace = "\"electrodes_file\": \"" + str(lfp_file) + "\""
    suffix = ".json" if config_file.endswith(".json") else ".BC"
    tmp_file = NamedTemporaryFile(suffix=suffix, dir=os.path.dirname(config_file), delete=True)
    shutil.copy2(config_file, tmp_file.name)

    with fileinput.FileInput(tmp_file.name, inplace=True) as file:
        for line in file:
            if config_file.endswith(".json"):
                print(line.replace("\"electrodes_file\": \"electrodes_file.h5\"",
                                   lfp_replace), end='')
    return tmp_file


def _read_sonata_lfp_file(lfp_file):
    import libsonata
    report = libsonata.ElementReportReader(lfp_file)
    pop_name = report.get_population_names()[0]
    node_ids = report[pop_name].get_node_ids()
    data = report[pop_name].get()
    return node_ids, data


def test_v5_sonata_lfp(tmpdir, test_file):
    import numpy.testing as npt
    from neurodamus import Neurodamus

    config_file = str(SIM_DIR / "v5_sonata" / "simulation_config_lfp.json")
    output_dir = str(SIM_DIR / "v5_sonata" / "output_coreneuron")

    lfp_weights_file = tmpdir.join("test_file.h5")
    tmp_file = _create_tmpconfig_lfp(config_file, lfp_weights_file)

    nd = Neurodamus(tmp_file.name, output_path=output_dir)
    nd.run()

    # compare results with refs
    t3_data = np.array([0.00029701614, -0.0009504516, 0.0013853279, -0.0044330494])
    t7_data = np.array([0.000315888, -0.0010108417, 0.0015036742, -0.0048117572])
    node_ids = np.array([62797, 63698])
    result_ids, result_data = _read_sonata_lfp_file(os.path.join(output_dir, "lfp.h5"))

    npt.assert_allclose(result_data.data[3], t3_data)
    npt.assert_allclose(result_data.data[7], t7_data)
    npt.assert_allclose(result_ids, node_ids)
