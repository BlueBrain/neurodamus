"""
Stimulus implementation where incoming synaptic events are replayed for a single gid

"""
from __future__ import absolute_import
import os
import logging
from collections import OrderedDict
import numpy as np
from .core import NeuronDamus as Nd
from .core.configuration import MPInfo
from .utils import compat, OrderedMap


class SynapseReplay(object):
    """ A SynapseReplay stim can be used for a single gid that has all the synapses instantiated.  
    Given an out.dat file from a previous run, this object uses a NetStim object to retrigger 
    the synapses at the appropriate time as though the presynaptic cells were present and active.
    """

    # Declare member variables
    # ------------------------
    # objref this, self._synapse_manager, self._gid_fire_events, self._mem_usage
    # public init, replay, readSpikeFile, isVerbose
    
    def __init__(self, synapse_manager, spike_filename, delay):
        """Constructor for SynapseReplay
        Args:
            synapse_manager: SynapseRuleManager used to handle the nrn.h5 file
            spike_filename: path to spike out file.  
                if ext is .bin, interpret as binary file; otherwise, interpret as ascii
            delay: delay to apply to spike times
         
        """
        self._synapse_manager = synapse_manager
        self._mem_usage = Nd.MemUsage()
        self._gid_fire_events = None
        Nd.distributedSpikes = 0  # Wonder the effects of this
        self.open_spike_file(spike_filename, delay)


    def open_spike_file(self, filename, delay):
        """Opens a given spike file
        Args:
            filename: path to spike out file. Interpret as binary or ascii according to extension
            delay: delay to apply to spike times
        """
        # determine if we have binary or ascii file

        # TODO: filename should be able to handle relative paths, 
        # using the Run.CurrentDir as an initial path
        if filename.endswith(".bin"):
            self._read_spikes_binary(filename, delay)
        else:
            self._read_spikes_ascii(filename, delay)

    #
    def _read_spikes_ascii(self, filename, delay):
        # open raises its own exception on error
        # file obj is automatically destroyed at the end
        logging.info("Reading ascii spike file %s", filename)
        reader = open(filename)

        # first line is '/scatter'
        next(reader)
        
        # read all subsequent entries - time gid pairs.

        tvec = compat.Vector("d")
        gidvec = compat.Vector("I")
        for line in reader:
            try:
                t, gid = line.strip().split()
            except ValueError:
                logging.error("Invalid line in spike file: %s" + line)
                raise
            tvec.append(float(t) + delay)
            gidvec.append(int(gid))
            
        reader.close()
        if len(tvec) > 0:
            logging.debug("Loaded %d spikes", len(tvec))
        else:
            logging.warning("No spike/gid found in spike file %s", filename)

        self._store_events(tvec, gidvec)
    
    #
    def _read_spikes_binary(self, filename, delay):
        """Read in the binary file with spike events.
        Format notes: The first half of file is interpreted as double precision time values
        followed by an equal number of double precision gid values.
        File must be produced on the same architecture where NEURON will run (i.e. no byte-swapping)
        Read the data on the root node, broadcasting info - This is fine as long as the entire data
        set fits in a single node's memory. Should it become significantly larger, this could be
        replaced with a distributed model where each node loads a portion of the file, and exchanges
        with other nodes so as to ultimately hold data for local gids.
        """
        logging.info("Reading Binary spike file %s", filename)
        # there *should* be a number of doubles (8 bytes) such that
        # it is divisible by 2 (half for time values, half for gids)
        statinfo = os.stat(filename)
        filesize = statinfo.st_size
        n_events = filesize // 16
        if not filesize % 16:
            logging.warning("File size doesn't conform to have same number of gids and times")

        # read data on cpu 0, broadcast to others
        if MPInfo.rank > 0:
            tvec = np.empty(n_events, dtype="d")
            gidvec = np.empty(n_events, dtype="uint32")
        else:
            with open(filename, "rb") as reader:
                tvec = np.fromfile(reader, "d")
                gidvec = np.fromfile(reader, "d").astype("uint32")

            if delay != 0:
                tvec += delay
            logging.debug("Loaded %d spikes", len(tvec))

        logging.debug("Broadcasting data...")
        MPInfo.comm.Bcast(tvec, root=0)
        MPInfo.comm.Bcast(gidvec, root=0)
        # There was code here to print stats on the time/mem usage. Do we really need that?
        self._store_events(tvec, gidvec)


    def _store_events(self, tvec, gidvec):
        if isinstance(tvec, compat.Vector):
            tvec = np.frombuffer(tvec)
            gidvec = np.frombuffer(gidvec)

        map = OrderedMap.create_duplicates_as_list(gidvec, tvec)
        if self._gid_fire_events is None:
            self._gid_fire_events = map
        else:
            # Merge them
            raise NotImplementedError()

    # 
    # @param $s1 Target name whose gids are to be replayed (should contain only 1 gid)
    # @param $o2 TargetManager from which to take target info
    # def replay():
    #
    #    # request the self._synapse_manager to use the synapse data
    #    self._synapse_manager.replay( $s1, self._gid_fire_events )
    