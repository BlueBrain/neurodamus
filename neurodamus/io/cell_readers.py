"""
Collection of Cell Readers from different sources (Pure HDF5, SynTool...)
"""
from __future__ import absolute_import
import logging
import numpy as np
import libsonata
from collections import defaultdict
from os import path as ospath

from ..core import NeurodamusCore as Nd
from ..core.configuration import ConfigurationError, SimConfig
from ..core import run_only_rank0
from ..metype import METypeManager, METypeItem
from ..utils import compat
from ..utils.logging import log_verbose

EMPTY_GIDVEC = np.empty(0, dtype="uint32")


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


def dry_run_distribution(gid_metype_bundle, stride=1, stride_offset=0, total_cells=None):
    """ Distribute gid in metype bundles for dry run.

    The principle is the following: all gids with the same metype
    have to be assigned to the same rank. This function receives
    a list of list of gids, each sublist containing gids of the same
    metype. The gid_metype_bundle list of lists is generated by the
    retrieve_unique_metype function. This function performs a
    round robin distribution of the inner lists, i.e. it returns
    a list of gids that are sequentially in the same metype.
    The return is a flattened numpy array of gids that shall be
    instantiated on the same rank.

    Example:
        gid_metype_bundle = [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10]]

        stride = 2
        stride_offset = 0
        return = [1, 2, 3, 7, 8, 9]

        stride = 2
        stride_offset = 1
        return = [4, 5, 6, 10]

    Args:
        gid_metype_bundle: list of lists of gids to be distributed
        mpi_size: MPI size
        mpi_rank: MPI rank
        total_cells: total number of cells in the circuit
    Returns:
        A numpy array of gids that are sequentially in the same metype
    """
    logging.info("Dry run distribution")

    if not gid_metype_bundle:
        return EMPTY_GIDVEC

    # if mpi_size is 1, return all gids flattened
    if stride == 1:
        return np.concatenate(gid_metype_bundle)
    else:
        groups = gid_metype_bundle[stride_offset::stride]
        return np.concatenate(groups) if groups else EMPTY_GIDVEC


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
    # NCS is historically under nrnPath which nowadays is a file path
    ncs_dir = circuit_conf.nrnPath
    if ospath.isfile(ncs_dir):
        ncs_dir = ospath.dirname(ncs_dir)
    ncs_path = ospath.join(ncs_dir, "start.ncs")

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

    return load_nodes_mvd3(circuit_conf, all_gids, stride, stride_offset)


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


def load_nodes_mvd3(circuit_conf, all_gids, stride=1, stride_offset=0):
    """Load cells from MVD3 file.
       node_population can be provided by load_sonata() and can be None. False to auto-detect
    """
    try:
        import mvdtool
    except ImportError:
        raise ConfigurationError("load_nodes: mvdtool is not available. Please install")
    pth = circuit_conf.CellLibraryFile
    assert pth.endswith('.mvd3'), "CellLibraryFile must be a mvd3 file"
    if not ospath.isfile(pth):
        pth = ospath.join(circuit_conf.CircuitPath, pth)
    if not ospath.isfile(pth):
        raise ConfigurationError("Could not find Nodes: " + circuit_conf.CellLibraryFile)

    node_reader = mvdtool.open(pth)
    combo_file = circuit_conf.MEComboInfoFile

    if not combo_file:
        logging.warning("Missing BlueConfig field 'MEComboInfoFile' which has gid:mtype:emodel")
    else:
        node_reader.open_combo_tsv(combo_file)

    total_cells = len(node_reader)

    meinfo = METypeManager()

    if SimConfig.dry_run:
        raise Exception("Dry run is not supported for MVD3")
    else:
        gidvec = split_round_robin(all_gids, stride, stride_offset, total_cells)

    if not len(gidvec):
        # Not enough cells to give this rank a few
        return gidvec, METypeManager(), total_cells

    fetch_MEinfo(node_reader, gidvec, combo_file, meinfo)

    return gidvec, meinfo, total_cells


def fetch_MEinfo(node_reader, gidvec, combo_file, meinfo):

    indexes = np.sort(gidvec - 1)  # MVDtool requires 0-indexed ids.
    gidvec = indexes + 1  # Return 1-indexed ids
    if len(indexes) < 10:  # Ensure array is not too small (pybind11 #1392)
        indexes = indexes.tolist()

    morpho_names = node_reader.morphologies(indexes)
    mtypes = node_reader.mtypes(indexes)
    emodels = node_reader.emodels(indexes) \
        if combo_file else None  # Rare but we may not need emodels (ngv)
    etypes = node_reader.etypes(indexes) \
        if combo_file else None
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

    meinfo.load_infoNP(gidvec, morpho_names, emodels, mtypes, etypes, threshold_currents,
                       holding_currents, exc_mini_freqs, inh_mini_freqs, positions, rotations)


