"""
Runtime configuration
"""
from __future__ import absolute_import
import logging
import os
import os.path
import re
from collections import defaultdict
from enum import Enum

from ..io.sonata_config import SonataConfig
from ..utils import compat
from ..utils.logging import log_verbose
from ..utils.pyutils import ConfigT
from ._shmutils import SHMUtil

EXCEPTION_NODE_FILENAME = ".exception_node"
"""A file which controls which rank shows exception"""


class LogLevel:
    ERROR_ONLY = 0
    DEFAULT = 1
    VERBOSE = 2
    DEBUG = 3


class ConfigurationError(Exception):
    """
    Error due to invalid settings in simulation config
    ConfigurationError should be raised by all ranks to be caught
    properly. Otherwise we might end up with deadlocks.
    For Exceptions that are raised by a single rank Exception
    should be used.
    This is due to the way Exceptions are caught from commands.py.
    """
    pass


class GlobalConfig:
    verbosity = LogLevel.DEFAULT
    debug_conn = os.getenv('ND_DEBUG_CONN', [])
    if debug_conn:
        debug_conn = [int(gid) for gid in os.getenv('ND_DEBUG_CONN', '').split(',')]
        verbosity = 3

    @classmethod
    def set_mpi(cls):
        os.environ["NEURON_INIT_MPI"] = "1"


class Feature(Enum):
    Replay = 1
    SpontMinis = 2
    SynConfigure = 3
    Stimulus = 4
    LoadBalance = 5


class CliOptions(ConfigT):
    build_model = None
    simulate_model = True
    model_path = None  # Currently is output-path
    output_path = None
    keep_build = False
    lb_mode = None
    modelbuilding_steps = None
    experimental_stims = False
    enable_coord_mapping = False
    save = False
    save_time = None
    restore = None
    enable_shm = False
    model_stats = False
    simulator = None
    dry_run = False
    num_target_ranks = None

    # Restricted Functionality support, mostly for testing

    class NoRestriction:
        """Provide container API, where `in` checks are always True"""
        def __contains__(self, _) -> bool:
            return True

    NoRestriction = NoRestriction()  # Singleton

    restrict_features = NoRestriction  # can also be a list
    restrict_node_populations = NoRestriction
    restrict_connectivity = 0          # no restriction, 1 to disable projections, 2 to disable all
    restrict_stimulus = NoRestriction  # possible list of Stim names


class CircuitConfig(ConfigT):
    _name = None
    Engine = None
    CircuitPath = ConfigT.REQUIRED
    nrnPath = ConfigT.REQUIRED
    CellLibraryFile = None
    MEComboInfoFile = None
    METypePath = None
    MorphologyType = None
    MorphologyPath = None
    CircuitTarget = None
    PopulationID = 0
    DetailedAxon = False


class RNGConfig(ConfigT):
    Modes = Enum("Mode", "COMPATIBILITY RANDOM123 UPMCELLRAN4")
    mode = Modes.COMPATIBILITY
    global_seed = None
    IonChannelSeed = None
    StimulusSeed = None
    MinisSeed = None
    SynapseSeed = None


class NeuronStdrunDefaults:
    """Neuron stdrun default (src: share/lib/hoc/stdrun.hoc"""
    using_cvode_ = 0
    stdrun_quiet = 0
    realtime = 0
    tstop = 5
    stoprun = 0
    steps_per_ms = 1 / .025
    nstep_steprun = 1
    global_ra = 35.4
    v_init = -65


class LoadBalanceMode(Enum):
    """An enumeration, inc parser, of the load balance modes.
    """
    RoundRobin = 0
    WholeCell = 1
    MultiSplit = 2
    Memory = 3

    @classmethod
    def parse(cls, lb_mode):
        """Parses the load balancing mode from a string.
        Options other than WholeCell or MultiSplit are considered RR
        """
        if lb_mode is None:
            return None
        _modes = {
            "rr": cls.RoundRobin,
            "roundrobin": cls.RoundRobin,
            "wholecell": cls.WholeCell,
            "loadbalance": cls.MultiSplit,
            "multisplit": cls.MultiSplit,
            "memory": cls.Memory
        }
        lb_mode_enum = _modes.get(lb_mode.lower())
        if lb_mode_enum is None:
            raise ConfigurationError("Unknown load balance mode: " + lb_mode)
        return lb_mode_enum

    class AutoBalanceModeParams:
        """Parameters for auto-selecting a load-balance mode"""
        multisplit_cpu_cell_ratio = 4  # For warning
        cell_count = 1000
        duration = 1000
        mpi_ranks = 200

    @classmethod
    def auto_select(cls, use_neuron, cell_count, duration, auto_params=AutoBalanceModeParams):
        """Simple heuristics for auto selecting load balance"""
        from ._neurodamus import MPI
        lb_mode = LoadBalanceMode.RoundRobin
        reason = ""
        if MPI.size == 1:
            lb_mode = LoadBalanceMode.RoundRobin
            reason = "Single rank - not worth using Load Balance"
        elif use_neuron and MPI.size >= auto_params.multisplit_cpu_cell_ratio * cell_count:
            logging.warn("There's potentially a high number of empty ranks. "
                         "To activate multi-split set --lb-mode=MultiSplit")
        elif (cell_count > auto_params.cell_count
              and duration > auto_params.duration
              and MPI.size > auto_params.mpi_ranks):
            lb_mode = LoadBalanceMode.WholeCell
            reason = 'Simulation size'
        return lb_mode, reason


