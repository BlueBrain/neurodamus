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


def distribute_dat_to_bucket(dat_entry, size, buckets, bucket_sizes, base_dir="."):
    """
    Distribute a single file into the bucket with the least total size.
    """
    # Pop the bucket with the smallest size
    smallest_size, smallest_bucket_index = heapq.heappop(bucket_sizes)
    # Assign the file to this bucket
    buckets[smallest_bucket_index].append(dat_entry + "\n")  # add newline for speedy write
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
    with open(files_dat_file, 'r') as file:
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
    entry_sizes = sorted(entry_sizes, key=lambda e: e[1], reverse=True)

    for dat_entry, size in entry_sizes:
        try:
            distribute_dat_to_bucket(dat_entry, size, buckets, bucket_heap, base_dir)
        except Exception as e:
            raise RuntimeError(f"Error processing dat entry {dat_entry}") from e

    if show_stats:
        rank_sizes = [bucket[0] for bucket in bucket_heap]
        show_histogram(rank_sizes)

    return buckets, metadata


def write_dat_file(buckets, infos: dict, output_file="rebalanced-files.dat"):
    """
    Output the result after processing all directories
    """
    logging.info("Writing out data from %d buckets to file: %s", len(buckets), output_file)

    # CoreNeuron does RoundRobin - we need to transpose the entries
    zipped_entries = itertools.zip_longest(*buckets)

    with open(output_file, "w") as out:
        print(infos["version"], file=out)
        print(infos["n_files"], file=out)

        for entries in zipped_entries:
            for entry in entries:
                if entry is not None:
                    out.write(entry)


def get_entry_size(base_dir, dat_entry):
    """Obtain the file size of a dat entry"""
    dat_file = f"{dat_entry}_2.dat"
    file_path = os.path.join(base_dir, dat_file)
    return os.path.getsize(file_path)


def with_progress(elements):
    """A quick and easy generator for displaying progress while iterating"""
    total_elems = len(elements)
    report_every = math.ceil(total_elems / 50)
    logging.info(f"Processing {total_elems} entries", )
    for i, elem in enumerate(elements):
        if i % report_every == 0:
            print(f"{i:10} [{i*100/total_elems:3.0f}%]", file=sys.stderr)
        yield elem


def show_histogram(rank_buckets, n_bins=50):
    """A simple histogram CLI visualizer"""
    logging.info("Histogram of the ranks sizes")
    freq, bins = numpy.histogram(rank_buckets, bins=n_bins)
    bin_start = bins[0]
    for count, bin_end in zip(freq, bins[1:]):
        if count:
            print(f"[{bin_start/1204/1024:5.0f} - {bin_end/1204/1024:5.0f}]: {count:0d}")
        bin_start = bin_end


def main():
    # Step 1: Set up argparse for the CLI
    parser = argparse.ArgumentParser(
        description="Redistribute CoreNeuron dat files, optimizing for a given number of ranks"
    )
    parser.add_argument(
        'input_file',
        type=str,
        help="Path to the CoreNeuron input file, typically files.dat"
    )
    parser.add_argument(
        'n_ranks',
        type=int,
        help="Number of target ranks"
    )
    parser.add_argument(
        '--max-entries',
        type=int,
        default=None,
        required=False,
        help="Consider only the first N entries of the input file"
    )
    parser.add_argument(
        '--output-file',
        type=str,
        default="rebalanced-files.dat",
        required=False,
        help="The rebalanced output file path"
    )
    # Optional argument for verbose output
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help="Enable verbose output for debugging."
    )
    parser.add_argument(
        '--histogram',
        action='store_true',
        help="Additionally display the histogram of the ranks accumulated sizes"
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
        args.input_file, args.n_ranks, args.max_entries, args.histogram
    )

    # Create a new files.dat according to the new buckets
    write_dat_file(buckets, infos, args.output_file)

    logging.info("DONE")


if __name__ == "__main__":
    sys.exit(main())
