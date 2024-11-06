#!/bin/env python3

"""
A script to inspect and show statistics of the load imposed by a given
CORENEURON input dir when loaded Round-Robin in a cluster.

Blue Brain Project - EPFL, 2024

"""

import argparse
import numpy
import os
import sys

PROGRESS_STEPS = 50
CORENRN_SKIP_MARK = "-1"
DEFAULT_HISTOGRAM_NBINS = 40
DEFAULT_RANKS_PER_MACHINE = 40


def files_dat_load_ranks(input_file, n_machines, ranks_per_machine, base_dir):
    print(f"Reading from input file: {input_file}")
    base_dir = base_dir or os.path.dirname(input_file)
    n_ranks = n_machines * ranks_per_machine
    ranks_size = [.0] * n_ranks

    with open(input_file, 'r') as file:
        next(file)  # header: version
        next(file)  # header: n_values
        for i, line in enumerate(with_progress(file.readlines())):
            if line[:2] == CORENRN_SKIP_MARK:
                continue
            size = get_entry_size(base_dir, line.strip())
            ranks_size[i % n_ranks] += size

    return ranks_size


def main():
    parser = argparse.ArgumentParser(
        description="Redistribute CoreNeuron dat files, optimizing for a given number of Machines"
    )
    parser.add_argument(
        'input_file',
        type=str,
        help="Path to the CoreNeuron input file, typically files.dat"
    )
    parser.add_argument(
        'n_machines',
        type=int,
        help="Number of target machines"
    )
    parser.add_argument(
        '--ranks-per-machine',
        type=int,
        default=DEFAULT_RANKS_PER_MACHINE,
        help="Number of target ranks"
    )
    parser.add_argument(
        '--dat-path',
        type=str,
        default=None,
        required=False,
        help="The base path of dat files"
    )
    args = parser.parse_args()

    ranks_size = files_dat_load_ranks(
        args.input_file,
        args.n_machines,
        args.ranks_per_machine,
        args.dat_path
    )

    # Collect Machine stats
    machine_size = [.0] * args.n_machines
    for rank_i, size in enumerate(ranks_size):
        machine_size[rank_i // args.ranks_per_machine] += size

    print("Machine histogram")
    show_histogram(machine_size)

    print("Rank histogram")
    show_histogram(ranks_size)


def show_histogram(buckets, n_bins=DEFAULT_HISTOGRAM_NBINS):
    """A simple histogram CLI visualizer"""
    MiB = float(1 << 20)
    freq, bins = numpy.histogram(buckets, bins=n_bins)
    bin_start = bins[0]
    for count, bin_end in zip(freq, bins[1:]):
        if count:
            print(f"  [{bin_start/MiB:5.0f} - {bin_end/MiB:5.0f}]: {count:0d}")
        bin_start = bin_end


def get_entry_size(base_dir, dat_entry):
    """Obtain the file size of a dat entry"""
    dat_file = f"{dat_entry}_2.dat"
    file_path = os.path.join(base_dir, dat_file)
    return os.path.getsize(file_path)


def with_progress(elements):
    """A quick and easy generator for displaying progress while iterating"""
    import math
    total_elems = len(elements)
    report_every = math.ceil(total_elems / PROGRESS_STEPS)
    print(f"Processing {total_elems} entries", )
    for i, elem in enumerate(elements):
        if i % report_every == 0:
            print(f"{i:10} [{i*100/total_elems:3.0f}%]", file=sys.stderr)
        yield elem


if __name__ == "__main__":
    main()
