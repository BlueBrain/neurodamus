"""
Collection of Cell Readers from different sources (Pure HDF5, SynTool...)
"""
from __future__ import absolute_import
import numpy as np
import logging
from os import path as Path
from .metype import METypeManager
from .utils import compat
from .utils.logging import log_verbose


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


def _preprocess_gidvec(gidvec, stride, stride_offset, total_cells):
    if gidvec is not None:
        log_verbose("Reading %d target cells out of %d from cell file", len(gidvec), total_cells)
        # Gidvec must be ordered we change to numpy
        gidvec = np.frombuffer(gidvec, dtype="uint32")
        if stride > 1:
            gidvec = gidvec[stride_offset::stride]
        gidvec.sort()
    else:
        log_verbose("Reading all %d cells from cell file", total_cells)
        # circuit.mvd3 uses intrinsic gids starting from 1
        cell_i = stride_offset + 1
        gidvec = np.arange(cell_i, total_cells + 1, stride, dtype="uint32")

    return gidvec


def load_ncs(run_conf, gidvec, stride=1, stride_offset=0):
    """ Obtain the gids and the metypes for cells in the base circuit.

    Args:
        run_conf: the Run secgion from the configuration
        gidvec: The cells ids to be loaded. If it's None then all the cells shall be loaded
        stride: If distribution is desired stride can be set to a value > 1
        stride_offset: When using distribution, the offset to be read within the stride
    Returns:
        A tuple of (gids, metypes, total_ncs_cells)
    """
    gids = compat.Vector("I")
    gid2mefile = {}
    ncs_path = Path.join(run_conf["nrnPath"], "start.ncs")

    with open(ncs_path, "r") as ncs_f:
        total_ncs_cells = _ncs_get_total(ncs_f)
        if gidvec is None:
            log_verbose("Using all %d cells from NCS file", total_ncs_cells)
            for cellIndex, gid, metype in _ncs_get_cells(ncs_f):
                if cellIndex % stride == stride_offset:
                    gids.append(gid)
                    gid2mefile[gid] = metype
        else:
            log_verbose("Reading %d target cells out of %d from NCS file",
                        len(gidvec), total_ncs_cells)
            # Index desired cells
            gid2mefile = {int(gid): None for i, gid in enumerate(gidvec)
                          if i % stride == stride_offset}
            gids.extend(gid2mefile.keys())
            for cellIndex, gid, metype in _ncs_get_cells(ncs_f):
                if gid in gid2mefile:
                    gid2mefile[gid] = metype
    return gids, gid2mefile, total_ncs_cells


def load_mvd3(run_conf, gidvec, stride=1, stride_offset=0):
    """Load cells from MVD3, required for v6 circuits
    """
    import h5py  # Can be heavy so loaded on demand
    pth = Path.join(run_conf["CircuitPath"], "circuit.mvd3")
    mvd = h5py.File(pth, 'r')

    mecombo_ds = mvd["/cells/properties/me_combo"]
    total_mvd_cells = len(mecombo_ds)

    gidvec = _preprocess_gidvec(gidvec, stride, stride_offset, total_mvd_cells)

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

    # now we can open the combo file and get the emodel + additional info
    meinfo = METypeManager()
    res = meinfo.load_info(run_conf, gidvec, combo_names, morpho_names)
    if res < 0:
        logging.warning("gidvec: " + str(gidvec))
        logging.warning("Memap: " + str(meinfo.gids))
        raise CellReaderError("Errors found during processing of mecombo file. See log")

    return gidvec, meinfo, total_mvd_cells


def load_nodes(run_conf, gidvec, stride=1, stride_offset=0):
    """Load cells from SONATA file
    """
    logging.info("Load SONATA file")
    import mvdtool
    pth = Path.join(run_conf["CircuitPath"], run_conf["CellLibraryFile"])
    nodeReader = mvdtool.open(pth)

    total_cells = len(nodeReader)

    gidvec = _preprocess_gidvec(gidvec, stride, stride_offset, total_cells)

    if not len(gidvec):
        # Not enough cells to give this rank a few
        return compat.Vector('I'), METypeManager(), total_cells

    # Indexes are 0-based, and cant be numpy
    indexes = compat.Vector("I", gidvec - 1)

    morpho_names = nodeReader.morphologies(indexes)
    emodels = nodeReader.emodels(indexes)

    # We require gidvec as compat.Vector
    gidvec = compat.Vector("I", gidvec)
    meinfo = METypeManager()

    if not nodeReader.hasCurrents():
        log_verbose("WARNING: Sonata file doesn't have currents fields. Assuming 0.")
        meinfo.load_infoNP(gidvec, morpho_names, emodels)
    else:
        threshold_currents = nodeReader.threshold_currents(indexes)
        holding_currents = nodeReader.holding_currents(indexes)
        meinfo.load_infoNP(gidvec, morpho_names, emodels, threshold_currents, holding_currents)

    return gidvec, meinfo, total_cells
