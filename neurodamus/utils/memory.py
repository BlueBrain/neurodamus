"""
Collection of utility functions related to clearing the used memory in neurodamus-py or NEURON
"""
import ctypes
import ctypes.util
import logging
import math
import os
import json
import psutil
import multiprocessing
import heapq
import pickle
import gzip
from collections import Counter
from typing import Tuple

from ..core import MPI, NeurodamusCore as Nd, run_only_rank0
from .compat import Vector
from collections import defaultdict
from ..io.sonata_config import ConnectionTypes

import numpy as np

# The factor to multiply the cell + synapses memory usage by to get the simulation memory estimate.
# This is an heuristic estimate based on tests on multiple circuits.
# More info in docs/architecture.rst.
SIM_ESTIMATE_FACTOR = 2.5


def trim_memory():
    """
    malloc_trim - release free memory from the heap (back to the OS)

    * We should only run malloc_trim if we are using the default glibc memory allocator.
    When using a custom allocator such as jemalloc, this could cause unexpected behavior
    including segfaults.

    * The malloc_trim function returns 1 if memory was actually
    released back to the system, or 0 if it was not possible to
    release any memory.
    """

    if os.getenv("LD_PRELOAD") and "jemalloc" in os.getenv("LD_PRELOAD"):
        logging.warning("malloc_trim works only with the default glibc memory allocator. "
                        "Please avoid using jemalloc (for now, we skip malloc_trim).")
        logging.info("malloc_trim: not possible to release any memory.")
    else:
        try:
            path_libc = ctypes.util.find_library("c")
            libc = ctypes.CDLL(path_libc)
            memory_trimmed = libc.malloc_trim(0)
            if memory_trimmed:
                logging.info("malloc_trim: memory released back to the system.")
        except (OSError, AttributeError):
            logging.error("Unable to call malloc_trim.")
            logging.info("malloc_trim: not possible to release any memory.")


def pool_shrink():
    """
    Shrink NEURON ArrayPools to the exact size still being used by NEURON.
    This is useful when clearing all the Nodes from NEURON (cells and synapses) and the underlying
    data structures holding the data of their mechanisms need to be shrinked down since they are
    not used any more.
    This feature is enabled in NEURON after version 8.2.2a.
    See https://github.com/neuronsimulator/nrn/pull/2033 for more information.
    """
    try:
        cv = Nd.CVode()
        cv.poolshrink(1)
    except AttributeError:
        logging.warning("Cannot shrink NEURON ArrayPools. "
                        "NEURON does not support CVode().poolshrink(1)")


def free_event_queues():
    """
    Apart from the NEURON SelfEventQueue and TQItem pools being clear we also free them from any
    memory still referencing to.
    """
    try:
        cv = Nd.CVode()
        cv.free_event_queues()
    except AttributeError:
        logging.warning("Cannot clear NEURON event queues."
                        "NEURON does not support CVode().free_event_queues()")


def print_node_level_mem_usage():
    """Print statistics of the memory usage per compute node."""
    from ..core._shmutils import SHMUtil

    # The association of MPI ranks to compute nodes isn't
    # always know. If unknown, don't print anything.
    if not SHMUtil.is_node_id_known():
        return

    rss = SHMUtil.get_nodewise_rss()

    min_usage_mb = np.min(rss) / 2**20
    max_usage_mb = np.max(rss) / 2**20
    avg_usage_mb = np.mean(rss) / 2**20
    dev_usage_mb = np.std(rss) / 2**20

    logging.info(
        "Memusage (RSS) per node [MB]: Max=%.2lf, Min=%.2lf, Mean(Stdev)=%.2lf(%.2lf)",
        max_usage_mb,
        min_usage_mb,
        avg_usage_mb,
        dev_usage_mb
    )


def get_task_level_mem_usage():
    """Return statistics of the memory usage per MPI task."""
    usage_mb = get_mem_usage_kb() / 1024

    min_usage_mb = MPI.pc.allreduce(usage_mb, MPI.MIN)
    max_usage_mb = MPI.pc.allreduce(usage_mb, MPI.MAX)
    avg_usage_mb = MPI.pc.allreduce(usage_mb, MPI.SUM) / MPI.size

    dev_usage_mb = math.sqrt(MPI.pc.allreduce((usage_mb - avg_usage_mb) ** 2, MPI.SUM) / MPI.size)

    return min_usage_mb, max_usage_mb, avg_usage_mb, dev_usage_mb


