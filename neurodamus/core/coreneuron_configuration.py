import os

from . import SimConfig
from ._utils import run_only_rank0

class _CoreConfig(object):
    """
    The CoreConfig class is responsible for managing the configuration of the CoreNEURON simulation.
    It writes the simulation / report configurations and calls the CoreNEURON solver.
    """
    def __init__(self, output_root, sim_config_file="sim.conf", report_config_file="report.conf"):
        self.output_root = output_root
        self.sim_config_file = sim_config_file
        self.report_config_file = report_config_file
        self.default_cell_permute = 0

    @run_only_rank0
    def write_report_config(
            self, report_name, target_name, report_type, report_variable,
            unit, report_format, target_type, dt, start_time, end_time, gids,
            buffer_size=8):
        import struct
        num_gids = len(gids)
        print(f"Adding report {report_name} for CoreNEURON with {num_gids} gids")
        report_conf = f"{self.output_root}/{self.report_config_file}"
        with open(report_conf, "ab") as fp:
            # Write the formatted string to the file
            fp.write((f"{report_name} {target_name} {report_type} "
                    f"{report_variable} {unit} {report_format} "
                    f"{int(target_type)} {float(dt)} {float(start_time)} "
                    f"{float(end_time)} {num_gids} {buffer_size}\n").encode())

            # Write the array of integers to the file in binary format
            fp.write(struct.pack(f'{num_gids}i', *gids))
            fp.write(b'\n')

    @run_only_rank0
    def write_sim_config(
            self, outpath, datpath, tstop, dt, forwardskip, prcellgid,
            pattern=None, seed=None, model_stats=False, enable_reports=True):
        simconf = f"{self.output_root}/{self.sim_config_file}"
        print(f"Writing sim config file: {simconf}")
        celsius = getattr(SimConfig, 'celsius', 34.0)
        v_init = getattr(SimConfig, 'v_init', -65.0)
        with open(simconf, "w") as fp:
            fp.write(f"outpath='{os.path.abspath(outpath)}'\n")
            fp.write(f"datpath='{os.path.abspath(datpath)}'\n")
            fp.write(f"tstop={tstop}\n")
            fp.write(f"dt={dt}\n")
            fp.write(f"forwardskip={forwardskip}\n")
            fp.write(f"prcellgid={prcellgid}\n")
            fp.write(f"celsius={celsius}\n")
            fp.write(f"voltage={v_init}\n")
            fp.write(f"cell-permute={self.default_cell_permute}\n")
            if pattern:
                fp.write(f"pattern={pattern}\n")
            if seed:
                fp.write(f"seed={int(seed)}\n")
            if model_stats:
                fp.write("'model-stats'\n")
            if enable_reports:
                fp.write(f"report-conf='{self.output_root}/{self.report_config_file}'\n")
            fp.write("mpi=true\n")

    @run_only_rank0
    def write_report_count(self, count):
        report_config = f"{self.output_root}/{self.report_config_file}"
        with open(report_config, "a") as fp:
            fp.write(f"{count}\n")

    @run_only_rank0
    def write_population_count(self, count):
        self.write_report_count(count)

    @run_only_rank0
    def write_spike_population(self, population_name, population_offset=None):
        report_config = f"{self.output_root}/{self.report_config_file}"
        with open(report_config, "a") as fp:
            fp.write(population_name)
            if population_offset is not None:
                fp.write(f" {int(population_offset)}")
            fp.write("\n")

    @run_only_rank0
    def write_spike_filename(self, filename):
        report_config = f"{self.output_root}/{self.report_config_file}"
        with open(report_config, "a") as fp:
            fp.write(filename)
            fp.write("\n")

    def psolve_core(self):
        from neuron import h
        h.CVode().cache_efficient(1)
        from neuron import coreneuron
        from . import NeurodamusCore as Nd
        coreneuron.enable = True
        coreneuron.sim_config = f"{self.output_root}/{self.sim_config_file}"
        coreneuron.save = getattr(SimConfig, "save", None)
        coreneuron.restore = getattr(SimConfig, "save", None)
        coreneuron.only_simulate = True
        Nd.pc.psolve(h.tstop)

# Singleton
CoreConfig = _CoreConfig()
