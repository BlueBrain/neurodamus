import os
import numpy.testing as npt
import numpy as np


def test_coreneuron_no_write_model(USECASE3):
    from libsonata import SpikeReader, ElementReportReader
    from neurodamus import Neurodamus
    from neurodamus.core.configuration import SimConfig
    nd = Neurodamus(
        str(USECASE3 / "simulation_sonata_coreneuron.json"),
        keep_build=True,
        skip_write_model=True
    )
    nd.run()
    coreneuron_data = SimConfig.coreneuron_datadir
    assert not next(os.scandir(coreneuron_data), None), f"{coreneuron_data} should be empty."

    spikes_path = os.path.join(SimConfig.output_root, nd._run_conf.get("SpikesFile"))
    spikes_reader = SpikeReader(spikes_path)
    pop_A = spikes_reader["NodeA"]
    pop_B = spikes_reader["NodeB"]
    spike_dict = pop_A.get_dict()
    npt.assert_allclose(spike_dict["timestamps"][:10], np.array([0.2, 0.3, 0.3, 2.5, 3.4,
                                                                4.2, 5.5, 7., 7.4, 8.6]))
    npt.assert_allclose(spike_dict["node_ids"][:10], np.array([0, 1, 2, 0, 1, 2, 0, 0, 1, 2]))
    assert not pop_B.get()

    soma_reader = ElementReportReader(SimConfig.reports.get("soma_report").get('FileName'))
    soma_A = soma_reader["NodeA"]
    soma_B = soma_reader["NodeB"]
    data_A = soma_A.get(tstop=0.5)
    data_B = soma_B.get(tstop=0.5)
    npt.assert_allclose(data_A.data, np.array([[-75.], [-39.78627], [-14.380434], [15.3370695],
                                               [1.7240616], [-13.333434]]))
    npt.assert_allclose(data_B.data, np.array([[-75.], [-75.00682], [-75.010414], [-75.0118],
                                               [-75.01173], [-75.010635]]))
