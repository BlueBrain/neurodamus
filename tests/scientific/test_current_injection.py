import os
import numpy
from pathlib import Path

SIM_DIR = Path(__file__).parent.parent.absolute()
SIM_DIR = SIM_DIR / "simulations" / "stimulus_injection"
# Read the soma report and return the voltages


def _read_sonata_soma_report(report_name):
    import libsonata
    report = libsonata.SomaReportReader(report_name)
    pop_name = report.get_population_names()[0]
    ids = report[pop_name].get_node_ids()
    data = report[pop_name].get(node_ids=[ids[0]])
    return numpy.array(data.data).flatten()


def test_current_injection_coreneuron():

    from neurodamus import Neurodamus

    config_file = str(SIM_DIR / "simulation_config_iclamp.json")
    os.chdir(SIM_DIR)
    nd = Neurodamus(config_file, disable_reports=False,
                    simulator="CORENEURON",
                    output_path="output_coreneuron_iclamp")

    nd.run()

    soma_report_path = os.path.join(nd._run_conf["OutputRoot"], "voltage.h5")
    voltage_vec_iclamp = _read_sonata_soma_report(soma_report_path)
    #
    config_file = str(SIM_DIR / "simulation_config_membranecurrentsource.json")
    nd2 = Neurodamus(config_file, disable_reports=False,
                     simulator="CORENEURON",
                     output_path="output_coreneuron_membranecurrentsource")
    nd2.run()

    soma_report_path = os.path.join(nd2._run_conf["OutputRoot"], "voltage.h5")
    voltage_vec_currentsource = _read_sonata_soma_report(soma_report_path)

    numpy.testing.assert_equal(voltage_vec_iclamp,
                               voltage_vec_currentsource)
