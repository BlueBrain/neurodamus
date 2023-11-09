import neurodamus.metype as metype
import numpy
import numpy.testing as npt


def test_coord_mapping1():
    ty = metype.METypeItem(
        morph_name='ABCD',
        position=[1.0, 1.0, 1.0],
        rotation=[0.0, 0.0, 0.0, 1.0],
        scale=1.0
    )
    x = ty.local_to_global_coord_mapping(numpy.array([[0.0, 0.0, 0.0]]))[0]
    y = ty.local_to_global_coord_mapping(numpy.array([[6.98622, 12.17931, 17.53813]]))[0]
    npt.assert_allclose(x, [1., 1., 1.])
    npt.assert_allclose(y, [7.98622, 13.17931, 18.53813])


def test_coord_mapping2():
    ty = metype.METypeItem(
        morph_name='ABCD',
        position=[1, .5, .25],
        rotation=[0.8728715609439696, 0.4364357804719848, 0.2182178902359924, 0.0],
        scale=1.0
    )
    x = ty.local_to_global_coord_mapping(numpy.array([[0.0, 0.0, 0.0]]))[0]
    y = ty.local_to_global_coord_mapping(numpy.array([[6.98622, 12.17931, 17.53813]]))[0]
    npt.assert_allclose(x, [1., 0.5, 0.25])
    npt.assert_allclose(y, [20.62011524, 1.62385762, -10.63654619])
