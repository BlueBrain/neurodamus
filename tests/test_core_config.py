import os
import struct

from neurodamus.core.coreneuron_configuration import CoreConfig


def test_write_report_config(tmpdir):
    CoreConfig.outpath = str(tmpdir.join("outpath"))
    CoreConfig.datpath = str(tmpdir.join("datpath"))
    # Define your test parameters
    report_name = "soma"
    target_name = "Mosaic"
    report_type = "compartment"
    report_variable = "v"
    unit = "mV"
    report_format = "SONATA"
    target_type = 1
    dt = 0.1
    start_time = 0.0
    end_time = 10.0
    gids = [1, 2, 3]
    buffer_size = 8

    report_count = 1
    population_count = 20
    population_name = "default"
    population_offset = 1000
    spikes_name = "spikes.h5"
    # Call the methods with the test parameters
    CoreConfig.write_report_count(report_count)
    CoreConfig.write_report_config(report_name, target_name, report_type, report_variable, unit,
                                    report_format, target_type, dt, start_time, end_time, gids,
                                    buffer_size)
    CoreConfig.write_population_count(population_count)
    CoreConfig.write_spike_population(population_name, population_offset)
    CoreConfig.write_spike_filename(spikes_name)

    # Check that the report configuration file was created
    report_config_file = os.path.join(CoreConfig.output_root, CoreConfig.report_config_file)
    assert os.path.exists(report_config_file)

    # Check the content of the report configuration file
    with open(report_config_file, "rb") as fp:
        lines = fp.readlines()
        assert lines[0].strip().decode() == f"{report_count}"
        parts = lines[1].strip().decode().split()
        assert parts[0] == report_name
        assert parts[1] == target_name
        assert parts[2] == report_type
        assert parts[3] == report_variable
        assert parts[4] == unit
        assert parts[5] == report_format
        assert int(parts[6]) == target_type
        assert float(parts[7]) == dt
        assert float(parts[8]) == start_time
        assert float(parts[9]) == end_time
        assert int(parts[10]) == len(gids)
        assert int(parts[11]) == buffer_size
        # Read the binary data and unpack it into a list of integers
        gids_from_file = struct.unpack(f'{len(gids)}i', lines[2].strip())
        assert gids_from_file == tuple(gids), "GIDs from file do not match original GIDs"
        assert lines[3].strip().decode() == f"{population_count}"
        assert lines[4].strip().decode() == f"{population_name} {population_offset}"
        assert lines[5].strip().decode() == f"{spikes_name}"


def test_write_sim_config(tmpdir):
    CoreConfig.output_root = str(tmpdir.join("outpath"))
    CoreConfig.datadir = str(tmpdir.join("datpath"))
    cell_permute = 0
    tstop = 100
    dt = 0.1
    forwardskip = 0
    prcellgid = 0
    seed = 12345
    celsius = 34.0
    v_init = -65.0
    model_stats = True
    pattern = "file_pattern"
    enable_reports = 1
    report_conf = f"{CoreConfig.output_root}/{CoreConfig.report_config_file}"
    CoreConfig.write_sim_config(
        tstop,
        dt,
        forwardskip,
        prcellgid,
        celsius,
        v_init,
        pattern,
        seed,
        model_stats,
        enable_reports
    )
    # Check that the sim configuration file was created
    sim_config_file = os.path.join(CoreConfig.output_root, CoreConfig.sim_config_file)
    assert os.path.exists(sim_config_file)
    # Check the content of the simulation configuration file
    with open(sim_config_file, "r") as fp:
        lines = fp.readlines()
        assert lines[0].strip() == f"outpath='{os.path.abspath(CoreConfig.output_root)}'"
        assert lines[1].strip() == f"datpath='{os.path.abspath(CoreConfig.datadir)}'"
        assert lines[2].strip() == f"tstop={tstop}"
        assert lines[3].strip() == f"dt={dt}"
        assert lines[4].strip() == f"forwardskip={forwardskip}"
        assert lines[5].strip() == f"prcellgid={prcellgid}"
        assert lines[6].strip() == f"celsius={celsius}"
        assert lines[7].strip() == f"voltage={v_init}"
        assert lines[8].strip() == f"cell-permute={cell_permute}"
        assert lines[9].strip() == f"pattern='{pattern}'"
        assert lines[10].strip() == f"seed={seed}"
        assert lines[11].strip() == "'model-stats'"
        assert lines[12].strip() == f"report-conf='{report_conf}'"
        assert lines[13].strip() == "mpi=true"
