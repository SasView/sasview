"""
    Unit tests for DistExplorer class
"""

import os.path
import unittest
# TODO: This import is broken. It needs to be rewritten if this test is to be renabled.
# from sas.sascalc.pr.invertor import Invertor
import pytest
from sas.sascalc.pr.distance_explorer import DistExplorer

pytest.skip(reason="Refactored invertor doesn't support this test", allow_module_level=True)

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
