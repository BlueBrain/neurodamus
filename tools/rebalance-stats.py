#!/bin/env python3

"""
A script to inspect and show statistics of the load imposed by a given
CORENEURON input dir when loaded Round-Robin in a cluster.

Blue Brain Project - EPFL, 2024

"""

import argparse
import os
from toolbox import get_dat_entry_size, show_histogram, with_progress

CORENRN_SKIP_MARK = "-1"
DEFAULT_RANKS_PER_MACHINE = 40


def files_dat_load_ranks(input_file, n_machines, ranks_per_machine, base_dir):
    """From a files.dat compute the total amount of data to load per rank
    """
    print(f"Reading from input file: {input_file}")
    base_dir = base_dir or os.path.dirname(input_file)
    n_ranks = n_machines * ranks_per_machine
    ranks_size = [0.0] * n_ranks

    with open(input_file, "r") as file:
        next(file)  # header: version
        next(file)  # header: n_values
        for i, line in enumerate(with_progress(file.readlines())):
            if line[:2] == CORENRN_SKIP_MARK:
                continue
            size = get_dat_entry_size(base_dir, line.strip())
            ranks_size[i % n_ranks] += size

    return ranks_size


def main():
    parser = argparse.ArgumentParser(
        description="Redistribute CoreNeuron dat files, optimizing for a given number of Machines"
    )
    parser.add_argument(
        "input_file",
        type=str,
        help="Path to the CoreNeuron input file, typically 'files.dat'",
    )
    parser.add_argument(
        "n_machines", type=int, help="Number of target machines running the simulation"
    )
    parser.add_argument(
        "--ranks-per-machine",
        type=int,
        default=DEFAULT_RANKS_PER_MACHINE,
        help=f"Number of ranks per machine (default: {DEFAULT_RANKS_PER_MACHINE})",
    )
    parser.add_argument(
        "--dat-path",
        type=str,
        default=None,
        required=False,
        help="The base path of dat files",
    )
    args = parser.parse_args()

    ranks_size = files_dat_load_ranks(
        args.input_file, args.n_machines, args.ranks_per_machine, args.dat_path
    )

    # Collect Machine stats
    machine_size = [0.0] * args.n_machines
    for rank_i, size in enumerate(ranks_size):
        machine_size[rank_i // args.ranks_per_machine] += size

    print("Machine histogram")
    show_histogram(machine_size)

    print("Rank histogram")
    show_histogram(ranks_size)


if __name__ == "__main__":
    main()
