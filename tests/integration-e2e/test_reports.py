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


@pytest.mark.slow
def test_v5_sonata_reports():
    import numpy.testing as npt
    from neurodamus import Neurodamus

    config_file = str(SIM_DIR / "simulation_config.json")
    output_dir = str(SIM_DIR / "output")

    nd = Neurodamus(config_file, output_path=output_dir)
    nd.run()

    report_refs = {
        "soma_report.h5":
            [(10, 20, -64.448616), (128, 10, -57.649437), (333, 5, -59.72419)],
        "summation_report.h5":
            [(20, 10, 6.16911e-17), (60, 26, 4.864002e-17), (283, 15, 9.540979e-18)],
        "synapse_report.h5":
            [(14, 3114, 0.00015797482), (151, 8297, 7.76133e-05), (392, 49, 6.0961706e-06)]
    }
    node_id_refs = [62797, 62945, 63256, 63622, 63698, 64163, 64233, 64665, 64787, 64861]

    # Go through each report and compare the results
    for report_name, refs in report_refs.items():
        result_ids, result_data = _read_sonata_report(os.path.join(output_dir, report_name))
        assert result_ids[:10] == node_id_refs
        for row, col, ref in refs:
            npt.assert_allclose(result_data.data[row][col], ref)
