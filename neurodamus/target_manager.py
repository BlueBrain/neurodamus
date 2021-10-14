import itertools
import logging
import os.path
from abc import abstractmethod
from functools import lru_cache
from typing import List

import numpy

from .core import MPI, NeurodamusCore as Nd
from .core.configuration import ConfigurationError, GlobalConfig, find_input_file
from .core.nodeset import NodeSet


class TargetError(Exception):
    """A Exception class specific to data error with targets and nodesets"""


class TargetSpec:
    """Definition of a new-style target, accounting for multipopulation"""

    def __init__(self, target_name):
        """Initialize a target specification

        Args:
            target_name: the target name. For specifying a population use
                the format ``population:target_name``
        """
        if target_name and ":" in target_name:
            self.population, self.name = target_name.split(":")
        else:
            self.name = target_name
            self.population = None
        if self.name == "":
            self.name = None

    def __str__(self):
        return (
            self.name
            if self.population is None
            else "{}:{}".format(self.population, self.name or "")
        )

    @property
    def simple_name(self):
        if self.name is None:
            return "_ALL_"
        return self.__str__().replace(":", "_")

    @property
    def is_full(self):
        return (self.name or "Mosaic") == "Mosaic"

    def matches(self, pop, target_name):
        """Check if it matches a given target. Mosaic and (empty) are equivalent"""
        return pop == self.population and (target_name or "Mosaic") == (self.name or "Mosaic")

    def match_filter(self, pop, target_name):
        return self.population == pop and (target_name or "Mosaic") in ("Mosaic", self.name)

    def __eq__(self, other):
        return self.matches(other.population, other.name)


class TargetManager:

    def __init__(self, run_conf):
        self._run_conf = run_conf
        self.parser = Nd.TargetParser()
        self._has_hoc_targets = False
        self.hoc = None  # The hoc level target manager
        self._targets = {}
        self._nodeset_reader = self._init_nodesets(run_conf)
        if MPI.rank == 0:
            self.parser.isVerbose = 1

    @classmethod
    def _init_nodesets(cls, run_conf):
        nodesets_file = run_conf.get("node_sets_file")
        if not nodesets_file and "TargetFile" in run_conf:
            target_file = run_conf["TargetFile"]
            if target_file.endswith(".json"):
                nodesets_file = target_file
        return nodesets_file and NodeSetReader(nodesets_file)

    def load_targets(self, circuit):
        """Provided that the circuit location is known and whether a user.target file has been
        specified, load any target files via a TargetParser.
        Note that these will be moved into a TargetManager after the cells have been distributed,
        instantiated, and potentially split.
        """
        if circuit.CircuitPath:
            self._try_open_start_target(circuit.CircuitPath)

        target_file = circuit.get("TargetFile")
        if target_file and not target_file.endswith(".json"):
            self.load_user_target(target_file)

        nodes_file = circuit.get("CellLibraryFile")
        if nodes_file and nodes_file.endswith(".h5") and self._nodeset_reader:
            self._nodeset_reader.register_node_file(nodes_file)

    def _try_open_start_target(self, circuit_path):
        start_target_file = os.path.join(circuit_path, "start.target")
        if not os.path.isfile(start_target_file):
            logging.warning("start.target not available! Check circuit.")
        else:
            self.parser.open(start_target_file, False)
            self._has_hoc_targets = True

    def load_user_target(self, target_file):
        # Old target files. Notice new targets with same should not happen
        user_target = find_input_file(target_file)
        self.parser.open(user_target, True)
        self._has_hoc_targets = True
        if MPI.rank == 0:
            logging.info(" => Loaded %d targets", self.parser.targetList.count())
            if GlobalConfig.verbosity >= 3:
                self.parser.printCellCounts()

    def register_target(self, target):
        self._targets[target.name] = target

    def get_target(self, target_spec: TargetSpec):
        if not isinstance(target_spec, TargetSpec):
            target_spec = TargetSpec(target_spec)
        target_name = target_spec.name
        simplename = target_spec.simple_name
        if simplename in self._targets:
            return self._targets[simplename]

        target = self._nodeset_reader and self._nodeset_reader.get_target(target_spec)
        if target is not None:
            logging.info("Retrieved gids from Sonata nodeset. Targets are Cell only")
        elif self._has_hoc_targets:
            if self.hoc is not None:
                hoc_target = self.hoc.getTarget(target_name)
            else:
                hoc_target = self.parser.getTarget(target_name)
            target = _HocTarget(target_name, target_spec.population, hoc_target)
        else:
            raise ConfigurationError(
                "Target {} can't be loaded. Check target sources".format(target_name)
            )
        self._targets[simplename] = target
        return target

    def init_hoc_manager(self, cell_manager):
        # give a TargetManager the TargetParser's completed targetList
        self.hoc = Nd.TargetManager(self.parser.targetList, cell_manager)

    def generate_subtargets(self, target_name, n_parts):
        """To facilitate CoreNeuron data generation, we allow users to use ModelBuildingSteps to
        indicate that the CircuitTarget should be split among multiple, smaller targets that will
        be built step by step.

        Returns:
            list with generated targets, or empty if no splitting was done
        """
        if not n_parts or n_parts == 1:
            return False

        target = self.parser.getTarget(target_name)
        allgids = target.completegids()
        new_targets = []

        for cycle_i in range(n_parts):
            target = Nd.Target()
            target.name = "{}_{}".format(target_name, cycle_i)
            new_targets.append(target)
            self.parser.updateTargetList(target)

        target_looper = itertools.cycle(new_targets)
        for gid in allgids.x:
            target = next(target_looper)
            target.gidMembers.append(gid)

        return new_targets

    def get_target_points(self, target, cell_manager, cell_use_compartment_cast=True):
        """Helper to retrieve the points of a target.
        If target is a cell then uses compartmentCast to obtain its points.
        Otherwise returns the result of calling getPointList directly on the target.

        Args:
            target: The target name or object (faster)
            manager: The cell manager to access gids and metype infos
            cell_use_compartment_cast: if enabled (default) will use target_manager.compartmentCast
                to get the point list.

        Returns: The target list of points
        """
        if isinstance(target, str):
            target = self.get_target(target)
        if target.isCellTarget() and cell_use_compartment_cast:
            target = self.hoc.compartmentCast(target, "")
        return target.getPointList(cell_manager)

    @lru_cache()
    def intersecting(self, target1, target2):
        """Checks whether two targets intersect"""
        target1_spec = TargetSpec(target1)
        target2_spec = TargetSpec(target2)
        if target1_spec.population != target2_spec.population:
            return False
        if (
            target1_spec.is_full
            or target2_spec.is_full
            or target1_spec.name == target2_spec.name
        ):
            return True
        # From this point, both are sub targets (and not the same)
        cells1 = self.get_target(target1_spec).get_gids()
        cells2 = self.get_target(target2_spec).get_gids()
        return not set(cells1).isdisjoint(cells2)

    def pathways_overlap(self, conn1, conn2, equal_only=False):
        src1, dst1 = conn1["Source"], conn1["Destination"]
        src2, dst2 = conn2["Source"], conn2["Destination"]
        if equal_only:
            return TargetSpec(src1) == TargetSpec(src2) and TargetSpec(dst1) == TargetSpec(dst2)
        return self.intersecting(src1, src2) and self.intersecting(dst1, dst2)


