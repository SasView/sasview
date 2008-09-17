"""
    
"""

"""
This software was developed by the University of Tennessee as part of the
Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
project funded by the US National Science Foundation. 

See the license text in license.txt

copyright 2008, University of Tennessee
"""
#TODO: copy the meta data from the 2D object to the resulting 1D object

from data_info import plottable_2D, Data1D
import math
import numpy

def get_q(dx, dy, det_dist, wavelength):
    """
        @param dx: x-distance from beam center [mm]
        @param dy: y-distance from beam center [mm]
        @return: q-value at the given position
    """
    # Distance from beam center in the plane of detector
    plane_dist = math.sqrt(dx*dx + dy*dy)
    # Half of the scattering angle
    theta      = 0.5*math.atan(plane_dist/det_dist)
    return (4.0*math.pi/wavelength)*math.sin(theta)
    


class Slabs:
    def __init__(self):
        pass
    
class Boxsum:
    pass

class CircularAverage(object):
    """
        Perform circular averaging on 2D data
        
        The data returned is the distribution of counts
        as a function of Q
    """
    def __init__(self, r_min=0.0, r_max=0.0, bin_width=0.001):
        # Minimum radius included in the average [A-1]
        self.r_min = r_min
        # Maximum radius included in the average [A-1]
        self.r_max = r_max
        # Bin width (step size) [A-1]
        self.bin_width = bin_width

    def __call__(self, data2D):
        """
            Perform circular averaging on the data
            
            @param data2D: Data2D object
            @return: Data1D object
        """
        if len(data2D.detector) != 1:
            raise RuntimeError, "Circular averaging: invalid number of detectors: %g" % len(data2D.detector)
        
        pixel_width = data2D.detector[0].pixel_size.x
        det_dist    = data2D.detector[0].distance
        wavelength  = data2D.source.wavelength
        center_x    = data2D.detector[0].beam_center.x/pixel_width
        center_y    = data2D.detector[0].beam_center.y/pixel_width
        
        # Find out the maximum Q range
        xwidth = numpy.size(data2D.data,1)*pixel_width
        dx_max = xwidth - data2D.detector[0].beam_center.x
        if xwidth-dx_max>dx_max:
            dx_max = xwidth-dx_max
            
        ywidth = numpy.size(data2D.data,0)*pixel_width
        dy_max = ywidth - data2D.detector[0].beam_center.y
        if ywidth-dy_max>dy_max:
            dy_max = ywidth-dy_max
        
        qmax = get_q(dx_max, dy_max, det_dist, wavelength)
        
        # Build array of Q intervals
        nbins = int(math.ceil((qmax-self.r_min)/self.bin_width))
        qbins = self.bin_width*numpy.arange(nbins)+self.r_min
        
        x  = numpy.zeros(nbins)
        y  = numpy.zeros(nbins)
        err_y = numpy.zeros(nbins)
        y_counts = numpy.zeros(nbins)
        
        for i in range(len(data2D.data)):
            dx = pixel_width*(i+0.5 - center_x)
            
            # Min and max x-value for the pixel
            minx = pixel_width*(i - center_x)
            maxx = pixel_width*(i+1.0 - center_x)
            
            for j in range(len(data2D.data)):
                dy = pixel_width*(j+0.5 - center_y)
            
                q_value = get_q(dx, dy, det_dist, wavelength)
            
                # Min and max y-value for the pixel
                miny = pixel_width*(j - center_y)
                maxy = pixel_width*(j+1.0 - center_y)
                
                # Calculate the q-value for each corner
                # q_[x min or max][y min or max]
                q_00 = get_q(minx, miny, det_dist, wavelength)
                q_01 = get_q(minx, maxy, det_dist, wavelength)
                q_10 = get_q(maxx, miny, det_dist, wavelength)
                q_11 = get_q(maxx, maxy, det_dist, wavelength)
                
                # Look for intercept between each side of the pixel
                # and the constant-q ring for qmax
                frac_max = get_pixel_fraction(self.r_max, q_00, q_01, q_10, q_11)
                
                # Look for intercept between each side of the pixel
                # and the constant-q ring for qmin
                frac_min = get_pixel_fraction(self.r_min, q_00, q_01, q_10, q_11)
                
                # We are interested in the region between qmin and qmax
                # therefore the fraction of the surface of the pixel
                # that we will use to calculate the number of counts to 
                # include is given by:
                frac = frac_max - frac_min

                i_q = int(math.ceil((q_value-self.r_min)/self.bin_width)) - 1
            
                x[i_q]          = q_value
                y[i_q]         += frac * data2D.data[j][i]
                if data2D.err_data == None or data2D.err_data[j][i]==0.0:
                    err_y[i_q] += frac * frac * math.fabs(data2D.data[j][i])
                else:
                    err_y[i_q] += frac * frac * data2D.err_data[j][i] * data2D.err_data[j][i]
                y_counts[i_q]  += frac
        
        # Average the sums
        for i in range(nbins):
            if y_counts[i]>0:
                err_y[i] = math.sqrt(err_y[i])/y_counts[i]
                y[i]     = y[i]/y_counts[i]
        
        return Data1D(x=x, y=y, dy=err_y)
    

