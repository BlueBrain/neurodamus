"""
Collection of utility functions related to clearing the used memory in neurodamus-py or NEURON
"""
from collections import Counter
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

from ..core import MPI, NeurodamusCore as Nd, run_only_rank0
from .compat import Vector
from collections import defaultdict

import numpy as np


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
def print_allocation_stats(rank_allocation, rank_memory):
    """
    Print statistics of the memory allocation across ranks.

    Args:
        rank_allocation (dict): A dictionary where keys are rank IDs and
                                values are lists of cell IDs assigned to each rank.
        rank_memory (dict): A dictionary where keys are rank IDs
                            and values are the total memory load on each rank.
    """
    logging.debug("Rank allocation: {}".format(rank_allocation))
    logging.debug("Total memory per rank: {}".format(rank_memory))
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
def export_allocation_stats(rank_allocation, filename):
    """
    Export allocation dictionary to serialized pickle file.
    """
    compressed_data = gzip.compress(pickle.dumps(rank_allocation))
    with open(filename, 'wb') as f:
        f.write(compressed_data)


@run_only_rank0
def import_allocation_stats(filename) -> dict:
    """
    Import allocation dictionary from serialized pickle file.
    """
    def convert_to_standard_types(obj):
        """Converts an object containing defaultdicts of Vectors to standard Python types."""
        result = {}
        for node, vectors in obj.items():
            result[node] = {key: np.array(vector) for key, vector in vectors.items()}
        return result

    with open(filename, 'rb') as f:
        compressed_data = f.read()

    return convert_to_standard_types(pickle.loads(gzip.decompress(compressed_data)))


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
        "ProbAMPANMDA": 1.7,
        "ProbGABAAB": 2.0,
        "Gap": 2.0,
        "Glue": 0.5
    }

    @classmethod
    def get_memory_usage(cls, count, synapse_type):
        return count * cls._synapse_memory_usage[synapse_type]


