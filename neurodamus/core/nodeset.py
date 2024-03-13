"""
Implementation of Gid Sets with the ability of self offsetting and avoid
global overlapping
"""
from contextlib import contextmanager
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
        cls._do_offsetting = True

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

    @classmethod
    @contextmanager
    def offset_freezer(cls):
        cls._do_offsetting = False
        yield
        cls._do_offsetting = True


class _NodeSetBase:
    """
    Common bits between nodesets, so they can be registered globally and get offsets
    """

    def __init__(self, *_, **_kw):
        self._offset  = 0
        self._max_gid = 0  # maximum raw gid (without offset)
        self._population_group = None  # register in a population so gids can be unique

    offset = property(lambda self: self._offset)
    max_gid = property(lambda self: self._max_gid)

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

    @property
    def population_name(self):
        return self._population_group.name if self._population_group else None

    def _check_update_offsets(self):
        if self._population_group:
            self._population_group._update(self)  # Note: triggers a reduce.

    @classmethod
    def unregister_all(cls):
        PopulationNodes.reset()

    def __len__(self):
        return NotImplemented

    def raw_gids(self):
        return NotImplemented

    def final_gids(self):
        return numpy.add(self.raw_gids(), self._offset, dtype="uint32")

    def intersection(self, _other, _raw_gids=False):
        return NotImplemented

    def intersects(self, other):
        """Check if the current nodeset intersects another

        For nodesets to intersect they must belong to the same population and
        have common gids
        """
        return len(self.intersection(other)) > 0


class NodeSet(_NodeSetBase):
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
        super().__init__()
        self._gidvec = compat.Vector()  # raw gids
        self._gid_info = {}
        self._metadata = metadata
        if gids is not None:
            self.add_gids(gids, gid_info)

    meta = property(lambda self: self._metadata)

    def add_gids(self, gids, gid_info=None):
        """Add raw gids, recomputing gid offsets as needed"""
        self._gidvec.extend(gids)
        if len(gids) > 0:
            self._max_gid = max(self.max_gid, max(gids))
        if gid_info:
            self._gid_info.update(gid_info)
        self._check_update_offsets()  # check offsets (uses reduce)
        return self

    def extend(self, other):
        return self.add_gids(other._gidvec, other._gid_info)

    def __len__(self):
        return len(self._gidvec)

    def raw_gids(self):
        return numpy.asarray(self._gidvec, dtype="uint32")

    def items(self, final_gid=False):
        offset_add = self._offset if final_gid else 0
        for gid in self._gidvec:
            yield gid + offset_add, self._gid_info.get(gid)

    def intersection(self, other, raw_gids=False):
        """Computes the intersection of two NodeSet's

        For nodesets to intersect they must belong to the same population and
        have common gids. Otherwise an empty list is returned.
        """
        if self.population_name != other.population_name:
            return []
        intersect = numpy.intersect1d(self.raw_gids(), other.raw_gids(), assume_unique=True)
        if raw_gids:
            return intersect
        return numpy.add(intersect, self._offset, dtype="uint32")

    def clear_cell_info(self):
        self._gid_info = None


