"""
Definitions for implementing new Engines to handle different cell types
"""

import logging
import importlib
import pkgutil
import os


class _EngineMeta(type):
    """A metaclass providing registration for new Engines
    """
    __engines = dict()
    __instances = dict()

    def __init__(cls, name, bases, attrs):
        type.__init__(cls, name, bases, attrs)
        ename = name.replace("Engine", "")
        logging.info(" * Registering Engine %s (%s.%s)", ename, cls.__module__, name)
        cls.__engines.setdefault(ename, cls)

    @property
    def engines(cls):
        return cls.__engines.keys()

    def get(cls, name):
        """Each engine is a singleton"""
        if name is None:
            return True  # Not setting means use default
        if name in cls.__instances:
            return cls.__instances[name]
        if name in cls.__engines:
            logging.info("Instantiating Neurodamus Engine: %s", name)
            obj = cls.__instances[name] = cls.__engines[name]()
            return obj
        raise RuntimeError("Engine could not be found: " + name)

    def find_plugins(cls):
        # Find/register plugins
        plugin_module = os.environ.get("NEURODAMUS_PLUGIN")
        if plugin_module:
            importlib.import_module(plugin_module)
        # Auto import correctly named modules
        for finder, name, ispkg in pkgutil.iter_modules():
            if name.startswith('neurodamus_'):
                importlib.import_module(name)
        logging.info(" => Engines Available: %s", list(cls.engines))


class EngineBase(metaclass=_EngineMeta):
    """A base class to define an engine.

    Engines are the fundamental blocks to handle different kinds of cells, like
    Glia or Point-Neurons, in a plugin-like interface.
    Engines must either implement their own create_cells and create_synapses
    methods (for full flexibility) or specify which are the Manager classes.

    Specifying the Manager classes is suitable for most cases.
    Without any customization an engine will default to use
      CellManagerCls = None   # Use existing instance of CellDistributor
      SynapseManagerCls = None  # Use existing instance of SynapseRuleManager

    Such setup is equivalent to not specifying the Engine for a given circuit,
    effectively handling additional circuits by the built-in Engine.
    Specifying CellManagerCls will instantiate cells with the new Engine. If a
    SynapseManagerCls is not provided then only cell creation happens.
    Specifying SynapseManagerCls alone is not supported.

    """

    CellManagerCls = None
    SynapseManagerCls = None

    def __init__(self):
        # For each engine a single cell manager and single synapse_manager exist
        # this makes possible to read several circuits of the same kind and
        # instantiate cells/connections in one go, per engine
        # They are lazily instantiated as Engines have full freedom to override the
        # methods below
        self._cell_manager = None
        self._synapse_manager = None

    cell_manager = property(lambda self: self._cell_manager)
    synapse_manager = property(lambda self: self._synapse_manager)

    def create_cells(self, circuit_conf, base_cell_manager, target_parser, *_):
        """Routine responsible for creating cells

        If not overridden, it will ensure a cell_manager exists and call
        load_cells() and finalize() on it.
        """
        if not self.CellManagerCls:
            return NotImplemented
        if not self._cell_manager:
            self._cell_manager = self.CellManagerCls(base_cell_manager.pnm,
                                                     target_parser,
                                                     base_cell_manager)
        self._cell_manager.load_cells(circuit_conf)

    def finalize_cells(self):
        self._cell_manager.finalize()

    def create_synapses(self, circuit_conf, target_manager, base_manager):
        """Routine responsible for creating synapses.

        If the user doesnt override it will, by default, attempt to create a
        SynapseManagerCls instance and return it. Node uses it to instantiate
        connections with the same routine it uses for the built-in SynapseManager.

        Returns: None in case no further actions should be taken, NotImplemented
        if the system SynapseManager should be used, or an instance of SynapseManager
        for a default instantiation over the custom container
        """
        if self.CellManagerCls is None:
            if self.SynapseManagerCls is None:
                return NotImplemented
            else:
                raise RuntimeError("Circuit Not Initialized. Please create_cells() first")
        if self.SynapseManagerCls is None:
            return None

        if not self._synapse_manager:
            self._synapse_manager = self.SynapseManagerCls(circuit_conf, target_manager,
                                                           self._cell_manager,
                                                           base_manager=base_manager)

        return self._synapse_manager

    def finalize_synapses(self):
        self._synapse_manager.finalize()
