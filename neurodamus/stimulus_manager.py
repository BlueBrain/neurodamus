# https://bbpteam.epfl.ch/project/spaces/display/BGLIB/Neurodamus
# Copyright 2005-2021 Blue Brain Project, EPFL. All rights reserved.
"""
    Implements coupling artificial stimulus into simulation

    New Stimulus classes must be registered, using the appropriate decorator.
    Also, when instantiated by the framework, __init__ is passed three arguments
    (1) target (2) stim_info: dict (3) cell_manager. Example

    >>> @StimulusManager.register_type
    >>> class ShotNoise:
    >>>
    >>> def __init__(self, target, stim_info: dict, cell_manager):
    >>>     tpoints = target.getPointList(cell_manager)
    >>>     for point in tpoints:
    >>>         gid = point.gid
    >>>         cell = cell_manager.getMEType(gid)

"""

import logging
from .core import NeurodamusCore as Nd
from .utils.logging import log_verbose


class StimulusManager:

    """
    A manager for synaptic artificial Stimulus.
    Old stimulus resort to hoc implementation
    """

    _stim_types = {}  # stimulus handled in Python

    def __init__(self, target_manager, elec_manager=None, *args):
        self._hoc = Nd.StimulusManager(target_manager.hoc, elec_manager, *args)
        self._target_manager = target_manager
        self._stimulus = []

    def interpret(self, target_spec, stim_info):
        stim_t = self._stim_types.get(stim_info["Pattern"])
        if stim_t:  # New style Stim, in Python
            log_verbose("Using new-gen stimulus")
            target = self._target_manager.get_target(target_spec.name)
            cell_manager = self._target_manager.hoc.cellDistributor
            stim = stim_t(target, stim_info, cell_manager)
            self._stimulus.append(stim)
        else:
            # Fallback to hoc stim manager
            self._hoc.interpret(target_spec.name, stim_info.hoc_map)

    def interpret_extracellulars(self, injects, stimuli):
        """Hoc only implementation for extra-cellulars"""
        self._hoc.interpretExtracellulars(injects.hoc_map, stimuli.hoc_map)

    def __getattr__(self, item):
        logging.debug("Pass unknown method request to Hoc")
        return getattr(self._hoc, item)

    @classmethod
    def register_type(cls, stim_class):
        """ Registers a new class as a handler for a new stim type """
        cls._stim_types[stim_class.__name__] = stim_class
        return stim_class
