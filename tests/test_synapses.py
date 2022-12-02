import numpy as np
import numpy.testing as npt
import os
import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile


# BlueConfig string
BC_str = """
Run Default
{{
    CellLibraryFile /gpfs/bbp.cscs.ch/project/proj83/circuits/Bio_M/20200805/circuit.mvd3
    nrnPath /gpfs/bbp.cscs.ch/project/proj83/circuits/sscx-v7-plasticity/edges.sonata
    CircuitPath /gpfs/bbp.cscs.ch/project/proj83/circuits/Bio_M/20200805

    BioName /gpfs/bbp.cscs.ch/project/proj83/circuits/Bio_M/20200805/bioname
    Atlas /gpfs/bbp.cscs.ch/project/proj83/data/atlas/S1/MEAN/P14-MEAN

    METypePath /gpfs/bbp.cscs.ch/project/proj83/singlecell/release_2020-07-31/hoc
    MEComboInfoFile \
/gpfs/bbp.cscs.ch/project/proj83/singlecell/fixed_L6_allBPC_thresholds/mecombo_emodel.tsv
    MorphologyPath /gpfs/bbp.cscs.ch/project/proj83/morphologies/fixed_ais_L23PC_20201210/ascii
    MorphologyType asc

    CurrentDir .
    OutputRoot .

    TargetFile {target_file}
    CircuitTarget L5_cells
    Duration 200
    Dt 0.025

    RNGMode Random123
    BaseSeed 549821

    Simulator NEURON
    RunMode WholeCell
    ForwardSkip 0

    ExtracellularCalcium 1.2
    MinisSingleVesicle 1
    SpikeLocation AIS
    V_Init -80
}}

Projection Thalamocortical_input_VPM
{{
    Path /gpfs/bbp.cscs.ch/project/proj83/circuits/Bio_M/20200805/projections/2022_04_04/\
vpm_region_by_region_flatmap/merged.sonata
    Source pre_VPM
    PopulationID 1
}}
"""

# Target file string
TGT_str = """
Target Cell L5_cells
{{
    pre_L5_BC pre_L5_PC post_L5_PC
}}

Target Cell pre_L5_BC
{{
    a{pre_L5_BC}
}}

Target Cell pre_L5_PC
{{
    a{pre_L5_PC}
}}

Target Cell pre_VPM
{{
    a{pre_VPM}
}}

Target Cell post_L5_PC
{{
    a{post_L5_PC}
}}
"""


@pytest.fixture(scope="module")
def blueconfig1():
    target_values = {
        "pre_L5_BC": 3587718,
        "pre_L5_PC": 4148946,
        "pre_VPM": 5067862,
        "post_L5_PC": 3424037
    }

    # dump config to files
    with NamedTemporaryFile("w", prefix='test_synapses_tgt', delete=False) as tgt_file:
        tgt_file.write(TGT_str.format(**target_values))
    with NamedTemporaryFile("w", prefix="test_synapses_bc", delete=False) as bc_file:
        bc_file.write(BC_str.format(target_file=tgt_file.name))

    yield target_values, bc_file.name

    os.unlink(bc_file.name)
    os.unlink(tgt_file.name)


@pytest.mark.slow
@pytest.mark.forked
@pytest.mark.skipif(
    not os.path.isfile("/gpfs/bbp.cscs.ch/project/proj83/circuits/Bio_M/20200805/circuit.mvd3"),
    reason="Circuit file not available")
@pytest.mark.skipif(
    not os.environ.get("NEURODAMUS_NEOCORTEX_ROOT"),
    reason="Test requires loading a neocortex model to run")
@pytest.mark.skipif(
    "bluepy" not in os.environ.get("PYTHONPATH"),
    reason="Test requires bluepy run")
