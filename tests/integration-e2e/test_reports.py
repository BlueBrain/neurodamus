import json
import os
import pytest
from pathlib import Path

from neurodamus.node import Node
from tempfile import NamedTemporaryFile

SIM_DIR = Path(__file__).parent.parent.absolute() / "simulations" / "v5_sonata"


@pytest.fixture
def sonata_config_new_report(sonata_config):

    extra_config = {"reports": {
        "new_report": {
            "type": "compartment",
            "cells": "Mosaic",
            "variable_name": "v",
            "sections": "all",
            "dt": 0.1,
            "start_time": 0.0,
            "end_time": 40.0
        }
    }}

    sonata_config.update(extra_config)

    return sonata_config


@pytest.fixture
def sonata_config_file_err(sonata_config_new_report):

    sonata_config_new_report["reports"]["new_report"]["variable_name"] = "wrong"

    with NamedTemporaryFile("w", suffix='.json', delete=False) as config_file:
        json.dump(sonata_config_new_report, config_file)

    yield config_file
    os.unlink(config_file.name)


@pytest.fixture
def sonata_config_file_disabled_report(sonata_config_new_report):

    sonata_config_new_report["reports"]["new_report"]["enabled"] = False

    with NamedTemporaryFile("w", suffix='.json', delete=False) as config_file:
        json.dump(sonata_config_new_report, config_file)

    yield config_file
    os.unlink(config_file.name)


@pytest.mark.slow
def test_report_config_error(sonata_config_file_err):
    with pytest.raises(Exception):
        n = Node(str(sonata_config_file_err.name))
        n.load_targets()
        n.create_cells()
        n.enable_reports()


@pytest.mark.slow
def test_report_disabled(sonata_config_file_disabled_report):
    n = Node(str(sonata_config_file_disabled_report.name))
    n.load_targets()
    n.create_cells()
    n.enable_reports()
    assert len(n.reports) == 0


def _read_sonata_report(report_file):
    import libsonata
    report = libsonata.ElementReportReader(report_file)
    pop_name = report.get_population_names()[0]
    node_ids = report[pop_name].get_node_ids()
    data = report[pop_name].get()
    return node_ids, data


def _create_tmpconfig_lfp(config_file):

    import json
    from tempfile import NamedTemporaryFile
    with open(config_file, 'r') as f:
        config = json.load(f)

    # Modify the necessary fields
    config["reports"] = config.get("reports", {})
    config["reports"]["summation_report"] = {
        "type": "summation",
        "cells": "Mosaic",
        "variable_name": "i_membrane,IClamp",
        "sections": "soma",
        "dt": 0.1,
        "start_time": 0.0,
        "end_time": 40.0
    }
    config["reports"]["synapse_report"] = {
        "type": "synapse",
        "cells": "Mosaic",
        "variable_name": "ProbAMPANMDA_EMS.g",
        "sections": "all",
        "dt": 0.1,
        "start_time": 0.0,
        "end_time": 40.0
    }

    # Get the directory of the original config file
    config_dir = Path(config_file).parent

    # Write the modified configuration to a temporary file
    tmp_file = NamedTemporaryFile(suffix=".json", delete=False, dir=config_dir, mode='w')
    json.dump(config, tmp_file, indent=4)
    tmp_file.close()

    return tmp_file


@pytest.mark.slow
def test_v5_sonata_reports():
    import numpy.testing as npt
    from neurodamus import Neurodamus

    config_file = str(SIM_DIR / "simulation_config_mini.json")
    output_dir = str(SIM_DIR / "output_reports")

    tmp_file = _create_tmpconfig_lfp(config_file)
    nd = Neurodamus(tmp_file.name, output_path=output_dir)
    nd.run()

    report_refs = {
        "soma_report.h5":
            [(10, 3, -64.92565), (128, 1, -60.309418), (333, 4, -39.864296)],
        "summation_report.h5":
            [(20, 2, 1.512462e-17), (60, 0, -2.9273459e-18), (283, 3, 3.2526065e-19)]
    }
    node_id_refs = [0, 1, 2, 3, 4]

    # Go through each report and compare the results
    for report_name, refs in report_refs.items():
        result_ids, result_data = _read_sonata_report(os.path.join(output_dir, report_name))
        assert result_ids == node_id_refs
        for row, col, ref in refs:
            npt.assert_allclose(result_data.data[row][col], ref)
