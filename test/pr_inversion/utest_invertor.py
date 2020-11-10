"""
    Unit tests for Invertor class
"""
# Disable "missing docstring" complaint
# pylint: disable-msg=C0111
# Disable "too many methods" complaint
# pylint: disable-msg=R0904
from __future__ import print_function

import os
import os.path
import unittest
import math
import warnings

import numpy as np

from sas.sascalc.pr.invertor import Invertor


def find(filename):
    return os.path.join(os.path.dirname(__file__), 'data', filename)

class TestFiguresOfMerit(unittest.TestCase):
    def setUp(self):
        self.invertor = Invertor()
        self.invertor.d_max = 100.0

        # Test array
        self.ntest = 5
        self.x_in = np.arange(1, self.ntest+1, dtype='d')

        x, y, err = load(find("sphere_80.txt"))

        # Choose the right d_max...
        self.invertor.d_max = 160.0
        # Set a small alpha
        self.invertor.alpha = .0007
        # Set data
        self.invertor.x   = x
        self.invertor.y   = y
        self.invertor.err = err
        # Perform inversion
        #out, cov = self.invertor.invert(10)

        self.out, self.cov = self.invertor.lstsq(10)

    def test_positive(self):
        """
            Test whether P(r) is positive
        """
        self.assertAlmostEqual(self.invertor.get_positive(self.out), 1)

    def test_positive_err(self):
        """
            Test whether P(r) is at least 1 sigma greater than zero
            for all r-values
        """
        self.assertTrue(self.invertor.get_pos_err(self.out, self.cov)>0.9)