class NodeSetReader:
    """
    Implements reading Sonata Nodesets
    """

    def __init__(self, nodeset_file):
        import libsonata
        self.nodesets = libsonata.NodeSets.from_file(nodeset_file)
        self._population_stores = {}

    def register_node_file(self, node_file):
        import libsonata
        storage = libsonata.NodeStorage(node_file)
        for pop_name in storage.population_names:
            self._population_stores[pop_name] = storage

    def __contains__(self, nodeset_name):
        return nodeset_name in self.nodesets.names

    @property
    def names(self):
        return self.nodesets.names

    def get_target(self, target_spec: TargetSpec):
        """Build node sets capable of offsetting.
        The empty population has a special meaning in Sonata, it matches
        all populations in simulation
        """
        nodeset_name = target_spec.name
        pop_name = target_spec.population
        if nodeset_name not in self.nodesets.names:
            return None
        if pop_name and pop_name not in self._population_stores:
            raise TargetError("No loaded node file contains population " + pop_name)

        def _get_nodeset(pop_name):
            storage = self._population_stores.get(pop_name)
            population = storage.open_population(pop_name)
            ns = NodeSet(self.nodesets.materialize(nodeset_name, population).flatten())
            ns.register_global(pop_name)
            return ns

        nodesets = [_get_nodeset(pop_name) for pop_name in self._population_stores]
        return NodesetTarget(target_spec.simple_name, nodesets)


class _TargetInterface:
    """
    Methods that target/target wrappers should implement
    """

    def __len__(self):
        return self.gid_count()

    @abstractmethod
    def gid_count(self):
        return NotImplemented

    @abstractmethod
    def get_gids(self):
        return NotImplemented

    @abstractmethod
    def get_hoc_target(self):
        return NotImplemented


class NodesetTarget(_TargetInterface):
    def __init__(self, name, nodesets: List[NodeSet]):
        self.name = name
        self.nodesets = nodesets

    def gid_count(self):
        return sum(len(ns) for ns in self.nodesets)

    def get_gids(self):
        if not self.nodesets:
            logging.warning("Nodeset '%s' can't be materialized. No node populations", self.name)
            return []
        gids = self.nodesets[0].final_gids()
        for extra_nodes in self.nodesets[1:]:
            gids.extend(extra_nodes.final_gids())
        return numpy.array(gids)

    @lru_cache()
    def get_hoc_target(self):
        gids = self.get_gids()
        target = Nd.Target(self.name)
        target.gidMembers.append(Nd.Vector(gids))
        return target

    # compat w Hoc

    def getCellCount(self):
        return self.gid_count()

    def completegids(self):
        return self.get_gids()

    def isCellTarget(self):
        return True

    def __getattr__(self, item):
        return getattr(self.get_hoc_target(), item)


class _HocTarget(_TargetInterface):
    """
    A wrapper around Hoc targets to match interface
    """

    def __init__(self, name, default_population, hoc_target):
        self.name = name
        self.default_population = default_population
        self.hoc_target = hoc_target

    def __len__(self):
        return self.gid_count()

    def gid_count(self):
        return self.hoc_target.getCellCount()

    def get_gids(self):
        return self.hoc_target.completegids().as_numpy().astype("uint32")

    def get_hoc_target(self):
        return self.hoc_target

    def __getattr__(self, item):
        return getattr(self.hoc_target, item)
