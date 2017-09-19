"""
Unit Tests for CorfuncCalculator class
"""
from __future__ import division, print_function

import unittest
import time

import numpy as np

from sas.sascalc.corfunc.corfunc_calculator import CorfuncCalculator
from sas.sascalc.dataloader.data_info import Data1D


class TestCalculator(unittest.TestCase):

    def setUp(self):
        self.data = load_data()
        # Note: to generate target values from the GUI:
        # * load the data from test/corfunc/test/98929.txt
        # * set qrange to (0, 0.013), (0.15, 0.24)
        # * select fourier transform type
        # * click Calculate Bg
        # * click Extrapolate
        # * click Compute Parameters
        # * copy the Guinier and Porod values to the extrapolate function
        # * for each graph, grab the data from DataInfo and store it in _out.txt
        self.calculator = CorfuncCalculator(data=self.data, lowerq=0.013,
            upperq=(0.15, 0.24))
        self.calculator.background = 0.3
        self.extrapolation = None
        self.transformation = None
        self.results = [np.loadtxt(filename+"_out.txt").T[2]
                        for filename in ("gamma1", "gamma3", "idf")]

    def extrapolate(self):
        params, extrapolation, s2 = self.calculator.compute_extrapolation()
        # Check the extrapolation parameters
        self.assertAlmostEqual(params['A'], 4.18970, places=5)
        self.assertAlmostEqual(params['B'], -25469.9, places=1)
        self.assertAlmostEqual(params['K'], 4.44660e-5, places=10)
        #self.assertAlmostEqual(params['sigma'], 1.70181e-10, places=15)

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

    def transform_callback(self, transforms):
        transform1, transform3, idf = transforms
        self.assertIsNotNone(transform1)
        self.assertAlmostEqual(transform1.y[0], 1)
        self.assertAlmostEqual(transform1.y[-1], 0, 5)
        self.transformation = transforms

    def extract_params(self):
        params = self.calculator.extract_parameters(self.transformation[0])
        self.assertIsNotNone(params)
        self.assertEqual(len(params), 6)
        self.assertLess(abs(params['max']-75), 2.5) # L_p ~= 75

    def check_transforms(self):
        gamma1, gamma3, idf = self.transformation
        gamma1_out, gamma3_out, idf_out = self.results
        def compare(a, b):
            return max(abs((a-b)/b))
        #print("gamma1 diff", compare(gamma1.y[gamma1.x<=200.], gamma1_out))
        #print("gamma3 diff", compare(gamma3.y[gamma3.x<=200.], gamma3_out))
        #print("idf diff", compare(idf.y[idf.x<=200.], idf_out))
        #self.assertLess(compare(gamma1.y[gamma1.x<=200.], gamma1_out), 1e-10)
        #self.assertLess(compare(gamma3.y[gamma3.x<=200.], gamma3_out), 1e-10)
        #self.assertLess(compare(idf.y[idf.x<=200.], idf_out), 1e-10)

    # Ensure tests are ran in correct order;
    # Each test depends on the one before it
    def test_calculator(self):
        steps = [self.extrapolate, self.transform, self.extract_params, self.check_transforms]
        for test in steps:
            try:
                test()
            except Exception as e:
                raise
                self.fail("{} failed ({}: {})".format(test, type(e), e))


def load_data(filename="98929.txt"):
    data = np.loadtxt(filename, dtype=np.float64)
    q = data[:,0]
    iq = data[:,1]
    return Data1D(x=q, y=iq)

if __name__ == '__main__':
    unittest.main()
