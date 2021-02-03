"""
Implementation of Gid Sets with the ability of self offsetting and avoid
global overlapping
"""
import weakref
from ..utils import compat
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

    _global_populations = {}
    """The registered global gid sets. dict{population_name -> PopulationNodes}"""

    def __init__(self, name):
        """Ctor for a group of nodes belonging to the same population.
        It wont probably be used publicly given `get()` is also a factory.
        """
        self.name = name
        self.nodesets = []  # each population might contain several NodeSet's
        self.max_gid = 0  # maximum raw gid (without offset)
        self.offset = 0

    def _append(self, nodeset):
        on_obj_deleted = lambda ref: self.nodesets.remove(ref)
        self.nodesets.append(weakref.proxy(nodeset, on_obj_deleted))
        self._update(nodeset)
        return self

    def _update(self, updated_nodeset):
        updated_nodeset._offset = self.offset
        # compute new max and update offsets if needed
        local_max = max(self.max_gid, updated_nodeset._max_gid)
        max_gid = int(MPI.allreduce(local_max, MPI.MAX))
        if max_gid > self.max_gid:
            self.max_gid = max_gid
            self._update_offsets()

    @classmethod
    def register(cls, population, nodeset):
        return cls.get(population, create=True)._append(nodeset)

    @classmethod
    def reset(cls):
        cls._global_populations.clear()

    @classmethod
    def all(cls):
        return cls._global_populations.values()

    @classmethod
    def get(cls, population, *, create=False):
        obj = cls._global_populations.get(population)
        if not obj and create:
            # When a set is first added it's empty, no need to update other offsets
            obj = cls._global_populations[population] = cls(population)
            cls._global_populations = dict(sorted(cls._global_populations.items()))  # Reorder
            obj._compute_offset(cls._find_previous(obj))
        return obj

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
        for nodeset in self.nodesets:
            nodeset._offset = offset

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

    def register_global(self, population):
        self._population_group = PopulationNodes.register(population, self)
        return self

    def __len__(self):
        return len(self._gidvec)

    def raw_gids(self):
        return self._gidvec

    def final_gids(self):
        return compat.Vector("I", (gid + self._offset for gid in self._gidvec))

    def items(self, final_gid=False):
        offset_add = self._offset if final_gid else 0
        for gid in self._gidvec:
            yield gid + offset_add, self._gid_info.get(gid)

    def clear_cell_info(self):
        self._gid_info = None

    @classmethod
    def unregister_all(cls):
        PopulationNodes.reset()
