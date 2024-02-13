"""
Stimulus implementation where incoming synaptic events are replayed for a single gid
"""
from __future__ import absolute_import
import os
import logging
import numpy
from .utils.logging import log_verbose
from .utils.multimap import GroupedMultiMap
from .utils.timeit import timeit


class SpikeManager:
    """ Holds and manages gid spike time information, specially for Replay.

    A SynapseReplay stim can be used for a single gid that has all the synapses instantiated.
    Given a spikes file from a previous run, this object uses a NetStim object to retrigger
    the synapses at the appropriate time as though the presynaptic cells were present and active.

    Internally the spikes are stored in a :py:class:`neurodamus.utils.multimap.GroupedMultiMap`
    """
    _ascii_spike_dtype = [('time', 'double'), ('gid', 'uint32')]

    @timeit(name="Replay init")
    def __init__(self, spike_filename, delay=0, population=None):
        """Constructor for SynapseReplay.

        Args:
            spike_filename: path to spike out file.
                if ext is .bin, interpret as binary file; otherwise, interpret as ascii
            delay: delay to apply to spike times
        """
        self._gid_fire_events = None
        # Nd.distributedSpikes = 0  # Wonder the effects of this
        self.open_spike_file(spike_filename, delay, population)

    #
    def open_spike_file(self, filename, delay, population=None):
        """Opens a given spike file.

        Args:
            filename: path to spike out file. Interpret as binary or ascii according to extension
            delay: delay to apply to spike times
        """
        # determine if we have binary or ascii file
        # TODO: filename should be able to handle relative paths,
        # using the Run.CurrentDir as an initial path
        # _read_spikes_xxx shall return numpy arrays
        if filename.endswith(".h5"):
            tvec, gidvec = self._read_spikes_sonata(filename, population)
        elif filename.endswith(".bin"):
            tvec, gidvec = self._read_spikes_binary(filename)
        else:
            tvec, gidvec = self._read_spikes_ascii(filename)

        if delay:
            tvec += delay

        self._store_events(tvec, gidvec)

    @classmethod
    def _read_spikes_sonata(cls, filename, population):
        import libsonata
        spikes_file = libsonata.SpikeReader(filename)
        if population not in spikes_file.get_population_names():
            raise MissingSpikesPopulationError("Spikes population not found: " + population)
        spikes = spikes_file[population]
        spike_dict = spikes.get_dict()
        return spike_dict["timestamps"], spike_dict["node_ids"] + 1

    @classmethod
    def _read_spikes_ascii(cls, filename):
        log_verbose("Reading ascii spike file %s", filename)
        # first line is '/scatter'
        spikes = numpy.loadtxt(filename, dtype=cls._ascii_spike_dtype, skiprows=1, ndmin=1)

        if len(spikes) > 0:
            log_verbose("Loaded %d spikes", len(spikes))
        else:
            logging.warning("No spike/gid found in spike file %s", filename)

        return spikes["time"], spikes["gid"]

    @staticmethod
    def _read_spikes_binary(filename):
        """Read in the binary file with spike events.

        Format notes: The first half of file is interpreted as double precision time values
        followed by an equal number of double precision gid values.
        File must be produced on the same architecture where NEURON will run (i.e. no byte-swapping)
        Read the data on the root node, broadcasting info - This is fine as long as the entire data
        set fits in a single node's memory. Should it become significantly larger, this could be
        replaced with a distributed model where each node loads a portion of the file, and exchanges
        with other nodes so as to ultimately hold data for local gids.
        """
        log_verbose("Reading Binary spike file %s", filename)
        # there *should* be a number of doubles (8 bytes) such that
        # it is divisible by 2 (half for time values, half for gids)
        statinfo = os.stat(filename)
        filesize = statinfo.st_size
        n_events = filesize // 16
        if not filesize % 16:
            logging.warning("File size doesn't conform to have same number of gids and times")

        with open(filename, "rb") as reader:
            tvec = numpy.fromfile(reader, "d", n_events)
            gidvec = numpy.fromfile(reader, "d", n_events).astype("uint32")

        log_verbose("Replay: Loaded %d spikes", len(tvec))

        return tvec, gidvec

    #
    def _store_events(self, tvec, gidvec):
        """Stores the events in the _gid_fire_events GroupedMultiMap.

        tvec and gidvec arguments should be numpy arrays
        """
        spike_map = GroupedMultiMap(gidvec, tvec)
        if self._gid_fire_events is None:
            self._gid_fire_events = spike_map
        else:
            self._gid_fire_events += spike_map

    def __len__(self):
        return len(self._gid_fire_events)

    def __getitem__(self, gid):
        return self._gid_fire_events.get(gid)

    def __contains__(self, gid):
        return gid in self._gid_fire_events

    def get_map(self):
        """Returns the :py:class:`GroupedMultiMap` with all the spikes."""
        return self._gid_fire_events

    def filter_map(self, pre_gids):
        """Returns a raw dict of pre_gid->spikes for the given pre gids."""
        return {key: self._gid_fire_events[key] for key in pre_gids}

    def dump_ascii(self, f, gid_offset=None):
        """Writes the spikes out, in compat ascii format.

        Args:
            f: The file name or handle
        """
        gids, times = self._gid_fire_events.flatten().data()
        if gid_offset:
            log_verbose("dump_ascii: add offset %d to gids", gid_offset)
            gids += gid_offset
        expanded_ds = numpy.stack((times, gids), axis=-1)

        if isinstance(f, str):
            # If given a filename we assume a new file is wanted, with new header
            with open(f, "w") as fx:
                fx.write("/scatter\n")
                numpy.savetxt(fx, expanded_ds, fmt='%.3lf\t%d')
        else:
            # If given a file handle, user wants control so we directly dump
            numpy.savetxt(f, expanded_ds, fmt='%.3lf\t%d')

        log_verbose("Replay: Written %d entries", len(expanded_ds))


class MissingSpikesPopulationError(Exception):
    """An exception triggered when a given node population is not found, we may want to handle"""
    pass
