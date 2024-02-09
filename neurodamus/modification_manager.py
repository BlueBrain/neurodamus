# https://bbpteam.epfl.ch/project/spaces/display/BGLIB/Neurodamus
# Copyright 2005-2021 Blue Brain Project, EPFL. All rights reserved.
"""
    Implements applying modifications that mimic experimental manipulations

    New Modification classes must be registered, using the appropriate decorator.
    Also, when instantiated by the framework, __init__ is passed three arguments
    (1) target (2) mod_info: dict (3) cell_manager. Example

    >>> @ModificationManager.register_type
    >>> class TTX:
    >>>
    >>> def __init__(self, target, mod_info: dict, cell_manager):
    >>>     tpoints = target.getPointList(cell_manager)
    >>>     for point in tpoints:
    >>>         for sec_id, sc in enumerate(point.sclst):
    >>>             if not sc.exists():
    >>>                 continue
    >>>             sec = sc.sec

"""

import ast
import logging
from .core import NeurodamusCore as Nd
from .core.configuration import ConfigurationError
from .utils.logging import log_verbose


class ModificationManager:

    """
    A manager for circuit Modifications.
    Overrides HOC manager, as the only Modification there (TTX) is outdated.
    """

    _mod_types = {}  # modification handled in Python

    def __init__(self, target_manager):
        self._target_manager = target_manager
        self._modifications = []

    def interpret(self, target_spec, mod_info):
        mod_t_name = mod_info["Type"]
        mod_t = self._mod_types.get(mod_t_name)
        if not mod_t:
            raise ConfigurationError("Unknown Modification {}".format(mod_t_name))
        target = self._target_manager.get_target(target_spec)
        cell_manager = self._target_manager._cell_manager
        mod = mod_t(target, mod_info, cell_manager)
        self._modifications.append(mod)

    @classmethod
    def register_type(cls, mod_class):
        """ Registers a new class as a handler for a new modification type """
        cls._mod_types[mod_class.__name__] = mod_class
        return mod_class


@ModificationManager.register_type
class TTX:
    """
    Applies sodium channel block to all sections of the cells in the given target

    Uses TTXDynamicsSwitch as in BGLibPy. Overrides HOC version, which is outdated
    """
    def __init__(self, target, mod_info: dict, cell_manager):
        tpoints = target.getPointList(cell_manager, sections='all')

        # insert and activate TTX mechanism in all sections of each cell in target
        for tpoint_list in tpoints:
            for sec_id, sc in enumerate(tpoint_list.sclst):
                if not sc.exists():  # skip sections not on this split
                    continue
                sec = sc.sec
                if not Nd.ismembrane("TTXDynamicsSwitch", sec=sec):
                    sec.insert("TTXDynamicsSwitch")
                sec.ttxo_level_TTXDynamicsSwitch = 1.0

    def compartment_cast(self, target, subset):
        if subset not in ("soma", "apic", "dend", ""):
            raise Exception("Unknown subset {} in compartment_cast".format(subset))

        wrapper = Nd.Target("temp", "Compartment")
        wrapper.subtargets.append(target)
        wrapper.targetSubsets.append(Nd.String(subset))
        wrapper.targetExtraValues.append(Nd.Vector())
        return wrapper


@ModificationManager.register_type
class ConfigureAllSections:
    """
    Perform one or more assignments involving section attributes,
    for all sections that have all the referenced attributes.

    Use case is modifying mechanism variables from config.
    """
    def __init__(self, target, mod_info: dict, cell_manager):
        config, config_attrs = self.parse_section_config(mod_info['SectionConfigure'])
        tpoints = target.getPointList(cell_manager, sections='all')

        napply = 0  # number of sections where config applies
        # change mechanism variable in all sections that have it
        for tpoint_list in tpoints:
            for _, sc in enumerate(tpoint_list.sclst):
                if not sc.exists():  # skip sections not on this split
                    continue
                sec = sc.sec
                if all(hasattr(sec, x) for x in config_attrs):  # if has all attributes
                    exec(config, {'__builtins__': None}, {'sec': sec})  # unsafe but sanitized
                    napply += 1

        log_verbose("Applied to {} sections".format(napply))

        if napply == 0:
            logging.warning("ConfigureAllSections applied to zero sections, "
                            "please check its SectionConfigure for possible mistakes")

    def compartment_cast(self, target, subset):
        if subset not in ("soma", "apic", "dend", ""):
            raise Exception("Unknown subset {} in compartment_cast".format(subset))

        wrapper = Nd.Target("temp", "Compartment")
        wrapper.subtargets.append(target)
        wrapper.targetSubsets.append(Nd.String(subset))
        wrapper.targetExtraValues.append(Nd.Vector())
        return wrapper

    def parse_section_config(self, config):
        config = config.replace('%s.', '__sec_wildcard__.')  # wildcard to placeholder
        all_attrs = self.AttributeCollector()
        tree = ast.parse(config)
        for elem in tree.body:  # for each semicolon-separated statement
            # check assignment targets
            for tgt in self.assignment_targets(elem):
                # must be single assignment of a __sec_wildcard__ attribute
                if not isinstance(tgt, ast.Attribute) or tgt.value.id != '__sec_wildcard__':
                    raise ConfigurationError("SectionConfigure only supports single assignments "
                                             "of attributes of the section wildcard %s")
            all_attrs.visit(elem)  # collect attributes in assignment
        config = config.replace('__sec_wildcard__.', 'sec.')  # placeholder to section variable

        return config, all_attrs.attrs

    class AttributeCollector(ast.NodeVisitor):
        """Node visitor collecting all attribute names in a set"""
        attrs = set()

        def visit_Attribute(self, node):
            self.attrs.add(node.attr)

    def assignment_targets(self, node):
        if isinstance(node, ast.Assign):
            return node.targets
        elif isinstance(node, ast.AugAssign):
            return [node.target]
        else:
            raise ConfigurationError("SectionConfigure must consist of one or more "
                                     "semicolon-separated assignments")