class TestBasicComponent(unittest.TestCase):
    def setUp(self):
        self.invertor = Invertor()
        self.invertor.d_max = 100.0

        # Test array
        self.ntest = 5
        self.x_in = np.arange(1, self.ntest+1, dtype='d')

    def test_est_bck_flag(self):
        """
            Tests the est_bck flag operations
        """
        self.assertEqual(self.invertor.est_bck, False)
        self.invertor.est_bck = True
        self.assertEqual(self.invertor.est_bck, True)
        def doit_float():
            self.invertor.est_bck = 2.0
        def doit_str():
            self.invertor.est_bck = 'a'

        self.assertRaises(ValueError, doit_float)
        self.assertRaises(ValueError, doit_str)

    def testset_dmax(self):
        """
            Set and read d_max
        """
        value = 15.0
        self.invertor.d_max = value
        self.assertEqual(self.invertor.d_max, value)

    def testset_alpha(self):
        """
            Set and read alpha
        """
        value = 15.0
        self.invertor.alpha = value
        self.assertEqual(self.invertor.alpha, value)

    def testset_x_1(self):
        """
            Setting and reading the x array the hard way
        """
        # Set x
        self.invertor.x = self.x_in

        # Read it back
        npts = self.invertor.get_nx()
        x_out = np.ones(npts)

        self.invertor.get_x(x_out)

        for i in range(self.ntest):
            self.assertEqual(self.x_in[i], x_out[i])

    def testset_x_2(self):
        """
            Setting and reading the x array the easy way
        """
        # Set x
        self.invertor.x = self.x_in

        # Read it back
        x_out = self.invertor.x

        for i in range(self.ntest):
            self.assertEqual(self.x_in[i], x_out[i])

    def testset_y(self):
        """
            Setting and reading the y array the easy way
        """
        # Set y
        self.invertor.y = self.x_in

        # Read it back
        y_out = self.invertor.y

        for i in range(self.ntest):
            self.assertEqual(self.x_in[i], y_out[i])

    def testset_err(self):
        """
            Setting and reading the err array the easy way
        """
        # Set err
        self.invertor.err = self.x_in

        # Read it back
        err_out = self.invertor.err

        for i in range(self.ntest):
            self.assertEqual(self.x_in[i], err_out[i])

    def test_iq(self):
        """
            Test iq calculation
        """
        q = 0.11
        v1 = (8.0*math.pi**2/q
              * self.invertor.d_max
              * math.sin(q*self.invertor.d_max)
              / (math.pi**2 - (q*self.invertor.d_max)**2))

        pars = np.ones(1)
        self.assertAlmostEqual(self.invertor.iq(pars, q), v1, 2)

    def test_pr(self):
        """
            Test pr calculation
        """
        r = 10.0
        v1 = 2.0*r*math.sin(math.pi*r/self.invertor.d_max)
        pars = np.ones(1)
        self.assertAlmostEqual(self.invertor.pr(pars, r), v1, 2)

    def test_getsetters(self):
        self.invertor.new_data = 1.0
        self.assertEqual(self.invertor.new_data, 1.0)
        self.assertEqual(self.invertor.test_no_data, None)

    def test_slitsettings(self):
        self.invertor.slit_width = 1.0
        self.assertEqual(self.invertor.slit_width, 1.0)
        self.invertor.slit_height = 2.0
        self.assertEqual(self.invertor.slit_height, 2.0)

    def test_inversion(self):
        """
            Test an inversion for which we know the answer
        """
        x, y, err = load(find("sphere_80.txt"))

        # Choose the right d_max...
        self.invertor.d_max = 160.0
        # Set a small alpha
        self.invertor.alpha = 1e-7
        # Set data
        self.invertor.x = x
        self.invertor.y = y
        self.invertor.err = err
        # Perform inversion
        out, cov = self.invertor.invert_optimize(10)
        #out, cov = self.invertor.invert(10)
        # This is a very specific case
        # We should make sure it always passes
        self.assertTrue(self.invertor.chi2/len(x) < 200.00)

        # Check the computed P(r) with the theory
        # for shpere of radius 80
        x = np.arange(0.01, self.invertor.d_max, self.invertor.d_max/51.0)
        y = np.zeros(len(x))
        dy = np.zeros(len(x))
        y_true = np.zeros(len(x))

        total = 0.0
        total_true = 0.0
        for i, xi in enumerate(x):
            #y[i] = self.invertor.pr(out, xi)
            (y[i], dy[i]) = self.invertor.pr_err(out, cov, xi)
            total += y[i]
            if xi < 80.0:
                y_true[i] = pr_theory(xi, 80.0)
            else:
                y_true[i] = 0
            total_true += y_true[i]

        y = y/total*self.invertor.d_max/len(x)
        dy = dy/total*self.invertor.d_max/len(x)
        y_true = y_true/total_true*self.invertor.d_max/len(x)

        chi2 = np.sum(((y-y_true)/dy)**2)

        try:
            self.assertTrue(chi2/51.0 < 10.0)
        except Exception:
            print("chi2 =", chi2/51.0)
            raise

    def test_lstsq(self):
        """
            Test an inversion for which we know the answer
        """
        x, y, err = load(find("sphere_80.txt"))

        # Choose the right d_max...
        self.invertor.d_max = 160.0
        # Set a small alpha
        self.invertor.alpha = .005
        # Set data
        self.invertor.x = x
        self.invertor.y = y
        self.invertor.err = err
        # Perform inversion
        #out, cov = self.invertor.invert(10)

        out, cov = self.invertor.lstsq(10)

        # This is a very specific case
        # We should make sure it always passes
        try:
            self.assertTrue(self.invertor.chi2/len(x) < 200.00)
        except Exception:
            print("Chi2(I(q)) =", self.invertor.chi2/len(x))
            raise

        # Check the computed P(r) with the theory
        # for shpere of radius 80
        x = np.arange(0.01, self.invertor.d_max, self.invertor.d_max/51.0)
        y = np.zeros(len(x))
        dy = np.zeros(len(x))
        y_true = np.zeros(len(x))

        total = 0.0
        total_true = 0.0
        for i, xi in enumerate(x):
            #y[i] = self.invertor.pr(out, xi)
            (y[i], dy[i]) = self.invertor.pr_err(out, cov, xi)
            total += y[i]
            if xi < 80.0:
                y_true[i] = pr_theory(xi, 80.0)
            else:
                y_true[i] = 0
            total_true += y_true[i]

        y = y/total*self.invertor.d_max/len(x)
        dy = dy/total*self.invertor.d_max/len(x)
        y_true = y_true/total_true*self.invertor.d_max/len(x)

        chi2 = np.sum(((y-y_true)/dy)**2)

        try:
            self.assertTrue(chi2/51.0 < 50.0)
        except Exception:
            print("chi2(P(r)) =", chi2/51.0)
            raise

        # Test the number of peaks
        self.assertEqual(self.invertor.get_peaks(out), 1)

    def test_q_zero(self):
        """
            Test error condition where a point has q=0
        """
        x, y, err = load(find("sphere_80.txt"))
        x[0] = 0.0

        # Choose the right d_max...
        self.invertor.d_max = 160.0
        # Set a small alpha
        self.invertor.alpha = 1e-7
        # Set data
        def doit():
            self.invertor.x = x
        self.assertRaises(ValueError, doit)

    def test_q_neg(self):
        """
            Test error condition where a point has q<0
        """
        x, y, err = load(find("sphere_80.txt"))
        x[0] = -0.2

        # Choose the right d_max...
        self.invertor.d_max = 160.0
        # Set a small alpha
        self.invertor.alpha = 1e-7
        # Set data
        self.invertor.x = x
        self.invertor.y = y
        self.invertor.err = err
        # Perform inversion
        out, cov = self.invertor.invert(4)

        try:
            self.assertTrue(self.invertor.chi2 > 0)
        except Exception:
            print("Chi2 =", self.invertor.chi2)
            raise

    def test_Iq_zero(self):
        """
            Test error condition where a point has q<0
        """
        x, y, err = load(find("sphere_80.txt"))
        y[0] = 0.0

        # Choose the right d_max...
        self.invertor.d_max = 160.0
        # Set a small alpha
        self.invertor.alpha = 1e-7
        # Set data
        self.invertor.x = x
        self.invertor.y = y
        self.invertor.err = err
        # Perform inversion
        out, cov = self.invertor.invert(4)

        try:
            self.assertTrue(self.invertor.chi2 > 0)
        except Exception:
            print("Chi2 =", self.invertor.chi2)
            raise

    def no_test_time(self):
        x, y, err = load(find("sphere_80.txt"))

        # Choose the right d_max...
        self.invertor.d_max = 160.0
        # Set a small alpha
        self.invertor.alpha = 1e-7
        # Set data
        self.invertor.x = x
        self.invertor.y = y
        self.invertor.err = err

        # time scales like nfunc**2
        # on a Lenovo Intel Core 2 CPU T7400 @ 2.16GHz,
        # I get time/(nfunc)**2 = 0.022 sec

        out, cov = self.invertor.invert(15)
        t16 = self.invertor.elapsed

        out, cov = self.invertor.invert(30)
        t30 = self.invertor.elapsed

        t30s = t30/30.0**2
        self.assertTrue((t30s-t16/16.0**2)/t30s < 1.2)

    def test_clone(self):
        self.invertor.x = self.x_in
        clone = self.invertor.clone()

        for i in range(len(self.x_in)):
            self.assertEqual(self.x_in[i], clone.x[i])

    def test_save(self):
        x, y, err = load(find("sphere_80.txt"))

        # Choose the right d_max...
        self.invertor.d_max = 160.0
        # Set a small alpha
        self.invertor.alpha = .0007
        # Set data
        self.invertor.x = x
        self.invertor.y = y
        self.invertor.err = err
        # Perform inversion

        out, cov = self.invertor.lstsq(10)

        # Save
        f_name = "test_output.txt"
        self.invertor.to_file(f_name)

        # Load
        self.invertor.from_file(f_name)
        self.assertEqual(self.invertor.d_max, 160.0)
        self.assertEqual(self.invertor.alpha, 0.0007)
        self.assertEqual(self.invertor.chi2, 836.797)
        self.assertAlmostEqual(self.invertor.pr(self.invertor.out, 10.0),
                               903.30597721, 4)
        if os.path.isfile(f_name):
            os.remove(f_name)

    def test_qmin(self):
        self.invertor.q_min = 1.0
        self.assertEqual(self.invertor.q_min, 1.0)

        self.invertor.q_min = None
        self.assertEqual(self.invertor.q_min, None)


    def test_qmax(self):
        self.invertor.q_max = 1.0
        self.assertEqual(self.invertor.q_max, 1.0)

        self.invertor.q_max = None
        self.assertEqual(self.invertor.q_max, None)


