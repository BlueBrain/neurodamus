"""
Collection of utility functions related to clearing the used memory in neurodamus-py or NEURON
"""
import ctypes
import ctypes.util
import os

from ..core import NeurodamusCore as Nd
import logging


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
        except OSError:
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
