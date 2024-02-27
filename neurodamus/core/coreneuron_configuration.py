import os
import logging
from pathlib import Path
from ._utils import run_only_rank0
from . import NeurodamusCore as Nd


class CompartmentMapping:
    """ Interface to register section segment mapping with NEURON.
    """
    def __init__(self, cell_distributor):
        self.cell_distributor = cell_distributor
        self.pc = Nd.ParallelContext()

    def get_section_index(self, cell, section):
        """
        Calculate the global index of a given section within its cell.
        :param cell: The cell instance containing the section of interest
        :param section: The specific section for which the index is required
        :return: The global index of the section, applicable for neuron mapping
        """
        section_name = str(section)
        base_offset = 0
        section_index = 0
        if "soma" in section_name:
            pass  # base_offset is 0
        elif "axon" in section_name:
            base_offset = cell.nSecSoma
        elif "dend" in section_name:
            base_offset = cell.nSecSoma + cell.nSecAxonalOrig
        elif "apic" in section_name:
            base_offset = cell.nSecSoma + cell.nSecAxonalOrig + cell.nSecBasal
        elif "ais" in section_name:
            base_offset = cell.nSecSoma + cell.nSecAxonalOrig + cell.nSecBasal + cell.nSecApical
        elif "node" in section_name:
            base_offset = cell.nSecSoma + cell.nSecAxonalOrig + cell.nSecBasal + cell.nSecApical \
                        + getattr(cell, 'nSecLastAIS', 0)
        elif "myelin" in section_name:
            base_offset = cell.nSecSoma + cell.nSecAxonalOrig + cell.nSecBasal + cell.nSecApical \
                        + getattr(cell, 'nSecLastAIS', 0) + getattr(cell, 'nSecNodal', 0)

        # Extract the index from the section name
        try:
            index_str = section_name.split('[')[-1].rstrip(']')
            section_index = int(index_str)
        except ValueError:
            logging.warning(f"Error while getting section index {index_str}")

        return int(base_offset + section_index)

    def create_section_vectors(self, section_id, section, secvec, segvec):
        num_segments = 0
        for seg in section:
            secvec.append(section_id)
            segvec.append(seg.node_index())
            num_segments += 1

        return num_segments

    def process_section(self, cell, sections, num_electrodes, all_lfp_factors, section_offset):
        secvec, segvec, lfp_factors = Nd.Vector(), Nd.Vector(), Nd.Vector()
        num_segments = 0
        section_attr = getattr(cell, sections[0], None)
        if section_attr:
            for sec in section_attr:
                section_index = self.get_section_index(cell, sec)
                num_segments += self.create_section_vectors(section_index, sec, secvec, segvec)

        if num_electrodes > 0 and all_lfp_factors.size() > 0 and num_segments > 0:
            start_idx = section_offset * num_electrodes
            end_idx = (section_offset + num_segments) * num_electrodes - 1
            lfp_factors.copy(all_lfp_factors, start_idx, end_idx)

        self.pc.nrnbbcore_register_mapping(cell.gid, sections[1], secvec, segvec,
                                           lfp_factors, num_electrodes)
        return num_segments

    def register_mapping(self):
        sections = [
            ('somatic', 'soma'),
            ('axonal', 'axon'),
            ('basal', 'dend'),
            ('apical', 'apic'),
            ('AIS', 'ais'),
            ('nodal', 'node'),
            ('myelinated', 'myelin')
        ]
        gidvec = self.cell_distributor.getGidListForProcessor()
        for activegid in gidvec:
            cellref = self.cell_distributor.getCell(activegid)
            all_lfp_factors = Nd.Vector()
            num_electrodes = 0
            lfp_manager = getattr(self.cell_distributor, "_lfp_manager", None)
            if lfp_manager:
                pop_info = self.cell_distributor.getPopulationInfo(activegid)
                num_electrodes = lfp_manager.get_number_electrodes(activegid, pop_info)
                all_lfp_factors = lfp_manager.read_lfp_factors(activegid, pop_info)

            section_offset = 0
            for section in sections:
                processed_segments = self.process_section(cellref, section, num_electrodes,
                                                          all_lfp_factors, section_offset)
                section_offset += processed_segments


