"""
Collection of Cell Readers from different sources (Pure HDF5, SynTool...)
"""
from __future__ import absolute_import
import logging
import numpy as np
from collections import defaultdict
from os import path as ospath
from ..core import NeurodamusCore as Nd
from ..core.configuration import ConfigurationError
from ..metype import METypeManager, METypeItem
from ..target_manager import TargetSpec
from ..utils import compat
from ..utils.logging import log_verbose


class CellReaderError(Exception):
    pass


def _ncs_get_total(ncs_f):
    # first lines might be comments. Skip '#'
    for tstr in ncs_f:
        if not tstr.strip().startswith("#"):
            break
    # should have "Cells x"
    try:
        total_circuit_cells = int(tstr.strip().split()[1])
    except IndexError:
        raise CellReaderError("NCS file contains invalid entry: " + tstr)
    return total_circuit_cells


def _ncs_get_cells(ncs_f):
    ncs_f.readline()  # skip the '{'

    for cell_i, line in enumerate(ncs_f):
        line = line.strip()
        if line == "}":
            break
        parts = line.split()
        assert len(parts) >= 5, "Error in ncs line " + line
        _gid = int(parts[0][1:])
        metype = parts[4]
        yield cell_i, _gid, metype


def split_round_robin(all_gids, stride=1, stride_offset=0, total_cells=None):
    """ Splits a numpy ndarray[uint32] round-robin.
    If the array is None generates new arrays based on the nr of total cells
    """
    if all_gids is not None:
        gidvec = all_gids[stride_offset::stride] if stride > 1 else all_gids
        gidvec.sort()
    else:
        assert total_cells, "split_round_robin: total_cells required without gids"
        cell_i = stride_offset + 1  # gids start from 1
        gidvec = np.arange(cell_i, total_cells + 1, stride, dtype="uint32")
    return gidvec


def load_ncs(circuit_conf, all_gids, stride=1, stride_offset=0):
    """ Obtain the gids and the metypes for cells in the base circuit.

    Args:
        circuit_conf: the Run secgion from the configuration
        all_gids: The cells ids to be loaded. If it's None then all the cells shall be loaded
        stride: If distribution is desired stride can be set to a value > 1
        stride_offset: When using distribution, the offset to be read within the stride
    Returns:
        A tuple of (gids, metypes, total_ncs_cells)
    """
    gids = compat.Vector("I")
    gid2mefile = {}
    ncs_path = ospath.join(circuit_conf.nrnPath, "start.ncs")

    with open(ncs_path, "r") as ncs_f:
        total_ncs_cells = _ncs_get_total(ncs_f)
        if all_gids is None:
            for cellIndex, gid, metype in _ncs_get_cells(ncs_f):
                if cellIndex % stride == stride_offset:
                    gids.append(gid)
                    gid2mefile[gid] = metype
        else:
            # Index desired cells
            gid2mefile = {int(gid): None for i, gid in enumerate(all_gids)
                          if i % stride == stride_offset}
            gids.extend(gid2mefile.keys())
            assigned_metypes = 0
            for cellIndex, gid, metype in _ncs_get_cells(ncs_f):
                if gid in gid2mefile:
                    gid2mefile[gid] = metype
                    assigned_metypes += 1
            if assigned_metypes < len(gid2mefile):
                logging.error("start.ncs: found info only for %d cells (out of %d)",
                              assigned_metypes, len(all_gids))
                raise CellReaderError("Target contains invalid circuit cells")
    return gids, gid2mefile, total_ncs_cells


def load_mvd3(circuit_conf, all_gids, stride=1, stride_offset=0):
    """Load cells from MVD3, required for v6 circuits
       reuse load_nodes with mvdtool by default
       if py-mvdtool not installed, use the old h5py loader
    """
    try:
        import mvdtool  # noqa: F401
    except ImportError:
        logging.warning("Cannot import mvdtool to load mvd3, will load with h5py")
        return _load_mvd3_h5py(circuit_conf, all_gids, stride, stride_offset)

    return load_nodes(circuit_conf, all_gids, stride, stride_offset)


def _load_mvd3_h5py(circuit_conf, all_gids, stride=1, stride_offset=0):
    """Load cells from MVD3 using h5py
    """
    import h5py  # Can be heavy so loaded on demand
    pth = ospath.join(circuit_conf.CircuitPath, "circuit.mvd3")
    mvd = h5py.File(pth, 'r')

    mecombo_ds = mvd["/cells/properties/me_combo"]
    total_mvd_cells = len(mecombo_ds)

    gidvec = split_round_robin(all_gids, stride, stride_offset, total_mvd_cells)

    if not len(gidvec):
        # Not enough cells to give this rank a few
        return compat.Vector('I'), METypeManager(), total_mvd_cells

    # Indexes are 0-based, and cant be numpy
    indexes = compat.Vector("I", gidvec - 1)

    morph_ids = mvd["/cells/properties/morphology"][indexes]
    combo_ids = mvd["/cells/properties/me_combo"][indexes]
    morpho_ds = mvd["/library/morphology"]
    morpho_names = [str(morpho_ds[i]) for i in morph_ids]
    combo_ds = mvd["/library/me_combo"]
    combo_names = [str(combo_ds[i]) for i in combo_ids]

    # We require gidvec as compat.Vector
    gidvec = compat.Vector("I", gidvec)

    # now we can take the combo file and get the emodel + additional info
    combo_file = circuit_conf.MEComboInfoFile
    me_manager = load_combo_metypes(combo_file, gidvec, combo_names, morpho_names)

    return gidvec, me_manager, total_mvd_cells


