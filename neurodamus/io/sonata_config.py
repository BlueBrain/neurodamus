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
        '_circuit_networks'
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
        self._entries = {}
        self._sections = {}

        with open(config_path) as config_fh:
            self._config_json: dict = json.load(config_fh)
        self._resolved_manifest = self._build_resolver(
            self._config_json.get("manifest") or {},
            self._config_dir
        )
        for entry_name in self._config_entries:
            value = self._config_json.get(entry_name, self._defaults.get(entry_name))
            self._entries[entry_name] = value and \
                self._resolve(value, entry_name, self._resolved_manifest)
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
        "parsedModifications": False,

        # Section fields
        # --------------
        "run": {
            # Mandatory
            "tstop": "Duration",
            "tstart": "Start",
            "dt": "Dt",
            "seed": "BaseSeed",
            # Optional
            "spike_threshold": "SpikeThreshold",
            "spike_location": "SpikeLocation",
            "integration_method": "SecondOrder",
            "forward_skip": "ForwardSkip",
        },
        "conditions": {
        },
        "projection": {
        },
        "connection_overrides": {
            "target": "Destination"
        },
        "inputs": {
            "module": "Pattern",
            "input_type": "Mode",
            "random_seed": "Seed",
            "node_set": "Target",  # for StimulusInject
            "type": "Type"
        },
        "reports": {
            "type": "Type",
            "cells": "Target",
            "variable_name": "ReportOn",
            "unit": "Unit",
            "dt": "Dt",
            "start_time": "StartTime",
            "end_time": "EndTime",
        }
    }

    @property
    def parsedRun(self):
        def copy_config_if_valid(value, dst, key):
            if value:
                dst[key] = value
        parsed_run = self._translate_dict(self._sections["run"], "run")
        parsed_run["CircuitPath"] = "<NONE>"  # Sonata doesnt have default circuit
        parsed_run["OutputRoot"] = self.output.get("output_dir", "output")
        copy_config_if_valid(self._entries.get("target_simulator"), parsed_run, "Simulator")
        copy_config_if_valid(self._entries.get("node_sets_file"), parsed_run, "TargetFile")
        copy_config_if_valid(self._entries.get("node_set"), parsed_run, "CircuitTarget")
        conditions = self._sections.get("conditions")
        if conditions:
            copy_config_if_valid(conditions.get("celsius"), parsed_run, "Celsius")
            copy_config_if_valid(conditions.get("v_init"), parsed_run, "V_Init")
            copy_config_if_valid(conditions.get("extracellular_calcium"), parsed_run,
                                 "ExtracellularCalcium")
        return parsed_run

    @property
    def Conditions(self):
        conditions = {}
        for k, v in self._sections["conditions"].items():
            if k not in ("celsius", "v_init", "extracellular_calcium"):
                conditions[k] = v
        return {"Conditions": conditions}

    @property
    def Circuit(self):
        node_info_to_circuit = {
            "nodes_file": "CellLibraryFile",
            "morphologies_dir": "MorphologyPath",
            "biophysical_neuron_models_dir": "METypePath",
            "type": "CellType"
        }

        if "node_set" not in self._entries:
            logging.warning("Simulating all populations from all node files...")
        network = self._circuit_networks

        def make_circuit(nodes_file, node_pop_name, population_info):
            circuit_conf = dict(
                CircuitPath=os.path.dirname(nodes_file) or "",
                CellLibraryFile=nodes_file,
                CircuitTarget=node_pop_name + ":" + (self._entries.get("node_set") or ""),
                MorphologyType="swc",
                **{
                    node_info_to_circuit.get(key, key): value
                    for key, value in population_info.items()
                }
            )
            if "alternate_morphologies" in population_info and \
                    "neurolucida-asc" in population_info["alternate_morphologies"]:
                circuit_conf["MorphologyPath"] = population_info["alternate_morphologies"]\
                    .get("neurolucida-asc")
                circuit_conf["MorphologyType"] = "asc"

            # find inner connectivity
            for edge_config in network["edges"]:
                for edge_pop_name in edge_config["populations"].keys():
                    edge_storage = self.circuits.edge_population(edge_pop_name)
                    if edge_storage.source == edge_storage.target == node_pop_name:
                        circuit_conf["nrnPath"] = edge_config["edges_file"] + ":" + edge_pop_name
            return circuit_conf

        return {
            pop_name: make_circuit(node_file_info["nodes_file"], pop_name, pop_info)
            for node_file_info in network["nodes"]
            for pop_name, pop_info in node_file_info["populations"].items()
        }

    @property
    def parsedProjections(self):
        projection_type_convert = dict(
            chemical="Synaptic",
            electrical="GapJunction",
        )
        projections = {}

        for edge_config in self._circuit_networks["edges"]:
            for population_name, edge_pop_config in edge_config["populations"].items():
                edge_pop = self.circuits.edge_population(population_name)
                if edge_pop.source == edge_pop.target:  # Inner connectivity
                    continue
                # projection
                pop_type = edge_pop_config.get("type", "chemical")
                projections["{0.source}-{0.target}".format(edge_pop)] = dict(
                    Path=edge_config["edges_file"] + ":" + population_name,
                    Source=edge_pop.source + ":",
                    Destination=edge_pop.target + ":",
                    Type=projection_type_convert.get(pop_type) or logging.warning(
                        "Unhandled synapse type: " + pop_type
                    )
                )
        return projections

    @property
    def parsedElectrodes(self):
        return None  # No electrodes in Sonata config

    @property
    def parsedConnects(self):
        connections = {}
        for conn_name, conn_dict in self._sections.get("connection_overrides").items():
            connect = self._translate_dict(conn_dict, "connection_overrides")
            connect = dict_change_keys_case(connect)
            connections[conn_name] = connect
        return connections

    @property
    def parsedStimuli(self):
        stimuli = {}
        for name, conf in self._sections["inputs"].items():
            stimulus = self._translate_dict(conf, "inputs")
            stimulus = dict_change_keys_case(stimulus)
            stimulus["Pattern"] = snake_to_camel(stimulus["Pattern"])
            stimuli[name] = stimulus
        return stimuli

    @property
    def parsedInjects(self):
        injects = {}
        for name, conf in self._sections["inputs"].items():
            inj = self._translate_dict(conf, "inputs")
            inj.setdefault("Stimulus", name)
            inj.setdefault("Source", "default:")
            injects["inject"+name] = inj
        return injects

    @property
    def parsedReports(self):
        reports = {}
        for name, conf in self._sections["reports"].items():
            rep = self._translate_dict(conf, "reports")
            # Some entries now have defaults. Introduce them here
            rep.setdefault("Type", "compartment")
            rep.setdefault("Format", "SONATA")
            rep.setdefault("Dt", self.run.get("dt"))
            rep.setdefault("StartTime", 0)
            rep.setdefault("Unit", "mV")
            rep.setdefault("Target", "_ALL_")
            reports[name] = rep
        return reports

    def _translate_dict(self, d, section_name) -> dict:
        item_translation = self._translation[section_name]
        return {item_translation.get(sonata_name, sonata_name): value
                for sonata_name, value in d.items()}

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


def dict_change_keys_case(d):
    return {snake_to_camel(k): v for k, v in d.items()}