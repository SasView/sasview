"""
    Unit tests for the SESANS .ses reader
"""

import unittest
from sas.sascalc.dataloader.loader_exceptions import FileContentsException,\
    DefaultReaderException
from sas.sascalc.dataloader.readers.sesans_reader import Reader
from sas.sascalc.dataloader.loader import  Loader

class sesans_reader(unittest.TestCase):

    def setUp(self):
        reader = Reader()
        self.loader = reader.read

    def test_full_load(self):
        """
            Test .SES in the full loader to make sure that the file type is correctly accepted
        """
        file = Loader().load("sesans_examples/sphere2micron.ses")
        f = file[0]
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
        file = self.loader("sesans_examples/sphere_isis.ses")
        f = file[0]
        self.assertEqual(len(f.x), 57)
        self.assertEqual(f.x[-1], 19303.4)
        self.assertEqual(f.source.wavelength[-1], 13.893668)
        self.assertEqual(f.source.wavelength[0], 1.612452)
        self.assertEqual(f.sample.yacceptance, (0.09, "radians"))
        self.assertEqual(f.sample.zacceptance, (0.09, "radians"))
        self.assertEqual(f.sample.thickness, 0.2)

    def test_sesans_no_data(self):
        """
            Confirm that sesans files with no actual data won't load.
        """
        self.assertRaises(
            FileContentsException,
            self.loader,
            "sesans_examples/sesans_no_data.ses")

    def test_sesans_no_spin_echo_unit(self):
        """
            Confirm that sesans files with no units from the spin echo length raise an appropriate error
        """
        self.assertRaises(
            FileContentsException,
            self.loader,
            "sesans_examples/no_spin_echo_unit.ses")

    def test_sesans_future_version(self):
        """
            Confirm that sesans files that, according to semantic version, are from a future, backwards-incompatible version of the SES file format throw an exception.
        """
        self.assertRaises(
            FileContentsException,
            self.loader,
            "sesans_examples/next_gen.ses")

    def test_sesans_mandatory_headers(self):
        """
            Confirm that sesans files throw an exception if one of the mandator headers is missing.
        """
        self.assertRaises(
            FileContentsException,
            self.loader,
            "sesans_examples/no_wavelength.ses")

    def test_sesans_columns_match_headers(self):
        """
            Confirm that sesans files throw an exception if one of the mandator headers is missing.
        """
        self.assertRaises(
            FileContentsException,
            self.loader,
            "sesans_examples/too_many_headers.ses")

if __name__ == "__main__":
    unittest.main()
