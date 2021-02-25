import unittest
import neurodamus.metype as metype
import numpy


class TransformationTest(unittest.TestCase):

    def test(self):
        ty = metype.METypeItem(morph_name='ABCD', position=[1.0, 1.0, 1.0],
                               rotation=[0.0, 0.0, 0.0, 1.0],
                               scale=1.0)
        x = ty.local_to_global_coord_mapping(numpy.array([[0.0, 0.0, 0.0]]))[0]
        y = ty.local_to_global_coord_mapping(numpy.array([[6.98622, 12.17931, 17.53813]]))[0]
        self.assertAlmostEqual(x[0], 1.0, 6)
        self.assertAlmostEqual(x[1], 1.0, 6)
        self.assertAlmostEqual(x[2], 1.0, 6)
        self.assertAlmostEqual(y[0], 7.98622, 6)
        self.assertAlmostEqual(y[1], 13.17931, 6)
        self.assertAlmostEqual(y[2], 18.53813, 6)
        ty = metype.METypeItem(morph_name='ABCD', position=[1, .5, .25],
                               rotation=[0.8728715609439696, 0.4364357804719848,
                                         0.2182178902359924, 0.0],
                               scale=1.0)
        x = ty.local_to_global_coord_mapping(numpy.array([[0.0, 0.0, 0.0]]))[0]
        self.assertAlmostEqual(x[0], 1, 6)
        self.assertAlmostEqual(x[1], 0.5, 6)
        self.assertAlmostEqual(x[2], 0.25, 6)
        y = ty.local_to_global_coord_mapping(numpy.array([[6.98622, 12.17931, 17.53813]]))[0]
        self.assertAlmostEqual(y[0], 20.62011524, 6)
        self.assertAlmostEqual(y[1], 1.62385762, 6)
        self.assertAlmostEqual(y[2], -10.63654619, 6)


if __name__ == '__main__':
    unittest.main()
