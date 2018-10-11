"""
    Unit tests for DistExplorer class
"""

import sys
import os.path
import unittest, math, numpy
from sas.sascalc.pr.invertor import Invertor
from sas.sascalc.pr.distance_explorer import DistExplorer

def find(filename):
    return os.path.join(os.path.dirname(__file__), filename)


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


# Note: duplicated from utest_invertor because the following failed:
#from .utest_invertor import load
def load(path = "sphere_60_q0_2.txt"):
    import numpy as np
    import math
    import sys
    # Read the data from the data file
    data_x   = np.zeros(0)
    data_y   = np.zeros(0)
    data_err = np.zeros(0)
    scale    = None
    if path is not None:
        input_f = open(path,'r')
        buff    = input_f.read()
        lines   = buff.split('\n')
        for line in lines:
            try:
                toks = line.split()
                x = float(toks[0])
                y = float(toks[1])
                if len(toks)>2:
                    err = float(toks[2])
                else:
                    if scale==None:
                        scale = 0.15*math.sqrt(y)
                    err = scale*math.sqrt(y)
                data_x = np.append(data_x, x)
                data_y = np.append(data_y, y)
                data_err = np.append(data_err, err)
            except:
                pass

    return data_x, data_y, data_err
        
if __name__ == '__main__':
    unittest.main()
