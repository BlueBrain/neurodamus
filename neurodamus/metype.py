"""
Module which defines and handles METypes config (v5/v6 cells)
"""
from __future__ import absolute_import, print_function
import logging
from abc import abstractmethod
from os import path as ospath
from .core.configuration import ConfigurationError, SimConfig
from .core import NeurodamusCore as Nd
import numpy as np


class BaseCell:
    """
    Class representing an basic cell, e.g. an artificial cell
    """
    __slots__ = ("_cellref", "_ccell")

    def __init__(self, gid, cell_info, circuit_info):
        self._cellref = None
        self._ccell = None

    @property
    def CellRef(self):
        return self._cellref

    @property
    def CCell(self):
        return self._ccell

    def connect2target(self, target_pp=None):
        """ Connects empty cell to target """
        return Nd.NetCon(self._cellref, target_pp)

    def re_init_rng(self, ion_seed):
        pass


class METype(BaseCell):
    """
    Class representing an METype. Will instantiate a Hoc-level cell as well
    """
    morpho_extension = "asc"
    """The extension to be applied to morphology files"""

    KEEP_AXON_FLAG = 400

    __slots__ = ('_threshold_current', '_hypAmp_current', '_netcons',
                 '_synapses', '_syn_helper_list', '_emodel_name',
                 'exc_mini_frequency', 'inh_mini_frequency',
                 'extra_attrs')

    def __init__(self, gid, etype_path, emodel, morpho_path, meinfos=None, detailed_axon=False):
        """Instantite a new Cell from METype

        Args:
            gid: Cell gid
            etype_path: path for etypes
            emodel: Emodel name
            morpho_path: path for morphologies
            meinfos: dictionary with v6 infos (if v6 circuit)
        """
        super().__init__(gid, meinfos, None)
        self._threshold_current = None
        self._hypAmp_current = None
        self._netcons = []
        self._synapses = None
        self._syn_helper_list = None
        self._emodel_name = emodel
        self.exc_mini_frequency = None
        self.inh_mini_frequency = None
        self.extra_attrs = None

        self._instantiate_cell(gid, etype_path, emodel, morpho_path, meinfos, detailed_axon)

    gid = property(lambda self: int(self._cellref.gid),
                   lambda self, val: setattr(self._cellref, 'gid', val))

    # Ensure no METype instances created. Only Subclasses
    @abstractmethod
    def _instantiate_cell(self, *args):
        """Method which instantiates the cell in the simulator"""
        pass

    @property
    def synlist(self):
        return self._synapses

    # Named for compat with still existing HOC modules
    def getThreshold(self):
        return self._threshold_current

    def setThreshold(self, value):
        self._threshold_current = value

    def getHypAmp(self):
        if self._hypAmp_current is None:
            logging.warning("EModel %s doesnt define HypAmp current", self._emodel_name)
            return 0
        return self._hypAmp_current

    def setHypAmp(self, value):
        self._hypAmp_current = value

    @staticmethod
    def getVersion():
        return 3

    def connect2target(self, target_pp=None):
        """ Connects MEtype cell to target

        Args:
            target_pp: target point process [default: None]

        Returns: NetCon obj
        """
        if SimConfig.spike_location == "soma":
            sec, seg = self.CellRef.soma[0], self.CellRef.soma[0](1)
        else:
            sec, seg = self.CellRef.axon[1], self.CellRef.axon[1](0.5)
        netcon = Nd.NetCon(seg._ref_v, target_pp, sec=sec)
        netcon.threshold = SimConfig.spike_threshold
        return netcon

    def re_init_rng(self, ion_seed):
        """Re-Init RNG for cell

        Args:
            ion_seed: ion channel seed
        """
        self._ccell.re_init_rng(ion_seed)

    def delete_axon(self):
        pass

    def __del__(self):
        if self._cellref:
            self._cellref.clear()  # cut cyclic reference


