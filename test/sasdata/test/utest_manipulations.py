"""
    Unit tests for data manipulations
"""
# TODO: what happens if you add a Data1D to a Data2D?

import math
import os.path
import unittest

import numpy as np
from numpy.testing import assert_allclose

from sas.sascalc.dataloader.loader import Loader
from sas.sascalc.dataloader.data_info import Data1D, Data2D

RTOL = 1e-12

def find(filename):
    return os.path.join(os.path.dirname(__file__), 'test_data', filename)

class DataInfoTests(unittest.TestCase):

    def setUp(self):
        data = Loader().load(find("cansas1d.xml"))
        self.data = data[0]

    def test_clone1D(self):
        """
            Test basic cloning
        """
        clone = self.data.clone_without_data()

        for i in range(len(self.data.detector)):
            self.assertEqual(
                self.data.detector[i].distance, clone.detector[i].distance)


class Theory1DTests(unittest.TestCase):

    def setUp(self):
        data = Loader().load(find("cansas1d.xml"))
        self.data = data[0]

    def test_clone_theory1D(self):
        """
            Test basic cloning
        """
        theory = Data1D(x=[], y=[], dy=None)
        theory.clone_without_data(clone=self.data)
        theory.copy_from_datainfo(data1d=self.data)
        for i in range(len(self.data.detector)):
            self.assertEqual(
                self.data.detector[i].distance, theory.detector[i].distance)

        for i in range(len(self.data.x)):
            self.assertEqual(self.data.x[i], theory.x[i])
            self.assertEqual(self.data.y[i], theory.y[i])
            self.assertEqual(self.data.dy[i], theory.dy[i])


class ManipTests(unittest.TestCase):

    def setUp(self):
        # Create two data sets to play with
        x_0 = np.arange(1, 6, dtype='d')
        y_0 = 2.0 * np.ones(5)
        dy_0 = 0.5 * np.ones(5)
        self.data = Data1D(x_0, y_0, dy=dy_0)

        x = self.data.x.copy()
        y = np.ones(5)
        dy = np.ones(5)
        self.data2 = Data1D(x, y, dy=dy)

    def test_load(self):
        """
            Test whether the test file was loaded properly
        """
        # There should be 5 entries in the file
        self.assertEqual(len(self.data.x), 5)

        for i in range(5):
            # The x values should be from 1 to 5
            self.assertEqual(self.data.x[i], float(i + 1))

        # All y-error values should be 0.5
        assert_allclose(self.data.dy, 0.5, RTOL)

        # All y values should be 2.0
        assert_allclose(self.data.y, 2.0, RTOL)

    def test_add(self):
        result = self.data2 + self.data
        assert_allclose(result.y, 3.0, RTOL)
        assert_allclose(result.dy, np.sqrt(0.5**2 + 1.0), RTOL)

    def test_sub(self):
        result = self.data2 - self.data
        assert_allclose(result.y, -1.0, RTOL)
        assert_allclose(result.dy, math.sqrt(0.5**2 + 1.0), RTOL)

    def test_mul(self):
        result = self.data2 * self.data
        assert_allclose(result.y, 2.0, RTOL)
        assert_allclose(
            result.dy, math.sqrt((0.5 * 1.0)**2 + (1.0 * 2.0)**2), RTOL)

    def test_div(self):
        result = self.data2 / self.data
        assert_allclose(result.y, 0.5, RTOL)
        assert_allclose(
            result.dy, math.sqrt((1.0 / 2.0)**2 + (0.5 * 1.0 / 4.0)**2), RTOL)

    def test_radd(self):
        result = self.data + 3.0
        assert_allclose(result.y, 5.0, RTOL)
        assert_allclose(result.dy, 0.5, RTOL)

        result = 3.0 + self.data
        assert_allclose(result.y, 5.0, RTOL)
        assert_allclose(result.dy, 0.5, RTOL)

    def test_rsub(self):
        result = self.data - 3.0
        assert_allclose(result.y, -1.0, RTOL)
        assert_allclose(result.dy, 0.5, RTOL)

        result = 3.0 - self.data
        assert_allclose(result.y, 1.0, RTOL)
        assert_allclose(result.dy, 0.5, RTOL)

    def test_rmul(self):
        result = self.data * 3.0
        assert_allclose(result.y, 6.0, RTOL)
        assert_allclose(result.dy, 1.5, RTOL)

        result = 3.0 * self.data
        assert_allclose(result.y, 6.0, RTOL)
        assert_allclose(result.dy, 1.5, RTOL)

    def test_rdiv(self):
        result = self.data / 4.0
        assert_allclose(result.y, 0.5, RTOL)
        assert_allclose(result.dy, 0.125, RTOL)

        result = 6.0 / self.data
        assert_allclose(result.y, 3.0, RTOL)
        assert_allclose(result.dy, 6.0 * 0.5 / 4.0, RTOL)


