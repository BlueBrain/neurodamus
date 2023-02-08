"""
Definitions for implementing new Engines to handle different cell types
"""

import importlib
import logging
import os
import pkgutil


class _EngineMeta(type):
    """A metaclass providing registration for new Engines
    """
    __engines = {}
    __connection_types = {}
    __instances = {}

    def __init__(cls, name, bases, attrs):
        type.__init__(cls, name, bases, attrs)
        ename = name.replace("Engine", "")
        logging.info(" * Registering Engine %s (%s.%s)", ename, cls.__module__, name)
        cls.__engines.setdefault(ename, cls)
        cls.__connection_types.update(cls.ConnectionTypes)

    @property
    def engines(cls):
        return cls.__engines.values()

    @property
    def connection_types(cls):
        return cls.__connection_types

    def get(cls, name):
        """Each engine is a singleton"""
        if name is None:
            return True  # Not setting means use default
        if name in cls.__engines:
            return cls.__engines[name]
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
        logging.info(" => Engines Available: %s", list(cls.__engines.keys()))
        logging.info("  : Connections Types: %s", list(cls.__connection_types.keys()))


class EngineBase(metaclass=_EngineMeta):
    """A base class to define an engine.

    Engines are the fundamental blocks to handle different kinds of cells, like
    Glia, in a plugin-like interface.
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
    InnerConnectivityCls = None
    ConnectionTypes = {}
    """A dict of the new connection types and associated Manager class"""
    CircuitPrecedence = 1
    """Precedence influences instantiation order. The lower the earlier setup"""

    @classmethod
    def new_cell_manager(cls, circuit_conf, target_parser, run_conf):
        if not cls.CellManagerCls:
            return NotImplemented
        return cls.CellManagerCls(circuit_conf, target_parser, run_conf)

    def new_synapse_manager(cls, circuit_conf, target_manager, cell_manager):
        """Routine responsible for creating connection managers.
        """
        if not cls.SynapseManagerCls:
            return NotImplemented
        if cell_manager is None:
            raise RuntimeError("Circuit Not Initialized. Please load_nodes() first")
        return cls.SynapseManagerCls(circuit_conf, target_manager, cell_manager)

    def report(report, target_parser, rep_target, corenrn_conf, cell_manager):
        """Create reports for this type of engine.
        """
        if cell_manager is None:
            raise RuntimeError("Circuit Not Initialized. Please load_nodes() first")
        return NotImplemented