class Cell_V6(METype):
    __slots__ = ("local_to_global_matrix",)

    def __init__(self, gid, meinfo, circuit_conf):
        mepath = circuit_conf.METypePath
        morpho_path = circuit_conf.MorphologyPath
        detailed_axon = circuit_conf.DetailedAxon
        super().__init__(gid, mepath, meinfo.emodel_tpl, morpho_path, meinfo, detailed_axon)

    def _instantiate_cell(self, gid, etype_path, emodel, morpho_path, meinfos_v6, detailed_axon):
        """Instantiates a SSCx v6 cell
        """
        Nd.load_hoc(ospath.join(etype_path, emodel))
        EModel = getattr(Nd, emodel)
        morpho_file = meinfos_v6.morph_name + "." + self.morpho_extension
        keep_axon = detailed_axon and self.KEEP_AXON_FLAG
        add_params = meinfos_v6.add_params or (keep_axon,)  # Keep axon incompatible with add_params

        logging.debug("Loading Gid %d: emodel: %s, Morphology: %s", gid, emodel, morpho_file)
        try:
            # For this step, do not call mpi_abort in neuron and let neurodamus handle and abort,
            # NB: Do not re-raise as ConfigurationError, neurodamus doesn't call mpi_abort so hangs
            old_flag = Nd.pc.mpiabort_on_error(0)
            self._cellref = EModel(gid, morpho_path, morpho_file, *add_params)
            Nd.pc.mpiabort_on_error(old_flag)
        except Exception as e:
            raise RuntimeError("Error from NEURON when loading Gid %d: emodel: %s, Morphology: %s"
                               ": %s" % (gid, emodel, morpho_file, str(e))) from e
        self._ccell = self._cellref
        self._synapses = Nd.List()
        self._syn_helper_list = Nd.List()
        self._threshold_current = meinfos_v6.threshold_current
        self._hypAmp_current = meinfos_v6.holding_current
        self.exc_mini_frequency = meinfos_v6.exc_mini_frequency
        self.inh_mini_frequency = meinfos_v6.inh_mini_frequency
        self.local_to_global_matrix = meinfos_v6.local_to_global_matrix
        self.extra_attrs = meinfos_v6.extra_attrs

    def local_to_global_coord_mapping(self, points):
        if self.local_to_global_matrix is False:
            raise ConfigurationError("To use local_to_global_coord_mapping please "
                                     "run neurodamus with `enable_coord_mapping=True`")
        elif self.local_to_global_matrix is None:
            raise Exception("Nodes don't provide all 3d position/rotation info")
        return vector_rotate_translate(points, self.local_to_global_matrix)

    def delete_axon(self):
        logging.info("Now deleting the axon! 🤩")
        self._cellref.replace_axon()

    def __getattr__(self, item):
        prop = self.extra_attrs.get(item)
        if prop is None:
            raise AttributeError(item)
        return prop


class EmptyCell(BaseCell):
    """
    Class representing an empty cell, e.g. an artificial cell
    Workaround for the neuron issue https://github.com/neuronsimulator/nrn/issues/635
    """
    __slots__ = ('gid',)

    def __init__(self, gid, cell):
        super().__init__(gid, None, None)
        self._cellref = cell
        self.gid = gid


# Metadata
# --------

