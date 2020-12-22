"""
Module to parse BlueConfigs
"""
import logging
from collections import defaultdict


class BlueConfigParserError(Exception):
    pass


class BlueConfig:
    _known_sections = (
        "Run", "Connection", "Projection", "Stimulus", "StimulusInject", "Report",
        "Electrode", "Modification", "NeuronConfigure", "Circuit", "Conditions",
    )

    def __init__(self, filename):
        self._sections = defaultdict(dict)
        with open(filename) as f:
            self._parse_top(f)
        if "Run" not in self._sections:
            raise BlueConfigParserError("Section 'Run' doesn't exist")
        self._sections['Run'] = self._sections['Run']['Default']

    def _parse_top(self, f):
        is_comment = False
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line[0] == '#':
                is_comment = True
                continue
            if line[0] == '{' and is_comment:
                logging.debug("Skipping BlueConfig section %s", line)
                self._skip_section(f)
                continue
            is_comment = False
            header_parts = line.split()
            if len(header_parts) != 2:
                raise BlueConfigParserError("Invalid section header: " + line)
            section = header_parts[0]
            section_data = self._parse_section(f)
            if isinstance(section_data, Exception):
                raise BlueConfigParserError(
                    "Invalid data in section '{}': {}".format(line, str(section_data)))
            self._sections[section][header_parts[1]] = section_data

    @staticmethod
    def _parse_section(file_iter):
        info = {}
        next(file_iter)  # skip {
        for line in file_iter:
            line = line.strip()
            if not line or line[0] == '#':
                continue
            if '#' in line:
                line = line[:line.index('#')].rstrip()
            if line == "}":
                break
            if line == "{":
                return BlueConfigParserError("Section not closed")
            parts = line.split(maxsplit=1)
            if len(parts) < 2:
                return BlueConfigParserError(line)
            try:
                value = float(parts[1])
            except ValueError:
                value = parts[1]
            info[parts[0]] = value
        return info

    @staticmethod
    def _skip_section(file_iter):
        for line in file_iter:
            line = line.strip(" \t#")
            if line.startswith("}"):
                break
            if line.startswith("{"):
                return BlueConfigParserError(line)

    def __getattr__(self, item):
        if item not in self._known_sections:
            raise KeyError("Config key not supported: " + item)
        return self._sections[item]  # defaultdict never excepts
