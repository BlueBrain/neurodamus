"""
Module implementing interfaces to the several synapse readers (eg.: synapsetool, Hdf5Reader)
"""
import logging
from abc import abstractmethod
from os import path as ospath

import numpy as np

from ..core import NeurodamusCore as Nd, MPI
from ..utils.logging import log_verbose


class _SynParametersMeta(type):
    def __init__(cls, name, bases, attrs):
        type.__init__(cls, name, bases, attrs)
        # Init public properties of the class
        assert hasattr(cls, "_synapse_fields"), "Please define _synapse_fields class attr"
        cls.dtype = np.dtype({"names": cls._synapse_fields,
                              "formats": ["f8"] * len(cls._synapse_fields)})
        cls.empty = np.recarray(0, cls.dtype)


class SynapseParameters(metaclass=_SynParametersMeta):
    """Synapse parameters, internally implemented as numpy record
    """
    _synapse_fields = ("sgid", "delay", "isec", "ipt", "offset", "weight", "U", "D", "F",
                       "DTC", "synType", "nrrp", "u_hill_coefficient", "conductance_ratio",
                       "maskValue", "location")  # total: 16

    def __new__(cls, *_):
        raise NotImplementedError()

    @classmethod
    def create_array(cls, length):
        npa = np.recarray(length, cls.dtype)
        npa.conductance_ratio = -1  # set to -1 (not-set). 0 is meaningful
        npa.maskValue = -1
        npa.location = 0.5
        return npa

    @classmethod
    def concatenate(cls, syn_params, extra_syn_params):
        from numpy.lib.recfunctions import merge_arrays
        new_params = merge_arrays((syn_params, extra_syn_params), asrecarray=True, flatten=True)
        return new_params


class SynapseReader(object):
    """ Synapse Readers base class.
        Factory create() will attempt to instantiate SynReaderSynTool, followed by SynReaderNRN.
    """
    # Data types to read
    SYNAPSES = 0
    GAP_JUNCTIONS = 1

    def __init__(self, src, conn_type, population=None, *_, **kw):
        self._conn_type = conn_type
        self._ca_concentration = kw.get("extracellular_calcium")
        self._syn_params = {}  # Parameters cache by post-gid (previously loadedMap)
        self._open_file(src, population, kw.get("verbose", False))

    def get_synapse_parameters(self, gid, mod_override=None):
        """Obtains the synapse parameters record for a given gid.
        """
        syn_params = self._syn_params.get(gid)
        if syn_params is None:
            syn_params = self._syn_params[gid] = self._load_synapse_parameters(gid)
            if mod_override:
                mod_override_params = self._read_extra_fields_from_mod_override(mod_override, gid)
                if mod_override_params is not None:
                    syn_params = SynapseParameters.concatenate(syn_params, mod_override_params)
            self._patch_delay_fp_inaccuracies(syn_params)
            self._scale_U_param(syn_params, self._ca_concentration, mod_override)
        return syn_params

    @abstractmethod
    def _load_synapse_parameters(self, gid):
        """The low level reading of synapses subclasses must override"""
        pass

    @staticmethod
    def _patch_delay_fp_inaccuracies(records):
        if len(records) == 0 or 'delay' not in records.dtype.names:
            return
        dt = Nd.dt
        records.delay = (records.delay / dt + 1e-5).astype('i4') * dt

    @staticmethod
    def _scale_U_param(syn_params, extra_cellular_calcium, mod_override):
        if len(syn_params) == 0 or 'u_hill_coefficient' not in syn_params.dtype.names:
            return
        if extra_cellular_calcium is None:
            return
        if not np.any(syn_params.u_hill_coefficient):
            return

        def hill(ca_conc, y, K_half):
            return y*ca_conc**4/(K_half**4 + ca_conc**4)

        def constrained_hill(K_half):
            y_max = (K_half**4 + 16) / 16
            return lambda x: hill(x, y_max, K_half)

        f_scale = lambda x, y: constrained_hill(x)(y)
        scale_factors = np.vectorize(f_scale)(syn_params.u_hill_coefficient,
                                              extra_cellular_calcium)
        syn_params.U *= scale_factors

        if mod_override is not None:
            override_helper = mod_override + "Helper"
            Nd.load_hoc(override_helper)

            # Read attribute names with format "attr1;attr2;attr3"
            attr_names = getattr(Nd, override_helper + "_UHillScaleVariables", None)
            if attr_names is not None:
                scale_vars = attr_names.split(";")
            else:
                return

            for scale_var in scale_vars:
                syn_params[scale_var] *= scale_factors

    @abstractmethod
    def _open_file(self, src, population, verbose=False):
        """Initializes the reader, opens the synapse file
        """

    @abstractmethod
    def has_nrrp(self):
        """Checks whether source data has the nrrp field.
        """

    @abstractmethod
    def has_property(self, field_name):
        """Checks whether source data has the given additional field.
        """

    @classmethod
    def create(cls, syn_src, conn_type=SYNAPSES, population=None, *args, **kw):
        """Instantiates a synapse reader, giving preference to SynReaderSynTool
        """
        # If create called from this class then FACTORY, try SynReaderSynTool
        if cls is SynapseReader:
            kw["verbose"] = (MPI.rank == 0)
            if cls.is_syntool_enabled():
                log_verbose("[SynReader] Using new-gen SynapseReader.")
                return SynReaderSynTool(syn_src, conn_type, population, **kw)
            else:
                if not ospath.isdir(syn_src) and not syn_src.endswith(".h5"):
                    raise SynToolNotAvail(
                        "Can't load new synapse formats without syntool. File: {}".format(syn_src))
                logging.info("[SynReader] Attempting legacy hdf5 reader.")
                return SynReaderNRN(syn_src, conn_type, None, *args, **kw)
        else:
            return cls(syn_src, conn_type, population, *args, **kw)

    @classmethod
    def is_syntool_enabled(cls):
        """Checks whether Neurodamus has built-in support for SynapseTool.
        """
        if not hasattr(cls, '_syntool_enabled'):
            cls._syntool_enabled = Nd.SynapseReader().modEnabled()
        return cls._syntool_enabled