class Manin2DTests(unittest.TestCase):

    def setUp(self):
        # Create two data sets to play with
        x_0 = 2.0 * np.ones(25)
        dx_0 = 0.5 * np.ones(25)
        qx_0 = np.arange(25)
        qy_0 = np.arange(25)
        mask_0 = np.zeros(25)
        dqx_0 = np.arange(25) / 100
        dqy_0 = np.arange(25) / 100
        q_0 = np.sqrt(qx_0 * qx_0 + qy_0 * qy_0)
        self.data = Data2D(data=x_0, err_data=dx_0, qx_data=qx_0,
                           qy_data=qy_0, q_data=q_0, mask=mask_0,
                           dqx_data=dqx_0, dqy_data=dqy_0)

        y = np.ones(25)
        dy = np.ones(25)
        qx = np.arange(25)
        qy = np.arange(25)
        mask = np.zeros(25)
        q = np.sqrt(qx * qx + qy * qy)
        self.data2 = Data2D(data=y, err_data=dy, qx_data=qx, qy_data=qy,
                            q_data=q, mask=mask)

    def test_load(self):
        """
            Test whether the test file was loaded properly
        """
        # There should be 5 entries in the file
        self.assertEqual(np.size(self.data.data), 25)

        for i in range(25):
            # All y-error values should be 0.5
            self.assertEqual(self.data.err_data[i], 0.5)

            # All y values should be 2.0
            self.assertEqual(self.data.data[i], 2.0)

    def test_add(self):
        result = self.data2 + self.data
        assert_allclose(result.data, 3.0, RTOL)
        assert_allclose(result.err_data, np.sqrt(0.5**2 + 1.0), RTOL)

    def test_sub(self):
        result = self.data2 - self.data
        assert_allclose(result.data, -1.0, RTOL)
        assert_allclose(result.err_data, math.sqrt(0.5**2 + 1.0), RTOL)

    def test_mul(self):
        result = self.data2 * self.data
        assert_allclose(result.data, 2.0, RTOL)
        assert_allclose(
            result.err_data, math.sqrt((0.5 * 1.0)**2 + (1.0 * 2.0)**2), RTOL)

    def test_div(self):
        result = self.data2 / self.data
        assert_allclose(result.data, 0.5, RTOL)
        assert_allclose(
            result.err_data,
            math.sqrt((1.0 / 2.0)**2 + (0.5 * 1.0 / 4.0)**2), RTOL)

    def test_radd(self):
        result = self.data + 3.0
        assert_allclose(result.data, 5.0, RTOL)
        assert_allclose(result.err_data, 0.5, RTOL)

        result = 3.0 + self.data
        assert_allclose(result.data, 5.0, RTOL)
        assert_allclose(result.err_data, 0.5, RTOL)

    def test_rsub(self):
        result = self.data - 3.0
        assert_allclose(result.data, -1.0, RTOL)
        assert_allclose(result.err_data, 0.5, RTOL)

        result = 3.0 - self.data
        assert_allclose(result.data, 1.0, RTOL)
        assert_allclose(result.err_data, 0.5, RTOL)

    def test_rmul(self):
        result = self.data * 3.0
        assert_allclose(result.data, 6.0, RTOL)
        assert_allclose(result.err_data, 1.5, RTOL)

        result = 3.0 * self.data
        assert_allclose(result.data, 6.0, RTOL)
        assert_allclose(result.err_data, 1.5, RTOL)

    def test_rdiv(self):
        result = self.data / 4.0
        assert_allclose(result.data, 0.5, RTOL)
        assert_allclose(result.err_data, 0.125, RTOL)

        result = 6.0 / self.data
        assert_allclose(result.data, 3.0, RTOL)
        assert_allclose(result.err_data, 6.0 * 0.5 / 4.0, RTOL)


if __name__ == '__main__':
    unittest.main()