class _SimConfig(object):
    """
    A class initializing several HOC config objects and proxying to simConfig
    """
    __slots__ = ()
    config_file = None
    cli_options = None
    run_conf = None
    output_root = None
    base_circuit = None
    extra_circuits = None
    sonata_circuits = None
    projections = None
    connections = None
    stimuli = None
    injects = None
    reports = None
    configures = None
    modifications = None

    # Hoc objects used
    _config_parser = None
    _parsed_run = None
    _simulation_config = None
    _simconf = None
    rng_info = None

    # In principle not all vars need to be required as they'r set by the parameter functions
    simulation_config_dir = None
    current_dir = None
    default_neuron_dt = 0.025
    buffer_time = 25
    save = None
    save_time = None
    restore = None
    extracellular_calcium = None
    secondorder = None
    use_coreneuron = False
    use_neuron = True
    coreneuron_datadir = None
    coreneuron_outputdir = None
    corenrn_buff_size = 8
    delete_corenrn_data = False
    modelbuilding_steps = 1
    build_model = True
    simulate_model = True
    loadbal_mode = None
    synapse_options = {}
    spike_location = "soma"
    spike_threshold = -30
    dry_run = False
    num_target_ranks = None

    _validators = []
    _requisitors = []
    _cell_requirements = {}

    restore_coreneuron = property(lambda self: self.use_coreneuron and bool(self.restore))
    cell_requirements = property(lambda self: self._cell_requirements)

    @classmethod
    def init(cls, config_file, cli_options):
        # Import these objects scope-level to avoid cross module dependency
        from . import NeurodamusCore as Nd
        Nd.init()
        if not os.path.isfile(config_file):
            raise ConfigurationError("Config file not found: " + config_file)
        logging.info("Initializing Simulation Configuration and Validation")

        log_verbose("ConfigFile: %s", config_file)
        log_verbose("CLI Options: %s", cli_options)
        cls.config_file = config_file
        cls._config_parser = cls._init_config_parser(config_file)
        cls._parsed_run = compat.Map(cls._config_parser.parsedRun)  # easy access to hoc Map
        cls._simulation_config = cls._config_parser   # Please refactor me
        cls.sonata_circuits = cls._config_parser.circuits
        cls.simulation_config_dir = os.path.dirname(os.path.abspath(config_file))

        cls.projections = compat.Map(cls._config_parser.parsedProjections)
        cls.connections = compat.Map(cls._config_parser.parsedConnects)
        cls.stimuli = compat.Map(cls._config_parser.parsedStimuli)
        cls.injects = compat.Map(cls._config_parser.parsedInjects)
        cls.reports = compat.Map(cls._config_parser.parsedReports)
        cls.configures = compat.Map(cls._config_parser.parsedConfigures or {})
        cls.modifications = compat.Map(cls._config_parser.parsedModifications or {})
        cls.cli_options = CliOptions(**(cli_options or {}))
        cls.dry_run = cls.cli_options.dry_run
        cls.num_target_ranks = cls.cli_options.num_target_ranks
        # change simulator by request before validator and init hoc config
        if cls.cli_options.simulator:
            cls._parsed_run["Simulator"] = cls.cli_options.simulator

        cls.run_conf = run_conf = cls._parsed_run.as_dict(parse_strings=True)
        for validator in cls._validators:
            validator(cls, run_conf)

        logging.info("Checking simulation requirements")
        for requisitor in cls._requisitors:
            requisitor(cls, cls._config_parser)

        logging.info("Initializing hoc config objects")
        cls._init_hoc_config_objs()

    @classmethod
    def _init_config_parser(cls, config_file):
        if not config_file.endswith(".json"):
            raise ConfigurationError("Invalid configuration file format. "
                                     "The configuration file must be a .json file.")
        try:
            config_parser = SonataConfig(config_file)
        except Exception as e:
            raise ConfigurationError(f"Failed to initialize SonataConfig with {config_file}: {e}")
        return config_parser

    @classmethod
    def _init_hoc_config_objs(cls):
        """Init objects which parse/check configs in the hoc world"""
        from neuron import h
        parsed_run = cls._parsed_run.hoc_map

        cls.rng_info = h.RNGSettings()
        cls.rng_info.interpret(parsed_run, cls.use_coreneuron)
        if parsed_run.exists("BaseSeed"):
            logging.info("User-defined RNG base seed %s", parsed_run.valueOf("BaseSeed"))

    @classmethod
    def validator(cls, f):
        """Decorator to register parameters / config validators"""
        cls._validators.append(f)

    @classmethod
    def requisitor(cls, f):
        """Decorator to register requirements investigators"""
        cls._requisitors.append(f)

    @classmethod
    def update_connection_blocks(cls, alias):
        """Convert source destination to real population names

        Args:
            alias: A dict associating alias->real_name's
        """
        from ..target_manager import TargetSpec  # avoid cyclic deps

        restrict_features = SimConfig.cli_options.restrict_features
        if Feature.SpontMinis not in restrict_features:
            logging.warning("Disabling SpontMinis (restrict_features)")
        if Feature.SynConfigure not in restrict_features:
            logging.warning("Disabling SynConfigure (restrict_features)")

        def update_item(conn, item):
            src_spec = TargetSpec(conn.get(item))
            src_spec.population = alias.get(src_spec.population, src_spec.population)
            conn[item] = str(src_spec)

        new_connections = {}
        for name, conn in cls.connections.items():
            conn = compat.Map(conn).as_dict(True)
            update_item(conn, "Source")
            update_item(conn, "Destination")
            if Feature.SpontMinis not in restrict_features:
                conn.pop("SpontMinis", None)
            if Feature.SynConfigure not in restrict_features:
                conn.pop("SynapseConfigure", None)

            new_connections[name] = conn

        cls.connections = new_connections

    @classmethod
    def check_connections_configure(cls, target_manager):
        check_connections_configure(cls, target_manager)  # top_level

    @classmethod
    def get_stim_inject(cls, stim_name):
        for _, inject in cls.injects.items():
            inject = compat.Map(inject).as_dict(parse_strings=True)
            if stim_name == inject["Stimulus"]:
                return inject
        return None

    @classmethod
    def check_cell_requirements(cls, target_manager):
        _input_resistance(cls, target_manager)  # top_level