class Ring(object):
    """
        Defines a ring on a 2D data set.
        The ring is defined by r_min, r_max, and
        the position of the center of the ring.
        
        The data returned is the distribution of counts
        around the ring as a function of phi.
        
    """
    
    def __init__(self, r_min=0, r_max=0, center_x=0, center_y=0):
        # Minimum radius
        self.r_min = r_min
        # Maximum radius
        self.r_max = r_max
        # Center of the ring in x
        self.center_x = center_x
        # Center of the ring in y
        self.center_y = center_y
        # Number of angular bins
        self.nbins_phi = 20
        
    def __call__(self, data2D):
        """
            Apply the ring to the data set.
            Returns the angular distribution for a given q range
            
            @param data2D: Data2D object
            @return: Data1D object
        """
        if data2D.__class__.__name__ not in ["Data2D", "plottable_2D"]:
            raise RuntimeError, "Ring averaging only take plottable_2D objects"
        
        data = data2D.data
        qmin = self.r_min
        qmax = self.r_max
        
        if len(data2D.detector) != 1:
            raise RuntimeError, "Ring averaging: invalid number of detectors: %g" % len(data2D.detector)
        pixel_width = data2D.detector[0].pixel_size.x
        det_dist = data2D.detector[0].distance
        wavelength = data2D.source.wavelength
        center_x = self.center_x/pixel_width
        center_y = self.center_y/pixel_width
        
        phi_bins   = numpy.zeros(self.nbins_phi)
        phi_counts = numpy.zeros(self.nbins_phi)
        phi_values = numpy.zeros(self.nbins_phi)
        phi_err    = numpy.zeros(self.nbins_phi)
        
        for i in range(len(data)):
            dx = pixel_width*(i+0.5 - center_x)
            
            # Min and max x-value for the pixel
            minx = pixel_width*(i - center_x)
            maxx = pixel_width*(i+1.0 - center_x)
            
            for j in range(len(data)):
                dy = pixel_width*(j+0.5 - center_y)
            
                q_value = get_q(dx, dy, det_dist, wavelength)
            
                # Min and max y-value for the pixel
                miny = pixel_width*(j - center_y)
                maxy = pixel_width*(j+1.0 - center_y)
                
                # Calculate the q-value for each corner
                # q_[x min or max][y min or max]
                q_00 = get_q(minx, miny, det_dist, wavelength)
                q_01 = get_q(minx, maxy, det_dist, wavelength)
                q_10 = get_q(maxx, miny, det_dist, wavelength)
                q_11 = get_q(maxx, maxy, det_dist, wavelength)
                
                # Look for intercept between each side of the pixel
                # and the constant-q ring for qmax
                frac_max = get_pixel_fraction(qmax, q_00, q_01, q_10, q_11)
                
                # Look for intercept between each side of the pixel
                # and the constant-q ring for qmin
                frac_min = get_pixel_fraction(qmin, q_00, q_01, q_10, q_11)
                
                # We are interested in the region between qmin and qmax
                # therefore the fraction of the surface of the pixel
                # that we will use to calculate the number of counts to 
                # include is given by:
                
                frac = frac_max - frac_min

                i_phi = int(math.ceil(self.nbins_phi*(math.atan2(dy, dx)+math.pi)/(2.0*math.pi)) - 1)
            
                phi_bins[i_phi] += frac * data[j][i]
                
                if data2D.err_data == None or data2D.err_data[j][i]==0.0:
                    phi_err[i_phi] += frac * frac * math.fabs(data2D.data[j][i])
                else:
                    phi_err[i_phi] += frac * frac * data2D.err_data[j][i] * data2D.err_data[j][i]
                phi_counts[i_phi] += frac
        
        for i in range(self.nbins_phi):
            phi_bins[i] = phi_bins[i] / phi_counts[i]
            phi_err[i] = math.sqrt(phi_err[i]) / phi_counts[i]
            phi_values[i] = 2.0*math.pi/self.nbins_phi*(1.0*i + 0.5)
            
        return Data1D(x=phi_values, y=phi_bins, dy=phi_err)
    
