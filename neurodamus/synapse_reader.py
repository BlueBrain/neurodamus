import logging
from abc import abstractmethod
from os import path
from .core import NeuronDamus as ND, MPI
from .connection import SynapseParameters
from .utils.logging import log_verbose


class SynapseReader:
    """ Synapse Readers base class.
        Factory create() will attempt to instantiate SynReaderSynTool, followed by SynReaderNRN.
    """
    _syn_reader = None
    _has_nrrp = None

    def __init__(self, src, *args, **kw):
        if self._syn_reader is None:
            raise TypeError("Subclasses must define _syn_reader")
        self._syn_params = {}  # Parameters cache by post-gid (previously loadedMap)

    def get_synapse_parameters(self, gid):
        syn_params = self._syn_params.get(gid)
        if syn_params is None:
            syn_params = self._syn_params[gid] = self._load_synapse_parameters(gid)
            self._patch_delay_fp_inaccuracies(syn_params)
        return syn_params

    @abstractmethod
    def _load_synapse_parameters(self, gid):
        """The low level reading of synapses subclasses must override"""
        pass

    @staticmethod
    def _patch_delay_fp_inaccuracies(records):
        if len(records) == 0:
            return
        dt = ND.dt
        records.delay = (records.delay / dt + 1e-5).astype('i4') * dt

    def has_nrrp(self):
        if self._has_nrrp is None:
            raise NotImplementedError("Uninitialized _has_nrrp field")
        return self._has_nrrp

    @classmethod
    def create(cls, syn_src, *args, **kw):
        # FACTORY
        if cls is SynapseReader:
            try:
                reader = SynReaderSynTool(syn_src, MPI.rank == 0)
                log_verbose("[SynReader] Using new-gen SynapseReader.")
            except NotImplementedError as e:
                logging.warning("[SynReader] " + str(e) + " Attempting legacy hdf5 reader.")
                reader = SynReaderNRN(syn_src, *args, **kw)
        else:
            reader = cls(args, **kw)
        return reader


class SynReaderSynTool(SynapseReader):
    """ Synapse Reader using synapse tool.
        Currently it uses the neuron NMODL interface.
    """
    def __init__(self, syn_source, verbose=False):
        self._syn_reader = reader = ND.SynapseReader(syn_source, verbose)
        if not reader.modEnabled():
            raise NotImplementedError("SynapseReader support not available.")
        self._has_nrrp = reader.hasNrrpField()
        SynapseReader.__init__(self, syn_source)

    def _load_synapse_parameters(self, gid):
        reader = self._syn_reader

        # Load data. SynapseTool is base 0
        nrow = int(reader.loadSynapses(gid - 1))
        if nrow < 1:
            return SynapseParameters.empty

        conn_syn_params = SynapseParameters.create_array(nrow)
        syn_params_mtx = conn_syn_params.view(('f8', len(conn_syn_params.dtype)))
        tmpParams = ND.Vector(12)

        for syn_i in range(nrow):
            reader.getSynapse(syn_i, tmpParams)
            # as_numpy() shares memory to ndarray[double] -> can be copied (assigned) to the view
            syn_params_mtx[syn_i, :12] = tmpParams.as_numpy()

        conn_syn_params.sgid += 1  # make s-gids 1-based (as expected by neurodamus)
        return conn_syn_params


class SynReaderNRN(SynapseReader):
    """ Synapse Reader for NRN format only, using the hdf5_reader mod.
    """
    def __init__(self, syn_src, local_gids, n_synapse_files):
        if path.isdir(syn_src):
            syn_src = path.join(syn_src, 'nrn.h5')
        # Hdf5 reader doesnt do checks, failing badly (and crypticly) later
        if not path.isfile(syn_src):
            if n_synapse_files == 1:
                raise RuntimeError("NRN synapses file not found: " + syn_src)
            else:
                if not path.isfile(syn_src + ".1"):
                    raise RuntimeError("NRN synapses files not found: " + syn_src + ".1")

        self._syn_reader = reader = ND.HDF5Reader(syn_src, n_synapse_files)
        self.nrn_version = reader.checkVersion()
        self._has_nrrp = self.nrn_version > 4
        self._n_synapse_files = n_synapse_files
        if n_synapse_files > 1:
            reader.exchangeSynapseLocations(local_gids)
        SynapseReader.__init__(self, syn_src)

    def _load_synapse_parameters(self, gid):
        reader = self._syn_reader
        cell_name = "a%d" % gid

        if self._n_synapse_files > 1:
            ret = reader.loadData(gid)
        else:
            ret = reader.loadData(cell_name)

        # Checks. Error (-1) or no data
        if ret < 0:
            return SynapseParameters.empty
        nrow = int(reader.numberofrows(cell_name))
        if nrow == 0:
            return SynapseParameters.empty

        conn_syn_params = SynapseParameters.create_array(nrow)

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
            if self._has_nrrp:
                params[11] = reader.getData(cell_name, i, 17)  # nrrp
            else:
                params[11] = -1

        return conn_syn_params
