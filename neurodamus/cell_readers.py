"""
Collection of Cell Readers from different sources (Pure HDF5, SynTool...)
"""
from __future__ import absolute_import
import logging
import numpy as np
from os import path as ospath
from .core.configuration import ConfigurationError
from .metype import METypeManager
from .utils import compat


class CellReaderError(Exception):
    pass


class TargetSpec:
    """Definition of a new-style target, accounting for multipopulation
    """

    def __init__(self, target_name):
        """Initialize a target specification

        Args:
            target_name: the target name. For specifying a population use
                the format ``population:target_name``
        """
        if target_name and ':' in target_name:
            self.population, self.name = target_name.split(':')
        else:
            self.name = target_name
            self.population = None

    def __str__(self):
        return self.name if self.population is None \
            else "{}:{}".format(self.population, self.name)

    def __bool__(self):
        return bool(self.name)

    @property
    def simple_name(self):
        if self.name is None:
            return "_ALL_"
        return self.__str__().replace(":", "_")


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


def split_round_robin(all_gids, stride, stride_offset, total_cells):
    """ Splits a numpy ndarray[uint32] round-robin.
    If the array is None generates new arrays based on the nr of total cells
    """
    if all_gids is not None:
        gidvec = all_gids[stride_offset::stride] if stride > 1 else all_gids
        gidvec.sort()
    else:
        cell_i = stride_offset + 1  # gids start from 1
        gidvec = np.arange(cell_i, total_cells + 1, stride, dtype="uint32")
    return gidvec


def load_ncs(run_conf, all_gids, stride=1, stride_offset=0):
    """ Obtain the gids and the metypes for cells in the base circuit.

    Args:
        run_conf: the Run secgion from the configuration
        all_gids: The cells ids to be loaded. If it's None then all the cells shall be loaded
        stride: If distribution is desired stride can be set to a value > 1
        stride_offset: When using distribution, the offset to be read within the stride
    Returns:
        A tuple of (gids, metypes, total_ncs_cells)
    """
    gids = compat.Vector("I")
    gid2mefile = {}
    ncs_path = ospath.join(run_conf["nrnPath"], "start.ncs")

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
            for cellIndex, gid, metype in _ncs_get_cells(ncs_f):
                if gid in gid2mefile:
                    gid2mefile[gid] = metype
            if any(v is None for v in gid2mefile.values()):
                raise CellReaderError("Target contains invalid circuit cells")
    return gids, gid2mefile, total_ncs_cells


def load_mvd3(run_conf, all_gids, stride=1, stride_offset=0):
    """Load cells from MVD3, required for v6 circuits
    """
    import h5py  # Can be heavy so loaded on demand
    pth = ospath.join(run_conf["CircuitPath"], "circuit.mvd3")
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

    # now we can open the combo file and get the emodel + additional info
    meinfo = METypeManager()
    res = meinfo.load_info(run_conf, gidvec, combo_names, morpho_names)
    if res < 0:
        logging.warning("gidvec: " + str(gidvec))
        logging.warning("Memap: " + str(meinfo.gids))
        raise CellReaderError("Errors found during processing of mecombo file. See log")

    return gidvec, meinfo, total_mvd_cells


def load_nodes(run_conf, all_gids, stride=1, stride_offset=0):
    """Load cells from SONATA file
    """
    import mvdtool
    pth = run_conf["CellLibraryFile"]
    if not ospath.isfile(pth):
        pth = ospath.join(run_conf["CircuitPath"], run_conf["CellLibraryFile"])
    if not ospath.isfile(pth):
        raise ConfigurationError("Could not find Nodes: " + run_conf["CellLibraryFile"])

    node_population = TargetSpec(run_conf.get("CircuitTarget")).population
    node_reader = mvdtool.open(pth, node_population or "")
    total_cells = len(node_reader)
    gidvec = split_round_robin(all_gids, stride, stride_offset, total_cells)

    if not len(gidvec):
        # Not enough cells to give this rank a few
        return gidvec, METypeManager(), total_cells

    meinfo = METypeManager()
    indexes = gidvec - 1  # MVDtool requires 0-indexed ids.
    if len(indexes) < 10:  # Ensure array is not too small (pybind11 #1392)
        indexes = indexes.tolist()

    morpho_names = node_reader.morphologies(indexes)
    emodels = node_reader.emodels(indexes)

    if not node_reader.hasCurrents():
        logging.warning("Sonata file doesn't have currents fields. Assuming 0.")
        meinfo.load_infoNP(gidvec, morpho_names, emodels)
    else:
        threshold_currents = node_reader.threshold_currents(indexes)
        holding_currents = node_reader.holding_currents(indexes)
        meinfo.load_infoNP(gidvec, morpho_names, emodels, threshold_currents, holding_currents)

    return gidvec, meinfo, total_cells
