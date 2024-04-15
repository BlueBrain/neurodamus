import pytest
import h5py
import os
import numpy as np
from pathlib import Path

SIM_DIR = Path(__file__).parent.parent.absolute() / "simulations" / "stimulus_injection"

# Read the soma report and return a list with the voltages
def _read_sonata_soma_report(report_name):
    import libsonata
    report = libsonata.SomaReportReader(report_name)
    pop_name = report.get_population_names()[0]
    ids = report[pop_name].get_node_ids()
    data = report[pop_name].get(node_ids=[ids[0]])
    return numpy.array(data.data).flatten().tolist()

def test_current_injection_coreneuron():
    
    from neurodamus import Neurodamus
    from neurodamus.replay import SpikeManager

    config_file = str(SIM_DIR / "simulation_config_iclamp.json")
    os.chdir(SIM_DIR)
    nd = Neurodamus(config_file, disable_reports=False, simulator="CORENEURON",
                    output_path="output_coreneuron")
    nd.run()

    soma_report_path = os.path.join(nd._run_conf["OutputRoot"], "voltage.h5")
    voltage_vec_iclamp = _read_sonata_soma_report(soma_report_path)

    config_file = str(SIM_DIR / "simulation_config_membranecurrentsource.json")
    os.chdir(SIM_DIR)
    nd = Neurodamus(config_file, disable_reports=False, simulator="CORENEURON",
                    output_path="output_coreneuron")
    nd.run()

    soma_report_path = os.path.join(nd._run_conf["OutputRoot"], "voltage.h5")
    voltage_vec_membranecurrentsource = _read_sonata_soma_report(soma_report_path)

def test_conductance_injection_coreneuron():
    
    from neurodamus import Neurodamus
    from neurodamus.replay import SpikeManager

    config_file = str(SIM_DIR / "simulation_config_seclamp.json")
    os.chdir(SIM_DIR)
    nd = Neurodamus(config_file, disable_reports=False, simulator="CORENEURON",
                    output_path="output_coreneuron")
    nd.run()

    soma_report_path = os.path.join(nd._run_conf["OutputRoot"], "voltage.h5")
    voltage_vec_seclamp = _read_sonata_soma_report(soma_report_path)

    config_file = str(SIM_DIR / "simulation_config_conductancesource.json")
    os.chdir(SIM_DIR)
    nd = Neurodamus(config_file, disable_reports=False, simulator="CORENEURON",
                    output_path="output_coreneuron")
    nd.run()

    soma_report_path = os.path.join(nd._run_conf["OutputRoot"], "voltage.h5")
    voltage_vec_conductancesource = _read_sonata_soma_report(soma_report_path)

    
