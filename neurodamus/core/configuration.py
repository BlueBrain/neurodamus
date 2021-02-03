"""
Runtime configuration
"""
from __future__ import absolute_import
import logging
import os
import os.path
from enum import Enum
from ..io.config_parser import BlueConfig
from ..utils import compat
from ..utils.logging import log_verbose
from ..utils.pyutils import ConfigT


class LogLevel:
    ERROR_ONLY = 0
    DEFAULT = 1
    VERBOSE = 2
    DEBUG = 3


class ConfigurationError(Exception):
    """Error due to invalid settings in BlueConfig"""
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


class RunOptions(ConfigT):
    build_model = None
    simulate_model = True
    model_path = None  # Currently is output-path
    output_path = None
    keep_build = False
    modelbuilding_steps = None


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
    projections = None
    connections = None
    stimuli = None
    injects = None
    reports = None
    configures = None

    # Hoc objects used
    _config_parser = None
    _parsed_run = None
    _blueconfig = None  # new python BlueConfig parser
    _simconf = None
    rng_info = None
    coreneuron = None  # bridge to CoreNeuron, instance of CoreConfig

    # In principle not all vars need to be required as they'r set by the parameter functions
    blueconfig_dir = None
    current_dir = None
    buffer_time = 25
    restore = None
    extracellular_calcium = None
    secondorder = None
    use_coreneuron = False
    use_neuron = True
    coreneuron_datadir = None
    coreneuron_ouputdir = None
    corenrn_buff_size = 8
    delete_corenrn_data = False
    modelbuilding_steps = 1
    build_model = True
    simulate_model = True
    synapse_options = {}

    _validators = []

    restore_coreneuron = property(lambda self: self.use_coreneuron and bool(self.restore))

    @classmethod
    def init(cls, config_file, cli_options):
        # Import these objects scope-level to avoid cross module dependency
        from ._neurodamus import NeurodamusCore as Nd
        assert os.path.isfile(config_file)
        logging.info("Initializing Simulation Configuration and Validation")
        log_verbose("ConfigFile: %s", config_file)
        log_verbose("CLI Options: %s", cli_options)
        cls.config_file = config_file
        cls._config_parser = cls._init_config_parser(config_file, Nd)
        cls._parsed_run = compat.Map(cls._config_parser.parsedRun)  # easy access to hoc Map
        cls._blueconfig = BlueConfig(config_file)
        cls.blueconfig_dir = os.path.dirname(os.path.abspath(config_file))

        cls.run_conf = run_conf = cls._parsed_run.as_dict(parse_strings=True)
        cls.projections = compat.Map(cls._config_parser.parsedProjections)
        cls.connections = compat.Map(cls._config_parser.parsedConnects)
        cls.stimuli = compat.Map(cls._config_parser.parsedStimuli)
        cls.injects = compat.Map(cls._config_parser.parsedInjects)
        cls.reports = compat.Map(cls._config_parser.parsedReports)
        cls.configures = compat.Map(cls._config_parser.parsedConfigures)
        cls.cli_options = RunOptions(**(cli_options or {}))

        for validator in cls._validators:
            validator(cls, run_conf)

        logging.info("Initializing hoc config objects")
        cls._parsed_run.update(run_conf)  # sync hoc config
        cls._init_hoc_config_objs(Nd)

    @classmethod
    def get_blueconfig_hoc_section(cls, section_name):
        return getattr(cls._config_parser, section_name)

    @classmethod
    def _init_config_parser(cls, config_file, Nd):
        config_parser = Nd.ConfigParser()
        config_parser.open(config_file)
        if Nd.pc.id() == 0:
            config_parser.toggleVerbose()
        if config_parser.parsedRun is None:
            raise ConfigurationError("No 'Run' block found in BlueConfig %s", config_file)
        return config_parser

    @classmethod
    def _init_hoc_config_objs(cls, Nd):
        """Init objects which parse/check configs in the hoc world"""
        h = Nd.h
        parsed_run = cls._parsed_run.hoc_map
        cls._simconf = h.simConfig
        cls._simconf.interpret(parsed_run)

        cls.rng_info = h.RNGSettings()
        cls.rng_info.interpret(parsed_run)

        if cls._simconf.coreNeuronUsed():
            cls.coreneuron = h.CoreConfig(cls.output_root)
            # NOTE: commenting out the following lines since locations are hardcoded
            #   and therefore now we set them in python directly (and early).
            #   The day we need to make it configurable, SimConfig needs to extract
            #   the locations from the parsedRun
            # cls.coreneuron_datadir = simconf.getCoreneuronDataDir().s

    @classmethod
    def validator(cls, f):
        """Decorator to register parameters / config validators"""
        cls._validators.append(f)

    @classmethod
    def update_connection_blocks(cls, alias):
        """Convert source destination to real population names

        Args:
            alias: A dict associating alias->real_name's
        """
        from ..target_manager import TargetSpec  # avoid cyclic deps
        if isinstance(cls.connections, dict):
            return  # Already processed

        def update_item(conn, item):
            src_spec = TargetSpec(conn.get(item))
            src_spec.population = alias.get(src_spec.population, src_spec.population)
            conn[item] = str(src_spec)

        new_connections = {}
        for name, conn in cls.connections.items():
            conn = compat.Map(conn).as_dict(True)
            update_item(conn, "Source")
            update_item(conn, "Destination")
            new_connections[name] = conn
        cls.connections = new_connections


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
    search_paths += (SimConfig.current_dir, SimConfig.blueconfig_dir)

    def try_find_in(fullpath):
        if os.path.isfile(fullpath):
            return fullpath
        if alt_filename is not None:
            alt_file_path = os.path.join(fullpath, alt_filename)
            if os.path.isfile(alt_file_path):
                return alt_file_path
        return None

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