class _CoreNEURONConfig(object):
    """
    The CoreConfig class is responsible for managing the configuration of the CoreNEURON simulation.
    It writes the simulation / report configurations and calls the CoreNEURON solver.
    """
    sim_config_file = "sim.conf"
    report_config_file = "report.conf"
    output_root = "output"
    datadir = f"{output_root}/coreneuron_input"
    default_cell_permute = 0
    artificial_cell_object = None

    # Instantiates the artificial cell object for CoreNEURON
    # This needs to happen only when CoreNEURON simulation is enabled
    def instantiate_artificial_cell(self):
        self.artificial_cell_object = Nd.CoreNEURONArtificialCell()

    @run_only_rank0
    def write_report_config(
            self, report_name, target_name, report_type, report_variable,
            unit, report_format, target_type, dt, start_time, end_time, gids,
            buffer_size=8):
        import struct
        num_gids = len(gids)
        logging.info(f"Adding report {report_name} for CoreNEURON with {num_gids} gids")
        report_conf = Path(self.output_root) / self.report_config_file
        report_conf.parent.mkdir(parents=True, exist_ok=True)
        with report_conf.open("ab") as fp:
            # Write the formatted string to the file
            fp.write(("%s %s %s %s %s %s %d %lf %lf %lf %d %d\n" % (
                report_name,
                target_name,
                report_type,
                report_variable,
                unit,
                report_format,
                target_type,
                dt,
                start_time,
                end_time,
                num_gids,
                buffer_size
            )).encode())
            # Write the array of integers to the file in binary format
            fp.write(struct.pack(f'{num_gids}i', *gids))
            fp.write(b'\n')

    @run_only_rank0
    def write_sim_config(
            self, tstop, dt, forwardskip, prcellgid, celsius, v_init,
            pattern=None, seed=None, model_stats=False, enable_reports=True):
        simconf = Path(self.output_root) / self.sim_config_file
        logging.info(f"Writing sim config file: {simconf}")
        simconf.parent.mkdir(parents=True, exist_ok=True)
        with simconf.open("w") as fp:
            fp.write(f"outpath='{os.path.abspath(self.output_root)}'\n")
            fp.write(f"datpath='{os.path.abspath(self.datadir)}'\n")
            fp.write(f"tstop={tstop}\n")
            fp.write(f"dt={dt}\n")
            fp.write(f"forwardskip={forwardskip}\n")
            fp.write(f"prcellgid={int(prcellgid)}\n")
            fp.write(f"celsius={celsius}\n")
            fp.write(f"voltage={v_init}\n")
            fp.write(f"cell-permute={int(self.default_cell_permute)}\n")
            if pattern:
                fp.write(f"pattern='{pattern}'\n")
            if seed:
                fp.write(f"seed={int(seed)}\n")
            if model_stats:
                fp.write("'model-stats'\n")
            if enable_reports:
                fp.write(f"report-conf='{self.output_root}/{self.report_config_file}'\n")
            fp.write("mpi=true\n")

    @run_only_rank0
    def write_report_count(self, count, mode="w"):
        report_config = Path(self.output_root) / self.report_config_file
        report_config.parent.mkdir(parents=True, exist_ok=True)
        with report_config.open(mode) as fp:
            fp.write(f"{count}\n")

    @run_only_rank0
    def write_population_count(self, count):
        self.write_report_count(count, mode="a")

    @run_only_rank0
    def write_spike_population(self, population_name, population_offset=None):
        report_config = Path(self.output_root) / self.report_config_file
        report_config.parent.mkdir(parents=True, exist_ok=True)
        with report_config.open("a") as fp:
            fp.write(population_name)
            if population_offset is not None:
                fp.write(f" {int(population_offset)}")
            fp.write("\n")

    @run_only_rank0
    def write_spike_filename(self, filename):
        report_config = Path(self.output_root) / self.report_config_file
        report_config.parent.mkdir(parents=True, exist_ok=True)
        with report_config.open("a") as fp:
            fp.write(filename)
            fp.write("\n")

    def psolve_core(self, save_path=None, restore_path=None):
        from neuron import coreneuron
        from . import NeurodamusCore as Nd

        Nd.cvode.cache_efficient(1)
        coreneuron.enable = True
        coreneuron.file_mode = True
        coreneuron.sim_config = f"{self.output_root}/{self.sim_config_file}"
        if save_path:
            coreneuron.save_path = save_path
        if restore_path:
            coreneuron.restore_path = restore_path
        # Model is already written to disk by calling pc.nrncore_write()
        coreneuron.skip_write_model_to_disk = True
        coreneuron.model_path = f"{self.datadir}"
        Nd.pc.psolve(Nd.tstop)


# Singleton
CoreConfig = _CoreNEURONConfig()