# Singleton
SimConfig = _SimConfig()


def find_input_file(filepath, search_paths=(), alt_filename=None):
    """Determine the full path of input files.

    Relative paths are built from Run configuration entries, and never pwd.
    In case filepath points to a file, alt_filename is disregarded

    Args:
        filepath: The relative or absolute path of the file to find
        path_conf_entries: (tuple) Run configuration entries to build the absolute path
        alt_filename: When the filepath is a directory, attempt finding a given filename
    Returns:
        The absolute path to the data file
    Raises:
        (ConfigurationError) If the file could not be found
    """
    search_paths += (SimConfig.current_dir, SimConfig.simulation_config_dir)

    def try_find_in(fullpath):
        if os.path.isfile(fullpath):
            return fullpath
        if not os.path.exists(fullpath):
            return None
        if alt_filename is not None:
            alt_file_path = os.path.join(fullpath, alt_filename)
            if os.path.isfile(alt_file_path):
                return alt_file_path
        logging.warning("Deprecated: Data source found is not a file")
        return fullpath

    if os.path.isabs(filepath):
        # if it's absolute path then can be used immediately
        file_found = try_find_in(filepath)
    else:
        file_found = None
        for path in search_paths:
            file_found = try_find_in(os.path.join(path, filepath))
            if file_found:
                break

    if not file_found:
        raise ConfigurationError("Could not find file %s" % filepath)

    logging.debug("data file %s path: %s", filepath, file_found)
    return file_found


def _check_params(section_name, data, required_fields,
                  numeric_fields=(), non_negatives=(),
                  valid_values=None, deprecated_values=None):
    """Generic function to check a dict-like data set conforms to the field prescription
    """
    for param in required_fields:
        if param not in data:
            raise ConfigurationError("simulation config mandatory param not present: [%s] %s"
                                     % (section_name, param))
    for param in set(numeric_fields + non_negatives):
        val = data.get(param)
        try:
            val and float(val)
        except ValueError:
            raise ConfigurationError("simulation config param must be numeric: [%s] %s"
                                     % (section_name, param))
    for param in non_negatives:
        val = data.get(param)
        if val and float(val) < 0:
            raise ConfigurationError("simulation config param must be positive: [%s] %s"
                                     % (section_name, param))

    for param, valid in (valid_values or {}).items():
        val = data.get(param)
        if val and val not in valid:
            raise ConfigurationError("simulation config param value is invalid: [%s] %s = %s"
                                     % (section_name, param, val))

    for param, deprecated in (deprecated_values or {}).items():
        val = data.get(param)
        if val and val in deprecated:
            logging.warning("simulation config param value is deprecated: [%s] %s = %s"
                            % (section_name, param, val))


@SimConfig.validator
def _run_params(config: _SimConfig, run_conf):
    required_fields = ("Duration",)
    numeric_fields = ("BaseSeed", "StimulusSeed", "Celsius", "V_Init")
    non_negatives = ("Duration", "Dt", "ModelBuildingSteps", "ForwardSkip")
    _check_params("Run default", run_conf, required_fields, numeric_fields, non_negatives)


@SimConfig.validator
def _loadbal_mode(config: _SimConfig, run_conf):
    cli_args = config.cli_options
    if Feature.LoadBalance not in cli_args.restrict_features:
        logging.warning("Disabled Load Balance (restrict_features)")
        config.loadbal_mode = LoadBalanceMode.RoundRobin
        return
    lb_mode_str = cli_args.lb_mode or run_conf.get("RunMode")
    config.loadbal_mode = LoadBalanceMode.parse(lb_mode_str)


@SimConfig.validator
def _projection_params(config: _SimConfig, run_conf):
    required_fields = ("Path",)
    non_negatives = ("PopulationID",)
    for name, proj in config.projections.items():
        _check_params("Projection " + name, compat.Map(proj), required_fields, (), non_negatives)
        _validate_file_extension(compat.Map(proj).get("Path"))