def test_synapses(blueconfig1):
    """
    A test of the impact of eager caching of synaptic parameters. BBPBGLIB-813
    """
    from neurodamus.core import NeurodamusCore as Nd
    from neurodamus.node import Node
    from neurodamus.core.configuration import GlobalConfig, SimConfig, LogLevel
    from neurodamus.io.synapse_reader import SynapseReader
    from neurodamus.utils import compat
    from neurodamus.utils.logging import log_verbose

    # create Node from config
    gids, blueconfig = blueconfig1
    GlobalConfig.verbosity = LogLevel.VERBOSE
    n = Node(blueconfig)
    conn_weight = 0.8  # for testing

    # append Connection blocks programmatically
    # plasticity
    CONN_plast = compat.Map(Nd.Map())
    CONN_plast["Source"] = "pre_L5_PC"
    CONN_plast["Destination"] = "post_L5_PC"
    CONN_plast["ModOverride"] = "GluSynapse"
    CONN_plast["Weight"] = conn_weight
    SimConfig.connections.hoc_map.put("plasticity", CONN_plast.hoc_map)
    # init_I_E
    CONN_i2e = compat.Map(Nd.Map())
    CONN_i2e["Source"] = "pre_L5_BC"
    CONN_i2e["Destination"] = "post_L5_PC"
    CONN_i2e["Weight"] = conn_weight
    SimConfig.connections.hoc_map.put("init_I_E", CONN_i2e.hoc_map)
    # init_VPM
    CONN_vpm = compat.Map(Nd.Map())
    CONN_vpm["Source"] = "pre_VPM"
    CONN_vpm["Destination"] = "post_L5_PC"
    CONN_vpm["Weight"] = conn_weight
    SimConfig.connections.hoc_map.put("init_VPM", CONN_vpm.hoc_map)
    # manually update item count in compat.Map
    SimConfig.connections._size = int(SimConfig.connections.hoc_map.count())

    # setup sim
    n.load_targets()
    n.create_cells()
    n.create_synapses()
    # init
    base_seed = n._run_conf.get("BaseSeed", 0)  # base seed for synapse RNG
    for syn_manager in n._circuits.all_synapse_managers():
        syn_manager.finalize(base_seed, False)
    n.sim_init()

    # 1) get values from bluepy
    from bluepy import Circuit
    from bluepy.enums import Synapse

    c = Circuit(blueconfig)

    dfs = {}
    properties = [Synapse.G_SYNX, Synapse.U_SYN, Synapse.DTC, Synapse.D_SYN, Synapse.F_SYN,
                  Synapse.NRRP, Synapse.CONDUCTANCE_RATIO, Synapse.U_HILL_COEFFICIENT]
    plast_params = ["volume_CR", "rho0_GB", "Use_d_TM", "Use_p_TM",
                    "gmax_d_AMPA", "gmax_p_AMPA", "theta_d", "theta_p"]

    df = c.connectome.pair_synapses([gids["pre_L5_BC"]], [gids["post_L5_PC"]], properties)
    df["weight"] = df[Synapse.G_SYNX] * conn_weight  # add weight column
    dfs['ProbGABAAB_EMS'] = df

    df = c.projection("Thalamocortical_input_VPM").pair_synapses(
        [gids["pre_VPM"]], [gids["post_L5_PC"]], properties)
    df["weight"] = df[Synapse.G_SYNX] * conn_weight  # add weight column
    dfs['ProbAMPANMDA_EMS'] = df

    df = c.connectome.pair_synapses(
        [gids["pre_L5_PC"]], [gids["post_L5_PC"]], properties + plast_params)
    df["gmax_NMDA"] = df[Synapse.G_SYNX] * df[Synapse.CONDUCTANCE_RATIO]  # add gmax_NMDA column
    df["weight"] = 1.0  # add weight column (not set in Connection block for GluSynapse)
    dfs['GluSynapse'] = df

    # scale Use with calcium
    # wrapper class for calling SynapseReader._scale_U_param
    class wrapU:
        def __init__(self, a, b):
            self.U = np.array(a)
            self.u_hill_coefficient = np.array(b)
            assert (self.U.size == self.u_hill_coefficient.size)

        def __len__(self):
            return self.U.size

    for _, df in dfs.items():
        tmp = wrapU(df[Synapse.U_SYN], df[Synapse.U_HILL_COEFFICIENT])
        SynapseReader._scale_U_param(tmp, SimConfig.extracellular_calcium, None)
        df[Synapse.U_SYN] = tmp.U

    # 2) get values from NEURON
    post_cell = n.circuits.global_manager.get_cellref(gids["post_L5_PC"])
    # here we collect all synapses for the post cell
    import re
    _match_index = re.compile(r"\[[0-9]+\]$")
    synlist = {}
    for nc in Nd.h.cvode.netconlist('', post_cell, ''):
        if nc.precell() is not None:  # minis netcons only
            continue
        syn = nc.syn()
        syntype = _match_index.sub('', syn.hname())
        d = {'weight': nc.weight[0]}
        for v in vars(syn):
            try:
                attr = getattr(syn, v)
                if attr.__class__.__name__ in ['int', 'float', 'str']:
                    d[v] = attr
            except Exception:
                continue
        synlist.setdefault(syntype, []).append(d)

    # sort lists by synapseID
    for _, x in synlist.items():
        x = sorted(x, key=lambda d: d['synapseID'])

    # 3) compare values: Neurodamus vs bluepy
    # mapping between Nd and bluepy properties
    properties = {
        'ProbAMPANMDA_EMS':
        {
            'conductance': Synapse.G_SYNX,
            'Dep': Synapse.D_SYN,
            'Fac': Synapse.F_SYN,
            'NMDA_ratio': Synapse.CONDUCTANCE_RATIO,
            'Nrrp': Synapse.NRRP,
            'tau_d_AMPA': Synapse.DTC,
            'Use': Synapse.U_SYN,
            'weight': "weight"
        },
        'ProbGABAAB_EMS':
        {
            'conductance': Synapse.G_SYNX,
            'Dep': Synapse.D_SYN,
            'Fac': Synapse.F_SYN,
            'GABAB_ratio': Synapse.CONDUCTANCE_RATIO,
            'Nrrp': Synapse.NRRP,
            'tau_d_GABAA': Synapse.DTC,
            'Use': Synapse.U_SYN,
            'weight': "weight"
        },
        'GluSynapse':
        {
            'Dep': Synapse.D_SYN,
            'Fac': Synapse.F_SYN,
            'gmax0_AMPA': Synapse.G_SYNX,
            'gmax_d_AMPA': "gmax_d_AMPA",
            'gmax_NMDA': "gmax_NMDA",
            'gmax_p_AMPA': "gmax_p_AMPA",
            'Nrrp': Synapse.NRRP,
            'rho0_GB': "rho0_GB",
            'tau_d_AMPA': Synapse.DTC,
            'theta_d_GB': "theta_d",
            'theta_p_GB': "theta_p",
            'Use': Synapse.U_SYN,
            'volume_CR': "volume_CR",
            'weight': "weight"
        }
    }

    for stype, syns in synlist.items():
        for i, info in enumerate(syns):
            log_verbose("%s[%d] (ID %d) (INDEX %d)" % (stype, i, info['synapseID'],
                                                       dfs[stype].index[i]))
            for prop, dfcol in properties[stype].items():
                log_verbose("    %12s %12.6f ~= %-12.6f %s" %
                            (prop, info[prop], dfs[stype][dfcol].iloc[i], dfcol))
                assert (info[prop] == pytest.approx(dfs[stype][dfcol].iloc[i]))