def print_task_level_mem_usage():
    """Print statistics of the memory usage per MPI task."""

    min_usage_mb, max_usage_mb, avg_usage_mb, dev_usage_mb = get_task_level_mem_usage()

    logging.info(
        "Memusage (RSS) per task [MB]: Max=%.2lf, Min=%.2lf, Mean(Stdev)=%.2lf(%.2lf)",
        max_usage_mb,
        min_usage_mb,
        avg_usage_mb,
        dev_usage_mb
    )


def print_mem_usage():
    """
    Print memory usage information across all ranks.
    """

    print_node_level_mem_usage()
    print_task_level_mem_usage()


def get_mem_usage_kb():
    """
    Return memory usage information across all ranks, in KiloBytes
    """
    usage_kb = psutil.Process(os.getpid()).memory_info().rss / 1024

    return usage_kb


def pretty_printing_memory_mb(memory_mb):
    """
    A simple function that given a memory usage in MB
    returns a string with the most appropriate unit.
    """
    if memory_mb < 1024:
        return "%.2lf MB" % memory_mb
    elif memory_mb < 1024 ** 2:
        return "%.2lf GB" % (memory_mb / 1024)
    elif memory_mb < 1024 ** 3:
        return "%.2lf TB" % (memory_mb / 1024 ** 2)
    else:
        return "%.2lf PB" % (memory_mb / 1024 ** 3)


@run_only_rank0
def print_allocation_stats(rank_memory):
    """
    Print statistics of the memory allocation across ranks.

    Args:
        rank_memory (dict): A dictionary where keys are rank IDs
                            and values are the total memory load on each rank.
    """
    logging.debug("Total memory per rank/cycle: {}".format(rank_memory))
    import statistics
    for pop, rank_dict in rank_memory.items():
        values = list(rank_dict.values())
        logging.info("Population: {}".format(pop))
        logging.info("Mean allocation per rank [KB]: {}".format(round(statistics.mean(values))))
        try:
            stdev = round(statistics.stdev(values))
        except statistics.StatisticsError:
            stdev = 0
        logging.info("Stdev of allocation per rank [KB]: {}".format(stdev))


@run_only_rank0
def export_allocation_stats(rank_allocation, filename, ranks, cycles=1):
    """
    Export allocation dictionary to a serialized pickle file.
    """

    compressed_data = gzip.compress(pickle.dumps(rank_allocation))
    new_filename = f"{filename}_r{ranks}_c{cycles}.pkl.gz"
    with open(new_filename, 'wb') as f:
        f.write(compressed_data)


@run_only_rank0
def export_metype_memory_usage(memory_per_metype, memory_per_metype_file):
    """
    Export memory per METype dictionary to a JSON file.
    """

    with open(memory_per_metype_file, 'w') as f:
        json.dump(memory_per_metype, f, indent=4)


@run_only_rank0
def import_metype_memory_usage(memory_per_metype_file):
    """
    Import memory per METype dictionary from a JSON file.
    """

    with open(memory_per_metype_file, 'r') as f:
        memory_per_metype = json.load(f)

    return memory_per_metype


@run_only_rank0
def import_allocation_stats(filename, cycle_i=0) -> dict:
    """
    Import allocation dictionary from serialized pickle file.
    """
    def convert_to_standard_types(obj):
        """Converts an object containing defaultdicts of Vectors to standard Python types."""
        result = {}
        for population, vectors in obj.items():
            result[population] = {key: np.array(vector) for key,
                                  vector in vectors.items() if key[1] == cycle_i}
        return result

    with gzip.open(filename, 'rb') as f:
        data = pickle.load(f)

    return convert_to_standard_types(data)


@run_only_rank0
def allocation_stats_exists(filename):
    """
    Check if the allocation stats file exists.
    """
    return os.path.exists(filename)


