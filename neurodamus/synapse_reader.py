"""
Module implementing interfaces to the several synapse readers (eg.: synapsetool, Hdf5Reader)
"""
import logging
from abc import abstractmethod
from os import path as Path
from .core import NeuronDamus as ND, MPI
from .connection import SynapseParameters
from .utils.logging import log_verbose


class SynapseReader(object):
    """ Synapse Readers base class.
        Factory create() will attempt to instantiate SynReaderSynTool, followed by SynReaderNRN.
    """
    # Data types to read
    SYNAPSES = 0
    GAP_JUNCTIONS = 1

    def __init__(self, src, conn_type, syn_reader, has_nrrp, *args, **kw):
        assert conn_type in (self.SYNAPSES, self.GAP_JUNCTIONS), "conn_type can only be Syn or Gap"
        assert syn_reader is not None, "syn_reader must not be None"
        self._conn_type = conn_type
        self._syn_reader = syn_reader
        self._has_nrrp = has_nrrp
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
    def create(cls, syn_src, conn_type=SYNAPSES, *args, **kw):
        # If create called from this class then FACTORY, try SynReaderSynTool
        if cls is SynapseReader:
            try:
                reader = SynReaderSynTool(syn_src, conn_type, verbose=(MPI.rank == 0))
                log_verbose("[SynReader] Using new-gen SynapseReader.")
            except SynToolNotAvail as e:
                if not syn_src.endswith(".h5"):
                    raise  # reraise because we cant use the fallback for non nrn files
                logging.info("[SynReader] " + str(e) + " Attempting legacy hdf5 reader.")
                reader = SynReaderNRN(syn_src, conn_type, *args, **kw)
        else:
            reader = cls(args, conn_type, *args, **kw)
        return reader


class SynReaderSynTool(SynapseReader):
    """ Synapse Reader using synapse tool.
        Currently it uses the neuron NMODL interface.
    """
    def __init__(self, syn_source, conn_type, verbose=False):
        # Instantiate the NMODL reader
        reader = ND.SynapseReader(syn_source, conn_type, verbose)
        if not reader.modEnabled():
            raise SynToolNotAvail("SynapseReader support not available.")
        SynapseReader.__init__(self, syn_source, conn_type, reader, reader.hasNrrpField())

    def _load_synapse_parameters(self, gid):
        reader = self._syn_reader

        nrow = int(reader.loadSynapses(gid) if self._conn_type == self.SYNAPSES
                   else reader.loadGapJunctions(gid))
        if nrow < 1:
            return SynapseParameters.empty

        conn_syn_params = SynapseParameters.create_array(nrow)
        syn_params_mtx = conn_syn_params.view(('f8', len(conn_syn_params.dtype)))
        tmpParams = ND.Vector(12)

        for syn_i in range(nrow):
            reader.getSynapse(syn_i, tmpParams)
            # as_numpy() shares memory to ndarray[double] -> can be copied (assigned) to the view
            syn_params_mtx[syn_i, :12] = tmpParams.as_numpy()

        return conn_syn_params


class SynReaderNRN(SynapseReader):
    """ Synapse Reader for NRN format only, using the hdf5_reader mod.
    """
    def __init__(self, syn_src, conn_type, local_gids, n_synapse_files, verbose=False):
        if Path.isdir(syn_src):
            syn_src = Path.join(syn_src, 'nrn.h5')
        # Hdf5 reader doesnt do checks, failing badly (and crypticly) later
        if not Path.isfile(syn_src) and not Path.isfile(syn_src + ".1"):
            raise RuntimeError("NRN synapses file not found: " + syn_src)

        reader = ND.HDF5Reader(syn_src, n_synapse_files)
        self.nrn_version = reader.checkVersion()
        self._n_synapse_files = n_synapse_files
        SynapseReader.__init__(self, syn_src, conn_type, reader, self.nrn_version > 4)

        if n_synapse_files > 1:
            # excg-location requires true vector
            vec = ND.Vector(len(local_gids))
            for num in local_gids:
                vec.append(num)
            reader.exchangeSynapseLocations(vec)

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


class SynToolNotAvail(Exception):
    pass