class METypeItem(object):
    """ Metadata about an METype, each possibly used by several cells.
    """
    __slots__ = ("morph_name", "layer", "fullmtype", "etype", "emodel_tpl", "combo_name",
                 "mtype", "threshold_current", "holding_current",
                 "exc_mini_frequency", "inh_mini_frequency", "add_params",
                 "local_to_global_matrix",
                 "extra_attrs")

    def __init__(self, morph_name, layer=None, fullmtype=None, etype=None, emodel_tpl=None,
                 combo_name=None, mtype=None, threshold_current=0, holding_current=0,
                 exc_mini_frequency=0, inh_mini_frequency=0, add_params=None,
                 position=None, rotation=None, scale=1.0):
        self.morph_name = morph_name
        self.layer = layer
        self.fullmtype = fullmtype
        self.etype = etype
        self.emodel_tpl = emodel_tpl
        self.combo_name = combo_name
        self.mtype = mtype
        self.threshold_current = float(threshold_current)
        self.holding_current = float(holding_current)
        self.exc_mini_frequency = float(exc_mini_frequency)
        self.inh_mini_frequency = float(inh_mini_frequency)
        self.add_params = add_params
        self.extra_attrs = {}
        cli_opts = SimConfig.cli_options
        self.local_to_global_matrix = self._make_coord_map_matrix(position, rotation, scale) \
            if cli_opts is None or cli_opts.enable_coord_mapping else False

    @staticmethod
    def _make_coord_map_matrix(position, rotation, scale):
        """Build the transformation matrix from local to global"""
        if rotation is None:
            return None
        from scipy.spatial.transform import Rotation
        m = np.empty((3, 4), np.float32)
        r = Rotation.from_quat(rotation)  # scipy auto-normalizes
        m[:, :3] = r.as_matrix()
        m[:, 3] = position
        m[:, 3] *= scale
        return m

    def local_to_global_coord_mapping(self, points):
        return vector_rotate_translate(points, self.local_to_global_matrix)


def vector_rotate_translate(points, transform_matrix):
    """Rotate/translate a vector of 3D points according to a transformation matrix.

    Note: Rotation is done directly using the Einstein Sum method, similarly to scipy,
        avoiding intermediate states.
    """
    if points.shape[0] == 0:
        return np.array([])
    if len(points.shape) != 2 or points.shape[1] != 3:
        raise ValueError("Matrix of input coordinates needs 3 columns.")
    rot_matrix = transform_matrix[None, :, :3]
    translation = transform_matrix[:, 3]
    return np.einsum('ijk,ik->ij', rot_matrix, points) + translation


class METypeManager(dict):
    """ Map to hold specific METype info and provide retrieval by gid
    """

    def insert(self, gid, morph_name, *me_data, **kwargs):
        """Function to add an METypeItem to internal data structure
        """
        self[int(gid)] = METypeItem(morph_name, *me_data, **kwargs)

    def load_infoNP(self, gidvec, morph_list, model_templates, mtypes, etypes,
                    threshold_currents=None, holding_currents=None,
                    exc_mini_freqs=None, inh_mini_freqs=None,
                    positions=None, rotations=None,
                    add_params_list=None):
        """Loads METype information in bulk from Numpy arrays
        """
        for idx, gid in enumerate(gidvec):
            th_current = threshold_currents[idx] if threshold_currents is not None else .0
            hd_current = holding_currents[idx] if holding_currents is not None else .0
            exc_mini_freq = exc_mini_freqs[idx] if exc_mini_freqs is not None else .0
            inh_mini_freq = inh_mini_freqs[idx] if inh_mini_freqs is not None else .0
            position = positions[idx] if positions is not None else None
            rotation = rotations[idx] if rotations is not None else None
            mtype = mtypes[idx] if mtypes is not None else None
            add_params = add_params_list[idx] if add_params_list is not None else None
            self[int(gid)] = METypeItem(
                morph_list[idx],
                etype=etypes[idx] if etypes is not None else None,
                emodel_tpl=model_templates and model_templates[idx],
                mtype=mtype,  # TODO: check this
                threshold_current=th_current,
                holding_current=hd_current,
                exc_mini_frequency=exc_mini_freq,
                inh_mini_frequency=inh_mini_freq,
                position=position,
                rotation=rotation,
                add_params=add_params
            )

    def retrieve_info(self, gid):
        return self.get(gid) \
            or logging.warning("No info for gid %d found.", gid)

    @property
    def gids(self):
        return self.keys()
