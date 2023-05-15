import numpy as np


def sld(r, theta, phi):
    inside = r + 20*np.sin(6*theta)*np.cos(3*phi) < 50
    out = np.zeros_like(r)
    out[inside] = 1.0
    return out


default_text = '''""" Default text goes here...

should probably define a simple function
"""

def sld(x,y,z):
    """ A cube with 100Ang side length"""

    inside = (np.abs(x) < 50) & (np.abs(y) < 50) & (np.abs(z) < 50)

    out = np.zeros_like(x)

    out[inside] = 1

    return out

'''