@SimConfig.validator
def _stimulus_params(config: _SimConfig, run_conf):
    required_fields = ("Mode", "Pattern", "Duration", "Delay",)
    numeric_fields = ("Dt", "RiseTime", "DecayTime", "AmpMean", "AmpVar", "MeanPercent",
                      "SDPercent", "AmpCV", "AmpStart", "AmpEnd", "PercentStart",
                      "PercentEnd", "PercentLess", "Mean", "Variance", "Voltage", "RS",)
    non_negatives = ("Duration", "Delay", "Rate", "Frequency", "Width", "Lambda", "Weight",
                     "NumOfSynapses", "Seed",)
    valid_values = {
        "Mode": ("Current", "Voltage", "Conductance", "spikes"),
        "Pattern": {
            "Hyperpolarizing", "Linear", "Noise", "Pulse", "RelativeLinear",
            "RelativeShotNoise", "SEClamp", "ShotNoise", "Sinusoidal",
            "SubThreshold", "SynapseReplay", "OrnsteinUhlenbeck",
            "NPoisson", "NPoissonInhomogeneous", "ReplayVoltageTrace",
            "AbsoluteShotNoise", "RelativeOrnsteinUhlenbeck"
        }
    }
    deprecated_values = {
        "Pattern": ("NPoisson", "NPoissonInhomogeneous", "ReplayVoltageTrace")
    }
    for name, stim in config.stimuli.items():
        _check_params("Stimulus " + name, compat.Map(stim), required_fields, numeric_fields,
                      non_negatives, valid_values, deprecated_values)


@SimConfig.validator
def _modification_params(config: _SimConfig, run_conf):
    required_fields = ("Target", "Type",)
    for name, mod_block in config.modifications.items():
        _check_params("Modification " + name, compat.Map(mod_block), required_fields, ())


def _make_circuit_config(config_dict, req_morphology=True):
    if config_dict.get("CircuitPath") == "<NONE>":
        config_dict["CircuitPath"] = False
        config_dict["nrnPath"] = False
        config_dict["MorphologyPath"] = False
    elif config_dict.get("nrnPath") == "<NONE>":
        config_dict["nrnPath"] = False
    _validate_circuit_morphology(config_dict, req_morphology)
    _validate_file_extension(config_dict.get("CellLibraryFile"))
    _validate_file_extension(config_dict.get("nrnPath"))
    return CircuitConfig(config_dict)


def _validate_circuit_morphology(config_dict, required=True):
    morph_path = config_dict.get("MorphologyPath")
    morph_type = config_dict.get("MorphologyType")
    if morph_path is None and required:
        raise ConfigurationError("No morphology path provided (Required!)")
    # Some circuit types may not require morphology files
    if not morph_path:
        log_verbose(" > Morphology src: <Disabled> MorphologyType: %s, ", morph_type or "<None>")
        return
    if morph_type is None:
        logging.warning("MorphologyType not set. Assuming ascii and legacy /ascii subdir")
        morph_type = "asc"
        morph_path = os.path.join(morph_path, "ascii")
        config_dict["MorphologyType"] = morph_type
        config_dict["MorphologyPath"] = morph_path
    assert morph_type in ("asc", "swc", "h5", "hoc"), "Invalid MorphologyType"
    log_verbose(" > MorphologyType = %s, src: %s", morph_type, morph_path)


def _validate_file_extension(path):
    if not path:
        return
    filepath = path.split(":")[0]  # for sonata, remove the edge_pop name appended to the file path
    if filepath.endswith(".sonata"):
        raise ConfigurationError("*.sonata files are no longer supported, "
                                 "please rename them to *.h5")


@SimConfig.validator
def _base_circuit(config: _SimConfig, run_conf):
    log_verbose("CIRCUIT (default): %s", run_conf.get("CircuitPath", "<DISABLED>"))
    config.base_circuit = _make_circuit_config(run_conf)


@SimConfig.validator
def _extra_circuits(config: _SimConfig, run_conf):
    from . import EngineBase
    extra_circuits = {}

    for name, circuit_info in config._simulation_config.Circuit.items():
        log_verbose("CIRCUIT %s (%s)", name, circuit_info.get("Engine", "(default)"))
        if "Engine" in circuit_info:
            # Replace name by actual engine
            circuit_info["Engine"] = EngineBase.get(circuit_info["Engine"])
        else:
            # Without custom engine, inherit base circuit infos
            for field in ("CircuitPath", "MorphologyPath", "MorphologyType",
                          "METypePath", "CellLibraryFile"):
                if field in config.base_circuit and field not in circuit_info:
                    log_verbose(" > Inheriting '%s' from base circuit", field)
                    circuit_info[field] = config.base_circuit[field]
        circuit_info.setdefault("nrnPath", False)
        extra_circuits[name] = _make_circuit_config(circuit_info, req_morphology=False)
        extra_circuits[name]._name = name

    # Sort so that iteration is deterministic
    config.extra_circuits = dict(sorted(
        extra_circuits.items(),
        key=lambda x: (x[1].Engine.CircuitPrecedence if x[1].Engine else 0, x[0])
    ))


@SimConfig.validator
def _global_parameters(config: _SimConfig, run_conf):
    from neuron import h
    config.celsius = run_conf.get("Celsius", 34)
    config.v_init = run_conf.get("V_Init", -65)
    config.extracellular_calcium = run_conf.get("ExtracellularCalcium")
    config.buffer_time = 25 * run_conf.get("FlushBufferScalar", 1)
    config.tstop = run_conf["Duration"]
    h.celsius = config.celsius
    h.set_v_init(config.v_init)
    h.tstop = config.tstop
    config.default_neuron_dt = h.dt
    h.dt = run_conf.get("Dt", h.dt)
    h.steps_per_ms = 1.0 / h.dt
    props = ("celsius", "v_init", "extracellular_calcium", "tstop", "buffer_time")
    log_verbose("Global params: %s",
                " | ".join(p + ": %s" % getattr(config, p) for p in props))
    if "CompartmentsPerSection" in run_conf:
        logging.warning("CompartmentsPerSection is currently not supported. "
                        "If needed, please request with a detailed usecase.")