def load_nodes(circuit_conf, all_gids, stride=1, stride_offset=0, *, has_extra_data=False):
    """Load cells from SONATA or MVD3 file
    """
    import mvdtool
    pth = circuit_conf.CellLibraryFile
    is_mvd = pth.endswith('.mvd3')

    if not ospath.isfile(pth):
        pth = ospath.join(circuit_conf.CircuitPath, pth)
    if not ospath.isfile(pth):
        raise ConfigurationError("Could not find Nodes: " + circuit_conf.CellLibraryFile)

    node_population = TargetSpec(circuit_conf.CircuitTarget).population
    node_reader = mvdtool.open(pth, node_population or "")
    combo_file = circuit_conf.MEComboInfoFile

    if is_mvd:
        if not combo_file:
            logging.warning("Missing BlueConfig field 'MEComboInfoFile' which has gid:mtype:emodel")
        else:
            node_reader.open_combo_tsv(combo_file)

    total_cells = len(node_reader)
    gidvec = split_round_robin(all_gids, stride, stride_offset, total_cells)

    if not len(gidvec):
        # Not enough cells to give this rank a few
        return gidvec, METypeManager(), total_cells

    indexes = gidvec - 1  # MVDtool requires 0-indexed ids.
    if len(indexes) < 10:  # Ensure array is not too small (pybind11 #1392)
        indexes = indexes.tolist()

    morpho_names = node_reader.morphologies(indexes)
    emodels = node_reader.emodels(indexes) \
        if not is_mvd or combo_file else None  # Rare but we may not need emodels (ngv)
    exc_mini_freqs = node_reader.exc_mini_frequencies(indexes) \
        if node_reader.hasMiniFrequencies() else None
    inh_mini_freqs = node_reader.inh_mini_frequencies(indexes) \
        if node_reader.hasMiniFrequencies() else None
    threshold_currents = node_reader.threshold_currents(indexes) \
        if node_reader.hasCurrents() else None
    holding_currents = node_reader.holding_currents(indexes) \
        if node_reader.hasCurrents() else None
    positions = node_reader.positions(indexes)
    rotations = node_reader.rotations(indexes) if node_reader.rotated else None
    # For Sonata and new emodel hoc template, we may need additional attributes for building metype
    add_params_list = _getNeededAttributes(node_reader, circuit_conf.METypePath, emodels, indexes) \
        if not is_mvd and has_extra_data else None

    meinfo = METypeManager()
    meinfo.load_infoNP(gidvec, morpho_names, emodels, threshold_currents, holding_currents,
                       exc_mini_freqs, inh_mini_freqs, positions, rotations, add_params_list)

    return gidvec, meinfo, total_cells


def load_combo_metypes(combo_file, gidvec, combo_list, morph_list):
    """ Read file with mecombo info, retaining only those that are local to this node
    Args:
        combo_file: Path to the combo file to read metype info from
        gidvec: local gids to load info about
        combo_list: comboList Combos corresponding to local gids
        morph_list: morphList Morpholgies corresponding to local gids
    """
    if not combo_file:
        logging.error("Missing BlueConfig field 'MEComboInfoFile' which has gid:mtype:emodel.")
        raise ConfigurationError("MEComboInfoFile not specified")

    # Optimization: index combos
    combo_ids = defaultdict(list)
    for i, c in enumerate(combo_list):
        combo_ids[c].append(i)

    log_verbose("Loading emodel+additional info from Combo f %s", combo_file)
    f = open(combo_file)
    next(f)  # Skip Header

    me_manager = METypeManager()
    for tstr in f:
        vals = tstr.strip().split()
        if len(vals) not in (6, 8):
            wmsg = ("Could not parse line %s from MEComboInfoFile %s."
                    "Expecting 6 (hippocampus) or 8 (somatosensory) fields")
            logging.warning(wmsg, tstr, combo_file)

        # metypes may be reused by several cells
        # We create a single item and later assign to each matching gid
        meitem = METypeItem(*vals)
        for i in combo_ids[meitem.combo_name]:
            if morph_list[i] == meitem.morph_name:
                me_manager[int(gidvec[i])] = meitem

    # confirm that all gids have been matched.
    # Otherwise, print combo + morph info to help finding issues
    nerr = 0
    for gid in gidvec:
        gid = int(gid)
        if gid not in me_manager:
            logging.error("MEComboInfoFile: No MEInfo for gid %d", gid)
            nerr += 1
    if nerr > 0:
        logging.error("gidvec: " + str(gidvec))
        logging.error("Memap: " + str(me_manager.gids))
        raise CellReaderError("Errors found during processing of mecombo file. See log")

    return me_manager


def _getNeededAttributes(node_reader, etype_path, emodels, indexes):
    """
    Read additional attributes required by emodel templates global var <emodel>__NeededAttributes
    Args:
        node_reader: Sonata node reader
        etype_path: Location of emodel hoc templates
        emodels: Array of emodel names
        indexes: Array of corresponding indexes in the node file
    """
    add_params_list = []
    for idx, emodel in zip(indexes, emodels):
        Nd.h.load_file(ospath.join(etype_path, emodel) + ".hoc")  # hoc doesn't throw
        attr_names = getattr(Nd, emodel + "_NeededAttributes", None)  # format "attr1;attr2;attr3"
        vals = []
        if attr_names is not None:
            if not hasattr(node_reader, "getAttribute"):
                logging.error("The MVDTool API is old. Please load a newer version of neurodamus")
                raise ConfigurationError("Please load a newer version of neurodamus")
            vals = [node_reader.getAttribute(name, idx, 1)[0] for name in attr_names.split(";")]
        add_params_list.append(vals)
    return add_params_list