def test__constrained_hill():
    from neurodamus.io.synapse_reader import _constrained_hill

    # original functions
    def hill(ca_conc, y, K_half):
        return y*ca_conc**4/(K_half**4 + ca_conc**4)

    def constrained_hill(K_half):
        y_max = (K_half**4 + 16) / 16
        return lambda x: hill(x, y_max, K_half)

    f_scale = lambda x, y: constrained_hill(x)(y)
    scale_factors = np.vectorize(f_scale)

    rng = np.random.default_rng(seed=42)
    a = 10 * rng.random(100)
    b = 10 * rng.random(100)

    npt.assert_allclose(scale_factors(a, 2), _constrained_hill(a, 2))
    npt.assert_allclose(scale_factors(a, 2.2), _constrained_hill(a, 2.2))
    npt.assert_allclose(scale_factors(a, b), _constrained_hill(a, b))


@pytest.mark.skipif(
    not os.environ.get("NEURODAMUS_NEOCORTEX_ROOT"),
    reason="Test requires loading a neocortex model to run")
def test_no_edge_creation(capsys):
    from neurodamus.node import Node

    USECASE3 = Path(__file__).parent.absolute() / "simulations" / "usecase3"
    contents = """
    {
        "manifest": {
            "$CIRCUIT_DIR": "%s"
        },
        "network": "$CIRCUIT_DIR/%s",
        "node_sets_file": "$CIRCUIT_DIR/nodesets.json",
        "run":
        {
            "random_seed": 12345,
            "dt": 0.05,
            "tstop": 1000
        }
    }
    """
    # create a tmp json file to read usecase3/no_edge_circuit_config.json
    with NamedTemporaryFile("w", suffix='.json', delete=False) as tmp_config:
        tmp_config.write(contents % (USECASE3, "no_edge_circuit_config.json"))

    n = Node(tmp_config.name)
    n.load_targets()
    n.create_cells()
    n.create_synapses()

    captured = capsys.readouterr()
    assert "Circuit internal connectivity has been DISABLED" in captured.out
    assert len(n.circuits.edge_managers) == 0

    os.unlink(tmp_config.name)
