# @file gj_user_corrections.py
# @brief Script for loading user corrections on gap junction connectivity
# @author Oren Amsalem, Weina Ji
# @date 2024-09-09


import logging
import numpy as np
import pickle
from neurodamus.core import MPI
from .core import NeurodamusCore as Nd
from .core.configuration import SimConfig

non_stochastic_mechs = ['NaTs2_t', 'SKv3_1', 'Nap_Et2', 'Ih', 'Im', 'KdShu2007',
                        'K_Pst', 'K_Tst', 'Ca', 'SK_E2', 'Ca_LVAst', 'CaDynamics_E2',
                        'NaTa_t', 'CaDynamics_DC0', 'Ca_HVA2', 'NaTg'] + \
                       ['TC_cad', 'TC_ih_Bud97', 'TC_Nap_Et2', 'TC_iA', 'TC_iL', 'TC_HH',
                        'TC_iT_Des98'] + \
                       ['kdrb', 'na3', 'kap', 'hd', 'can', 'cal', 'cat', 'cagk', 'kca',
                        'cacum', 'kdb', 'kmb', 'kad', 'nax', 'cacumb']

stochastic_mechs = ['StochKv', 'StochKv2', 'StochKv3']


def load_user_modifications(gj_manager):
    node_manager = gj_manager.cell_manager
    settings = SimConfig.beta_features
    gjc = settings.get('gjc')

    # deterministic_StochKv
    if settings.get('determanisitc_stoch'):
        logging.info("Set deterministic = 1 for StochKv")
        _determanisitc_stoch(node_manager)

    # update gap conductance
    if settings.get('procedure_type') in ['validation_sim', 'find_holding_current']:
        process_gap_conns = _update_conductance(gjc, gj_manager)
        all_ranks_total = MPI.allreduce(process_gap_conns, MPI.SUM)
        logging.info(f"Set GJc = {gjc} for {int(all_ranks_total)} gap synapses")

    # remove active channels
    remove_channels = settings.get('remove_channels')
    Mechanisims = []
    if remove_channels == 'all':
        Mechanisims = non_stochastic_mechs + stochastic_mechs
    if remove_channels == 'only_stoch':
        Mechanisims = stochastic_mechs
    if remove_channels == 'only_non_stoch':
        Mechanisims = non_stochastic_mechs
    if remove_channels:
        logging.info("Removing channels type = " + remove_channels)
        _perform_remove_channels(node_manager, Mechanisims)

    if 'special_tag' in settings:
        gjc = 0.1
        logging.info("****\n**** special_tag ****\n****")

    # load g_pas
    if filename := settings.get('load_g_pas_file'):
        processed_cells = _update_gpas(node_manager, filename, gjc,
                                       settings.get("correction_iteration_load", -1))
        all_ranks_total = int(MPI.allreduce(processed_cells, MPI.SUM))
        logging.info(f"Update g_pas to fit {gjc} - file {filename} for {all_ranks_total} cells")

    # load current clamps
    holding_ic_per_gid = {}
    if filename := settings.get('manual_MEComboInfo_file'):
        # Oren's note: If I manually injecting different holding current for each cell,
        # I will inject the current - the holding the emMEComboInfoFile
        if settings.get('procedure_type') == 'find_holding_current':
            raise Exception("not make any sense")
        holding_ic_per_gid = _load_holding_ic(node_manager, filename, gjc=gjc)
        all_ranks_total = int(MPI.allreduce(len(holding_ic_per_gid), MPI.SUM))
        logging.info(f"Load holding_ic from manual_MEComboInfoFile {filename} "
                     f"for {all_ranks_total} cells")

    SEClamp_current_per_gid = {}
    if settings.get('procedure_type') == 'find_holding_current' \
            and isinstance(settings.get('vc_amp'), str):
        logging.info("Find_holding_current - voltage file - {settings['vc_amp']}")
        if not settings.get('disable_holding'):
            logging.warning("Doing V_clamp and not disable holding!")

        SEClamp_current_per_gid = _find_holding_current(node_manager, settings.get('vc_amp'))
        _save_seclamps(SEClamp_current_per_gid, output_dir=SimConfig.output_root)

    return holding_ic_per_gid, SEClamp_current_per_gid


