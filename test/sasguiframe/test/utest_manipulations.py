"""
    Unit tests for data manipulations
"""
# TODO: what happens if you add a Data1D to a Data2D?

import math
import os.path
import unittest

import numpy as np

from sas.sascalc.dataloader.loader import Loader
from sas.sasgui.guiframe.dataFitting import Data1D
from sas.sasgui.guiframe.dataFitting import Data2D


class DataInfoTests(unittest.TestCase):

    def setUp(self):
        data = Loader().load("cansas1d.xml")
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
        data = Loader().load("cansas1d.xml")
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
        x_0 = np.ones(5)
        for i in range(5):
            x_0[i] = x_0[i] * (i + 1.0)

        y_0 = 2.0 * np.ones(5)
        dy_0 = 0.5 * np.ones(5)
        self.data = Data1D(x_0, y_0, dy=dy_0)

        x = self.data.x
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
            self.assertEqual(self.data.dy[i], 0.5)

            # All y values should be 2.0
            self.assertEqual(self.data.y[i], 2.0)

    def test_add(self):
        result = self.data2 + self.data
        for i in range(5):
            self.assertEqual(result.y[i], 3.0)
            self.assertEqual(result.dy[i], math.sqrt(0.5**2 + 1.0))

    def test_sub(self):
        result = self.data2 - self.data
        for i in range(5):
            self.assertEqual(result.y[i], -1.0)
            self.assertEqual(result.dy[i], math.sqrt(0.5**2 + 1.0))

    def test_mul(self):
        result = self.data2 * self.data
        for i in range(5):
            self.assertEqual(result.y[i], 2.0)
            self.assertEqual(result.dy[i], math.sqrt(
                (0.5 * 1.0)**2 + (1.0 * 2.0)**2))

    def test_div(self):
        result = self.data2 / self.data
        for i in range(5):
            self.assertEqual(result.y[i], 0.5)
            self.assertEqual(result.dy[i], math.sqrt(
                (1.0 / 2.0)**2 + (0.5 * 1.0 / 4.0)**2))

    def test_radd(self):
        result = self.data + 3.0
        for i in range(5):
            self.assertEqual(result.y[i], 5.0)
            self.assertEqual(result.dy[i], 0.5)

        result = 3.0 + self.data
        for i in range(5):
            self.assertEqual(result.y[i], 5.0)
            self.assertEqual(result.dy[i], 0.5)

    def test_rsub(self):
        result = self.data - 3.0
        for i in range(5):
            self.assertEqual(result.y[i], -1.0)
            self.assertEqual(result.dy[i], 0.5)

        result = 3.0 - self.data
        for i in range(5):
            self.assertEqual(result.y[i], 1.0)
            self.assertEqual(result.dy[i], 0.5)

    def test_rmul(self):
        result = self.data * 3.0
        for i in range(5):
            self.assertEqual(result.y[i], 6.0)
            self.assertEqual(result.dy[i], 1.5)

        result = 3.0 * self.data
        for i in range(5):
            self.assertEqual(result.y[i], 6.0)
            self.assertEqual(result.dy[i], 1.5)

    def test_rdiv(self):
        result = self.data / 4.0
        for i in range(5):
            self.assertEqual(result.y[i], 0.5)
            self.assertEqual(result.dy[i], 0.125)

        result = 6.0 / self.data
        for i in range(5):
            self.assertEqual(result.y[i], 3.0)
            self.assertEqual(result.dy[i], 6.0 * 0.5 / 4.0)


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
        self.data = Data2D(image=x_0, err_image=dx_0, qx_data=qx_0,
                           qy_data=qy_0, q_data=q_0, mask=mask_0,
                           dqx_data=dqx_0, dqy_data=dqy_0)

        y = np.ones(25)
        dy = np.ones(25)
        qx = np.arange(25)
        qy = np.arange(25)
        mask = np.zeros(25)
        q = np.sqrt(qx * qx + qy * qy)
        self.data2 = Data2D(image=y, err_image=dy, qx_data=qx, qy_data=qy,
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
        for i in range(25):
            self.assertEqual(result.data[i], 3.0)
            self.assertEqual(result.err_data[i], math.sqrt(0.5**2 + 1.0))

    def test_sub(self):
        result = self.data2 - self.data
        for i in range(25):
            self.assertEqual(result.data[i], -1.0)
            self.assertEqual(result.err_data[i], math.sqrt(0.5**2 + 1.0))

    def test_mul(self):
        result = self.data2 * self.data
        for i in range(25):
            self.assertEqual(result.data[i], 2.0)
            self.assertEqual(result.err_data[i], math.sqrt(
                (0.5 * 1.0)**2 + (1.0 * 2.0)**2))

    def test_div(self):
        result = self.data2 / self.data
        for i in range(25):
            self.assertEqual(result.data[i], 0.5)
            self.assertEqual(result.err_data[i], math.sqrt(
                (1.0 / 2.0)**2 + (0.5 * 1.0 / 4.0)**2))

    def test_radd(self):
        result = self.data + 3.0
        for i in range(25):
            self.assertEqual(result.data[i], 5.0)
            self.assertEqual(result.err_data[i], 0.5)

        result = 3.0 + self.data
        for i in range(25):
            self.assertEqual(result.data[i], 5.0)
            self.assertEqual(result.err_data[i], 0.5)

    def test_rsub(self):
        result = self.data - 3.0
        for i in range(25):
            self.assertEqual(result.data[i], -1.0)
            self.assertEqual(result.err_data[i], 0.5)

        result = 3.0 - self.data
        for i in range(25):
            self.assertEqual(result.data[i], 1.0)
            self.assertEqual(result.err_data[i], 0.5)

    def test_rmul(self):
        result = self.data * 3.0
        for i in range(25):
            self.assertEqual(result.data[i], 6.0)
            self.assertEqual(result.err_data[i], 1.5)

        result = 3.0 * self.data
        for i in range(25):
            self.assertEqual(result.data[i], 6.0)
            self.assertEqual(result.err_data[i], 1.5)

    def test_rdiv(self):
        result = self.data / 4.0
        for i in range(25):
            self.assertEqual(result.data[i], 0.5)
            self.assertEqual(result.err_data[i], 0.125)

        result = 6.0 / self.data
        for i in range(25):
            self.assertEqual(result.data[i], 3.0)
            self.assertEqual(result.err_data[i], 6.0 * 0.5 / 4.0)


class ExtraManip2DTests(unittest.TestCase):

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
        self.data = Data2D(image=x_0, err_image=dx_0, qx_data=qx_0,
                           qy_data=qy_0, q_data=q_0, mask=mask_0,
                           dqx_data=dqx_0, dqy_data=dqy_0)

        y = np.ones(25)
        dy = np.ones(25)
        qx = np.arange(25)
        qy = np.arange(25)
        mask = np.zeros(25)
        q = np.sqrt(qx * qx + qy * qy)
        self.data2 = Data2D(image=y, err_image=dy, qx_data=qx, qy_data=qy,
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
        for i in range(25):
            self.assertEqual(result.data[i], 3.0)
            self.assertEqual(result.err_data[i], math.sqrt(0.5**2 + 1.0))

    def test_sub(self):
        result = self.data2 - self.data
        for i in range(25):
            self.assertEqual(result.data[i], -1.0)
            self.assertEqual(result.err_data[i], math.sqrt(0.5**2 + 1.0))

    def test_mul(self):
        result = self.data2 * self.data
        for i in range(25):
            self.assertEqual(result.data[i], 2.0)
            self.assertEqual(result.err_data[i], math.sqrt(
                (0.5 * 1.0)**2 + (1.0 * 2.0)**2))

    def test_div(self):
        result = self.data2 / self.data
        for i in range(25):
            self.assertEqual(result.data[i], 0.5)
            self.assertEqual(result.err_data[i], math.sqrt(
                (1.0 / 2.0)**2 + (0.5 * 1.0 / 4.0)**2))

    def test_radd(self):
        result = self.data + 3.0
        for i in range(25):
            self.assertEqual(result.data[i], 5.0)
            self.assertEqual(result.err_data[i], 0.5)

        result = 3.0 + self.data
        for i in range(25):
            self.assertEqual(result.data[i], 5.0)
            self.assertEqual(result.err_data[i], 0.5)

    def test_rsub(self):
        result = self.data - 3.0
        for i in range(25):
            self.assertEqual(result.data[i], -1.0)
            self.assertEqual(result.err_data[i], 0.5)

        result = 3.0 - self.data
        for i in range(25):
            self.assertEqual(result.data[i], 1.0)
            self.assertEqual(result.err_data[i], 0.5)

    def test_rmul(self):
        result = self.data * 3.0
        for i in range(25):
            self.assertEqual(result.data[i], 6.0)
            self.assertEqual(result.err_data[i], 1.5)

        result = 3.0 * self.data
        for i in range(25):
            self.assertEqual(result.data[i], 6.0)
            self.assertEqual(result.err_data[i], 1.5)

    def test_rdiv(self):
        result = self.data / 4.0
        for i in range(25):
            self.assertEqual(result.data[i], 0.5)
            self.assertEqual(result.err_data[i], 0.125)

        result = 6.0 / self.data
        for i in range(25):
            self.assertEqual(result.data[i], 3.0)
            self.assertEqual(result.err_data[i], 6.0 * 0.5 / 4.0)


if __name__ == '__main__':
    unittest.main()