class SynapseMemoryUsage:
    ''' A small class that works as a lookup table
    for the memory used by each type of synapse.
    The values are in KB. The values cannot be set by the user.
    '''
    _synapse_memory_usage = {
        ConnectionTypes.Synaptic: 1.9,  # Average between 1.7 (AMPA) and 2.0 (GABAAB)
        ConnectionTypes.GapJunction: 2.0,
    }

    @classmethod
    def get_memory_usage(cls, count, synapse_type=ConnectionTypes.Synaptic):
        return count * cls._synapse_memory_usage[synapse_type]


class DryRunStats:
    _MEMORY_USAGE_FILENAME = "cell_memory_usage.json"
    _ALLOCATION_FILENAME = "allocation"
    _MEMORY_USAGE_PER_METYPE_FILENAME = "memory_per_metype.json"

    @staticmethod
    def defaultdict_vector():
        return defaultdict(Vector)

    @staticmethod
    def defaultdict_float():
        return defaultdict(float)

    def __init__(self) -> None:
        self.metype_memory = {}
        self.metype_cell_syn_average = Counter()
        self.pop_metype_gids = {}
        self.metype_counts = Counter()
        self.synapse_counts = defaultdict(int)  # [syn_type -> count]
        self.suggested_nodes = 0
        self.synapse_memory_total = 0
        _, _, self.base_memory, _ = get_task_level_mem_usage()

    @run_only_rank0
    def estimate_cell_memory(self) -> float:
        from .logging import log_verbose
        memory_total = 0
        log_verbose("+{:=^81}+".format(" METype Memory Estimates (MiB) "))
        log_verbose("| {:^40s} | {:^10s} | {:^10s} | {:^10s} |".format(
            'METype', 'Mem/cell', 'N Cells', 'Mem Total'))
        log_verbose("+{:-^81}+".format(""))
        for metype, count in self.metype_counts.items():
            metype_mem = self.metype_memory[metype] / 1024
            metype_total = count * metype_mem
            memory_total += metype_total
            log_verbose("| {:<40s} | {:10.2f} | {:10.0f} | {:10.1f} |".format(
                metype, metype_mem, count, metype_total))
        log_verbose("+{:-^81}+".format(""))
        self.cell_memory_total = memory_total
        logging.info("  Total memory usage for cells: %s", pretty_printing_memory_mb(memory_total))
        return memory_total

    def add(self, other):
        self.metype_memory.update(other.metype_memory)
        self.metype_counts += other.metype_counts

    def collect_all_mpi(self):
        # We combine memory dict via update(). That means if a previous circuit computed
        # cells for the same METype (hopefully unlikely!) the last estimate prevails.
        self.metype_memory = MPI.py_reduce(self.metype_memory, {}, lambda x, y: x.update(y))
        self.metype_cell_syn_average = MPI.py_sum(self.metype_cell_syn_average, Counter())
        self.metype_counts = self.metype_counts  # Cell counts is complete in every rank

    @run_only_rank0
    def export_cell_memory_usage(self):
        with open(self._MEMORY_USAGE_FILENAME, 'w') as fp:
            json.dump(self.metype_memory, fp, sort_keys=True, indent=4)

    def try_import_cell_memory_usage(self):
        if not os.path.exists(self._MEMORY_USAGE_FILENAME):
            return
        logging.info("Loading memory usage from %s...", self._MEMORY_USAGE_FILENAME)
        with open(self._MEMORY_USAGE_FILENAME, 'r') as fp:
            self.metype_memory = json.load(fp)

    def collect_display_syn_counts(self):
        from .logging import log_verbose
        master_counter = MPI.py_sum(self.synapse_counts, Counter())

        # Done with MPI. Use rank0 to display
        if MPI.rank != 0:
            return

        logging.info(" - Estimated synapse memory usage (MB):")
        log_verbose("+{:=^68}+".format(" Synapse Count "))
        log_verbose("| {:^40s} | {:^10s} | {:^10s} |".format("Synapse Type", "Count", "Memory"))
        log_verbose("+{:-^68}+".format(""))

        # Some synapse types are numeric, others are strings, so we need to handle both
        for syn_type, count in master_counter.items():
            mem_mb = SynapseMemoryUsage.get_memory_usage(count, syn_type) / 1024
            self.synapse_memory_total += mem_mb
            mem_str = pretty_printing_memory_mb(mem_mb)
            log_verbose("| {:<40s} | {:10.0f} | {:>10s} |".format(str(syn_type), count, mem_str))

        log_verbose("+{:-^68}+".format(""))  # Close table
        logging.info(" - TOTAL : %s", pretty_printing_memory_mb(self.synapse_memory_total))

    @run_only_rank0
    def display_total(self):
        logging.info("+{:=^57}+".format(" Total Memory Estimates "))
        logging.info("| {:^40s} | {:^12s} |".format("Item", "Memory (MiB)"))
        logging.info("+{:-^57}+".format(""))
        full_overhead = self.base_memory * MPI.size
        logging.info("| {:<40s} | {:12.1f} |".format(f"Overhead (ranks={MPI.size})", full_overhead))
        logging.info("| {:<40s} | {:12.1f} |".format("Cells", self.cell_memory_total))
        logging.info("| {:<40s} | {:12.1f} |".format("Synapses", self.synapse_memory_total))
        self.simulation_estimate = (self.cell_memory_total
                                    + self.synapse_memory_total) * SIM_ESTIMATE_FACTOR
        logging.info("| {:<40s} | {:12.1f} |".format("Simulation", self.simulation_estimate))
        logging.info("+{:-^57}+".format(""))
        grand_total = (full_overhead
                       + self.cell_memory_total
                       + self.synapse_memory_total
                       + self.simulation_estimate)
        grand_total = pretty_printing_memory_mb(grand_total)
        logging.info("| {:<40s} | {:>12s} |".format("GRAND TOTAL", grand_total))
        logging.info("+{:-^57}+".format(""))

    def total_memory_available():
        """
        Returns the total memory available in the system in MB
        """
        try:
            virtual_memory = psutil.virtual_memory()
            return virtual_memory.total / (1024 * 1024)  # Total available memory in MB
        except Exception as e:
            logging.error(f"Error: {e}")
            return None

    @run_only_rank0
    def suggest_nodes(self, margin):
        """
        A function to calculate the suggested number of nodes to run the simulation
        The function takes into account the fact that the memory overhead is
        variable with the amount of ranks the simulation it's ran with.
        One can also specify a custom margin to add to the memory usage.
        """

        try:
            ranks_per_node = os.cpu_count()
        except AttributeError:
            ranks_per_node = multiprocessing.cpu_count()

        full_overhead = self.base_memory * ranks_per_node

        # initialize variable for iteration
        est_nodes = 0
        prev_est_nodes = None
        max_iter = 5
        iter_count = 0

        while (prev_est_nodes is None or est_nodes != prev_est_nodes) and iter_count < max_iter:
            prev_est_nodes = est_nodes
            simulation_estimate = (self.cell_memory_total +
                                   self.synapse_memory_total) * SIM_ESTIMATE_FACTOR
            mem_usage_per_node = (full_overhead
                                  + self.cell_memory_total
                                  + self.synapse_memory_total
                                  + simulation_estimate)
            mem_usage_with_margin = mem_usage_per_node * (1 + margin)
            est_nodes = math.ceil(mem_usage_with_margin / DryRunStats.total_memory_available())
            full_overhead = self.base_memory * ranks_per_node * est_nodes
            iter_count += 1

        return est_nodes

    @run_only_rank0
    def display_node_suggestions(self):
        """
        Display suggestions for how many nodes are approximately
        necessary to run the simulation based on the memory available
        on the current node.
        """
        node_total_memory = DryRunStats.total_memory_available()
        if node_total_memory is None:
            logging.warning("Unable to get the total memory available on the current node.")
            return
        self.suggested_nodes = self.suggest_nodes(0.3)
        logging.info(f"Based on the memory available on the current node, "
                     f"it is suggested to use at least {self.suggested_nodes} node(s).")
        logging.info("This is just a suggestion and the actual number of nodes "
                     "needed to run the simulation may be different.")
        logging.info(f"The calculation was based on a total memory available of "
                     f"{pretty_printing_memory_mb(node_total_memory)} on the current node.")
        logging.info("Please remember that it is suggested to use the same class of nodes "
                     "for both the dryrun and the actual simulation.")

    def get_num_target_ranks(self, num_ranks):
        """
        Return the number of ranks to target for dry-run load balancing
        """
        if num_ranks is None:
            logging.info("No number of ranks specified. Using suggested number of nodes.")
            logging.info("Detected number of physical cores: %d", psutil.cpu_count(logical=False))
            return self.suggested_nodes * psutil.cpu_count(logical=False)
        else:
            return int(num_ranks)

    @run_only_rank0
    def distribute_cells(
        self,
        num_ranks,
        cycles=None,
        metype_file=None,
        batch_size=10
    ) -> Tuple[dict, dict, dict]:
        """
        Distributes cells across ranks and cycles based on their memory load.

        This function uses a greedy algorithm to distribute cells across ranks and cycles such that
        the total memory load is balanced. Cells with higher memory load are distributed first.

        Args:
            num_ranks (int): The number of ranks.
            cycles (int): The number of cycles to distribute cells over.
            batch_size (int): The number of cells to assign to each bucket at a time.
            metype_file (str): The path to a JSON file containing memory usage for each METype.

        Returns:
            bucket_allocation (dict): A dictionary where keys are tuples (pop, rank_id, cycle_id)
                                    and values are lists of cell IDs assigned to each bucket.
            bucket_memory (dict): A dictionary where keys are tuples (pop, rank_id, cycle_id)
                                and values are the total memory load on each bucket.
            metype_memory_usage (dict): A dictionary where keys are METype IDs
                                        and values are the memory load of each METype.
        """
        logging.info("Distributing cells across %d ranks and %d cycles", num_ranks, cycles)

        self.validate_inputs_distribute(num_ranks, batch_size)
        bucket_allocation = defaultdict(DryRunStats.defaultdict_vector)
        bucket_memory = defaultdict(DryRunStats.defaultdict_float)

        # Prepare the memory usage for each METype
        if metype_file:
            metype_memory_usage = import_metype_memory_usage(metype_file)
        else:
            metype_memory_usage = {}
            for metype, metype_mem in self.metype_memory.items():
                syns_mem = SynapseMemoryUsage.get_memory_usage(self.metype_cell_syn_average[metype])
                metype_memory_usage[metype] = metype_mem + syns_mem
            export_metype_memory_usage(metype_memory_usage, self._MEMORY_USAGE_PER_METYPE_FILENAME)

        def assign_cells_to_bucket(rank_allocation, rank_memory, batch, batch_memory):
            total_memory, (rank_id, cycle_id) = heapq.heappop(buckets)
            logging.debug("Assigning batch to bucket (%d, %d)", rank_id, cycle_id)
            rank_allocation[(rank_id, cycle_id)].extend(batch)
            total_memory += batch_memory
            rank_memory[(rank_id, cycle_id)] = total_memory
            heapq.heappush(buckets, (total_memory, (rank_id, cycle_id)))

        # Loop over ALL the gids which would be instantiated, per metype
        for pop, metype_gids in self.pop_metype_gids.items():
            logging.info("Distributing cells of population %s", pop)
            rank_allocation = defaultdict(Vector)
            rank_memory = {}
            batch = []
            batch_memory = 0

            # (total_memory, (rank_id, cycle_id))
            buckets = [(0, (i, j)) for i in range(num_ranks) for j in range(cycles)]
            heapq.heapify(buckets)

            for metype, gids in metype_gids.items():
                total_mem_per_cell = metype_memory_usage[metype]

                for cell_id in gids:
                    batch.append(cell_id)
                    batch_memory += total_mem_per_cell
                    if len(batch) == batch_size[pop]:
                        assign_cells_to_bucket(rank_allocation, rank_memory, batch, batch_memory)
                        batch = []
                        batch_memory = 0

            if batch:
                assign_cells_to_bucket(rank_allocation, rank_memory, batch, batch_memory)

            bucket_allocation[pop] = rank_allocation
            bucket_memory[pop] = rank_memory
        return bucket_allocation, bucket_memory, metype_memory_usage

    def validate_inputs_distribute(self, num_ranks, batch_size):
        assert isinstance(num_ranks, int), "num_ranks must be an integer"
        assert num_ranks > 0, "num_ranks must be a positive integer"
        assert isinstance(batch_size, dict), "batch_size must be a dict"
        assert all(size > 0 for size in batch_size.values()), "batch_size must be positive"

        all_metypes = set()
        for values in self.pop_metype_gids.values():
            all_metypes.update(values.keys())

        # Assert our simulated metypes are a subset of the (pre-) computed ones
        cell_memory_metypes = set(self.metype_memory.keys())
        assert all_metypes <= cell_memory_metypes, all_metypes - cell_memory_metypes

        # NOTE: We shall not assume that we have synapses counts for all metypes
        #       According to override blocks, some cells may be disconnected.
        #       Also Counter() will discard 0-count entries
        # syn_count_metypes = set(self.metype_cell_syn_average)
        # assert all_metypes <= syn_count_metypes, all_metypes - syn_count_metypes

    def check_all_buckets_have_gids(self, bucket_allocation, num_ranks, cycles):
        """
        Checks if all possible buckets determined by num_ranks and cycles have at least one GID
        assigned.

        Args:
            bucket_allocation (dict): The allocation dictionary containing the assignment of GIDs
                                      to ranks and cycles.
            num_ranks (int): The number of ranks.
            cycles (int): The number of cycles.

        Returns:
            bool: True if all buckets have at least one GID assigned, False otherwise.
        """
        for pop, rank_allocation in bucket_allocation.items():
            for rank_id in range(num_ranks):
                for cycle_id in range(cycles):
                    if not rank_allocation.get((rank_id, cycle_id)):
                        logging.warning(f"Bucket ({rank_id}, {cycle_id}) in population '{pop}' "
                                        f"has no GIDs assigned.")
                        return False
        return True

    @run_only_rank0
    def distribute_cells_with_validation(self,
                                         num_ranks,
                                         cycles=None,
                                         metype_file=None
                                         ) -> Tuple[dict, dict, dict]:
        """
        Wrapper function to distribute cells with ever smaller assignment batches until
        all buckets have at least one GID assigned (or fail if no valid distribution is found).

        Args:
            num_ranks (int): The number of ranks.
            cycles (int): The number of cycles to distribute cells over.
            metype_file (str): The path to a JSON file containing memory usage for each METype.

        Returns:
            Tuple[dict, dict, dict]: Returns the same as distribute_cells once a valid distribution
                                     is found.
        """
        if not cycles:
            cycles = 1

        valid_distribution = False

        def calculate_total_elements_per_population(self):
            total_elements_per_population = {}
            for population, metypes in self.pop_metype_gids.items():
                total_elements = sum(len(gids) for gids in metypes.values())
                total_elements_per_population[population] = total_elements
            return total_elements_per_population

        total_cells_per_population = calculate_total_elements_per_population(self)
        average_cells_per_population = {
            population: total / (num_ranks * cycles)
            for population, total in total_cells_per_population.items()}

        batch_size = {
            population: max(1, int(average / 10))
            for population, average in average_cells_per_population.items()}

        while not valid_distribution and any(size > 0 for size in batch_size.values()):
            bucket_allocation, bucket_memory, metype_memory_usage = self.distribute_cells(
                num_ranks, cycles, metype_file, batch_size=batch_size
            )
            valid_distribution = self.check_all_buckets_have_gids(bucket_allocation,
                                                                  num_ranks,
                                                                  cycles)
            if not valid_distribution:
                batch_size = {population: max(0, size - 1)
                              for population, size in batch_size.items()}

        if all(size == 0 for size in batch_size.values()):
            raise RuntimeError("Unable to find a valid distribution with the given parameters. "
                               "Please try again with a smaller number of ranks or cycles. "
                               "No allocation file was created.")

        print_allocation_stats(bucket_memory)
        export_allocation_stats(bucket_allocation,
                                self._ALLOCATION_FILENAME,
                                num_ranks,
                                cycles)

        return bucket_allocation, bucket_memory, metype_memory_usage
