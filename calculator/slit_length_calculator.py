"""
This software was developed by the University of Tennessee as part of the
Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
project funded by the US National Science Foundation. 

See the license text in license.txt

copyright 2008, 2009, University of Tennessee
"""
from numpy import *

class SlitlengthCalculator(object):
    """
        compute slit length from SAXSess beam profile (1st col. Q , 2nd col. I , and 3rd col. dI.: don't need the 3rd)
        @object: data where are data.y and data.x
    """
    def __init__(self):
        
        # x data
        self.x = None
        # y data
        self.y = None
        #default slit length
        self.slit_length = 0.0
        
        # The unit is unknown from SAXSess profile: 
        # It seems 1/nm but it could be not fixed, 
        # so users should be notified to determine the unit by themselves.
        self.slit_length_unit = "unknown"
    
    def set_data(self, x=None, y=None):
        """
            set data
            @ Param x, y: x array and y array
        """
        self.x = x
        self.y = y
        
        
    def calculate_slit_length(self):
        """
            Calculate slit length using 10 max point
            ToDo: Near future, it should be re-factored in better method.
        """
        # None data do nothing
        if self.y == None or self.x == None:
            return
        
        # set local variable
        y = self.y
        x = self.x

        # find max y
        max_y = y.max()
        
        # initial values 
        y_sum = 0.0
        y_max = 0.0
        ind = 0.0
        
        # sum 10 or more y values until getting max_y, 
        while (True):
            if ind >= 10 and y_max == max_y:
                break
            y_sum = y_sum + y[ind]
            if y[ind] > y_max: y_max = y[ind]
            ind += 1
     
        # find the average value/2 of the top values  
        y_half = y_sum/(2.0*ind)
        
        # defaults
        y_half_d = 0.0
        ind = 0.0
        # find indices where it crosses y = y_half.
        while (True):
            ind += 1                # no need to check when ind == 0
            y_half_d = y[ind]       # y value and ind just after passed the spot of the half height 
            if y[ind] < y_half: break
   
        y_half_u = y[ind-1]         # y value and ind just before passed the spot of the half height
        
        # get corresponding x values
        x_half_d = x[ind]
        x_half_u = x[ind-1] 
        
        # calculate x at y = y_half using linear interpolation
        if y_half_u == y_half_d:
            x_half = (x_half_d + x_half_u)/2.0
        else:
            x_half = (x_half_u * (y_half - y_half_d) + x_half_d*(y_half_u-y_half))/(y_half_u - y_half_d)
        
        # multiply by 2 due to the beam profile is for half beam
        slit_length = 2.0 * x_half
        
        # set slit_length
        self.slit_length = slit_length
   
    def get_slit_length(self): 
        """
            Calculate and return the slit length
        """
        self.calculate_slit_length()
        return self.slit_length
        
    def get_slit_length_unit(self): 
        """
            return the slit length unit
        """
        return self.slit_length_unit
