"""
A wrapper for MorphIO objects. Provides additional neuron
features on top of MorphIO basic morphology handling.
"""
import os
import logging
import numpy as np
from numpy.linalg import eig, norm


'''
    [START] Implementations retrieved from nse/morph-tool (!= hpc/morpho-tool !!!)
    These functions are needed for soma points computation (a la import3d).
    TODO: Once we have something stable, integrate nse/morph-tool
'''
X, Y, Z, R = 0, 1, 2, 3


def split_morphology_path(morphology_path):
    '''Split `{collection_path}/{morph_name}.{ext}`'''

    if os.path.exists(morphology_path):
        collection_path = os.path.dirname(morphology_path)
        morph_name, morph_ext = os.path.splitext(os.path.basename(morphology_path))
        return collection_path, morph_name, morph_ext

    else:
        collection_path = morphology_path
        while not os.path.exists(collection_path):
            assert collection_path != os.path.dirname(collection_path), "Failed to split path."
            collection_path = os.path.dirname(collection_path)

        morph_name, morph_ext = os.path.splitext(os.path.relpath(morphology_path, collection_path))

        return collection_path, morph_name, morph_ext


def contourcenter(xyz):
    '''python implementation of NEURON code: lib/hoc/import3d/import3d_sec.hoc '''
    # xyz = xyz.astype('d')
    # print(xyz.dtype)
    # print(xyz[0])
    POINTS = 101

    points = np.vstack((np.diff(xyz[:, [X, Y]], axis=0), xyz[0, [X, Y]]))
    perim = np.cumsum(np.hstack(((0,), norm(points, axis=1))))[:-1]

    d = np.linspace(0, perim[-1], POINTS)
    new_xyz = np.zeros((POINTS, 3))
    for i in range(3):
        new_xyz[:, i] = np.interp(x=d, xp=perim, fp=xyz[:, i])

    mean = np.mean(new_xyz, axis=0)

    return mean, new_xyz


def get_sides(points, major, minor):
    '''
    Circular permutation of the points so that the point with the largest
    coordinate along the major axis becomes the last point
    tobj = major.c.mul(d.x[i])  ###### uneeded? line 1191
    '''

    major_coord, minor_coord = np.dot(points, major), np.dot(points, minor)

    imax = np.argmax(major_coord)
    # pylint: disable=invalid-unary-operand-type
    major_coord, minor_coord = (np.roll(major_coord, -imax),
                                np.roll(minor_coord, -imax))

    imin = np.argmin(major_coord)

    sides = [major_coord[:imin][::-1], major_coord[imin:]]
    rads = [minor_coord[:imin][::-1], minor_coord[imin:]]
    return sides, rads


def make_convex(sides, rads):
    '''Keep only points that make path convex'''

    def convex_idx(m):
        '''Return index to elements of m that make it convex

        Note: not efficient at the moment
        # now we have the two sides without the min and max points (rads[0]=0)
        # we hope both sides now monotonically increase, i.e. convex
        # make it convex

        '''
        idx = np.ones_like(m, dtype=bool)
        last_val = m[-1]
        for i in range(len(m) - 2, -1, -1):
            if m[i] < last_val:
                last_val = m[i]
            else:
                idx[i] = False
        return idx

    for i_side in [0, 1]:
        ci = convex_idx(sides[i_side])
        sides[i_side] = sides[i_side][ci]
        rads[i_side] = rads[i_side][ci]
    return sides, rads


def contour2centroid(mean, points):
    '''this follows the function in
            lib/hoc/import3d/import3d_gui.hoc
       most of the comments are from there, so if you want to follow along, it should
       break up the function the same way
    '''
    logging.debug('Converting soma contour into a stack of cylinders')

    # find the major axis of the ellipsoid that best fits the shape
    # assuming (falsely in general) that the center is the mean

    points = (points - mean)
    eigen_values, eigen_vectors = eig(np.dot(points.T, points))

    # To be consistent with NEURON eigen vector directions
    eigen_vectors *= -1

    idx = np.argmax(eigen_values)
    major = eigen_vectors[:, idx]
    # minor is normal and in xy plane
    idx = 3 - np.argmin(eigen_values) - np.argmax(eigen_values)
    minor = eigen_vectors[:, idx]
    minor[2] = 0

    sides, rads = get_sides(points, major, minor)
    sides, rads = make_convex(sides, rads)

    tobj = np.sort(np.hstack(sides))
    new_major_coord = np.linspace(tobj[1], tobj[-2], 21)
    rads[0] = np.interp(new_major_coord, sides[0], rads[0])
    rads[1] = np.interp(new_major_coord, sides[1], rads[1])

    points = major * new_major_coord[:, np.newaxis] + mean
    diameters = np.abs(rads[0] - rads[1])

    # avoid 0 diameter ends
    diameters[0] = np.mean(diameters[:2])
    diameters[-1] = np.mean(diameters[-2:])

    return points, diameters