@SimConfig.validator
def _set_simulator(config: _SimConfig, run_conf):
    user_config = config.cli_options
    simulator = run_conf.get("Simulator")

    if simulator is None:
        run_conf["Simulator"] = simulator = "NEURON"
    if simulator not in ("NEURON", "CORENEURON"):
        raise ConfigurationError("'Simulator' value must be either NEURON or CORENEURON")
    if simulator == "NEURON" and (user_config.build_model is False
                                  or user_config.simulate_model is False):
        raise ConfigurationError("Disabling model building or simulation is only"
                                 " compatible with CoreNEURON")

    log_verbose("Simulator = %s", simulator)
    config.use_neuron = (simulator == "NEURON")
    config.use_coreneuron = (simulator == "CORENEURON")


@SimConfig.validator
def _spike_parameters(config: _SimConfig, run_conf):
    spike_location = run_conf.get("SpikeLocation", "soma")
    if spike_location not in ["soma", "AIS"]:
        raise ConfigurationError("Possible options for SpikeLocation are 'soma' and 'AIS'")
    spike_threshold = run_conf.get("SpikeThreshold", -30)
    log_verbose("Spike_Location = %s", spike_location)
    log_verbose("Spike_Threshold = %s", spike_threshold)
    config.spike_location = spike_location
    config.spike_threshold = spike_threshold


_condition_checks = {
    "secondorder": (
        (0, 1, 2),
        ConfigurationError(
            "Time integration method (SecondOrder value) {} is invalid. Valid options are:"
            " '0' (implicitly backward euler),"
            " '1' (Crank-Nicolson) and"
            " '2' (Crank-Nicolson with fixed ion currents)")
    ),
    "randomize_Gaba_risetime": (
        ("True", "False", "0", "false"),
        ConfigurationError("randomize_Gaba_risetime must be True or False")
    ),
    "SYNAPSES__minis_single_vesicle": ((0, 1), None),
    "synapses__minis_single_vesicle": ((0, 1), None),
    "SYNAPSES__init_depleted": ((0, 1), None),
    "synapses__init_depleted": ((0, 1), None),
}


@SimConfig.validator
def _simulator_globals(config: _SimConfig, run_conf):
    if not hasattr(config._simulation_config, "Conditions"):
        return None
    from neuron import h
    # Hackish but some constants only live in the helper
    h.load_file("GABAABHelper.hoc")

    for group in config._simulation_config.Conditions.values():
        for key, value in group.items():
            validator = _condition_checks.get(key)
            if validator:
                config_exception = validator[1] or ConfigurationError(
                    "Value {} not valid for key {}. Allowed: {}".format(value, key, validator[0])
                )
                if value not in validator[0]:
                    raise config_exception
            synvar_prefix = "SYNAPSES__"
            if key.startswith(synvar_prefix) or key.startswith(synvar_prefix.lower()):
                key = key[len(synvar_prefix):]
                config.synapse_options[key] = value
                log_verbose("SYNAPSES %s = %s", key, value)
                for synapse_name in ("ProbAMPANMDA_EMS", "ProbGABAAB_EMS", "GluSynapse"):
                    setattr(h, key + "_" + synapse_name, value)
            else:
                log_verbose("GLOBAL %s = %s", key, value)
                setattr(h, key, value)
            if "cao_CR" in key and value != config.extracellular_calcium:
                logging.warning("Value of %s (%s) is not the same as extracellular_calcium (%s)"
                                % (key, value, config.extracellular_calcium))


@SimConfig.validator
def _second_order(config: _SimConfig, run_conf):
    second_order = run_conf.get("SecondOrder")
    if second_order is None:
        return None
    second_order = int(second_order)
    if second_order in (0, 1, 2):
        from neuron import h
        log_verbose("SecondOrder = %g", second_order)
        config.second_order = second_order
        h.secondorder = second_order
    else:
        raise _condition_checks["secondorder"][1]


@SimConfig.validator
def _single_vesicle(config: _SimConfig, run_conf):
    if "MinisSingleVesicle" not in run_conf:
        return
    from neuron import h
    if not hasattr(h, "minis_single_vesicle_ProbAMPANMDA_EMS"):
        raise NotImplementedError("Synapses don't implement minis_single_vesicle. "
                                  "More recent neurodamus model required.")
    minis_single_vesicle = int(run_conf["MinisSingleVesicle"])
    log_verbose("minis_single_vesicle = %d", minis_single_vesicle)
    h.minis_single_vesicle_ProbAMPANMDA_EMS = minis_single_vesicle
    h.minis_single_vesicle_ProbGABAAB_EMS = minis_single_vesicle
    h.minis_single_vesicle_GluSynapse = minis_single_vesicle


