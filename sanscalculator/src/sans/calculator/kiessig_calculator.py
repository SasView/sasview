"""
This module is a small tool to allow user to quickly
determine the size value in real space  from the
fringe width in q space.
"""
from math import pi, fabs
_DQ_DEFAULT = 0.05


class KiessigThicknessCalculator(object):
    """
    compute thickness from the fringe width of data
    """
    def __init__(self):
        
        # dq value
        self.deltaq = _DQ_DEFAULT
        # thickenss value
        self.thickness = None
        # unit of the thickness
        self.thickness_unit = 'A'
        
    def set_deltaq(self, dq=None):
        """
        Receive deltaQ value
        
        :param dq: q fringe width in 1/A unit
        """
        # set dq
        self.deltaq = dq
        
    def get_deltaq(self):
        """
        return deltaQ value in 1/A unit
        """
        # return dq
        return self.deltaq

    def compute_thickness(self):
        """
        Calculate thickness.
        
        :return: the thickness.
        """
        # check if it is float
        try:
            dq = float(self.deltaq)
        except:
            return None
        # check if delta_q is zero
        if dq == 0.0 or dq == None:
            return None
        else:
            # calculate thickness
            thickness = 2*pi/fabs(dq)
            # return thickness value
            return thickness
  
    def get_thickness_unit(self):
        """
        :return: the thickness unit.
        """
        # unit of thickness
        return self.thickness_unit
