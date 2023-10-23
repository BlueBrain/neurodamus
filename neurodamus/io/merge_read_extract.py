import numpy as np

def merge(selection, min_gap):
    selection = np.atleast_2d(selection)

    if selection.size == 0:
        return np.empty((0,2))

    jumps = selection[1:, 0] - selection[:-1, 1]
    jumps = jumps >= min_gap
    jump_points = np.argwhere(jumps)

    ranges = np.empty(jump_points.size + 2, dtype="int64")
    ranges[0] = 0
    ranges[1:-1] = jump_points[:, 0] + 1
    ranges[-1] = selection.shape[0]

    ranges = np.array(list(zip(ranges[:-1], ranges[1:])))

    return np.array(
        [
            (selection[k_begin, 0], selection[k_end - 1, 1])
            for (k_begin, k_end) in ranges
        ]
    )


def flatsize(selection):
    selection = np.atleast_2d(selection)
    if selection.size == 0:
        return 0

    return np.sum(selection[:, 1] - selection[:, 0])


def extract(all_values, merged_selection, selection):
    merged_selection = np.atleast_2d(merged_selection)
    selection = np.atleast_2d(selection)

    values = np.empty((flatsize(selection),) + all_values.shape[1:], dtype=all_values.dtype)

    if values.size == 0:
        return values

    # Index naming convention:
    # i: top-level index
    # j: into the respective `values`.
    # k: index into respective selection.

    # Which range of `merged_selection` are we processing?
    k0_large = 0

    # Beginning of the current range in `all_values` and `values`.
    large_offset = 0
    small_offset = 0

    for i0_small, i1_small in selection:
        j0_small = small_offset
        j1_small = j0_small + i1_small - i0_small

        # Top-level index of the large range:
        i0_large = merged_selection[k0_large, 0]
        i1_large = merged_selection[k0_large, 1]

        j0_large = large_offset + i0_small - i0_large
        j1_large = j0_large + i1_small - i0_small

        values[j0_small:j1_small] = all_values[j0_large:j1_large]

        # Preparatory work for the next iteration:
        small_offset += i1_small - i0_small
        if i1_small >= i1_large:
            large_offset += i1_large - i0_large
            k0_large += 1

    return values


def merge_read_extract(selection, min_gap, read_callback):
    merged_selection = merge(selection, min_gap)
    all_values = read_callback(merged_selection)

    return extract(all_values, merged_selection, selection)


class RepeatedMergeReadExtract:
    def __init__(self, selection, min_gap):
        self._selection = selection
        self._merged_selection = merge(selection, min_gap)

    def __call__(self, read_callback):
        all_values = read_callback(self._merged_selection)
        return extract(all_values, self._merged_selection, self._selection)


class SONATARepeatedMergeReadExtract:
    def __init__(self, selection, min_gap):
        self._selection = np.array(selection.ranges)
        self._merged_selection = merge(self._selection, min_gap)

    def __call__(self, read_callback):
        import libsonata
        all_values = read_callback(libsonata.Selection(self._merged_selection))
        return extract(all_values, self._merged_selection, self._selection)
