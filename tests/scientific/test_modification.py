from pathlib import Path
from neurodamus.utils.logging import log_verbose
# !! NOTE: Please dont import Neuron or Nd objects. pytest will trigger Neuron instantiation!

SIM_DIR = Path(__file__).parent.parent.absolute() / "simulations" / "v5_sonata"
CONFIG_FILE_MINI = SIM_DIR / "simulation_config_mini.json"


def test_TTX_modification():
    """
    A test of enabling TTX with a short simulation.
    Expected outcome is non-zero spike count without TTX, zero with TTX.

    We require launching with mpiexec (numprocs=1).
    """
    from neurodamus.core import NeurodamusCore as Nd
    from neurodamus.core.configuration import GlobalConfig, LogLevel, SimConfig
    from neurodamus.node import Node

    GlobalConfig.verbosity = LogLevel.VERBOSE
    n = Node(str(CONFIG_FILE_MINI))

    # setup sim
    n.load_targets()
    n.create_cells()
    n.create_synapses()
    n.enable_stimulus()
    n.sim_init()
    n.solve()
    # _spike_vecs is a list of (spikes, ids)
    nspike_noTTX = sum(len(spikes) for spikes, _ in n._spike_vecs)

    # append modification to config directly
    TTX_mod = {"Type": "TTX", "Target": "Mini5"}
    SimConfig.modifications["applyTTX"] = TTX_mod

    # setup sim again
    Nd.t = 0.0
    n._sim_ready = False
    n.enable_modifications()
    n.sim_init()
    n.solve()
    nspike_TTX = sum(len(spikes) for spikes, _ in n._spike_vecs)

    log_verbose("spikes without TTX = %s, with TTX = %s", nspike_noTTX, nspike_TTX)
    assert nspike_noTTX > 0
    assert nspike_TTX == 0


def test_ConfigureAllSections_modification():
    """
    A test of performing ConfigureAllSections with a short simulation.
    Expected outcome is higher spike count when enabled.

    We require launching with mpiexec (numprocs=1).
    """
    from neurodamus.core import NeurodamusCore as Nd
    from neurodamus.core.configuration import GlobalConfig, LogLevel, SimConfig
    from neurodamus.node import Node

    GlobalConfig.verbosity = LogLevel.VERBOSE
    n = Node(str(CONFIG_FILE_MINI))

    # setup sim
    n.load_targets()
    n.create_cells()
    n.create_synapses()
    n.enable_stimulus()
    n.sim_init()
    n.solve(tstop=150)  # longer duration to see influence on spikes
    nspike_noConfigureAllSections = sum(len(spikes) for spikes, _ in n._spike_vecs)

    # append modification to config directly
    ConfigureAllSections_mod = {"Type": "ConfigureAllSections",
                                "Target": "Mini5",
                                "SectionConfigure": "%s.gSK_E2bar_SK_E2 = 0"}
    SimConfig.modifications["no_SK_E2"] = ConfigureAllSections_mod

    # setup sim again
    Nd.t = 0.0
    n._sim_ready = False
    n.enable_modifications()
    n.sim_init()
    n.solve(tstop=150)
    nspike_ConfigureAllSections = sum(len(spikes) for spikes, _ in n._spike_vecs)

    log_verbose("spikes without ConfigureAllSections = %s, with ConfigureAllSections = %s",
                nspike_ConfigureAllSections, nspike_noConfigureAllSections)
    assert (nspike_ConfigureAllSections > nspike_noConfigureAllSections)
