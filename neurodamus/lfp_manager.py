import logging
import numpy

from .core import NeurodamusCore as Nd
from .core.configuration import ConfigurationError


class LFPManager:
    """
    Class handling the lfp functionality
    """
    def __init__(self):
        self._lfp_file = None

    def load_lfp_config(self, lfp_weights_file, population_list):
        """Loads lfp weigths from h5 file
        """
        logging.info("Reading LFP configuration info from '%s'", lfp_weights_file)
        import h5py
        try:
            self._lfp_file = h5py.File(lfp_weights_file, 'r')
        except IOError as e:
            raise ConfigurationError(f"Error opening LFP electrodes file: {e}")

        # Check that the file contains the required groups for at least 1 population
        populations_found = []
        for pop_name in population_list:

            req_groups = [f'/electrodes/{pop_name}/scaling_factors', f'{pop_name}/node_ids',
                          f'{pop_name}/offsets']
            if all(group in self._lfp_file for group in req_groups):
                populations_found.append(pop_name)

        if not populations_found:
            raise ConfigurationError("The LFP weights file does not contain the necessary datasets "
                                     "'scaling_factors', 'node_ids' and 'offsets' "
                                     "in any of the populations {}.".format(population_list))

    def get_sonata_node_id(self, gid, population_info):
        return population_info[0], gid - population_info[1] - 1

    def get_node_id_subsets(self, node_id, population_name):
        node_ids = self._lfp_file[population_name]["node_ids"]
        # Look for the index of the node_id
        index = numpy.where(numpy.array(node_ids) == node_id)[0][0]
        offsets_dataset = self._lfp_file[population_name]["offsets"]
        electrodes_dataset = self._lfp_file["electrodes"][population_name]["scaling_factors"]
        index_low = offsets_dataset[index]
        index_high = offsets_dataset[index+1]
        # Get the subset data for the node_id and the section index
        subset_data = electrodes_dataset[index_low:index_high, :]
        return subset_data

    def read_lfp_factors(self, gid, population_info=("default", 0)):
        """
        Reads the local field potential (LFP) factors for a specific gid
        from an HDF5 file and returns the factors as a Nd.Vector.

        Args:
        gid (int): The unique cell identifier
        population_info (Pair(str, int)): Population info ("population_name", population_offset)

        Returns:
        Nd.Vector: A vector containing the LFP factors for the specified gid
        """
        scalar_factors = Nd.Vector()
        if self._lfp_file:
            try:
                population_name, node_id = self.get_sonata_node_id(gid, population_info)
                subset_data = self.get_node_id_subsets(node_id, population_name)
                for electrode_factors in subset_data:
                    scalar_factors.append(Nd.Vector(electrode_factors))
            except (KeyError, IndexError) as e:
                logging.warning("Node id {} not found in the electrodes file for population {}: {}"
                                .format(node_id, population_name, str(e)))
        return scalar_factors

    def get_number_electrodes(self, gid, population_info=("default", 0)):
        """Get number of electrodes of a certain gid
        """
        num_electrodes = 0
        if self._lfp_file:
            try:
                population_name, node_id = self.get_sonata_node_id(gid, population_info)
                subset_data = self.get_node_id_subsets(node_id, population_name)
                num_electrodes = subset_data.shape[1]
            except (KeyError, IndexError) as e:
                logging.warning("Node id {} not found in the electrodes file for population {}: {}"
                                .format(node_id, population_name, str(e)))
        return num_electrodes
