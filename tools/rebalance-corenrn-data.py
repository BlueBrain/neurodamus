#!/bin/env python3

"""
A post-processing script to redistribute CoreNeuron input files
more evenly across ranks based on their filesystem size.

Blue Brain Project - EPFL, 2024

"""

import argparse
import heapq
import itertools
import logging
import math
import os
import sys

# Numpy may be required (histogram)
numpy = None

DEFAULT_OUTPUT_FILE = "rebalanced-files.dat"
CORENRN_SKIP_MARK = "-1"
PROGRESS_STEPS = 50
DEFAULT_HISTOGRAM_NBINS = 40
DEFAULT_RANKS_PER_MACHINE = 40


def distribute_dat_to_bucket(dat_entry, size, buckets, bucket_sizes):
    """
    Distribute a single file into the bucket with the least total size.
    """
    # Pop the bucket with the smallest size
    smallest_size, smallest_bucket_index = heapq.heappop(bucket_sizes)
    # Assign the file to this bucket
    buckets[smallest_bucket_index].append(dat_entry)
    # Update the bucket size in the heap
    new_size = smallest_size + size
    heapq.heappush(bucket_sizes, (new_size, smallest_bucket_index))


def redistribute_files_dat(files_dat_file, n_buckets, max_entries=None, show_stats=False):
    """
    Read and process each entry from the dat file and distribute them into buckets.
    """
    base_dir = os.path.dirname(files_dat_file)
    metadata = {}

    logging.debug("Reading distribution file: %s", files_dat_file)
    with open(files_dat_file, "r") as file:
        # read header
        metadata["version"] = file.readline().strip()
        n_entries = file.readline()

        metadata["n_files"] = max_entries or n_entries

        # read all dat entries
        dat_entries = file.readlines()

    if (n_files := int(metadata["n_files"])) < len(dat_entries):
        logging.warning("files.dat: processing reduced number of entries: %d", n_files)
        dat_entries = dat_entries[:n_files]

    logging.info("Distributing files into %d buckets...", n_buckets)

    if len(dat_entries) < n_buckets:
        raise RuntimeError("Too little data for selected number of ranks. Specify less")

    # Initialize empty buckets
    buckets = [[] for _ in range(n_buckets)]

    # Create a heap to keep track of bucket sizes. Each entry is (bucket_size, bucket_index)
    bucket_heap = [(0, i) for i in range(n_buckets)]
    heapq.heapify(bucket_heap)  # Turn the list into a heap

    dat_entries = [entry.strip() for entry in dat_entries]
    entry_sizes = [(entry, get_entry_size(base_dir, entry)) for entry in with_progress(dat_entries)]
    # Knapsack: sort entries from larger to smaller,
    entry_sizes = sorted(entry_sizes, key=lambda e: e[1], reverse=True)

    for dat_entry, size in entry_sizes:
        try:
            distribute_dat_to_bucket(dat_entry, size, buckets, bucket_heap)
        except Exception as e:
            raise RuntimeError(f"Error processing dat entry {dat_entry}") from e

    if show_stats:
        logging.info("Top 10 machines accumulated sizes")
        for size, mach_i in heapq.nlargest(10, bucket_heap):
            print(f"  Machine {mach_i}: {size/(1024*1024):.1f} MiB")

        mach_sizes = [bucket[0] for bucket in bucket_heap]
        show_histogram(mach_sizes)

    return buckets, metadata


def write_dat_file(buckets, infos: dict, ranks_per_machine, output_file="rebalanced-files.dat"):
    """
    Output the result after processing all directories
    """
    DEFAULT_LINE = f"{CORENRN_SKIP_MARK}\n" * ranks_per_machine
    logging.info("Writing out data from %d buckets to file: %s", len(buckets), output_file)

    # CoreNeuron does RoundRobin - we need to transpose the entries
    # When a sequence finishes use "-1" (to keep in sync)

    def batch(iterable, first=0):
        last = first + ranks_per_machine
        group = iterable[first:last]
        while group:
            if len(group) < ranks_per_machine:
                yield group + [CORENRN_SKIP_MARK] * (ranks_per_machine - len(group))
                break
            yield group
            first, last = last, last + 40
            group = iterable[first:last]

    with open(output_file, "w") as out:
        print(infos["version"], file=out)
        print(infos["n_files"], file=out)

        for buckets in itertools.zip_longest(*[batch(m) for m in buckets]):
            for entries in buckets:
                if entries is None:
                    out.write(DEFAULT_LINE)
                else:
                    for entry in entries:
                        out.write(entry + "\n")


def get_entry_size(base_dir, dat_entry):
    """Obtain the file size of a dat entry"""
    dat_file = f"{dat_entry}_2.dat"
    file_path = os.path.join(base_dir, dat_file)
    return os.path.getsize(file_path)


def with_progress(elements):
    """A quick and easy generator for displaying progress while iterating"""
    total_elems = len(elements)
    report_every = math.ceil(total_elems / PROGRESS_STEPS)
    logging.info(f"Processing {total_elems} entries")
    for i, elem in enumerate(elements):
        if i % report_every == 0:
            print(f"{i:10} [{i*100/total_elems:3.0f}%]", file=sys.stderr)
        yield elem


def show_histogram(buckets, n_bins=DEFAULT_HISTOGRAM_NBINS):
    """A simple histogram CLI visualizer"""
    logging.info("Histogram of the Machine accumulated data")
    freq, bins = numpy.histogram(buckets, bins=n_bins)
    bin_start = bins[0]
    for count, bin_end in zip(freq, bins[1:]):
        if count:
            print(f"  [{bin_start/(1024*1024):5.0f} - {bin_end/(1024*1024):5.0f}]: {count:0d}")
        bin_start = bin_end


def main():
    parser = argparse.ArgumentParser(
        usage="%(prog)s  [OPTION]...  <input_file>  <n_machines>",
        description="Redistribute CoreNeuron dat files, optimizing for a given number of Machines",
    )
    parser.add_argument(
        "input_file",
        type=str,
        help="Path to the CoreNeuron input file, typically files.dat",
    )
    parser.add_argument(
        "n_machines", type=int, help="The number of target machines running the simulation"
    )
    parser.add_argument(
        "--ranks-per-machine",
        type=int,
        default=DEFAULT_RANKS_PER_MACHINE,
        help=f"Number of ranks per machine (default: {DEFAULT_RANKS_PER_MACHINE})",
    )
    parser.add_argument(
        "--max-entries",
        type=int,
        default=None,
        help="Consider only the first N entries of the input file",
    )
    parser.add_argument(
        "--output-file",
        default=DEFAULT_OUTPUT_FILE,
        help="The rebalanced output file path",
    )
    # Optional argument for verbose output
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output for debugging.",
    )
    parser.add_argument(
        "--histogram",
        action="store_true",
        help="Additionally display the histogram of the machine accumulated sizes",
    )

    args = parser.parse_args()

    logging_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=logging_level, format="%(levelname)s :: %(message)s")

    if args.histogram:
        global numpy
        import numpy

    if not os.path.isfile(args.input_file):
        logging.error("Input file could not be found!")
        return 1
    else:
        logging.info(f"Reading from input file: {args.input_file}")

    # Do the redistribution
    buckets, infos = redistribute_files_dat(
        args.input_file, args.n_machines, args.max_entries, args.histogram
    )

    # Create a new files.dat according to the new buckets
    write_dat_file(buckets, infos, args.ranks_per_machine, args.output_file)

    logging.info("DONE")


if __name__ == "__main__":
    sys.exit(main())
