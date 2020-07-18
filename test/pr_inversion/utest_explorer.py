"""
    Unit tests for DistExplorer class
"""

import sys
import os.path
import unittest, math, numpy
from sas.sascalc.pr.invertor import Invertor
from sas.sascalc.pr.distance_explorer import DistExplorer

try:
    from utest_invertor import load
except ImportError:
    from .utest_invertor import load

def find(filename):
    return os.path.join(os.path.dirname(__file__), 'data', filename)


class TestExplorer(unittest.TestCase):
            
    def setUp(self):
        self.invertor = Invertor()
        x, y, err = load(find('sphere_80.txt'))
        
        # Choose the right d_max...
        self.invertor.d_max = 160.0
        # Set a small alpha
        self.invertor.alpha = .0007
        # Set data
        self.invertor.x   = x
        self.invertor.y   = y
        self.invertor.err = err        
        self.invertor.nfunc = 15
        
        self.explo = DistExplorer(self.invertor)
        
    def test_exploration(self):
        results = self.explo(120, 200, 25)
        self.assertEqual(len(results.errors), 0)
        self.assertEqual(len(results.chi2), 25)

if __name__ == '__main__':
    unittest.main()