def _update_conductance(gjc, gj_manager):
    n_conn = 0
    for conn in gj_manager.all_connections():
        conn.update_conductance(gjc)
        n_conn += 1
    return n_conn


def _determanisitc_stoch(node_manager):
    for cell in node_manager.cells:
        for sec in cell._cellref.all:
            if 'StochKv3' in dir(sec(.5)): sec.deterministic_StochKv3 = 1
            if 'StochKv2' in dir(sec(.5)): sec.deterministic_StochKv2 = 1
            if 'StochKv1' in dir(sec(.5)): sec.deterministic_StochKv1 = 1


def _perform_remove_channels(node_manager, Mechanisms: list):
    for cell in node_manager.cells:
        for sec in cell._cellref.all:
            for mec in Mechanisms:
                if mec in dir(sec(.5)): sec.uninsert(mec)


def _update_gpas(node_manager, filename, gjc, correction_iteration_load):
    import h5py
    processed_cells = 0
    g_pas_file = h5py.File(filename, 'r')
    raw_cell_gids = node_manager.local_nodes.raw_gids()
    offset = node_manager.local_nodes.offset
    for agid in g_pas_file[f'g_pas/{gjc}/']:
        gid = int(agid[1:])
        if gid in raw_cell_gids:  # if the node has a part of the cell
            cell = node_manager.getCell(gid+offset)
            processed_cells += 1
            for sec in cell.all:
                for seg in sec:
                    seg.g_pas = g_pas_file[f'g_pas/{gjc}/{agid}'][str(seg)[str(seg).index('.')+1:]][correction_iteration_load] # noqa
    g_pas_file.close()
    return processed_cells


def _load_holding_ic(node_manager, filename, gjc):
    import h5py
    holding_ic_per_gid = {}
    holding_per_gid = h5py.File(filename, 'r')
    raw_cell_gids = node_manager.local_nodes.raw_gids()
    offset = node_manager.local_nodes.offset
    for agid in holding_per_gid['holding_per_gid'][str(gjc)]:
        gid = int(agid[1:])
        if gid in raw_cell_gids:
            holding_ic_per_gid[gid] = Nd.h.IClamp(0.5, sec=node_manager.getCell(gid+offset).soma[0])
            holding_ic_per_gid[gid].dur = 9e9
            holding_ic_per_gid[gid].amp = holding_per_gid['holding_per_gid'][str(gjc)][agid][()]
    return holding_ic_per_gid


def _find_holding_current(node_manager, filename):
    import h5py
    v_per_gid = h5py.File(filename, 'r')  # load v_per_gid
    SEClmap_per_gid = {}
    SEClamp_current_per_gid = {}
    raw_cell_gids = node_manager.local_nodes.raw_gids()
    offset = node_manager.local_nodes.offset
    for agid in v_per_gid['v_per_gid']:
        gid = int(agid[1:])
        if gid in raw_cell_gids:
            SEClmap_per_gid[gid] = Nd.h.SEClamp(0.5, sec=node_manager.getCell(gid+offset).soma[0])
            SEClmap_per_gid[gid].dur1 = 9e9
            SEClmap_per_gid[gid].amp1 = float(v_per_gid['v_per_gid'][agid][()])
            SEClmap_per_gid[gid].rs  = 0.0000001
            SEClamp_current_per_gid[gid] = Nd.h.Vector()
            SEClamp_current_per_gid[gid].record(SEClmap_per_gid[gid]._ref_i)
    v_per_gid.close()
    return SEClamp_current_per_gid


def _save_seclamps(SEClamp_current_per_gid, output_dir):
    logging.info('Saving SEClamp Data')
    SEClamp_current_per_gid_a = {}
    for gid in SEClamp_current_per_gid:
        SEClamp_current_per_gid_a[gid] = np.array(SEClamp_current_per_gid[gid])
    pickle.dump(SEClamp_current_per_gid_a,
                open(f'{output_dir}/data_for_host_{MPI.rank}.p', 'wb'))