def _make_circuit_config(config_dict, req_morphology=True):
    if config_dict["CircuitPath"] == "<NONE>":
        config_dict["CircuitPath"] = False
        config_dict["nrnPath"] = False
        config_dict["MorphologyPath"] = False
    elif config_dict["nrnPath"] == "<NONE>":
        config_dict["nrnPath"] = False
    _validate_circuit_morphology(config_dict, req_morphology)
    return CircuitConfig(config_dict)


def _validate_circuit_morphology(config_dict, required=True):
    morph_path = config_dict.get("MorphologyPath")
    morph_type = config_dict.get("MorphologyType")
    if morph_path is None and required:
        raise ConfigurationError("No morphology path provided (Required!)")
    # Some circuit types may not require morphology files (eg: Point Neurons)
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


@SimConfig.validator
def _base_circuit(config: _SimConfig, run_conf):
    log_verbose("CIRCUIT (default): %s", run_conf.get("CircuitPath", "<DISABLED>"))
    config.base_circuit = _make_circuit_config(run_conf)


@SimConfig.validator
def _extra_circuits(config: _SimConfig, run_conf):
    from . import EngineBase
    extra_circuits = {}

    for name, circuit_info in config._blueconfig.Circuit.items():
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
    config.extra_circuits = extra_circuits


@SimConfig.validator
def _global_parameters(config: _SimConfig, run_conf):
    from neuron import h
    config.celsius = run_conf.get("Celsius", 34)
    config.v_init = run_conf.get("V_Init", -65)
    config.extracellular_calcium = run_conf.get("ExtracellularCalcium")
    config.buffer_time = 25 * run_conf.get("FlushBufferScalar", 1)
    config.tstop = run_conf["Duration"]
    h.celsius = config.celsius
    h.v_init = config.v_init
    h.tstop = config.tstop
    h.dt = run_conf.get("Dt", 0.025)
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
            " '1' (crank-nicholson) and"
            " '2' (crank-nicholson with fixed ion currents)")
    ),
    "randomize_Gaba_risetime": (
        ("True", "False", "0", "false"),
        ConfigurationError("randomize_Gaba_risetime must be True or False")
    ),
    "SYNAPSES__minis_single_vesicle": ((0, 1), None),
    "SYNAPSES__init_depleted": ((0, 1), None),
}