def load_sonata(circuit_conf, all_gids, stride=1, stride_offset=0, *,
                node_population, load_dynamic_props=(), has_extra_data=False):
    """
    A reader supporting additional dynamic properties from Sonata files.
    """
    import libsonata
    node_file = circuit_conf.CellLibraryFile
    node_store = libsonata.NodeStorage(node_file)
    node_pop = node_store.open_population(node_population)
    attr_names = node_pop.attribute_names
    dynamics_attr_names = node_pop.dynamics_attribute_names

    def load_nodes_base_info():
        meinfos = METypeManager()
        total_cells = node_pop.size
        if SimConfig.dry_run:
            logging.info("Sonata dry run mode: looking for unique metype instances")
            gid_metype_bundle, meinfos.counts = _retrieve_unique_metypes(node_pop, all_gids)
            gidvec = dry_run_distribution(gid_metype_bundle, stride, stride_offset, total_cells)
        else:
            gidvec = split_round_robin(all_gids, stride, stride_offset, total_cells)

        if not len(gidvec):
            # Not enough cells to give this rank a few
            return gidvec, meinfos, total_cells

        node_sel = libsonata.Selection(gidvec - 1)  # 0-based node indices
        morpho_names = node_pop.get_attribute("morphology", node_sel)
        mtypes = node_pop.get_attribute("mtype", node_sel)
        try:
            etypes = node_pop.get_attribute("etype", node_sel)
        except libsonata.SonataError:
            logging.warning("etype not found in node population, setting to None")
            etypes = None
        _model_templates = node_pop.get_attribute("model_template", node_sel)
        emodel_templates = [emodel.removeprefix("hoc:") for emodel in _model_templates]
        if set(["exc_mini_frequency", "inh_mini_frequency"]).issubset(attr_names):
            exc_mini_freqs = node_pop.get_attribute("exc_mini_frequency", node_sel)
            inh_mini_freqs = node_pop.get_attribute("inh_mini_frequency", node_sel)
        else:
            exc_mini_freqs = None
            inh_mini_freqs = None
        if set(["threshold_current", "holding_current"]).issubset(dynamics_attr_names):
            threshold_currents = node_pop.get_dynamics_attribute("threshold_current", node_sel)
            holding_currents = node_pop.get_dynamics_attribute("holding_current", node_sel)
        else:
            threshold_currents = None
            holding_currents = None
        positions = np.array([node_pop.get_attribute("x", node_sel),
                              node_pop.get_attribute("y", node_sel),
                              node_pop.get_attribute("z", node_sel)]).T
        rotations = _get_rotations(node_pop, node_sel)

        # For Sonata and new emodel hoc template, we need additional attributes for building metype
        # TODO: validate it's really the emodel_templates var we should pass here, or etype
        add_params_list = None if not has_extra_data \
            else _getNeededAttributes(node_pop, circuit_conf.METypePath, emodel_templates, gidvec-1)

        meinfos.load_infoNP(gidvec, morpho_names, emodel_templates, mtypes, etypes,
                            threshold_currents, holding_currents,
                            exc_mini_freqs, inh_mini_freqs, positions, rotations,
                            add_params_list)
        return gidvec, meinfos, total_cells

    # If dynamic properties are not specified simply return early
    if not load_dynamic_props:
        return load_nodes_base_info()

    # Check properties exist, eventually removing prefix
    def validate_property(prop_name):
        if prop_name.startswith("@dynamics:"):
            actual_prop_name = prop_name[len("@dynamics:"):]  # remove prefix
            if actual_prop_name not in dynamics_attr_names:
                raise Exception('Required Dynamics property %s not present' % prop_name)
        elif prop_name not in attr_names:
            raise Exception('Required extra property %s not present' % prop_name)

    [validate_property(p) for p in load_dynamic_props]

    # All good. Lets start reading!
    gidvec, meinfos, fullsize = load_nodes_base_info()
    node_sel = libsonata.Selection(gidvec - 1)  # 0-based node indices

    for prop_name in load_dynamic_props:
        log_verbose("Loading extra property: %s ", prop_name)
        if prop_name.startswith("@dynamics:"):
            prop_name = prop_name[len("@dynamics:"):]
            prop_data = node_pop.get_dynamics_attribute(prop_name, node_sel)
        else:
            prop_data = node_pop.get_attribute(prop_name, node_sel)
        for gid, val in zip(gidvec, prop_data):
            meinfos[gid].extra_attrs[prop_name] = val

    return gidvec, meinfos, fullsize


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


