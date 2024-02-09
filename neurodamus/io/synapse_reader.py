"""
Module implementing interfaces to the several synapse readers (eg.: synapsetool, Hdf5Reader)
"""
import logging
from abc import abstractmethod

import libsonata
import numpy as np

from ..core import NeurodamusCore as Nd, MPI
from ..utils.logging import log_verbose


def _constrained_hill(K_half, y):
    K_half_fourth = K_half**4
    y_fourth = y**4
    return (K_half_fourth + 16) / 16 * y_fourth / (K_half_fourth + y_fourth)


class _SynParametersMeta(type):
    def __init__(cls, name, bases, attrs):
        type.__init__(cls, name, bases, attrs)
        # Init public properties of the class
        assert hasattr(cls, "_synapse_fields"), "Please define _synapse_fields class attr"
        cls.dtype = np.dtype({"names": cls._synapse_fields,
                              "formats": ["f8"] * len(cls._synapse_fields)})
        cls.empty = np.recarray(0, cls.dtype)
        if not hasattr(cls, "_optional"):
            cls._optional = ()
        # Reserved fields are used to hold extra info, don't come from edge files
        if not hasattr(cls, "_reserved"):
            cls._reserved = ()

        cls.load_fields = set(cls._synapse_fields) - set(cls._reserved)

    @property
    def all_fields(cls):
        return set(cls._synapse_fields)

    def fields(cls, exclude: set = (), with_translation: dict = None):
        fields = cls.load_fields - exclude if exclude else cls.load_fields
        if with_translation:
            return [(f, with_translation.get(f, f), f in cls._optional) for f in fields]
        else:
            return [(f, f in cls._optional) for f in fields]

    def create_array(cls, length):
        return np.recarray(length, cls.dtype)


class SynapseParameters(metaclass=_SynParametersMeta):
    """Synapse parameters, internally implemented as numpy record
    """
    _synapse_fields = ("sgid", "delay", "isec", "ipt", "offset", "weight", "U", "D", "F",
                       "DTC", "synType", "nrrp", "u_hill_coefficient", "conductance_ratio",
                       "maskValue", "location")  # total: 16

    _optional = ("u_hill_coefficient", "conductance_ratio")
    _reserved = ("maskValue", "location")

    def __new__(cls, *_):
        raise NotImplementedError()

    @classmethod
    def create_array(cls, length):
        npa = np.recarray(length, cls.dtype)
        npa.conductance_ratio = -1  # set to -1 (not-set). 0 is meaningful
        npa.maskValue = -1
        npa.location = 0.5
        return npa


class SynapseReader:
    """ Synapse Readers base class.
        Factory create() will instantiate a SONATA reader.
    """

    def __init__(self, src, population=None, *_, **kw):
        self._ca_concentration = kw.get("extracellular_calcium")
        self._syn_params = {}  # Parameters cache by post-gid (previously loadedMap)
        self._open_file(src, population, kw.get("verbose", False))
        # NOTE u_hill_coefficient and conductance_scale_factor are optional, BUT
        # while u_hill_coefficient can always be readif avail, conductance reader may not.
        self._uhill_property_avail = self.has_property("u_hill_coefficient")
        self._extra_fields = tuple()
        self._extra_scale_vars = []

    def preload_data(self, ids):
        pass

    def configure_override(self, mod_override):
        if not mod_override:
            return

        override_helper = mod_override + "Helper"
        Nd.load_hoc(override_helper)

        # Read attribute names with format "attr1;attr2;attr3"
        attr_names = getattr(Nd, override_helper + "_NeededAttributes", None)
        if attr_names:
            log_verbose('Reading parameters "{}" for mod override: {}'.format(
                ", ".join(attr_names.split(";")), mod_override)
            )
            self._extra_fields = tuple(attr_names.split(";"))

        # Read attribute names with format "attr1;attr2;attr3"
        attr_names = getattr(Nd, override_helper + "_UHillScaleVariables", None)
        if attr_names:
            self._extra_scale_vars = attr_names.split(";")

    def get_synapse_parameters(self, gid):
        """Obtains the synapse parameters record for a given gid.
        """
        syn_params = self._syn_params.get(gid)
        if syn_params is None:
            syn_params = self._load_synapse_parameters(gid)

            # Modify parameters
            self._patch_delay_fp_inaccuracies(syn_params)
            if self._uhill_property_avail:
                self._scale_U_param(syn_params, self._ca_concentration, self._extra_scale_vars)
            self._syn_params[gid] = syn_params  # cache parameters
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
    def _scale_U_param(syn_params, extra_cellular_calcium, extra_scale_vars):
        if len(syn_params) == 0:
            return
        if extra_cellular_calcium is None:
            return

        scale_factors = _constrained_hill(syn_params.u_hill_coefficient,
                                          extra_cellular_calcium)
        syn_params.U *= scale_factors

        for scale_var in extra_scale_vars:
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

    @staticmethod
    def _get_sonata_circuit(path):
        """Returns a SONATA edge file in path if present
        """
        if path.endswith(".h5"):
            import h5py
            f = h5py.File(path, 'r')
            if "edges" in f:
                return path
        return None

    @classmethod
    def create(cls, syn_src, population=None, *args, **kw):
        """Instantiates a synapse reader, by default SonataReader.
           syn_src must point to a SONATA edge file.
        """
        kw["verbose"] = (MPI.rank == 0)
        if fn := cls._get_sonata_circuit(syn_src):
            if cls is not SynapseReader:
                return cls(fn, population, *args, **kw)
            else:
                log_verbose("[SynReader] Using SonataReader.")
                return SonataReader(fn, population, *args, **kw)
        else:
            raise FormatNotSupported(f"File: {syn_src}. Please provide SONATA edges")


