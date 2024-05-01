import json
import numpy
import os
import pytest
from tempfile import NamedTemporaryFile


@pytest.fixture
def sonata_config_files(sonata_config, input_type):
    config_files = []
    for represents_physical_electrode in [True, False]:
        # Create a deep copy of sonata_config for each configuration to avoid conflicts
        config_copy = json.loads(json.dumps(sonata_config))

        stimulus_config = {
            "input_type": input_type,
            "delay": 5,
            "duration": 2100,
            "node_set": "l4pc",
            "represents_physical_electrode": represents_physical_electrode
        }

        if input_type == "current_clamp":
            stimulus_config.update({
                "module": "noise",
                "mean": 0.05,
                "variance": 0.01
            })
        elif input_type == "conductance":
            stimulus_config.update({
                "module": "ornstein_uhlenbeck",
                "mean": 0.05,
                "sigma": 0.01,
                "tau": 0.1
            })

        config_copy["inputs"] = {"Stimulus": stimulus_config}
        config_copy["reports"] = {
            "current": {
                "type": "summation",
                "cells": "l4pc",
                "variable_name": "i_membrane",
                "unit": "nA",
                "dt": 0.1,
                "start_time": 0.0,
                "end_time": 50.0
            },
            "voltage": {
                "type": "compartment",
                "cells": "l4pc",
                "variable_name": "v",
                "unit": "mV",
                "dt": 0.1,
                "start_time": 0.0,
                "end_time": 50.0
            }
        }

        with NamedTemporaryFile("w", suffix='.json', delete=False) as config_file:
            json.dump(config_copy, config_file)
            config_files.append(config_file.name)

    yield tuple(config_files)

    # Cleanup
    for config_file in config_files:
        os.unlink(config_file)


def _read_sonata_soma_report(report_name):
    import libsonata
    report = libsonata.SomaReportReader(report_name)
    pop_name = report.get_population_names()[0]
    ids = report[pop_name].get_node_ids()
    data = report[pop_name].get(node_ids=[ids[0]])
    return numpy.array(data.data).flatten()


def _run_simulation(config_file):
    import subprocess
    output_dir = "output_current_conductance"
    command = [
        "neurodamus",
        config_file,
        f"--output-path={output_dir}"
    ]
    config_dir = os.path.dirname(config_file)
    subprocess.run(command, cwd=config_dir, check=True)
    soma_report_path = os.path.join(config_dir, output_dir, "voltage.h5")
    return _read_sonata_soma_report(soma_report_path)


@pytest.mark.parametrize("input_type", [
    "current_clamp",
    "conductance",
])
def test_current_conductance_injection(sonata_config_files):
    """
    Test the consistency of voltage traces between original and new configurations
    (set by 'represents_physical_electrode': true/false)
    under different types of input (current clamp and conductance).
    """
    import numpy.testing as npt
    config_file_original, config_file_new = sonata_config_files

    voltage_vec_original = _run_simulation(config_file_original)
    voltage_vec_new = _run_simulation(config_file_new)

    npt.assert_equal(voltage_vec_original, voltage_vec_new)
