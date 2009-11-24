"""
    This module implements invariant and its related computations.
    @author: Gervaise B. Alina/UTK
"""

import math 
import numpy.linalg.lstsq

from DataLoader.data_info import Data1D as LoaderData1D
from DataLoader.qsmearing import smear_selection

INFINITY = 10
MINIMUM  = 1e-5
STEPS = 1000

class Functor:
    """
        compute f(x)
    """
    def __init__(self,data , function):
        """
            @param function :the function used for computing residuals
            @param Data: data used for computing residuals
        """
        self.function = function
        self.data  = data
        x_len = len(self.data.x) -1
        #fitting range 
        self.qmin =  self.data[0]    
        if self.qmin == 0:
            self.qmin = MINIMUM 
    
        self.qmax = self.data[x_len]
        #Unsmeared q range
        self._qmin_unsmeared = 0
        self._qmax_unsmeared = self.data[x_len]
        
        #bin for smear data
        self._first_unsmeared_bin = 0
        self._last_unsmeared_bin  = x_len
        
        # Identify the bin range for the unsmeared and smeared spaces
        self.idx = (self.x>=self.qmin) & (self.x <= self.qmax)
        self.idx_unsmeared = (self.x>=self._qmin_unsmeared) & (self.x <= self._qmax_unsmeared)
  
        #get the smear object of data
        self.smearer = smear_selection( self.data )
        self.func_name = "Residuals"
        
    def setFitRange(self):
        """ to set the fit range"""
        self.qmin =  self.data[0]    
        if self.qmin== 0:
            self.qmin= MINIMUM 
        
        x_len= len(self.data.x) -1
        self.qmax= self.data[x_len]
            
        # Determine the range needed in unsmeared-Q to cover
        # the smeared Q range
        self._qmin_unsmeared = self.qmin
        self._qmax_unsmeared = self.qmax    
        
        self._first_unsmeared_bin = 0
        self._last_unsmeared_bin  = len(self.data.x)-1
        
        if self.smearer!=None:
            self._first_unsmeared_bin, self._last_unsmeared_bin = self.smearer.get_bin_range(self.qmin, self.qmax)
            self._qmin_unsmeared = self.data.x[self._first_unsmeared_bin]
            self._qmax_unsmeared = self.data.x[self._last_unsmeared_bin]
            
        # Identify the bin range for the unsmeared and smeared spaces
        self.idx = (self.data.x>=self.qmin) & (self.data.x <= self.qmax)
        self.idx_unsmeared = (self.data.x>=self._qmin_unsmeared) & (self.data.x <= self._qmax_unsmeared)
  
        
    def _get_residuals(self, params):
        """
            Compute residuals
            @return res: numpy array of float of size.self.data.x
        """
         # Compute theory data f(x)
        fx = numpy.zeros(len(self.data.x))
        fx[self.idx_unsmeared] = self.funtion(self.data.x[self.idx_unsmeared])
       
        ## Smear theory data
        if self.smearer is not None:
            fx = self.smearer(fx, self._first_unsmeared_bin, self._last_unsmeared_bin)
       
        ## Sanity check
        if numpy.size(self.data.dy)!= numpy.size(fx):
            raise RuntimeError, "Residuals: invalid error array %d <> %d" % (numpy.shape(self.data.dy),
                                                                              numpy.size(fx))
                                                                              
        return (self.data.y[self.idx]-fx[self.idx])/self.data.dy[self.idx]
    
    
    def __call__(self,params):
        """
            Compute residuals
            @param params: value of parameters to fit
        """
        return self._get_residuals(params)
    
