"""
Module to load configuration from a libsonata config
"""
import json
import libsonata
import logging
import os.path


class SonataConfig:

    __slots__ = (
        "_entries",
        "_sections",
        '_config_dir',
        '_config_json',
        '_resolved_manifest',
        'circuits',
        '_circuit_networks',
        '_sim_conf'
    )

    _config_entries = (
        "network", "target_simulator", "node_sets_file", "node_set"
    )
    _config_sections = (
        "run", "conditions", "output", "inputs", "reports", "connection_overrides"
    )
    # New defaults in Sonata config (not applicable to BlueConfig)
    _defaults = {
        "network": "circuit_config.json",
    }
    _path_entries_without_suffix = (
        "network",
    )

    def __init__(self, config_path):
        self._config_dir = os.path.abspath(os.path.dirname(config_path))
        self._sim_conf = libsonata.SimulationConfig.from_file(config_path)
        self._entries = {}
        self._sections = {}

        with open(config_path) as config_fh:
            self._config_json: dict = json.load(config_fh)
        self._resolved_manifest = self._build_resolver(
            self._config_json.get("manifest") or {},
            self._config_dir
        )
        for entry_name in self._config_entries:
            value = getattr(self._sim_conf, entry_name)
            self._entries[entry_name] = value
        for section_name in self._config_sections:
            section_value = self._config_json.get(section_name, {})
            self._sections[section_name] = self._resolve_section(section_value,
                                                                 self._resolved_manifest)

        self.circuits = libsonata.CircuitConfig.from_file(self.network)
        self._circuit_networks = json.loads(self.circuits.expanded_json)["networks"]

    @classmethod
    def _resolve(cls, entry, name, manifest: dict):
        if not isinstance(entry, str):
            return entry  # ints, floats... no need to resolve
        if not name.lower().endswith(("_file", "_dir")) \
                and name.lower() not in cls._path_entries_without_suffix:
            return entry  # not a path
        slash_p = entry.find("/")
        if slash_p == 0:  # abs path
            return entry
        if not entry.startswith("$"):
            return os.path.normpath(os.path.join(manifest["$__CONFIG_DIR"], entry))
        # Handle variable substitution
        if slash_p > -1:
            var_name = entry[: slash_p]
            remaining = entry[slash_p:]
        else:
            var_name = entry  # just alias
            remaining = ""
        if var_name not in manifest:
            raise Exception("Cant decode path entry {}. Unknown var {}"
                            .format(entry, var_name))
        return os.path.normpath(manifest[var_name] + remaining)

    @classmethod
    def _build_resolver(cls, manifest, config_dir):
        resolved = {"$__CONFIG_DIR": config_dir}  # special entry to resolve rel paths
        for key, value in manifest.items():
            resolved[key] = cls._resolve(value, key, resolved)
        return resolved

    @classmethod
    def _resolve_section(cls, section, manifest):
        return {key: cls._resolve(val, key, manifest) for key, val in section.items()}

    _translation = {
        # Section Names
        # -------------
        "Run": "run",
        "Conditions": "conditions",
        "Projection": None,
        "StimulusInject": "inputs",
        "Connection": "connection_overrides",
        "parsedConfigures": False,

        # Section fields
        # --------------
        "run": {
            # Mandatory
            "tstop": "Duration",
            "dt": "Dt",
            "random_seed": "BaseSeed",
            # Optional
            "tstart": "Start",
            "spike_threshold": "SpikeThreshold",
            "spike_location": "SpikeLocation",
            "integration_method": "SecondOrder"
        },
        "conditions": {
            "randomize_gaba_rise_time": "randomize_Gaba_risetime",
            "synapses_init_depleted": "SYNAPSES__init_depleted"
        },
        "projection": {
        },
        "connection_overrides": {
            "target": "Destination",
            "modoverride": "ModOverride",
            "synapse_delay_override": "SynDelayOverride",
            "neuromodulation_dtc": "NeuromodDtc",
            "neuromodulation_strength": "NeuromodStrength"
        },
        "inputs": {
            "module": "Pattern",
            "input_type": "Mode",
            "random_seed": "Seed",
            "series_resistance": "RS",
            "node_set": "Target",  # for StimulusInject
            "source": "Source",  # for StimulusInject
            "sd_percent": "SDPercent"

        },
        "reports": {
            "type": "Type",
            "cells": "Target",
            "sections": "Sections",
            "scaling": "Scaling",
            "compartments": "Compartments",
            "variable_name": "ReportOn",
            "unit": "Unit",
            "dt": "Dt",
            "start_time": "StartTime",
            "end_time": "EndTime",
            "file_name": "FileName",
            "enabled": "Enabled"
        },
        "modifications": {
            "node_set": "Target"
        }
    }

    @property
    def parsedRun(self):
        parsed_run = self._translate_dict("run", self._sim_conf.run)
        self._adapt_libsonata_fields(parsed_run)
        parsed_run["CircuitPath"] = "<NONE>"  # Sonata doesnt have default circuit
        # "OutputRoot" and "SpikesFile" will be read from self._sim_conf.output
        # once libsonata resolves the manifest info
        parsed_run["OutputRoot"] = self._sim_conf.output.output_dir
        parsed_run["TargetFile"] = self.circuits.node_sets_path
        parsed_run["SpikesFile"] = self._sim_conf.output.spikes_file
        parsed_run["SpikesSortOrder"] = self._sim_conf.output.spikes_sort_order.name
        parsed_run["Simulator"] = self._sim_conf.target_simulator.name
        parsed_run["TargetFile"] = self._sim_conf.node_sets_file
        parsed_run["CircuitTarget"] = self._sim_conf.node_set
        conditions = self._sections.get("conditions")
        if conditions:
            parsed_run["Celsius"] = self._sim_conf.conditions.celsius
            parsed_run["V_Init"] = self._sim_conf.conditions.v_init
            parsed_run["ExtracellularCalcium"] = self._sim_conf.conditions.extracellular_calcium
        return parsed_run

    @property
    def Conditions(self):
        conditions = {}
        blacklist = (
            "Celsius",
            "VInit",
            "ExtracellularCalcium",
            "ListModificationNames",
            "SpikeLocation",
        )
        for key, value in self._translate_dict("conditions", self._sim_conf.conditions).items():
            if key in blacklist:
                continue
            if key == "Mechanisms":
                for suffix, dict_var in value.items():
                    for name, val in dict_var.items():
                        conditions[name+"_"+suffix] = val
            else:
                conditions[key] = value
        conditions["randomize_Gaba_risetime"] = str(conditions["randomize_Gaba_risetime"])
        return {"Conditions": conditions}

    @property
    def Circuit(self):
        node_info_to_circuit = {
            "nodes_file": "CellLibraryFile",
            "type": "PopulationType"
        }

        if "node_set" not in self._entries:
            logging.warning("Simulating all populations from all node files...")
        network = self._circuit_networks

        def make_circuit(nodes_file, node_pop_name, population_info):
            if not os.path.isabs(nodes_file):
                nodes_file = os.path.join(os.path.dirname(self.network), nodes_file)
            circuit_conf = dict(
                CircuitPath=os.path.dirname(nodes_file) or "",
                CellLibraryFile=nodes_file,
                # Use the extended ":" syntax to filter the nodeset by the related population
                CircuitTarget=node_pop_name + ":" + (self._entries.get("node_set") or ""),
                **{
                    node_info_to_circuit.get(key, key): value
                    for key, value in population_info.items()
                }
            )
            node_prop = self.circuits.node_population_properties(node_pop_name)
            circuit_conf["MorphologyPath"] = node_prop.morphologies_dir
            circuit_conf["MorphologyType"] = "h5" if node_prop.type == "astrocyte" else "swc"
            circuit_conf["METypePath"] = node_prop.biophysical_neuron_models_dir
            if node_prop.alternate_morphology_formats:
                if "neurolucida-asc" in node_prop.alternate_morphology_formats:
                    circuit_conf["MorphologyPath"] = \
                        node_prop.alternate_morphology_formats["neurolucida-asc"]
                    circuit_conf["MorphologyType"] = "asc"
                elif "h5v1" in node_prop.alternate_morphology_formats:
                    circuit_conf["MorphologyPath"] = node_prop.alternate_morphology_formats["h5v1"]
                    circuit_conf["MorphologyType"] = "h5"
            circuit_conf["Engine"] = "NGV" if node_prop.type == "astrocyte" else "METype"

            # find inner connectivity
            for edge_config in network.get("edges") or []:
                for edge_pop_name in edge_config["populations"].keys():
                    edge_storage = self.circuits.edge_population(edge_pop_name)
                    edge_type = self.circuits.edge_population_properties(edge_pop_name).type
                    if edge_storage.source == edge_storage.target == node_pop_name and \
                            edge_type == "chemical":
                        edges_file = edge_config["edges_file"]
                        if not os.path.isabs(edges_file):
                            edges_file = os.path.join(os.path.dirname(self.network), edges_file)
                        circuit_conf["nrnPath"] = edges_file + ":" + edge_pop_name
            return circuit_conf

        return {
            pop_name: make_circuit(node_file_info["nodes_file"], pop_name, pop_info)
            for node_file_info in network["nodes"]
            for pop_name, pop_info in node_file_info["populations"].items()
            if pop_info.get("type") != "vasculature"
        }

    @property
    def parsedProjections(self):
        projection_type_convert = dict(
            chemical="Synaptic",
            electrical="GapJunction",
            synapse_astrocyte="NeuroGlial",
            endfoot="GlioVascular"
        )
        projections = {}

        for edge_config in self._circuit_networks.get("edges") or []:
            for population_name, edge_pop_config in edge_config["populations"].items():
                edge_pop = self.circuits.edge_population(population_name)
                pop_type = edge_pop_config.get("type", "chemical")
                # skip unhandled synapse type or inner connectivity
                if pop_type not in projection_type_convert or \
                        (edge_pop.source == edge_pop.target and pop_type == "chemical"):
                    logging.warning("Unhandled synapse type: " + pop_type)
                    continue
                edges_file = edge_config["edges_file"]
                if not os.path.isabs(edges_file):
                    edges_file = os.path.join(os.path.dirname(self.network), edges_file)
                # projection
                projection = dict(
                    Path=edges_file + ":" + population_name,
                    Source=edge_pop.source + ":",
                    Destination=edge_pop.target + ":",
                    Type=projection_type_convert.get(pop_type)
                )
                # Reverse projection direction for Astrocyte projection: from neurons to astrocytes
                if projection.get("Type") == "NeuroGlial":
                    projection["Source"], projection["Destination"] = projection["Destination"], \
                        projection["Source"]
                projections["{0.source}-{0.target}".format(edge_pop)] = projection
        return projections

    @property
    def parsedElectrodes(self):
        return None  # No electrodes in Sonata config

    @property
    def parsedConnects(self):
        connections = {}
        for conn_name in self._sections.get("connection_overrides").keys():
            connect = self._translate_dict("connection_overrides",
                                           self._sim_conf.connection_override(conn_name))
            connections[conn_name] = connect
        return connections

    @property
    def parsedStimuli(self):
        _input_type_translation = {
            "spikes": "Current",
            "current_clamp": "Current",
            "voltage_clamp": "Voltage",
            "extracellular_stimulation": "Extracellular",
            "conductance": "Conductance"
        }

        stimuli = {}
        for name in self._sections["inputs"].keys():
            stimulus = self._translate_dict("inputs", self._sim_conf.input(name))
            self._adapt_libsonata_fields(stimulus)
            stimulus["Pattern"] = "SEClamp" if stimulus["Pattern"] == "seclamp" \
                else snake_to_camel(stimulus["Pattern"])
            stimulus["Mode"] = _input_type_translation.get(stimulus["Mode"], stimulus["Mode"])
            stimuli[name] = stimulus
        return stimuli

    @property
    def parsedInjects(self):
        injects = {}
        for name in self._sections["inputs"].keys():
            inj = self._translate_dict("inputs", self._sim_conf.input(name))
            inj.setdefault("Stimulus", name)
            injects["inject"+name] = inj
        return injects

    @property
    def parsedReports(self):
        _report_type_translation = {
            "summation": "Summation",
            "synapse": "Synapse"
        }
        reports = {}
        for name in self._sections["reports"].keys():
            rep = self._translate_dict("reports", self._sim_conf.report(name))
            # Adapt enums and variable names read from libsonata
            self._adapt_libsonata_fields(rep)
            # Format is SONATA with sonata_config
            rep["Format"] = "SONATA"
            rep["Type"] = _report_type_translation.get(rep["Type"], rep["Type"])
            reports[name] = rep
        return reports

    @property
    def parsedModifications(self):
        modifications = {}
        for name in self._sim_conf.conditions.list_modification_names:
            setting = self._translate_dict("modifications",
                                           self._sim_conf.conditions.modification(name))
            self._adapt_libsonata_fields(setting)
            modifications[name] = setting
        return modifications

    def _dir(self, obj):
        return [x for x in dir(obj) if not x.startswith('__') and not callable(getattr(obj, x))]

    def _adapt_libsonata_fields(self, rep):
        for key in rep:
            # Convert enums to its string representation
            if key in ("Type", "Sections", "Scaling", "Compartments", "Mode", "Pattern",
                       "SpikeLocation"):
                if not isinstance(rep[key], str):
                    rep[key] = rep[key].name
            # Convert comma separated variable names to space separated
            if key == "ReportOn":
                rep[key] = rep[key].replace(",", " ")
            # Get the int value of the enum
            elif key == "SecondOrder":
                rep[key] = int(rep[key])

    def _translate_dict(self, section_name, libsonata_obj=None) -> dict:
        item_translation = self._translation[section_name]
        result = {}
        for att in self._dir(libsonata_obj):
            key = item_translation.get(att, snake_to_camel(att))
            parsed_value = getattr(libsonata_obj, att)
            if parsed_value is not None:
                result[key] = parsed_value
        return result

    def __getattr__(self, item):
        # Immediately return native items
        if item in self._config_entries:
            return self._entries.get(item, None)
        if item in self._config_sections:
            return self._sections.get(item, {})
        # Otherwise attempt translation
        item_tr = self._translation.get(item)
        if item_tr is None:
            logging.warning("Non-native Property needs conversion: " + item)
            return {}
        return self._entries.get(item_tr) or self._sections.get(item_tr) or {}


def snake_to_camel(word):
    return ''.join(x.capitalize() or '_' for x in word.split('_'))
