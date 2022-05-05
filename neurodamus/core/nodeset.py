"""
Implementation of Gid Sets with the ability of self offsetting and avoid
global overlapping
"""
import numpy
from ..utils import compat, WeakList
from . import MPI


class PopulationNodes:
    """
    Handle NodeSets belonging to a population. Given that Neuron doesnt
    inherently handle populations, we will have to apply gid offsetting.
    The class stores `NodeSet`s, and makes the required offsetting on-the-fly.

    This class is intended to be internal, since NodeSet instances can be
    freely created but only "apply" for offsetting when registered globally,
    in which case it delegates the processing to PopulationNodes.

    We store internal class-level _global_populations so that offsets are truly
    global, independently of the CellManager
    """

    _global_populations = []
    """Populations which may have offset"""
    _has_base_population = False
    """Select one population to be the first one, no offset"""
    _do_offsetting = True
    """False will freeze offsets to ensure final gids are consistent"""

    def __init__(self, name):
        """Ctor for a group of nodes belonging to the same population.
        It wont probably be used publicly given `get()` is also a factory.
        """
        self.name = name
        self.nodesets = WeakList()  # each population might contain several NodeSet's
        self.max_gid = 0  # maximum raw gid (without offset)
        self.offset = 0

    def _append(self, nodeset):
        self.nodesets.append(nodeset)
        self._update(nodeset)
        return self

    def _update(self, updated_nodeset):
        updated_nodeset._offset = self.offset
        if not self._do_offsetting:
            return
        local_max = max(self.max_gid, updated_nodeset._max_gid)
        max_gid = int(MPI.allreduce(local_max, MPI.MAX))
        if max_gid > self.max_gid:
            self.max_gid = max_gid
            self._update_offsets()

    @classmethod
    def register(cls, population, nodeset, **create_kw):
        return cls.get(population, create=True, **create_kw)._append(nodeset)

    @classmethod
    def freeze_offsets(cls):
        cls._do_offsetting = False

    @classmethod
    def reset(cls):
        cls._global_populations.clear()

    @classmethod
    def all(cls):
        return cls._global_populations

    @classmethod
    def get(cls, population_name, *, create=False, **create_kw):
        obj = next(filter(lambda x: x.name == population_name, cls._global_populations), None)
        if not obj and create:
            obj = cls.create_pop(population_name, **create_kw)
        return obj

    @classmethod
    def create_pop(cls, population_name, *, is_base_pop=False):
        new_population = cls(population_name)
        if is_base_pop:
            cls._global_populations.insert(0, new_population)
            cls._has_base_population = True
            return new_population

        # Otherwise insert at the end and do sorting
        cls._global_populations.append(new_population)
        base_pop, other_pops = [], cls._global_populations
        if cls._has_base_population:
            base_pop, other_pops = cls._global_populations[0:1], cls._global_populations[1:]
        cls._global_populations = base_pop + sorted(other_pops, key=lambda x: x.name)
        new_population._compute_offset(cls._find_previous(new_population))
        return new_population

    @classmethod
    def _find_previous(cls, cur_pop):
        prev_nodeset = None
        for obj in cls.all():
            if obj is cur_pop:
                return prev_nodeset
            prev_nodeset = obj
        return None

    def _compute_offset(self, prev_gidpop):
        offset = 0
        # This offset is gonna be the offset+max_gid of the previous population, round up
        if prev_gidpop is not None:
            cur_max = prev_gidpop.offset + prev_gidpop.max_gid
            # round up 1000's. GIDs are 1 based: Blocks [1-1000], [1001-2000]
            offset = ((cur_max - 1) // 1000 + 1) * 1000
        self.offset = offset
        # Update individual nodesets
        for nodeset in self.nodesets:  # nodeset is a weakref
            nodeset()._offset = offset

    def _update_offsets(self):
        """Update all global offsets after adding gids"""
        update = False
        prev_gidpop = None
        for gidpop in self.all():
            if gidpop is self:
                update = True
                prev_gidpop = gidpop
                continue
            if update:
                # We are in a subsequent nodeset - re-set offsetting
                gidpop._compute_offset(prev_gidpop)
            prev_gidpop = gidpop


class NodeSet:
    """A set of nodes. When registered globally offset computation happens
    so that different population's gids dont overlap
    """

    def __init__(self, gids=None, gid_info=None, **metadata):
        """Create a NodeSet.

        Args:
            gids: The gids to handle
            gid_info: a map containing METype information about each cell.
                In v5 and v6 values are METypeItem's

        """
        self._gidvec = compat.Vector("I")  # raw gids
        self._gid_info = {}
        self._max_gid = 0  # maximum raw gid (without offset)
        self._offset = 0
        self._metadata = metadata
        self._population_group = None  # register in a population so gids can be unique
        if gids is not None:
            self.add_gids(gids, gid_info)

    offset = property(lambda self: self._offset)
    max_gid = property(lambda self: self._max_gid)
    meta = property(lambda self: self._metadata)

    @property
    def population_name(self):
        return self._population_group.name if self._population_group else None

    def add_gids(self, gids, gid_info=None):
        """Add raw gids, recomputing gid offsets as needed"""
        self._gidvec.extend(gids)
        if len(gids) > 0:
            self._max_gid = max(self.max_gid, max(gids))
        if self._population_group:
            self._population_group._update(self)  # Note: triggers a reduce.
        if gid_info:
            self._gid_info.update(gid_info)
        return self

    def extend(self, other):
        return self.add_gids(other._gidvec, other._gid_info)

    def register_global(self, population_name, is_base_pop=False):
        """ Registers a node set as being part of a population, potentially implying an offsett

        Args:
            population_name: The name of the population these ids belong to
            is_base_population: In case we want this population the be the base, without offset
        """
        self._population_group = PopulationNodes.register(
            population_name, self, is_base_pop=is_base_pop
        )
        return self

    def __len__(self):
        return len(self._gidvec)

    def raw_gids(self):
        return self._gidvec

    def final_gids(self):
        # int64 auto-converts to double on addition
        return (numpy.asarray(self._gidvec) + self._offset).astype("uint32")

    def items(self, final_gid=False):
        offset_add = self._offset if final_gid else 0
        for gid in self._gidvec:
            yield gid + offset_add, self._gid_info.get(gid)

    def intersects(self, other):
        """Check if the current nodeset intersects another

        For nodesets to intersect they must belong to the same population and
        have common gids
        """
        if self.population_name != other.population_name:
            return False
        intersection = numpy.intersect1d(numpy.asarray(self._gidvec), numpy.asarray(other._gidvec))
        return len(intersection) > 0

    def clear_cell_info(self):
        self._gid_info = None

    @classmethod
    def unregister_all(cls):
        PopulationNodes.reset()