class SynReaderSynTool(SynapseReader):
    """ Synapse Reader using synapse tool.
        Currently it uses the neuron NMODL interface.
    """
    SYNREADER_MOD_NFIELDS_DEFAULT = 14
    _has_warned_field_count_mismatch = False

    def _open_file(self, syn_src, population, verbose=False):
        if not self.is_syntool_enabled():
            raise SynToolNotAvail("SynapseReader support not available.")
        if ospath.isdir(syn_src) and self._conn_type == self.GAP_JUNCTIONS:
            alt_gj_nrn_file = ospath.join(syn_src, "nrn_gj.h5")
            if ospath.isfile(alt_gj_nrn_file):
                log_verbose("Found gj nrn file: nrn_gj.h5")
                syn_src = alt_gj_nrn_file
            # else pass the dir as is, SynapseReader can find e.g. nrn.h5
        reader = self._syn_reader = Nd.SynapseReader(syn_src, verbose)
        if population:
            reader.selectPopulation(population)

    def _load_synapse_parameters(self, gid):
        reader = self._syn_reader
        nrow = int(reader.loadSynapses(gid))
        if nrow < 1:
            return SynapseParameters.empty

        conn_syn_params = SynapseParameters.create_array(nrow)
        syn_params_mtx = conn_syn_params.view(('f8', len(conn_syn_params.dtype)))
        tmpParams = Nd.Vector(self.SYNREADER_MOD_NFIELDS_DEFAULT)

        # Do checks for the matching of the record size
        reader.getSynapse(0, tmpParams)
        record_size = tmpParams.size()
        supported_nfields = len(conn_syn_params.dtype) - 2  # non-mod fields: mask and location
        n_fields = min(record_size, supported_nfields)
        if supported_nfields < record_size and not self._has_warned_field_count_mismatch:
            logging.warning("SynapseReader records are %d fields long while neurodamus-py "
                            "only recognizes %d. Update neurodamus-py to use them.",
                            record_size, supported_nfields)
            SynReaderSynTool._has_warned_field_count_mismatch = True

        for syn_i in range(nrow):
            reader.getSynapse(syn_i, tmpParams)
            # as_numpy() shares memory to ndarray[double] -> can be copied (assigned) to the view
            syn_params_mtx[syn_i, :n_fields] = tmpParams.as_numpy()[:n_fields]

        return conn_syn_params

    def has_nrrp(self):
        return self._syn_reader.hasNrrpField()

    def has_property(self, field_name):
        return hasattr(self._syn_reader, 'hasProperty') \
            and bool(self._syn_reader.hasProperty(field_name))

    def get_property(self, gid, field_name, *is_pre):
        """Retrieves a full property (vector) given a gid and the property name.
        """
        self._syn_reader.loadSynapseCustom(gid, field_name, *is_pre)
        field_data = Nd.Vector()
        self._syn_reader.getPropertyData(0, field_data)
        return field_data  # Returns the vector to avoid copies to numpy

    def _read_extra_fields_from_mod_override(self, mod_override, tgid):
        if mod_override is None:
            return None

        override_helper = mod_override + "Helper"
        Nd.load_hoc(override_helper)

        # Read attribute names with format "attr1;attr2;attr3"
        attr_names = getattr(Nd, override_helper + "_NeededAttributes", None)
        if attr_names is None:
            return None
        log_verbose('Reading parameters "{}" for mod override: {}'.format(
            ", ".join(attr_names.split(";")), mod_override))

        class CustomSynapseParameters(SynapseParameters):
            _synapse_fields = tuple(attr_names.split(";"))

        reader = self._syn_reader
        req_fields_str = ", ".join(CustomSynapseParameters._synapse_fields)
        nrow = int(reader.loadSynapseCustom(tgid, req_fields_str))
        if nrow < 1:
            return CustomSynapseParameters.empty

        conn_syn_params = CustomSynapseParameters.create_array(nrow)
        syn_params_mtx = conn_syn_params.view(('f8', len(conn_syn_params.dtype)))
        tmpParams = Nd.Vector(len(conn_syn_params.dtype))

        for syn_i in range(nrow):
            reader.getSynapse(syn_i, tmpParams)
            syn_params_mtx[syn_i] = tmpParams.as_numpy()

        return conn_syn_params


