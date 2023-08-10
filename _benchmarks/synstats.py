# Small script to measure memory usage of synapse objects in NEURON.
# Usage: nrniv (or special) -python synstats.py

from neuron import h
import os


def get_mem_usage():
    """
    Return memory usage information in KB.
    """
    with open("/proc/self/statm") as fd:
        _, data_size, _ = fd.read().split(maxsplit=2)
    usage_kb = float(data_size) * os.sysconf("SC_PAGE_SIZE") / 1024

    return usage_kb


# Dummy class to pass to synapse objects
class SynParams:
    def __getattr__(self, item):
        return 1


n_inst = 1000000

h.load_file("RNGSettings.hoc")
h.load_file("Map.hoc")

map_hoc = h.Map()
RNGset = h.RNGSettings()
RNGset.interpret(map_hoc)

pc = h.ParallelContext()

sec = h.Section()
sec.push()
params_obj = SynParams()

h.load_file("AMPANMDAHelper.hoc")
mem = get_mem_usage()
AMPA_helper = [h.AMPANMDAHelper(1, params_obj, 0.5, i, 0) for i in range(n_inst)]
netcon_ampa = [pc.gid_connect(1000, helper.synapse) for helper in AMPA_helper]
mem2 = get_mem_usage()
print('Memory usage per object ProbAMPA: %f KB' % ((mem2 - mem) / n_inst))

h.load_file("GABAABHelper.hoc")
mem = get_mem_usage()
GABAAB_helper = [h.GABAABHelper(1, params_obj, 0.5, i, 0) for i in range(n_inst)]
netcon_gabaab = [pc.gid_connect(1000, helper.synapse) for helper in GABAAB_helper]
mem2 = get_mem_usage()
print('Memory usage per object ProbGABAAB: %f KB' % ((mem2 - mem) / n_inst))

h.load_file("GluSynapseHelper.hoc")
mem = get_mem_usage()
GluSynapse_helper = [h.GluSynapseHelper(1, params_obj, 0.5, i, 0, map_hoc) for i in range(n_inst)]
netcon_glu = [pc.gid_connect(1000, helper.synapse) for helper in GluSynapse_helper]
mem2 = get_mem_usage()
print('Memory usage per object GluSynapse: %f KB' % ((mem2 - mem) / n_inst))

mem = get_mem_usage()
Gap_helper = [h.Gap(0.5) for i in range(n_inst)]
mem2 = get_mem_usage()
print('Memory usage per object Gap: %f KB' % ((mem2 - mem) / n_inst))