class InvariantCalculator(object):
    """
        Compute invariant if data is given.
        Can provide volume fraction and surface area if the user provides
        Porod constant  and contrast values.
        @precondition:  the user must send a data of type DataLoader.Data1D
                        the user provide background and scale values.
                        
        @note: Some computations depends on each others. 
    """
    def __init__(self, data, background=0, scale=1 ):
        """
            Initialize variables
            @param data: data must be of type DataLoader.Data1D
            @param contrast: contrast value of type float
            @param pConst: Porod Constant of type float
        """
        self.data = None
        self.qstar = None
        self.background = background
        self.scale = scale
        
    def _get_guinier(self, x, scale=1, radius=0.1):
        """
            Compute a F(x) = scale* e-((radius*x)**2/3).
            @param x: a vector of q values or one q value
            @param scale: the scale value
            @param radius: the guinier radius value
            @return F(x)
        """
        
    def _get_power_law(self, x, scale=1, power=4):
        """
            F(x) = scale* (x)^(-power)
                when power= 4. the model is porod 
                else power_law
            The model has three parameters: 
            @param power: power of the function
            @param scale : scale factor value
            @param F()
        """
        
    def _get_data(self):
        """
            @note this function must be call before computing any type
             of invariant
            @return data= self.scale *self.data - self.background
        """
        
    def _fit(self, function, params=[]):
        """
            fit data with function using 
            data= self._get_data()
            fx= Functor(data , function)
            y = data.y
            out, cov_x = linalg.lstsq(y,fx)

        
            @param function: the function to use during the fit
            @param params: the list of parameters values to use during the fit
            
        """
        
    def _get_qstar(self):
        """
            Compute the invariant of the local copy of data.
            Implementation:
                data = self._get_data()
                if slit smear:
                    return self._get_qstar_smear(data)
                else:
                    return self._get_qstar_unsmear(data)
            @return q_star: invariant of the data within data's q range
        """
    def _get_qstar_unsmear(self, data):
        """
            Compute invariant for pinhole data.
            This invariant is given by:
        
                q_star = x0**2 *y0 *dx0 +x1**2 *y1 *dx1 
                            + ..+ xn**2 *yn *dxn 
            where n= infinity
            dxi = 1/2*(xi+1 - xi) + (xi - xi-1)
            dx0 = (x1 - x0)/2
            dxn = xn - xn-1
            @param data: data of type Data1D
            @return q_star: invariant value for pinhole data.
        """
        
    def _get_qstar_smear(self, data):
        """
            Compute invariant for slit-smeared data.
            This invariant is given by:
                q_star = x0*dxl *y0*dx0 + x1*dxl *y1 *dx1 
                            + ..+ xn*dxl *yn *dxn 
            where n= infinity
            dxi = 1/2*(xi+1 - xi) + (xi - xi-1)
            dx0 = x0+ (x1 - x0)/2
            dxn = xn - xn-1
            dxl: slit smear value
            @param data: data of type Data1D
            @return q_star: invariant value for slit smeared data.
        """
        
    def _get_qstar_unsmear_uncertainty(self, data):
        """
            Compute invariant uncertainty with with pinhole data.
            This uncertainty is given as follow:
               dq_star = math.sqrt[(x0**2*(dy0)*dx0)**2 +
                    (x1**2 *(dy1)*dx1)**2 + ..+ (xn**2 *(dyn)*dxn)**2 ]
            where n = infinity
            dxi = 1/2*(xi+1 - xi) + (xi - xi-1)
            dx0 = x0+ (x1 - x0)/2
            dxn = xn - xn-1
            dyn: error on dy
            @param data: data of type Data1D where the scale is applied
                        and the background is subtracted.
            note: if data doesn't contain dy assume dy= math.sqrt(data.y)
        """
    def _get_qstar_smear_uncertainty(self, data):
        """
            Compute invariant uncertainty with slit smeared data.
            This uncertainty is given as follow:
                dq_star = x0*dxl *dy0 *dx0 + x1*dxl *dy1 *dx1 
                            + ..+ xn*dxl *dyn *dxn 
            where n= infinity
            dxi = 1/2*(xi+1 - xi) + (xi - xi-1)
            dx0 = x0+ (x1 - x0)/2
            dxn = xn - xn-1
            dxl: slit smearing value
            dyn : error on dy
            @param data: data of type Data1D where the scale is applied
                        and the background is subtracted.
          
            note: if data doesn't contain dy assume dy= math.sqrt(data.y)
        """
    def _get_qstar_total(self):
        """
            Compute the total invariant whether or not it is extrapolated.
            Implementation:
                qstar = self._get_qstar() + self._get_qstar_min()
                        + self._get_qstar_max()
            @return q_star: invariant total value
        """
        
    def set_background(self, background=0):
        """
            Set the value of the background
            @param background : the value uses to set the local background
        """
        
    def set_scale(self, scale=1):
        """
            Set the value of the scale
            @param scale: the value to set the scale.
        """
        
    def get_surface(self,contrast, porod_const):
        """
            Compute the surface of the data.
            
            Implementation:
                V= self.get_volume_fraction(contrast)
        
              Compute the surface given by:
                surface = (2*pi *V(1- V)*porod_const)/ q_star
                
            @param contrast: contrast value to compute the volume
            @param porod_const: Porod constant to compute the surface 
            @return: specific surface
        """
       
    def get_volume_fraction(self, contrast):
        """
            Compute volume fraction is deduced as follow:
            
            q_star = 2*(pi*contrast)**2* volume( 1- volume)
            for k = 10^(8)*q_star/(2*(pi*|contrast|)**2)
            we get 2 values of volume:
                 volume1 = (1- sqrt(1- 4*k))/2
                 volume2 = (1+ sqrt(1- 4*k))/2
           
            q_star: the invariant value included extrapolation is applied
                         unit  1/A^(3)*1/cm
                    q_star = self._get_qstar_total()
                    
            the result returned will be 0<= volume <= 1
            
            @param contrast: contrast value provides by the user of type float.
                     contrast unit is 1/A^(2)= 10^(16)cm^(2)
            @return: volume fraction
            @note: volume fraction must have no unit
        """
        
    def get_qstar_min(self, npts=0, power_law=False):
        """
            Compute the invariant for extrapolated data at low q range.
            
            Implementation:
                data = self.get_extra_data_low( npts, power_law)
                return self._get_qstar()
                
            @param npts: data the number of points of the local data to consider
                when fitting and created extrapolated data.
                
            @return q_star: the invariant for data extrapolated at low q.
        """
        
    def get_qstar_max(self, npts=0):
        """
            Compute the invariant for extrapolated data at high q range.
            
            Implementation:
                data = self.get_extra_data_high( npts)
                return self._get_qstar()
                
            @param npts: data the number of points of the local data to consider
                when fitting and created extrapolated data.
            @return q_star: the invariant for data extrapolated at high q.
        """
        
    def get_extra_data_low(self, data, npts, power_law=False):
        """
            This method creates a new_data from the invariant calculator  data
            It takes npts first points of  data , 
            fits them with a given model
            then uses
            the new parameters resulting from the fit to create a new data.
            the new data first point is MINIMUM .
            the last point of the new data is the first point of the local data.
            the number of q points of this data is STEPS.
            
            @param power_law: a flag to allow the function used for fitting
                to switch between a guinier or a power_law model.
                if set to True: the power_law will be used for fitting
                else: the guinier will be used.
            @param data : the data to used to extrapolated
                        assume data is scale and the background is removed
            @param npts: the number of last points of data to fit.
            
            @return new_data: a new data of type Data1D
        """
    def get_extra_data_high(self, data, npts):
        """
            This method creates a new_data from the invariant calculator data
            It takes npts last points of data , 
            fits them with a given model
            (for this function only power_law will be use), then uses
            the new parameters resulting from the fit to create a new_data.
            the new_data first point is the last point of  data.
            the last point of the new data is INFINITY.
            the number of q points of this data is STEPS.
            @param data : the data to used to extrapolated
                        assume data is scale and the background is removed
            @param npts: the number of last points of  data to fit.
            
            @return new_data: a new data of type Data1D
        """
    def get_qstar_uncertainty(self):
        """
            Compute the invariant uncertainty.
            This uncertainty computation depends on whether or not the data is
            smeared.
            @return dq_star:
                data = self._get_data()
                if slit smear:
                    return self._get_qstar_smear_uncertainty(data)
                else:
                    return self._get_qstar_unsmear_uncertainty(data) 
        """
        
    def get_volume_fraction_uncertainty(self, contrast):
        """
            Compute uncertainty on volume value.
            This uncertainty is given by the following equation:
            dV = 0.5 * (4*k* dq_star) /(2* math.sqrt(1-k* q_star))
                                 
            for k = 10^(8)*q_star/(2*(pi*|contrast|)**2)
            q_star: the invariant value including extrapolated value if existing
            dq_star: the invariant uncertainty
            dV: the volume uncertainty
            @param contrast: contrast value 
        """
        
    def get_surface_uncertainty(self, contrast, porod_const):
        """
            Compute uncertainty of the surface value.
            this uncertainty is given as follow:
            
            dS = porod_const *2*pi[( dV -2*V*dV)/q_star
                 + dq_star(v-v**2)
                 
            q_star: the invariant value including extrapolated value if existing
            dq_star: the invariant uncertainty
            V: the volume fraction value
            dV: the volume uncertainty
            
            @param contrast: contrast value
            @param porod_const: porod constant value 
            @return dS: the surface uncertainty
        """
        
    