@SimConfig.validator
def _randomize_gaba_risetime(config: _SimConfig, run_conf):
    randomize_risetime = run_conf.get("RandomizeGabaRiseTime")
    if randomize_risetime is None:
        return
    from neuron import h
    h.load_file("GABAABHelper.hoc")
    if not hasattr(h, "randomize_Gaba_risetime"):
        raise NotImplementedError("Models don't support setting RandomizeGabaRiseTime. "
                                  "Please load a more recent model or drop the option.")
    assert randomize_risetime in ("True", "False", "0", "false")  # any non-"True" value is negative
    log_verbose("randomize_Gaba_risetime = %s", randomize_risetime)
    h.randomize_Gaba_risetime = randomize_risetime


@SimConfig.validator
def _current_dir(config: _SimConfig, run_conf):
    curdir = run_conf.get("CurrentDir")

    if curdir is None:
        log_verbose("CurrentDir using simulation config path [default]")
        curdir = config.simulation_config_dir
    else:
        if not os.path.isabs(curdir):
            if curdir == ".":
                logging.warning("Setting CurrentDir to '.' is discouraged and "
                                "shall never be used in production jobs.")
            else:
                raise ConfigurationError("CurrentDir: Relative paths not allowed")
            curdir = os.path.abspath(curdir)
        if not os.path.isdir(curdir):
            raise ConfigurationError("CurrentDir doesnt exist: " + curdir)

    log_verbose("CurrentDir = %s", curdir)
    run_conf["CurrentDir"] = curdir
    config.current_dir = curdir


@SimConfig.validator
def _output_root(config: _SimConfig, run_conf):
    def check_oputput_directory(output_dir):
        """
        Checks if output directory exists and is a directory.
        If it doesn't exists create it.
        This logic is based in old utility.mod.
        """
        if os.path.exists(output_dir):
            if not os.path.isdir(output_dir):
                raise Exception(f"{output_dir} does not name a directory.")
        else:
            try:
                os.makedirs(output_dir)
            except Exception as e:
                raise Exception(f"Failed to create OutputRoot directory {output_dir} with {e}")
            log_verbose(f"Directory {output_dir} does not exist.  Creating...")

    """confirm output_path exists and is usable"""
    output_path = run_conf.get("OutputRoot")

    if config.cli_options.output_path not in (None, output_path):
        output_path = config.cli_options.output_path
    if output_path is None:
        raise ConfigurationError("'OutputRoot' configuration not set")
    if not os.path.isabs(output_path):
        output_path = os.path.join(config.current_dir, output_path)

    from ._neurodamus import MPI
    if MPI.rank == 0:
        check_oputput_directory(output_path)
        # Delete coreneuron_input link since it may conflict with restore
        corenrn_input = output_path + "/coreneuron_input"
        if os.path.islink(corenrn_input):
            os.remove(corenrn_input)

    # Barrier to make sure that the output_path is created in case it doesn't exist
    MPI.barrier()

    log_verbose("OutputRoot = %s", output_path)
    run_conf["OutputRoot"] = output_path
    config.output_root = output_path


@SimConfig.validator
def _check_save(config: _SimConfig, run_conf):
    cli_args = config.cli_options
    save_path = cli_args.save or run_conf.get("Save")
    save_time = cli_args.save_time or run_conf.get("SaveTime")

    if not save_path:
        if save_time:
            logging.warning("SaveTime/--save-time IGNORED. Reason: no 'Save' config entry")
        return

    if not config.use_coreneuron:
        raise ConfigurationError("Save-restore only available with CoreNeuron")

    # Handle save
    assert isinstance(save_path, str), "Save must be a string path"
    if save_time:
        save_time = float(save_time)
        if save_time > config.tstop:
            logging.warning("SaveTime specified beyond Simulation Duration. "
                            "Setting SaveTime to simulation end time.")
            save_time = None

    config.save = os.path.join(config.current_dir, save_path)
    config.save_time = save_time


@SimConfig.validator
def _check_restore(config: _SimConfig, run_conf):
    restore = config.cli_options.restore or run_conf.get("Restore")
    if not restore:
        return

    if not config.use_coreneuron:
        raise ConfigurationError("Save-restore only available with CoreNeuron")

    # sync restore settings to hoc, otherwise we end up with an empty coreneuron_input dir
    run_conf["Restore"] = restore

    restore_path = os.path.join(config.current_dir, restore)
    assert os.path.isdir(os.path.dirname(restore_path))
    config.restore = restore_path


@SimConfig.validator
def _coreneuron_params(config: _SimConfig, run_conf):
    buffer_size = run_conf.get("ReportingBufferSize")
    if buffer_size is not None:
        assert buffer_size > 0
        log_verbose("ReportingBufferSize = %g", buffer_size)
        config.corenrn_buff_size = int(buffer_size)

    # Set defaults for CoreNeuron dirs since SimConfig init/verification happens after
    config.coreneuron_outputdir = config.output_root
    coreneuron_datadir = os.path.join(config.output_root, "coreneuron_input")

    if config.use_coreneuron and config.restore:
        # Most likely we will need to reuse coreneuron_input from first part
        if not os.path.isdir(coreneuron_datadir):
            logging.info("RESTORE: Searching for coreneuron_input besides " + config.restore)
            coreneuron_datadir = os.path.join(config.restore, "..", "coreneuron_input")
        assert os.path.isdir(coreneuron_datadir), "coreneuron_input dir not found"

    config.coreneuron_datadir = coreneuron_datadir