def get_pixel_fraction(qmax, q_00, q_01, q_10, q_11):
    """
        Returns the fraction of the pixel defined by
        the four corners (q_00, q_01, q_10, q_11) that 
        has q < qmax.
        
                q_01                q_11
        y=1         +--------------+
                    |              |
                    |              |
                    |              |
        y=0         +--------------+
                q_00                q_01
        
                    x=0            x=1
        
    """
    
    # y side for x = minx
    x_0 = get_intercept(qmax, q_00, q_01)
    # y side for x = maxx
    x_1 = get_intercept(qmax, q_10, q_11)
    
    # x side for y = miny
    y_0 = get_intercept(qmax, q_00, q_10)
    # x side for y = maxy
    y_1 = get_intercept(qmax, q_01, q_11)
    
    # surface fraction for a 1x1 pixel
    frac_max = 0
    
    if x_0 and x_1:
        frac_max = (x_0+x_1)/2.0
    
    elif y_0 and y_1:
        frac_max = (y_0+y_1)/2.0
    
    elif x_0 and y_0:
        if q_00 < q_10:
            frac_max = x_0*y_0/2.0
        else:
            frac_max = 1.0-x_0*y_0/2.0
    
    elif x_0 and y_1:
        if q_00 < q_10:
            frac_max = x_0*y_1/2.0
        else:
            frac_max = 1.0-x_0*y_1/2.0
    
    elif x_1 and y_0:
        if q_00 > q_10:
            frac_max = x_1*y_0/2.0
        else:
            frac_max = 1.0-x_1*y_0/2.0
    
    elif x_1 and y_1:
        if q_00 < q_10:
            frac_max = 1.0 - (1.0-x_1)*(1.0-y_1)/2.0
        else:
            frac_max = (1.0-x_1)*(1.0-y_1)/2.0
            
    # If we make it here, there is no intercept between
    # this pixel and the constant-q ring. We only need
    # to know if we have to include it or exclude it.
    elif (q_00+q_01+q_10+q_11)/4.0 < qmax:
        frac_max = 1.0
   
    return frac_max
             
def get_intercept(q, q_0, q_1):
    """
        Returns the fraction of the side at which the
        q-value intercept the pixel, None otherwise.
        The values returned is the fraction ON THE SIDE
        OF THE LOWEST Q.
        
        
        
                A        B    
         +-----------+--------+
         0                    1     <--- pixel size
         
        Q_0 -------- Q ----- Q_1    <--- equivalent Q range
        
        
        if Q_1 > Q_0, A is returned
        if Q_1 < Q_0, B is returned
        
        if Q is outside the range of [Q_0, Q_1], None is returned
         
    """
    if q_1 > q_0:
        if (q > q_0 and q <= q_1):
            return (q-q_0)/(q_1 - q_0)    
    else:
        if (q > q_1 and q <= q_0):
            return (q-q_1)/(q_0 - q_1)
    return None
    

class Sector:
    """
        Defines a sector region on a 2D data set.
        The sector is defined by r_min, r_max, phi_min, phi_max,
        and the position of the center of the ring. 
    """
    pass

if __name__ == "__main__": 

    from loader import Loader
    

    #d = Loader().load('test/MAR07232_rest.ASC')
    d = Loader().load('test/MP_New.sans')

    
    r = CircularAverage(r_min=.0, r_max=.075,bin_width=0.0003)
    o = r(d)
    for i in range(len(o.x)):
        print o.x[i], o.y[i], o.dy[i]
    
 
    