class SelectionNodeSet(_NodeSetBase):
    """
    A lightweight shim over a `libsonata.Selection` so that gids get offset
    """

    def __init__(self, sonata_selection):
        super().__init__()
        self._selection = sonata_selection
        # Max gid is the end of the last range since we need +1 (1 based)
        self._max_gid = sonata_selection.ranges[-1][1] if sonata_selection.ranges else 0
        self._size = sonata_selection.flat_size

    def __len__(self):
        return self._size

    def raw_gids(self):
        return numpy.add(self._selection.flatten(), 1, dtype="uint32")

    def raw_gids_iter(self):
        for r_start, r_end in self._selection.ranges:
            yield from range(r_start + 1, r_end + 1)

    def final_gids_iter(self):
        for gid in self.raw_gids_iter():
            yield gid + self._offset

    def intersection(self, other: _NodeSetBase, raw_gids=False, _quick_check=False):
        """Computes intersection of two nodesets.
        """
        # NOTE: A _quick_check param can be set to True so that we effectively only check for
        # intersection (True/False) instead of computing the actual intersection (internal).
        if self.population_name != other.population_name:
            return []

        sel2 = getattr(other, "_selection", None)
        if sel2:
            intersect = _ranges_overlap(self._selection.ranges, sel2.ranges, True, _quick_check)
        else:
            # Selection ranges are 0-based. We must bring gids to 0-based
            base_gids = numpy.subtract(other.raw_gids(), 1, dtype="uint32")
            intersect = _ranges_vec_overlap(self._selection.ranges, base_gids, _quick_check)

        if _quick_check:
            return intersect
        if len(intersect):
            if raw_gids:
                # TODO: We should change the return type to be another `SelectionNodeSet`
                # Like that we could still keep ranges internally and have PROPER API to get raw ids
                return numpy.add(intersect, 1, dtype=intersect.dtype)
            return numpy.add(intersect, self.offset + 1, dtype=intersect.dtype)
        return numpy.array([], dtype="uint32")

    def intersects(self, other):
        return self.intersection(other, _quick_check=True)


def _ranges_overlap(ranges1, ranges2, flattened_out=False, quick_check=False, dtype="uint32"):
    """
    Detect overlaps between two lists of ranges.
    This is especially important for nodesets since we can access the ranges in no time
    without the need to flatten and consume GBs of memory

    Args:
        ranges1: The first list of ranges
        ranges2: The second list of ranges
        flattened_out (bool): Whether to return the overlaps as a flat list. Otherwise range list
        quick_check: Whether to short-circuit and return True if any overlap exists
        dtype: The output dtype in case flattened_out is requested [default: "uint32"]
    """

    if not ranges1 or not ranges2:
        return []

    all_ranges = []
    r1_iter = iter(ranges1)
    r2_iter = iter(ranges2)
    r1, r2 = next(r1_iter), next(r2_iter)

    while r1 and r2:
        if r2[0] >= r1[1]:  # r2 past over end r1. Move r1
            r1 = next(r1_iter, None)
            continue
        if r2[1] <= r1[0]:  # r2 before whole range r1. Move r2
            r2 = next(r2_iter, None)
            continue

        # Phew, finally some intersection
        low, high = max(r1[0], r2[0]), min(r1[1], r2[1])
        if low < high:
            if quick_check:
                return True
            all_ranges.append((low, high))

        # Now move the one that still has potential for more overlap without moving the other
        if r2[1] > r1[1]:
            r1 = next(r1_iter, None)
        else:
            r2 = next(r2_iter, None)

    if quick_check:
        return False  # We know it's False as quick_check returns True in the loop
    if not flattened_out:
        return all_ranges
    if not all_ranges:
        return []
    return numpy.concatenate([numpy.arange(*r, dtype=dtype) for r in all_ranges])


def _ranges_vec_overlap(ranges1, vector, quick_check=False):
    """
    Detect overlaps between a list of ranges and a vector of ints
    This is particularly used to know the overlap between a SelectionNodeSet and a list
    of gids, e.g. the list of local gids.

    Args:
        ranges1: The list of ranges
        vector: The array of values to intersect with
        quick_check: Whether to short-circuit and return True if any overlap exists
    """
    if not ranges1 or len(vector) == 0:
        return []
    vector = numpy.asarray(vector)
    all_ranges = []

    for r1 in ranges1:
        if vector[-1] < r1[0]:  # gids before whole range r1
            break
        if vector[0] >= r1[1]:  # r2 past over end r1
            continue
        mask = (r1[0] <= vector) & (vector < r1[1])
        if numpy.any(mask):
            if quick_check:
                return True
            all_ranges.append(vector[mask])

    if quick_check:
        return False
    if not all_ranges:
        return []
    return numpy.concatenate(all_ranges)
