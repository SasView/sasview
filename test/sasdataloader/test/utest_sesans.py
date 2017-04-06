"""
    Unit tests for the SESANS .ses reader
"""

import unittest
from sas.sascalc.dataloader.loader import Loader


class sesans_reader(unittest.TestCase):

    def setUp(self):
        self.loader = Loader()

    def test_sesans_load(self):
        """
            Test .SES file loading
        """
        f = self.loader.load("sphere2micron.ses")
        # self.assertEqual(f, 5)
        self.assertEqual(len(f.x), 40)
        self.assertEqual(f.x[0], 391.56)
        self.assertEqual(f.x[-1], 46099)
        self.assertEqual(f.y[-1], -0.19956)
        self.assertEqual(f.x_unit, "A")
        self.assertEqual(f.y_unit, "A-2 cm-1")
        self.assertEqual(f.sample.name, "Polystyrene 2 um in 53% H2O, 47% D2O")
        self.assertEqual(f.sample.thickness, 0.2)
        self.assertEqual(f.sample.zacceptance, (0.0168, "radians"))
        self.assertEqual(f.isSesans, True)

    def test_sesans_tof(self):
        """
            Test .SES loading on a TOF dataset
        """
        f = self.loader.load("sphere_isis.ses")
        self.assertEqual(len(f.x), 57)
        self.assertEqual(f.x[-1], 19303.4)
        self.assertEqual(f.source.wavelength[-1], 13.893668)


if __name__ == "__main__":
    unittest.main()