class DryRunStats:
    _MEMORY_USAGE_FILENAME = "cell_memory_usage.json"
    _ALLOCATION_FILENAME = "allocation.pkl.gz"

    def __init__(self) -> None:
        self.metype_memory = {}
        self.average_syns_per_cell = {}
        self.metype_gids = {}
        self.metype_counts = Counter()
        self.synapse_counts = Counter()
        self.suggested_nodes = 0
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
        self.average_syns_per_cell = MPI.py_reduce(self.average_syns_per_cell, {},
                                                   lambda x, y: x.update(y))
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
        master_counter = MPI.py_sum(self.synapse_counts, Counter())

        # Done with MPI. Use rank0 to display
        if MPI.rank != 0:
            return

        logging.info(" - Estimated synapse memory usage (MB):")
        from .logging import log_verbose
        inh_count = exc_count = 0
        log_verbose("+{:=^68}+".format(" Synapse Count "))
        log_verbose("| {:^40s} | {:^10s} | {:^10s} |".format("Synapse Type", "Family", "Count"))
        log_verbose("+{:-^68}+".format(""))
        for syn_type, count in sorted(master_counter.items()):
            is_inh = syn_type < 100
            syn_type_str = "INH" if is_inh else "EXC"
            log_verbose("| {:40.0f} | {:<10s} | {:10.0f} |".format(syn_type, syn_type_str, count))
            if is_inh:
                inh_count += count
            else:
                exc_count += count
        log_verbose("+{:-^68}+".format(""))

        in_mem = SynapseMemoryUsage.get_memory_usage(inh_count, "ProbGABAAB") / 1024
        ex_mem = SynapseMemoryUsage.get_memory_usage(exc_count, "ProbAMPANMDA") / 1024
        self.synapse_memory_total = in_mem + ex_mem
        logging.info("   - Inhibitory: %s", pretty_printing_memory_mb(in_mem))
        logging.info("   - Excitatory: %s", pretty_printing_memory_mb(ex_mem))
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
        logging.info("+{:-^57}+".format(""))
        grand_total = full_overhead + self.cell_memory_total + self.synapse_memory_total
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
            mem_usage_per_node = full_overhead + self.cell_memory_total + self.synapse_memory_total
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

    @run_only_rank0
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
    def distribute_cells(self, num_ranks, batch_size=10) -> (dict, dict):
        """
        Distributes cells across ranks based on their memory load.

        This function uses a greedy algorithm to distribute cells across ranks such that
        the total memory load is balanced. Cells with higher memory load are distributed first.

        Args:
            dry_run_stats (DryRunStats): A DryRunStats object.
            num_ranks (int): The number of ranks.

        Returns:
            rank_allocation (dict): A dictionary where keys are rank IDs and
                                    values are lists of cell IDs assigned to each rank.
            rank_memory (dict): A dictionary where keys are rank IDs
                                and values are the total memory load on each rank.
        """
        logging.info("Distributing cells across %d ranks", num_ranks)

        self.validate_inputs_distribute(num_ranks, batch_size)

        # Multiply the average number of synapses per cell by 2.0
        # This is done since the biggest memory load for a synapse is 2.0 kB and at this point in
        # the code we have lost the information on whether they are excitatory or inhibitory
        # so we just take the biggest value to be safe. (the difference between the two is minimal)
        average_syns_mem_per_cell = {k: v * 2.0 for k, v in self.average_syns_per_cell.items()}

        # Prepare a list of tuples (cell_id, memory_load)
        # We sum the memory load of the cell type and the average number of synapses per cell
        def generate_cells(metype_gids):
            for cell_type, gids in metype_gids.items():
                memory_usage = (self.metype_memory[cell_type] +
                                average_syns_mem_per_cell[cell_type])
                for gid in gids:
                    yield gid, memory_usage

        ranks = [(0, i) for i in range(num_ranks)]  # (total_memory, rank_id)
        heapq.heapify(ranks)
        all_allocation = {}
        all_memory = {}

        def assign_cells_to_rank(rank_allocation, rank_memory, batch, batch_memory):
            total_memory, rank_id = heapq.heappop(ranks)
            logging.debug("Assigning batch to rank %d", rank_id)
            rank_allocation[rank_id].extend(batch)
            total_memory += batch_memory
            rank_memory[rank_id] = total_memory
            heapq.heappush(ranks, (total_memory, rank_id))

        for pop, metype_gids in self.metype_gids.items():
            logging.info("Distributing cells of population %s", pop)
            rank_allocation = defaultdict(Vector)
            rank_memory = {}
            batch = []
            batch_memory = 0

            for cell_id, memory in generate_cells(metype_gids):
                batch.append(cell_id)
                batch_memory += memory
                if len(batch) == batch_size:
                    assign_cells_to_rank(rank_allocation, rank_memory, batch, batch_memory)
                    batch = []
                    batch_memory = 0

            if batch:
                assign_cells_to_rank(rank_allocation, rank_memory, batch, batch_memory)

            all_allocation[pop] = rank_allocation
            all_memory[pop] = rank_memory

        print_allocation_stats(all_allocation, all_memory)
        export_allocation_stats(all_allocation, self._ALLOCATION_FILENAME)

        return all_allocation, rank_memory

    def validate_inputs_distribute(self, num_ranks, batch_size):
        assert isinstance(num_ranks, int), "num_ranks must be an integer"
        assert num_ranks > 0, "num_ranks must be a positive integer"
        assert isinstance(batch_size, int), "batch_size must be an integer"
        assert batch_size > 0, "batch_size must be a positive integer"
        set_metype_gids = set()
        for values in self.metype_gids.values():
            set_metype_gids.update(values.keys())
        assert set_metype_gids == set(self.metype_memory.keys())
        average_syns_keys = set(self.average_syns_per_cell.keys())
        metype_memory_keys = set(self.metype_memory.keys())
        assert average_syns_keys == metype_memory_keys