@SimConfig.validator
def _check_model_build_mode(config: _SimConfig, run_conf):
    user_config = config.cli_options
    config.build_model = user_config.build_model
    config.simulate_model = user_config.simulate_model

    if config.build_model is True:  # just create the data
        return
    if config.use_coreneuron is False:
        if config.build_model is False:
            raise ConfigurationError("Skipping model build is only available with CoreNeuron")
        else:  # was None
            config.build_model = True
            return

    # CoreNeuron restore is a bit special and already had its input dir checked
    if config.restore:
        config.build_model = False
        return

    # It's a CoreNeuron run. We have to check if build_model is AUTO or OFF
    core_data_location = config.coreneuron_datadir

    try:
        # Ensure that 'sim.conf' and 'files.dat' exist, and that '/dev/shm' was not used
        with open(os.path.join(config.output_root, "sim.conf"), 'r') as f:
            core_data_exists = (
                "datpath='/dev/shm/" not in f.read()
                and os.path.isfile(os.path.join(core_data_location, "files.dat"))
            )
    except FileNotFoundError:
        core_data_exists = False

    if config.build_model in (None, "AUTO"):
        # If enable-shm option is given we have to rebuild the model and delete any previous files
        # in /dev/shm or gpfs
        # In any case when we start model building any data in the core_data_location_shm if it
        # exists are deleted
        if not core_data_exists:
            core_data_location_shm = SHMUtil.get_datadir_shm(core_data_location)
            data_location = (
                core_data_location_shm
                if (
                    user_config.enable_shm and core_data_location_shm is not None
                )
                else core_data_location
            )
            logging.info("Valid CoreNeuron input data not found in '%s'. "
                         "Neurodamus will proceed to model building.",
                         data_location)
            config.build_model = True
        else:
            logging.info("CoreNeuron input data found in %s. Skipping model build",
                         core_data_location)
            config.build_model = False

    if not config.build_model and not core_data_exists:
        raise ConfigurationError("Model build DISABLED but no CoreNeuron data found")


@SimConfig.validator
def _keep_coreneuron_data(config: _SimConfig, run_conf):
    if config.use_coreneuron:
        keep_core_data = False
        if config.cli_options.keep_build or run_conf.get("KeepModelData", False) == "True":
            keep_core_data = True
        elif not config.cli_options.simulate_model or config.save:
            logging.warning("Keeping coreneuron data for CoreNeuron following run")
            keep_core_data = True
        config.delete_corenrn_data = not keep_core_data
    log_verbose("delete_corenrn_data = %s", config.delete_corenrn_data)


@SimConfig.validator
def _model_building_steps(config: _SimConfig, run_conf):
    user_config = config.cli_options
    if user_config.modelbuilding_steps is not None:
        ncycles = int(user_config.modelbuilding_steps)
    else:
        return None

    assert ncycles > 0, "ModelBuildingSteps set to 0. Required value > 0"

    if not SimConfig.use_coreneuron:
        logging.warning("IGNORING ModelBuildingSteps since simulator is not CORENEURON")
        return None

    if "CircuitTarget" not in run_conf:
        raise ConfigurationError(
            "Multi-iteration coreneuron data generation requires CircuitTarget")

    logging.info("Splitting Target for multi-iteration CoreNeuron data generation")
    logging.info(" -> Cycles: %d. [src: %s]", ncycles, "CLI")
    config.modelbuilding_steps = ncycles


@SimConfig.validator
def _report_vars(config: _SimConfig, run_conf):
    """Compartment reports read voltages or i_membrane only. Other types must be summation"""
    mandatory_fields = ("Type", "StartTime", "Target", "Dt", "ReportOn", "Unit", "Format")
    report_types = {"compartment", "Summation", "Synapse", "PointType", "lfp"}
    non_negatives = ("StartTime", "EndTime", "Dt")
    report_configs_dict = {}

    for rep_name, rep_config in config.reports.items():
        rep_config = compat.Map(rep_config).as_dict(parse_strings=True)
        report_configs_dict[rep_name] = rep_config

        _check_params("Report " + rep_name, rep_config, mandatory_fields,
                      non_negatives=non_negatives,
                      valid_values={'Type': report_types})

        if rep_config["Format"] != "SONATA":
            raise ConfigurationError(
                f"Unsupported report format: '{rep_config['Format']}'. Use 'SONATA' instead.")

        if config.use_coreneuron and rep_config["Type"] == "compartment":
            if rep_config["ReportOn"] not in ("v", "i_membrane"):
                logging.warning("Compartment reports on vars other than v and i_membrane "
                                " are still not fully supported (CoreNeuron)")
    # Overwrite config with a pure dict since we never need underlying hoc map
    config.reports = report_configs_dict


@SimConfig.validator
def _spikes_sort_order(config: _SimConfig, run_conf):
    order = run_conf.get("SpikesSortOrder", "by_time")
    if order not in ["none", "by_time"]:
        raise ConfigurationError("Unsupported spikes sort order %s, " % order +
                                 "BBP supports 'none' and 'by_time'")


def get_debug_cell_gid(cli_options):
    gid = cli_options.get("dump_cell_state") if cli_options else None
    if gid:
        try:
            # Convert to integer and adjust for sonata mode (0-based to 1-based indexing)
            gid = int(gid) + 1
        except ValueError as e:
            raise ConfigurationError("Cannot parse Gid for dump-cell-state: " + gid) from e
    return gid


