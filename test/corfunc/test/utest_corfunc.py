"""
Unit Tests for CorfuncCalculator class
"""

import unittest
import time
import numpy as np
from sas.sascalc.corfunc.corfunc_calculator import CorfuncCalculator
from sas.sascalc.dataloader.data_info import Data1D
import matplotlib.pyplot as plt

class TestCalculator(unittest.TestCase):

    def setUp(self):
        self.data = load_data()
        self.calculator = CorfuncCalculator(data=self.data, lowerq=0.013,
            upperq=(0.15, 0.24))
        self.extrapolation = None

    def extrapolate(self):
        extrapolation = self.calculator.compute_extrapolation()

        # Ensure the extraplation tends to the background value
        self.assertAlmostEqual(extrapolation.y[-1], self.calculator.background)

        # Test extrapolation for q values between 0.02 and 0.24
        mask = np.logical_and(self.data.x > 0.02, self.data.x < 0.24)
        qs = self.data.x[mask]
        iqs = self.data.y[mask]

        for q, iq in zip(qs, iqs):
            # Find the q value in the extraplation nearest to the value in
            # the data
            q_extrap = min(extrapolation.x, key=lambda x:abs(x-q))
            # Find the index of this value in the extrapolation
            index = list(extrapolation.x).index(q_extrap)
            # Find it's corresponding intensity value
            iq_extrap = extrapolation.y[index]
            # Check the extrapolation agrees to the data at this point to 1 d.p
            self.assertAlmostEqual(iq_extrap, iq, 1)

        self.extrapolation = extrapolation

    def transform(self):
        self.calculator.compute_transform(self.extrapolation, 'fourier',
            completefn=self.transform_callback)
        # Transform is performed asynchronously; give it time to run
        while True:
            time.sleep(0.001)
            if not self.calculator.transform_isrunning():
                break

    def transform_callback(self, transform):
        self.assertIsNotNone(transform)
        self.assertAlmostEqual(transform.y[0], 1)
        self.assertAlmostEqual(transform.y[-1], 0, 5)
        self.transformation = transform

    def extract_params(self):
        params = self.calculator.extract_parameters(self.transformation)
        self.assertIsNotNone(params)
        self.assertEqual(len(params), 6)
        self.assertLess(abs(params['max']-75), 2.5) # L_p ~= 75
        self.assertLess(abs(params['dtr']-6), 2.5) # D_tr ~= 6


    # Ensure tests are ran in correct order;
    # Each test depends on the one before it
    def test_calculator(self):
        steps = [self.extrapolate, self.transform, self.extract_params]
        for test in steps:
            try:
                test()
            except Exception as e:
                self.fail("{} failed ({}: {})".format(test, type(e), e))


def load_data(filename="98929.txt"):
    data = np.loadtxt(filename, dtype=np.float32)
    q = data[:,0]
    iq = data[:,1]
    return Data1D(x=q, y=iq)

if __name__ == '__main__':
    unittest.main()
