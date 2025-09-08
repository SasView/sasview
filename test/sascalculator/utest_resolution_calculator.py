"""
    Unit test for resolution_calculator
"""

import unittest

from sas.sascalc.calculator.resolution_calculator import ResolutionCalculator as calculator


class resolution_calculator(unittest.TestCase):

    def setUp(self):

        self.cal = calculator()

    def test_resolution_calculation(self):
        """
            Test resolution_calculator"
        """
        self.cal.set_wavelength(15)
        self.cal.set_source_aperture_size([2])
        self.cal.set_sample_aperture_size([1])
        self.cal.set_detector_pix_size([1])
        self.cal.set_source2sample_distance([1500])
        self.cal.set_sample2detector_distance([1500])
        self.cal.set_wavelength_spread(0.1)
        # all instr. params for cal
        self.cal.get_all_instrument_params()
        qr, phi, sigma_1, sigma_2, _, sigma_1d = self.cal.compute(15, 0.1,
                                                        0, 0, coord = 'polar')
        sigma_1d = self.cal.sigma_1d

        # The value "0.000213283" was obtained by manual calculation.
        self.assertAlmostEqual(sigma_1d,   0.000213283, 5)


if __name__ == '__main__':
    unittest.main()

