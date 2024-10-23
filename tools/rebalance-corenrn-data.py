import argparse
import heapq
import itertools
import logging
import math
import os
import sys


def distribute_dat_to_bucket(dat_entry, buckets, bucket_sizes, base_dir="."):
    """
    Distribute a single file into the bucket with the least total size.
    """
    dat_file = f"{dat_entry}_2.dat"
    file_path = os.path.join(base_dir, dat_file)
    size = os.path.getsize(file_path)
    # Pop the bucket with the smallest size
    smallest_size, smallest_bucket_index = heapq.heappop(bucket_sizes)
    # Assign the file to this bucket
    buckets[smallest_bucket_index].append(dat_entry + "\n")  # add newline for speedy write
    # Update the bucket size in the heap
    new_size = smallest_size + size
    heapq.heappush(bucket_sizes, (new_size, smallest_bucket_index))


def redistribute_files_dat(files_dat_file, n_buckets):
    """
    Read and process each entry from the dat file and distribute them into buckets.
    """
    base_dir = os.path.dirname(files_dat_file)
    metadata = {}

    logging.debug("Reading distribution file: %s", files_dat_file)
    with open(files_dat_file, 'r') as file:
        metadata["version"] = file.readline().strip()
        metadata["n_files"] = file.readline()
        dat_entries = file.readlines()

    if (n_files := int(metadata["n_files"])) < len(dat_entries):
        logging.warning("files.dat line 2 sets a small numer of entries: %d", n_files)
        dat_entries = dat_entries[:n_files]

    logging.info("Distributing files into %d buckets...", n_buckets)

    if len(dat_entries) < n_buckets:
        raise RuntimeError("Too little data for selected number of ranks. Specify less")

    # Initialize empty buckets
    buckets = [[] for _ in range(n_buckets)]

    # Create a heap to keep track of bucket sizes. Each entry is (bucket_size, bucket_index)
    bucket_heap = [(0, i) for i in range(n_buckets)]
    heapq.heapify(bucket_heap)  # Turn the list into a heap

    for entry in with_progress(dat_entries):
        dat_entry = entry.strip()
        try:
            distribute_dat_to_bucket(dat_entry, buckets, bucket_heap, base_dir)
        except Exception as e:
            raise RuntimeError(f"Error processing dat entry {dat_entry}") from e

    return buckets, metadata


def write_dat_file(buckets, infos: dict):
    """
    Output the result after processing all directories
    """

    # CoreNeuron does RoundRobin - we need to transpose the entries
    zipped_entries = itertools.zip_longest(*buckets)

    with open("rebalanced-files.dat", "w") as out:
        print(infos["version"], file=out)
        print(infos["n_files"], file=out)

        for entries in zipped_entries:
            for entry in entries:
                if entry is not None:
                    out.write(entry)


def with_progress(elements):
    """A quick and easy generator for displaying progress while iterating"""
    total_elems = len(elements)
    report_every = math.ceil(total_elems / 50)
    logging.info(f"Processing {total_elems} entries", )
    for i, elem in enumerate(elements):
        if i % report_every == 0:
            print(f"{i:10} [{i*100/total_elems:3.0f}%]", file=sys.stderr)
        yield elem


def main():
    # Step 1: Set up argparse for the CLI
    parser = argparse.ArgumentParser(
        description="Redistribute the dat files into N buckets based on file sizes."
    )
    parser.add_argument(
        'input_file',
        type=str,
        help="Path to the file containing directory paths (one per line)."
    )
    parser.add_argument(
        'n_ranks',
        type=int,
        help="Optimize the distribution for given number of ranks"
    )
    # Optional argument for verbose output
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help="Enable verbose output for debugging."
    )

    args = parser.parse_args()

    logging_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=logging_level, format="%(levelname)s :: %(message)s'")

    if not os.path.isfile(args.input_file):
        logging.error("Input file could not be found!")
        return 1
    else:
        logging.info(f"Reading from input file: {args.input_file}")

    # Do the redistribution
    buckets, infos = redistribute_files_dat(args.input_file, args.n_ranks)

    # Create a new files.dat according to the new buckets
    write_dat_file(buckets, infos)

    logging.info("DONE")


if __name__ == "__main__":
    sys.exit(main())
