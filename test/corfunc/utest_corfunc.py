"""
Unit Tests for CorfuncCalculator class
"""


import os.path
import unittest

import numpy as np

from sasdata.dataloader.data_info import Data1D

from sas.sascalc.corfunc.calculation_data import SettableExtrapolationParameters
from sas.sascalc.corfunc.corfunc_calculator import CorfuncCalculator, extract_lamellar_parameters


def find(filename):
    return os.path.join(os.path.dirname(__file__), 'data', filename)


class TestCalculator(unittest.TestCase):

    def setUp(self):
        self.data = load_data()

        self.parameters = SettableExtrapolationParameters(0.013, 0.15, 0.24)

        self.expected_results = [np.loadtxt(find(filename+"_out.txt")).T[2]
                                 for filename in ("gamma1", "gamma3", "idf")]

    def test_extrapolation(self):

        calculator = CorfuncCalculator(self.data, self.parameters)
        # calculator._background.data = 0.3
        # calculator._background.allow_fit = False

        calculator.run()

        self.assertAlmostEqual(calculator.guinier.A, 4.18970, places=1)
        self.assertAlmostEqual(calculator.guinier.B, -25469.9, delta=2000)
        self.assertAlmostEqual(calculator.porod.K, 4.44660e-5, places=10)

        # Ensure the extraplation tends to the background value
        self.assertIsNotNone(calculator._extrapolation_data)
        if calculator._extrapolation_data is not None:
            self.assertAlmostEqual(calculator._extrapolation_data.y[-1], calculator.background)


    def test_transform(self):

        calculator = CorfuncCalculator(self.data, self.parameters)
        # calculator._background.data = 0.3
        # calculator._background.allow_fit = False

        calculator.run()

        self.assertIsNotNone(calculator.transformed)

        if calculator.transformed is not None:

            self.assertIsNotNone(calculator.transformed.gamma_1)
            self.assertAlmostEqual(calculator.transformed.gamma_1.y[0], 1)
            self.assertAlmostEqual(calculator.transformed.gamma_1.y[-1], 0, 5)

    def test_extract(self):
        params = extract_lamellar_parameters(
                    self.data,
                    self.parameters.point_1,
                    self.parameters.point_2,
                    self.parameters.point_3)

        self.assertLess(abs(params.long_period-75), 2.5) # L_p ~= 75


def load_data(filename="98929.txt"):
    data = np.loadtxt(find(filename), dtype=np.float64)
    q = data[:,0]
    iq = data[:,1]
    return Data1D(x=q, y=iq)


if __name__ == '__main__':
    unittest.main()
