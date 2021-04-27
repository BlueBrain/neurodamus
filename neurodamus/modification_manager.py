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

from .core import NeurodamusCore as Nd
from .core.configuration import ConfigurationError


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
        target = self._target_manager.get_target(target_spec.name)
        cell_manager = self._target_manager.hoc.cellDistributor
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
        if target.isCellTarget():  # get all compartments for each cell
            tpoints = self.compartment_cast(target, "").getPointList(cell_manager)
        else:  # use compartments present in target
            tpoints = target.getPointList(cell_manager)

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