class SonataReader(SynapseReader):
    """Reader for SONATA edge files.

    Uses libsonata directly and contains a bunch of workarounds to accomodate files
    created in the transition to SONATA. Also translates all GIDs from 0-based as on disk
    to the 1-based convention in Neurodamus.

    Will read each attribute for multiple GIDs at once and cache read data in a columnar
    fashion.

    FIXME Remove the caching at the np.recarray level.
    """

    SYNAPSE_INDEX_NAMES = ("synapse_index",)
    LOOKUP_BY_TARGET_IDS = True  # False to lookup by Source Ids
    Parameters = SynapseParameters  # By default we load synapses

    custom_parameters = {"isec", "ipt", "offset"}
    """Custom parameters are skipped from direct loading and trigger _load_params_custom()"""

    parameter_mapping = {
        "weight": "conductance",
        "U": "u_syn",
        "D": "depression_time",
        "F": "facilitation_time",
        "DTC": "decay_time",
        "synType": "syn_type_id",
        "nrrp": "n_rrp_vesicles",
        "conductance_ratio": "conductance_scale_factor",
    }

    def _open_file(self, src, population, _):
        try:
            from mpi4py import MPI
            hdf5_reader = libsonata.make_collective_reader(MPI.COMM_WORLD, False, True)
        except ModuleNotFoundError:
            hdf5_reader = libsonata.Hdf5Reader()

        storage = libsonata.EdgeStorage(src, hdf5_reader=hdf5_reader)
        if not population:
            assert len(storage.population_names) == 1
            population = next(iter(storage.population_names))
        self._population = storage.open_population(population)
        # _data is a cache which stores all the fields for each gid
        # E.g. {1: {"sgid": property_numpy}}
        self._data = {}

    def has_nrrp(self):
        """This field is required in SONATA."""
        return True

    def has_property(self, field_name):
        if field_name in self.SYNAPSE_INDEX_NAMES:
            return True
        return field_name in self._population.attribute_names

    def get_property(self, gid, field_name):
        """Retrieves a full pre-loaded property given a gid and the property name.
        """
        return self._data[gid][field_name]

    def preload_data(self, ids):
        """Preload SONATA fields for the specified IDs"""
        compute_fields = set(("sgid", "tgid") + self.SYNAPSE_INDEX_NAMES)
        needed_ids = sorted(set(ids) - set(self._data.keys()))

        def get_edge_and_lookup_gids(needed_ids):
            gids_0based = np.array(needed_ids, dtype="int64") - 1
            if self.LOOKUP_BY_TARGET_IDS:
                edge_ids = self._population.afferent_edges(gids_0based)
                return edge_ids, self._population.target_nodes(edge_ids) + 1
            else:
                edge_ids = self._population.efferent_edges(gids_0based)
                return edge_ids, self._population.source_nodes(edge_ids) + 1

        needed_edge_ids, lookup_gids = get_edge_and_lookup_gids(needed_ids)

        def _populate(field, data):
            # Populate cache. Unavailable entries are stored as a plain -1
            if data is None:
                data = -1
            for gid in needed_ids:
                existing_gid_data = self._data.setdefault(gid, {})
                existing_gid_data[field] = data if np.isscalar(data) else data[lookup_gids == gid]

        def _read(attribute, optional=False):
            if attribute in self._population.attribute_names:
                return self._population.get_attribute(attribute, needed_edge_ids)
            elif optional:
                log_verbose("Defaulting to -1.0 for attribute %s", attribute)
                return -1
            else:
                raise AttributeError(f"Missing attribute {attribute} in the SONATA edge file")

        # Populate the opposite node id
        if self.LOOKUP_BY_TARGET_IDS:
            _populate("sgid", self._population.source_nodes(needed_edge_ids) + 1)
        else:
            _populate("tgid", self._population.target_nodes(needed_edge_ids) + 1)

        # Make synapse index in the file explicit
        for name in sorted(self.SYNAPSE_INDEX_NAMES):
            _populate(name, needed_edge_ids.flatten())

        # Generic synapse parameters
        fields_load_sonata = self.Parameters.fields(exclude=self.custom_parameters | compute_fields,
                                                    with_translation=self.parameter_mapping)
        for (field, sonata_attr, is_optional) in sorted(fields_load_sonata):
            _populate(field, _read(sonata_attr, is_optional))

        if self.custom_parameters:
            self._load_params_custom(_populate, _read)

        # Extend Gids data with the additional requested fields
        # This has to work for when we call preload() a second/third time
        # so we are unsure about which gids were loaded what properties
        # We nevertheless can skip any base fields
        extra_fields = set(self._extra_fields) - (self.Parameters.all_fields | compute_fields)
        for field in sorted(extra_fields):
            now_needed_ids = sorted(set(gid for gid in ids if field not in self._data[gid]))
            if needed_ids != now_needed_ids:
                needed_ids = now_needed_ids
                needed_edge_ids, lookup_gids = get_edge_and_lookup_gids(needed_ids)
            sonata_attr = self.parameter_mapping.get(field, field)
            _populate(field, _read(sonata_attr))

    def _load_params_custom(self, _populate, _read):
        # Position of the synapse
        if self.has_property("afferent_section_id"):
            _populate("isec", _read("afferent_section_id"))
            # SONATA compliant synapse position: (section, section_fraction) takes precedence
            # over the older (section, segment, segment_offset) synapse position.
            #
            # Re-using field names for historical reason, where -1 means N/A.
            # FIXME Use dedicated fields
            if self.has_property("afferent_section_pos"):
                _populate("ipt", -1)
                _populate("offset", _read("afferent_section_pos"))
            # This was a temporary naming scheme
            # FIXME Circuits using this field should be fixed
            elif self.has_property("afferent_section_fraction"):
                logging.warning(
                    "Circuit uses non-standard compliant attribute `afferent_section_fraction`"
                )
                _populate("ipt", -1)
                _populate("offset", _read("afferent_section_fraction"))
            else:
                logging.warning(
                    "Circuit is missing standard compliant attribute `afferent_section_pos`"
                )
                _populate("ipt", _read("afferent_segment_id"))
                _populate("offset", _read("afferent_segment_offset"))
        else:
            # FIXME All this should go the way of the dodo
            logging.warning(
                "Circuit uses attribute notation using `morpho_` and is not SONATA compliant"
            )
            _populate("isec", _read("morpho_section_id_post"))
            if self.has_property("morpho_section_fraction_post"):
                _populate("ipt", -1)
                _populate("offset", _read("morpho_section_fraction_post"))
            else:
                _populate("ipt", _read("morpho_segment_id_post"))
                _populate("offset", _read("morpho_offset_segment_post"))

    def _load_synapse_parameters(self, gid):
        if gid not in self._data:
            self.preload_data([gid])

        data = self._data[gid]
        edge_count = len(next(iter(data.values())))

        if self._extra_fields:
            class CustomSynapseParameters(self.Parameters):
                _synapse_fields = self.Parameters._synapse_fields + self._extra_fields
            conn_syn_params = CustomSynapseParameters.create_array(edge_count)
        else:
            conn_syn_params = self.Parameters.create_array(edge_count)

        for name in self.Parameters.load_fields:
            conn_syn_params[name] = data[name]
        for name in self._extra_fields:
            conn_syn_params[name] = data[name]

        return conn_syn_params

    def get_counts(self, raw_ids, group_by):
        """
        Counts synapses and groups by the given field.
        """
        edge_ids = self._population.afferent_edges(raw_ids - 1)
        data = self._population.get_attribute(group_by, edge_ids)
        values, counts = np.unique(data, return_counts=True)
        return dict(zip(values, counts))


class FormatNotSupported(Exception):
    """Exception thrown when the circuit requires SynapseTool and it is NOT built-in.
    """
    pass