def _getNeededAttributes(node_reader, etype_path, emodels, gidvec):
    """
    Read additional attributes required by emodel templates global var <emodel>__NeededAttributes
    Args:
        node_reader: libsonata node population
        etype_path: Location of emodel hoc templates
        emodels: Array of emodel names
        gidvec: Array of 0-based cell gids
    """
    add_params_list = []
    for gid, emodel in zip(gidvec, emodels):
        Nd.h.load_file(ospath.join(etype_path, emodel) + ".hoc")  # hoc doesn't throw
        attr_names = getattr(Nd, emodel + "_NeededAttributes", None)  # format "attr1;attr2;attr3"
        vals = []
        if attr_names is not None:
            vals = [node_reader.get_dynamics_attribute(name, gid) for name in attr_names.split(";")]
        add_params_list.append(vals)
    return add_params_list


def _get_rotations(node_reader, selection):
    """
    Read rotations attributes, returns a double vector of size [N][4] with the rotation quaternions
    in the order (x,y,z,w)
    Args:
        node_reader: libsonata node population
        selection: libsonata selection
    """
    attr_names = node_reader.attribute_names
    if set(["orientation_x", "orientation_y",
            "orientation_z", "orientation_w"]).issubset(attr_names):
        # Preferred way to present the rotation as quaternions
        return np.array([node_reader.get_attribute("orientation_x", selection),
                         node_reader.get_attribute("orientation_y", selection),
                         node_reader.get_attribute("orientation_z", selection),
                         node_reader.get_attribute("orientation_w", selection)]).T
    elif set(["rotation_angle_xaxis",
              "rotation_angle_yaxis",
              "rotation_angle_zaxis"]).intersection(attr_names):
        # Some sonata nodes files use the Euler angle rotations, convert them to quaternions
        from scipy.spatial.transform import Rotation
        angle_x = node_reader.get_attribute("rotation_angle_xaxis", selection) \
            if "rotation_angle_xaxis" in attr_names else 0
        angle_y = node_reader.get_attribute("rotation_angle_yaxis", selection) \
            if "rotation_angle_yaxis" in attr_names else 0
        angle_z = node_reader.get_attribute("rotation_angle_zaxis", selection) \
            if "rotation_angle_yaxis" in attr_names else 0
        euler_rots = np.array([angle_x, angle_y, angle_z]).T
        return Rotation.from_euler("xyz", euler_rots).as_quat()
    else:
        return None


@run_only_rank0
def _retrieve_unique_metypes(node_reader, all_gids) -> dict:
    """
    Find unique mtype+emodel combinations in target to estimate resources in dry run.
    This function returns a list of lists of unique mtype+emodel combinations.
    Each of the inner lists contains gid for the same mtype+emodel combinations.

    Args:
        node_reader: node reader, libsonata only
        all_gids: list of all gids in target
    Returns:
        list of lists of unique mtype+emodel combinations
    """
    gidvec = np.array(all_gids)
    indexes = gidvec - 1
    if len(indexes) < 10:  # Ensure array is not too small (pybind11 #1392)
        indexes = indexes.tolist()

    if isinstance(node_reader, libsonata.NodePopulation):
        etypes = node_reader.get_attribute("etype", libsonata.Selection(indexes))
        mtypes = node_reader.get_attribute("mtype", libsonata.Selection(indexes))
    else:
        raise Exception(f"Reader type {type(node_reader)} incompatible with dry run.")

    gids_per_metype = defaultdict(list)
    count_per_metype = defaultdict(int)
    for gid, mtype, etype in zip(gidvec, mtypes, etypes):
        metype = f"{mtype}-{etype}"
        gids_per_metype[metype].append(gid)
        count_per_metype[metype] += 1

    logging.info("Out of %d cells, found %d unique mtype+emodel combination",
                 len(gidvec), len(gids_per_metype))
    for metype, gid_list in gids_per_metype.items():
        logging.debug("METype: %-20s instances: %-8d gids: %s",
                      metype, len(gid_list), gid_list)

    # For each key in unique_metypes dictionary, add the relative value to a list.
    # If the list is longer than 50, truncate it to 50 elements.
    # If the metype is already computed, skip it
    gid_metype_bundle = []
    for metype, gid_list in gids_per_metype.items():
        if metype not in SimConfig.metype_mem_usage:
            gid_metype_bundle.append(np.array(gid_list[:50], dtype="uint32"))
        else:
            log_verbose("Skipping METype '%s' since it's already known", metype)

    return gid_metype_bundle, count_per_metype