class SynReaderNRN(SynapseReader):
    """ Synapse Reader for NRN format only, using the hdf5_reader mod.
    """
    def __init__(self,
                 syn_src, conn_type, population=None,
                 n_synapse_files=None, local_gids=(),  # Specific to NRNReader
                 *_, **kw):
        if ospath.isdir(syn_src):
            filename = "nrn_gj.h5" if conn_type == self.GAP_JUNCTIONS else "nrn.h5"
            syn_src = ospath.join(syn_src, filename)
            log_verbose("Found nrn file: %s", filename)

        # Hdf5 reader doesnt do checks, failing badly (and cryptically) later
        if not ospath.isfile(syn_src) and not ospath.isfile(syn_src + ".1"):
            raise RuntimeError("NRN synapses file not found: " + syn_src)

        # Generic init now that we know the file
        self._n_synapse_files = n_synapse_files or 1  # needed during init
        SynapseReader.__init__(self, syn_src, conn_type, population, **kw)

        if self._n_synapse_files > 1:
            vec = Nd.Vector(len(local_gids))  # excg-location requires true vector
            for num in local_gids:
                vec.append(num)
            self._syn_reader.exchangeSynapseLocations(vec)

    def _open_file(self, syn_src, population, verbose=False):
        if population:
            raise RuntimeError("HDF5Reader doesn't support Populations.")
        log_verbose("Opening synapse file: %s", syn_src)
        self._syn_reader = Nd.HDF5Reader(syn_src, self._n_synapse_files)
        self.nrn_version = self._syn_reader.checkVersion()

    def has_nrrp(self):
        return self.nrn_version > 4

    def has_property(self, field_name):
        return NotImplemented  # nrn has a predefined set of fields. worthless checking

    def _load_synapse_parameters(self, gid):
        reader = self._syn_reader
        cell_name = "a%d" % gid

        ret = reader.loadData(gid) if self._n_synapse_files > 1 \
            else reader.loadData(cell_name)

        if ret < 0:  # No dataset
            return SynapseParameters.empty
        nrow = int(reader.numberofrows(cell_name))
        if nrow == 0:
            return SynapseParameters.empty

        conn_syn_params = SynapseParameters.create_array(nrow)
        has_nrrp = self.has_nrrp()

        for i in range(nrow):
            params = conn_syn_params[i]
            params[0] = reader.getData(cell_name, i, 0)   # sgid
            params[1] = reader.getData(cell_name, i, 1)   # delay
            params[2] = reader.getData(cell_name, i, 2)   # isec
            params[3] = reader.getData(cell_name, i, 3)   # ipt
            params[4] = reader.getData(cell_name, i, 4)   # offset
            params[5] = reader.getData(cell_name, i, 8)   # weight
            params[6] = reader.getData(cell_name, i, 9)   # U
            params[7] = reader.getData(cell_name, i, 10)  # D
            params[8] = reader.getData(cell_name, i, 11)  # F
            params[9] = reader.getData(cell_name, i, 12)  # DTC
            params[10] = reader.getData(cell_name, i, 13)  # isynType
            if has_nrrp:
                params[11] = reader.getData(cell_name, i, 17)  # nrrp
            else:
                params[11] = -1

            # placeholder for u_hill_coefficient and conductance_ratio, not supported by HDF5Reader
            params[12] = 0
            params[13] = -1

        return conn_syn_params


class SynToolNotAvail(Exception):
    """Exception thrown when the circuit requires SynapseTool and it is NOT built-in.
    """
    pass
