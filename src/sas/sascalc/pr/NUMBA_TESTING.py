"""
Test driver code used to test/benchmark calc.py, will be removed.
"""
import sys
import math
import time
import copy
import os
import re
import logging
import time

import numpy as np
#from numpy import pi
import timeit
from functools import reduce

pi = np.float64(3.1416) #to pass tests
try:
    raise ImportError()
    from numba import njit
except ImportError:
    # identity decorator for njit which ignores type signature [untested]
    njit = lambda *args, **kw: (lambda x: x)

@njit('f8(f8[:], f8, u8)')
def test_method(x, y, z):
    res = 0.0

    for i in range(len(x)):
        res += x[i] * y * z

    return res

if(__name__ == "__main__"):
    x = np.arange(3000, dtype = np.float64)
    y = 6.7
    z = 5
    setup = '''
from __main__ import test_method
import numpy as np
x = np.arange(3000, dtype = np.float64)
y = 6.7
z = 5'''
    run = '''
test_method(x, y, z)'''

    results = timeit.repeat(setup = setup, stmt = run, repeat = 10, number = 1)
    print(results)
    print(test_method(x, y, z))