def _to_sphere(neuron):
    '''Convert a 3-pts cylinder or a 1-pt sphere into a circular
    contour that represents the same sphere'''
    radius = neuron.soma.diameters[0] / 2.
    N = 20
    points = np.zeros((N, 3))
    phase = 2 * np.pi / (N - 1) * np.arange(N)
    points[:, 0] = radius * np.cos(phase)
    points[:, 1] = radius * np.sin(phase)
    points += neuron.soma.points[0]
    neuron.soma.points = points
    neuron.soma.diameters = np.repeat(radius, N)


def single_point_sphere_to_circular_contour(neuron):
    '''Transform a single point soma that represents a sphere
    into a circular contour that represents the same sphere'''
    logging.debug('Converting 1-point soma (sperical soma) to circular contour '
                  'representing the same sphere')
    _to_sphere(neuron)


'''
    [END] Implementations retrieved from nse/morph-tool (!= hpc/morpho-tool !!!)
'''


class MorphIOWrapper:
    """
        A class that wraps a MorphIO object and gets everything ready for HOC usage
    """
    morph = property(lambda self: self._morph)
    section_index2name_dict = property(lambda self: self._sec_idx2names)
    section_typeid_distrib = property(lambda self: self._sec_typeid_distrib)

    def __init__(self, input_file, options=0):
        self._collection_dir, self._morph_name, self._morph_ext = split_morphology_path(input_file)
        self._options = options
        self._build_morph()
        self._sec_idx2names = {}
        self._build_sec_idx2names()
        self._build_sec_typeid_distrib()

    def _build_morph(self):
        """ Build immutable morphology, going trough mutable and applying neuron adjustemnts """
        try:
            # Lazy import morphio since it has an issue with execl
            from morphio import SomaType, Option
            from morphio import Morphology
            from morphio import Collection
        except ImportError as e:
            raise RuntimeError("MorphIO is not available") from e

        collection = Collection(self._collection_dir, extensions=[self._morph_ext])
        options = self._options | Option.nrn_order
        self._morph = collection.load(self._morph_name, options, mutable=True)

        # Re-compute the soma points as they are computed in import3d_gui.hoc
        if self._morph.soma_type not in {SomaType.SOMA_SINGLE_POINT, SomaType.SOMA_SIMPLE_CONTOUR}:
            raise Exception(
                'A H5 file morphology is not supposed to have a soma of type: {}'.format(
                    self._morph.soma_type))
        logging.debug(
            "(%s, %s, %s) has soma type : %s",
            self._collection_dir, self._morph_name, self._morph_ext, self._morph.soma_type
        )

        if self._morph.soma_type == SomaType.SOMA_SINGLE_POINT:
            ''' See NRN import3d_gui.hoc -> instantiate()
                            -> sphere_rep(xx, yy, zz, dd) '''
            single_point_sphere_to_circular_contour(self._morph)
        elif self._morph.soma_type == SomaType.SOMA_SIMPLE_CONTOUR:
            ''' See NRN import3d_gui.hoc -> instantiate()
                            -> contour2centroid(xx, yy, zz, dd, sec) '''
            mean, new_xyz = contourcenter(self._morph.soma.points)
            self._morph.soma.points, self._morph.soma.diameters = contour2centroid(
                mean, new_xyz)

        self._morph = Morphology(self._morph)

    def _build_sec_idx2names(self):
        """ Build section index to nrn section names mapping on top of MorphIO section.id """

        # soma is not accounted for in sections
        self._sec_idx2names[0] = 'soma'

        idx_adjust = 0  # section ids don't restart from 0 for each type in MorphIO
        current_type = -1  # used for index adjustment
        for i, sec in enumerate(self._morph.sections):
            index = i + 1
            # When we have a new type, update idx_adjust
            if self._morph.section_types[sec.id] != current_type:
                current_type = self._morph.section_types[sec.id]
                idx_adjust = i

            self._sec_idx2names[index] = self.name(current_type, i - idx_adjust)

    def _build_sec_typeid_distrib(self):
        """ Build typeid distribution on top of MorphIO section_types """

        '''
            This will hold np.array that will map the different type ids to the
            start id wrt to section_types and their count. For example, axon type(2)
            starts at section.id 0 and and totals 2724 sections.

                | type_id | start_id  |   count   |
                | ------- | --------- | --------- |
                |      2  |        0  |     2724  |
                |      3  |     2724  |       75  |


            >>> _sec_typeid_distrib
            array([[(2,    0, 2724)],
                   [(3, 2724,   75)]],
                  dtype=[('type_id', '<i8'), ('start_id', '<i8'), ('count', '<i8')])

            Then use it like this:
            >>> _sec_typeid_distrib[['type_id', 'start_id']]
            array([[(2,    0)],
                   [(3, 2724)]],
                  dtype={'names':['type_id','start_id'],....}
        '''
        self._sec_typeid_distrib = np.dstack(np.unique(self._morph.section_types,
                                                       return_counts=True,
                                                       return_index=True))[0]
        self._sec_typeid_distrib = np.concatenate(([(1, -1, 1)], self._sec_typeid_distrib), axis=0)
        self._sec_typeid_distrib.dtype = [('type_id', '<i8'), ('start_id', '<i8'), ('count', '<i8')]

    def morph_as_hoc(self):
        """ Uses morphio object to read and generate hoc commands just like import3d_gui.hoc """

        cmds = []

        '''
            We need to get the number of sections for each type in order
            to generate the create commands. E.g.:
                ( soma , 1  )
                ( dend , 52 )
                ( axon , 23 )
                ( apic , 5  )
        '''
        # generate create commands
        for [(type_id, count)] in self._sec_typeid_distrib[['type_id', 'count']]:
            tstr = self.type2name(type_id)
            tstr1 = "create {}[{}]".format(tstr, count)
            cmds.append(tstr1)
            tstr1 = self.mksubset(type_id, count, tstr)
            cmds.append(tstr1)

        cmds.append("forall all.append")

        # generate 3D soma points commands. Order is reversed wrt NEURON's soma points.
        cmds.extend(("soma {{ pt3dadd({:.8g}, {:.8g}, {:.8g}, {:.8g}) }}"
                     .format(p[0], p[1], p[2], d)
                     for p, d in zip(reversed(self._morph.soma.points),
                                     reversed(self._morph.soma.diameters))))

        # generate sections connect + their respective 3D points commands
        for i, sec in enumerate(self._morph.sections):
            index = i + 1
            tstr = self._sec_idx2names[index]

            if not sec.is_root:
                if sec.parent is not None:
                    parent_index = sec.parent.id + 1
                    tstr1 = self._sec_idx2names[parent_index]
                    tstr1 = "{} connect {}(0), {}".format(tstr1, tstr, 1)
                    cmds.append(tstr1)
            else:
                tstr1 = "soma connect {}(0), {}".format(tstr, 0.5)
                cmds.append(tstr1)

                # pt3dstyle does not impact simulation numbers. This will be kept for x-reference.
                # tstr1 = "{} {{ pt3dstyle(1, {:.8g}, {:.8g}, {:.8g}) }}".format
                #                   (tstr, mean[0], mean[1], mean[2])
                # cmds.append(tstr1)

            # 3D point info
            cmds.extend("{} {{ pt3dadd({:.8g}, {:.8g}, {:.8g}, {:.8g}) }}"
                        .format(tstr, p[0], p[1], p[2], d)
                        for p, d in zip(sec.points, sec.diameters))

        return cmds

    '''
         [START] Python versions of import3d_gui.hoc helper functions
         Note: nrn function names will be kept for reference
    '''

    _type2name_dict = {1: "soma",
                       2: "axon",
                       3: "dend",
                       4: "apic"}

    @classmethod
    def type2name(cls, type_id):
        """
        :param type_id: id of section type
        :return: name representation of the section type.
                 If not found in _type2name_dict, then default is:
                    if (type < 0): "minus_{}".format(-type)
                    else: "dend_{}".format(type)
        """
        return cls._type2name_dict.get(type_id) or \
            ("minus_{}".format(-type_id) if type_id < 0
             else "dend_{}".format(type_id))

    _mksubset_dict = {1: "somatic",
                      2: "axonal",
                      3: "basal",
                      4: "apical"}

    @classmethod
    def mksubset(cls, type_id, freq, type_name):
        """
        :param type_id: id of section type
        :param freq: frequency of that section type id
        :param type_name: the name of the section type
        :return: command to append section type to subset
        """
        tstr = cls._mksubset_dict.get(type_id) or \
            ("minus_{}set".format(-type_id) if type_id < 0
             else "dendritic_{}".format(type_id))

        tstr1 = "forsec \"{}\" {}.append".format(type_name, tstr)
        return tstr1

    @classmethod
    def name(cls, type_id, index):
        return "{}[{}]".format(cls.type2name(type_id), index)

    '''
        [END] Python versions of import3d_gui.hoc helper functions
    '''