def check_connections_configure(SimConfig, target_manager):
    """Check connection block configuration and raise warnings for:
    1. Global variable should be set in the Conditions block,
    2. Connection overriding chains (t=0)
    3. Connections with Weight=0 not overridden by delayed (not instantiated)
    4. Partial Connection overriding -> Error
    5. Connections with delay > 0 not overriding anything
    """
    config_assignment = re.compile(r"(\S+)\s*\*?=\s*(\S+)")
    processed_conn_blocks = []
    zero_weight_conns = []
    conn_configure_global_vars = defaultdict(list)

    def get_overlapping_connection_pathway(base_conns, conn):
        for base_conn in reversed(base_conns):
            if target_manager.pathways_overlap(base_conn, conn):
                yield base_conn

    def process_t0_parameter_override(conn):
        if float(conn.get("Weight", 1)) == 0:
            zero_weight_conns.append(conn)
        for overridden_conn in get_overlapping_connection_pathway(processed_conn_blocks, conn):
            conn["_overrides"] = overridden_conn
            if target_manager.pathways_overlap(conn, overridden_conn, equal_only=True):
                overridden_conn["_full_overridden"] = True
            break  # We always compute only against the first overridden block
        processed_conn_blocks.append(conn)

    def process_weight0_override(conn):
        is_overriding = False
        for conn2 in get_overlapping_connection_pathway(zero_weight_conns, conn):
            is_overriding = True
            # If there isn't a full override for zero weights, we must raise exception (later)
            if not conn2.get("_full_overridden"):
                conn2["_full_overridden"] = target_manager.pathways_overlap(conn, conn2, True)
        if not is_overriding:
            logging.warning("Delayed connection %s is not overriding any weight=0 Connection",
                            conn["_name"])

    def get_syn_config_vars(conn):
        return [var for var, _ in config_assignment.findall(conn.get("SynapseConfigure", ""))]

    def display_overriding_chain(conn):
        logging.warning("Connection %s takes part in overriding chain:", conn["_name"])
        while conn is not None:
            logging.info(
                " -> %-6s %-60.60s Weight: %-8s SpontMinis: %-8s SynConfigure: %s",
                "(base)" if not conn.get("_overrides") else " ^",
                "{0[_name]}  {0[Source]} -> {0[Destination]}".format(conn),
                conn.get("Weight", "-"),
                conn.get("SpontMinis", "-"),
                ", ".join(get_syn_config_vars(conn))
            )
            if conn.get("_visited"):
                break
            conn["_visited"] = True
            conn = conn.get("_overrides")

    logging.info("Checking Connection Configurations")
    all_conn_blocks = [compat.Map(conn).as_dict(parse_strings=True)
                       for conn in SimConfig.connections.values()]

    # On a first phase process only for t=0
    for name, conn_conf in zip(SimConfig.connections, all_conn_blocks):
        conn_conf["_name"] = name
        if float(conn_conf.get("Delay", 0)) > .0:
            continue
        for var in get_syn_config_vars(conn_conf):
            if not var.startswith("%s"):
                conn_configure_global_vars[name].append(var)
        # Process all conns to show full override chains to help debug
        process_t0_parameter_override(conn_conf)

    # Second phase: find overridden zero_weights at t > 0
    for conn_conf in all_conn_blocks:
        if float(conn_conf.get("Delay", 0)) > 0:
            process_weight0_override(conn_conf)

    # CHECK 1: Global vars
    if conn_configure_global_vars:
        logging.warning("Global variables in SynapseConfigure. Review the following "
                        "connections and move the global vars to Conditions block")
        for name, vars in conn_configure_global_vars.items():
            logging.warning(" -> %s: %s", name, vars)
    else:
        logging.info(" => CHECK No Global vars!")

    # CHECK 2: Block override chains
    if not [display_overriding_chain(conn_conf)
            for conn_conf in reversed(processed_conn_blocks)
            if conn_conf.get("_overrides") and not conn_conf.get("_visited")]:
        logging.info(" => CHECK No Block Overrides!")

    # CHECK 3: Weight 0 not/badly overridden
    not_overridden_weight_0 = []
    for conn in zero_weight_conns:
        full_overriden = conn.get("_full_overridden")
        if full_overriden is None:
            not_overridden_weight_0.append(conn)
        elif full_overriden is False:  # incomplete override
            raise ConfigurationError(
                "Partial Weight=0 override is not supported: Conn %s" % conn["_name"])
    if not_overridden_weight_0:
        logging.warning("The following connections with Weight=0 are not overridden, "
                        "thus won't be instantiated:")
        for conn in not_overridden_weight_0:
            logging.warning(" -> %s", conn["_name"])
    else:
        logging.info(" => CHECK No single Weight=0 blocks!")


def _input_resistance(config: _SimConfig, target_manager):
    prop = "@dynamics:input_resistance"
    for stim_name, stim in config.stimuli.items():
        stim = compat.Map(stim).as_dict(parse_strings=True)
        stim_inject = config.get_stim_inject(stim_name)
        if stim_inject is None:
            continue  # not injected, do not care
        target_name = stim_inject["Target"]
        if stim["Mode"] == "Conductance" and \
           stim["Pattern"] in ["RelativeShotNoise", "RelativeOrnsteinUhlenbeck"]:
            # NOTE: use target_manager to read the population names of hoc or NodeSet targets
            target = target_manager.get_target(target_name)
            for population in target.population_names:
                config._cell_requirements.setdefault(population, set()).add(prop)
                log_verbose('[cell] %s (%s:%s)' % (prop, population, target.name))