@SimConfig.validator
def _simulator_globals(config: _SimConfig, run_conf):
    if not hasattr(config._blueconfig, "Conditions"):
        return None
    from neuron import h
    # Hackish but some constants only live in the helper
    h.load_file("GABAABHelper.hoc")

    for group in config._blueconfig.Conditions.values():
        for key, value in group.items():
            validator = _condition_checks.get(key)
            if validator:
                config_exception = validator[1] or ConfigurationError(
                    "Value {} not valid for key {}. Allowed: {}".format(value, key, validator[0])
                )
                if value not in validator[0]:
                    raise config_exception
            if key.startswith("SYNAPSES__"):
                key = key[len("SYNAPSES__"):]
                config.synapse_options[key] = value
                log_verbose("SYNAPSES %s = %s", key, value)
                for synapse_name in ("ProbAMPANMDA_EMS", "ProbGABAAB_EMS", "GluSynapse"):
                    setattr(h, key + "_" + synapse_name, value)
            else:
                log_verbose("GLOBAL %s = %s", key, value)
                setattr(h, key, value)


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
    run_conf["BlueConfigDir"] = config.blueconfig_dir

    if curdir is None:
        log_verbose("CurrentDir using BlueConfig path [default]")
        curdir = config.blueconfig_dir
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
    """confirm output_path exists and is usable -> use utility.mod"""
    output_path = run_conf.get("OutputRoot")

    if config.cli_options.output_path not in (None, output_path):
        output_path = config.cli_options.output_path
    if output_path is None:
        raise ConfigurationError("'OutputRoot' configuration not set")
    if not os.path.isabs(output_path):
        output_path = os.path.join(config.current_dir, output_path)

    from ._neurodamus import NeurodamusCore as Nd, MPI
    if MPI.rank == 0:
        if Nd.checkDirectory(output_path) < 0:
            raise ConfigurationError("Error with OutputRoot: %s" % output_path)

    log_verbose("OutputRoot = %s", output_path)
    run_conf["OutputRoot"] = output_path
    config.output_root = output_path


@SimConfig.validator
def _check_restore(config: _SimConfig, run_conf):
    if "Restore" not in run_conf:
        return
    restore_path = os.path.join(config.current_dir, run_conf["Restore"])
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
    config.coreneuron_ouputdir = config.output_root
    config.coreneuron_datadir = os.path.join(config.output_root, "coreneuron_input")


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

    # It's a CoreNeuron run. We have to check if build_model is AUTO or OFF
    core_data_location = config.coreneuron_datadir
    core_data_exists = (
        os.path.isfile(os.path.join(config.output_root, "sim.conf"))
        and os.path.isfile(os.path.join(core_data_location, "files.dat"))
    )
    if config.build_model in (None, "AUTO"):
        if not core_data_exists:
            logging.info("CoreNeuron input data not found in '%s'. "
                         "Neurodamus will proceed to model building.",
                         core_data_location)
            config.build_model = True
        else:
            logging.info("CoreNeuron input data found. Skipping model build")
            config.build_model = False

    if not config.build_model and not core_data_exists:
        raise ConfigurationError("Model build DISABLED but no CoreNeuron data found")


@SimConfig.validator
def _keep_coreneuron_data(config: _SimConfig, run_conf):
    if config.use_coreneuron:
        keep_core_data = False
        if config.cli_options.keep_build or run_conf.get("KeepModelData", False) == "True":
            keep_core_data = True
        elif not config.cli_options.simulate_model or "Save" in run_conf:
            logging.warning("Keeping coreneuron data for CoreNeuron following run")
            keep_core_data = True
        config.delete_corenrn_data = not keep_core_data
    log_verbose("delete_corenrn_data = %s", config.delete_corenrn_data)


@SimConfig.validator
def _model_building_steps(config: _SimConfig, run_conf):
    user_config = config.cli_options
    if user_config.modelbuilding_steps is not None:
        ncycles = int(user_config.modelbuilding_steps)
        src_is_cli = True
    elif "ModelBuildingSteps" in run_conf:
        ncycles = int(run_conf["ModelBuildingSteps"])
        src_is_cli = False
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
    logging.info(" -> Cycles: %d. [src: %s]", ncycles, "CLI" if src_is_cli else "BlueConfig")
    config.modelbuilding_steps = ncycles