class TestErrorConditions(unittest.TestCase):
    def setUp(self):
        self.invertor = Invertor()
        self.invertor.d_max = 100.0

        # Test array
        self.ntest = 5
        self.x_in = np.arange(1, self.ntest+1, dtype='d')

    def test_negative_errs(self):
        """
            Test an inversion for which we know the answer
        """
        x, y, err = load(find("data_error_1.txt"))

        # Choose the right d_max...
        self.invertor.d_max = 160.0
        # Set a small alpha
        self.invertor.alpha = .0007
        # Set data
        self.invertor.x = x
        self.invertor.y = y
        self.invertor.err = err
        # Perform inversion

        out, cov = self.invertor.lstsq(10)

    def test_zero_errs(self):
        """
            Have zero as an error should raise an exception
        """
        x, y, err = load(find("data_error_2.txt"))

        # Set data
        self.invertor.x = x
        self.invertor.y = y
        self.invertor.err = err
        # Perform inversion
        self.assertRaises(RuntimeError, self.invertor.invert, 10)

    def test_invalid(self):
        """
            Test an inversion for which we know the answer
        """
        x, y, err = load(find("data_error_1.txt"))

        # Set data
        self.invertor.x = x
        self.invertor.y = y
        err = np.zeros(len(x)-1)
        self.invertor.err = err
        # Perform inversion
        self.assertRaises(RuntimeError, self.invertor.invert, 10)

    def test_zero_q(self):
        """
            One of the q-values is zero.
            An exception should be raised.
        """
        x, y, err = load(find("data_error_3.txt"))

        # Set data
        self.assertRaises(ValueError, self.invertor.__setattr__, 'x', x)

    def test_zero_Iq(self):
        """
            One of the I(q) points has a value of zero
            Should not complain or crash.
        """
        x, y, err = load(find("data_error_4.txt"))

        # Set data
        self.invertor.x = x
        self.invertor.y = y
        self.invertor.err = err
        # Perform inversion
        out, cov = self.invertor.lstsq(10)

    def test_negative_q(self):
        """
            One q value is negative.
            Makes not sense, but should not complain or crash.
        """
        x, y, err = load(find("data_error_5.txt"))

        # Set data
        self.invertor.x = x
        self.invertor.y = y
        self.invertor.err = err
        # Perform inversion
        out, cov = self.invertor.lstsq(10)

    def test_negative_Iq(self):
        """
            One I(q) value is negative.
            Makes not sense, but should not complain or crash.
        """
        x, y, err = load(find("data_error_6.txt"))

        # Set data
        self.invertor.x = x
        self.invertor.y = y
        self.invertor.err = err
        # Perform inversion
        out, cov = self.invertor.lstsq(10)

    def test_nodata(self):
        """
             No data was loaded. Should not complain.
        """
        out, cov = self.invertor.lstsq(10)


def pr_theory(r, R):
    """
       P(r) for a sphere
    """
    if r <= 2*R:
        return 12.0 * ((0.5*r/R)**2) * ((1.0-0.5*r/R)**2) * (2.0 + 0.5*r/R)
    else:
        return 0.0


def load(path = find("sphere_60_q0_2.txt")):
    # Read the data from the data file
    if path is None:
        raise TypeError("expected filename to load")
    data = []
    scale = None
    with open(path, 'r') as input_f:
        for line in input_f:
            try:
                toks = line.split()
                x = float(toks[0])
                y = float(toks[1])
                if len(toks) > 2:
                    err = float(toks[2])
                else:
                    if scale is None:
                        scale = 0.15*math.sqrt(y)
                    err = scale*math.sqrt(y)
                data.append((x, y, err))
            except Exception:
                # TODO: doesn't handle column headers:  <X> <Y> <dY>
                #warnings.warn("Bad in in %r: %s"%(path, line))
                pass

    data_x, data_y, data_err = (np.asarray(v) for v in zip(*data))
    return data_x, data_y, data_err


if __name__ == '__main__':
    unittest.main(testRunner=unittest.TextTestRunner(verbosity=2))
