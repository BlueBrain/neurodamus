# Blue Brain Project - EPFL, 2024
"""A library of functions shared across tools.
"""

import math
import os
import sys

PROGRESS_STEPS = 50
DEFAULT_HISTOGRAM_NBINS = 40


def show_histogram(buckets, n_bins=DEFAULT_HISTOGRAM_NBINS):
    """A simple histogram CLI visualizer"""
    import numpy  # optional
    MiB = float(1024 * 1024)
    freq, bins = numpy.histogram(buckets, bins=n_bins)
    bin_start = bins[0]
    for count, bin_end in zip(freq, bins[1:]):
        if count:
            print(f"  [{bin_start/MiB:5.0f} - {bin_end/MiB:5.0f}]: {count:0d}")
        bin_start = bin_end


def get_dat_entry_size(base_dir, dat_entry):
    """Obtain the file size of a dat entry"""
    dat_file = f"{dat_entry}_2.dat"
    file_path = os.path.join(base_dir, dat_file)
    return os.path.getsize(file_path)


def with_progress(elements):
    """A quick and easy generator for displaying progress while iterating"""
    total_elems = len(elements)
    report_every = math.ceil(total_elems / PROGRESS_STEPS)
    print(f"Processing {total_elems} entries")
    for i, elem in enumerate(elements):
        if i % report_every == 0:
            print(f"{i:10} [{i*100/total_elems:3.0f}%]", file=sys.stderr)
        yield elem
