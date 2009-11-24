"""
    This module implements invariant and its related computations.
    @author: Gervaise B. Alina/UTK
"""

import math 
import numpy.linalg.lstsq

from DataLoader.data_info import Data1D as LoaderData1D
from DataLoader.qsmearing import smear_selection


# PLEASE NEVER USE SUCH A DIRTY TRICK. Change your logic instead.
#INFINITY = 10

# The minimum q-value to be used when extrapolating
Q_MINIMUM  = 1e-5

# The maximum q-value to be used when extrapolating
Q_MAXIMUM  = 10

# Number of steps in the extrapolation
INTEGRATION_NSTEPS = 1000

class FitFunctor:
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
    
    
def guinier(x, scale=1, radius=0.1):
    """
        Compute a F(x) = scale* e-((radius*x)**2/3).
        @param x: a vector of q values or one q value
        @param scale: the scale value
        @param radius: the guinier radius value
        @return F(x)
    """
    
def power_law(x, scale=1, power=4):
    """
        F(x) = scale* (x)^(-power)
            when power= 4. the model is porod 
            else power_law
        The model has three parameters: 
        @param power: power of the function
        @param scale : scale factor value
        @param F(x)
    """    

    
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
        # Background and scale should be private data member if the only way to
        # change them are by instantiating a new object.
        self._background = background
        self._scale = scale
        
        # The data should be private
        self._data = self._get_data(data)
        
        # Since there are multiple variants of Q*, you should force the
        # user to use the get method and keep Q* a private data member
        self._qstar = None
        
        # You should keep the error on Q* so you can reuse it without
        # recomputing the whole thing.
        self._qstar_err = 0
        
        # Extrapolation parameters
        self._low_extrapolation_npts = 4
        self._low_extrapolation_function = guinier
        self._low_extrapolation_power = 4
        
        self._high_extrapolation_npts = 4
        self._high_extrapolation_function = power_law
        self._high_extrapolation_power = 4
        
    def set_extrapolation(self, range, npts=4, function=None, power=4):
        """
            Set the extrapolation parameters for the high or low Q-range.
            Note that this does not turn extrapolation on or off.
        """
        range = range.lower()
        if range not in ['high', 'low']:
            raise ValueError, "Extrapolation range should be 'high' or 'low'"
        function = function.lower()
        if function not in ['power_law', 'guinier']:
            raise ValueError, "Extrapolation function should be 'guinier' or 'power_law'"
        
        if range=='high':
            if function != 'power_law':
                raise ValueError, "Extrapolation only allows a power law at high Q"
            self._high_extrapolation_npts  = npts
            self._high_extrapolation_power = power
        else:
            if function == 'power_law':
                self._low_extrapolation_function = power_law
            else:
                self._low_extrapolation_function = guinier
            self._low_extrapolation_npts  = npts
            self._low_extrapolation_power = power
        
    def _get_data(self, data):
        """
            @note this function must be call before computing any type
             of invariant
            @return data= self._scale *data - self._background
        """
        if not issubclass(data.__class__, LoaderData1D):
            #Process only data that inherited from DataLoader.Data_info.Data1D
            raise ValueError,"Data must be of type DataLoader.Data1D"
        
        
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
        
    def get_qstar(self, extrapolation=None):
        """
            Compute the invariant of the local copy of data.
            Implementation:
                if slit smear:
                    qstar_0 = self._get_qstar_smear()
                else:
                    qstar_0 = self._get_qstar_unsmear()
                    
                if extrapolation==low:
                    return qstar_0 + self._get_qstar_low()
                elif extrapolation==high:
                    return qstar_0 + self._get_qstar_high()
                elif extrapolation==both:
                    return qstar_0 + self._get_qstar_low() + self._get_qstar_high()
                    
            @return q_star: invariant of the data within data's q range
        """
        
        
    def _get_qstar_unsmear(self):
        """
            Compute invariant for pinhole data.
            This invariant is given by:
        
                q_star = x0**2 *y0 *dx0 +x1**2 *y1 *dx1 
                            + ..+ xn**2 *yn *dxn 
                            
            where n= SOME GOOD DEFAULT
            dxi = 1/2*(xi+1 - xi) + (xi - xi-1)
            dx0 = (x1 - x0)/2
            dxn = xn - xn-1

            @return q_star: invariant value for pinhole data.
        """
        
    def _get_qstar_smear(self):
        """
            Compute invariant for slit-smeared data.
            This invariant is given by:
                q_star = x0*dxl *y0*dx0 + x1*dxl *y1 *dx1 
                            + ..+ xn*dxl *yn *dxn 
            where n= SOME GOOD DEFAULT
            dxi = 1/2*(xi+1 - xi) + (xi - xi-1)
            dx0 = x0+ (x1 - x0)/2
            dxn = xn - xn-1
            dxl: slit smear value
            
            @return q_star: invariant value for slit smeared data.
        """
        
    def _get_qstar_unsmear_uncertainty(self):
        """
            Compute invariant uncertainty with with pinhole data.
            This uncertainty is given as follow:
               dq_star = math.sqrt[(x0**2*(dy0)*dx0)**2 +
                    (x1**2 *(dy1)*dx1)**2 + ..+ (xn**2 *(dyn)*dxn)**2 ]
            where n = SOME GOOD DEFAULT
            dxi = 1/2*(xi+1 - xi) + (xi - xi-1)
            dx0 = x0+ (x1 - x0)/2
            dxn = xn - xn-1
            dyn: error on dy
            @param data: data of type Data1D where the scale is applied
                        and the background is subtracted.
            note: if data doesn't contain dy assume dy= math.sqrt(data.y)
        """
        
    def _get_qstar_smear_uncertainty(self):
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
        
    def _get_qstar_low(self):
        """
            Compute the invariant for extrapolated data at low q range.
            
            Implementation:
                data = self.get_extra_data_low()
                return self._get_qstar()
                
            @return q_star: the invariant for data extrapolated at low q.
        """
        
    def _get_qstar_high(self):
        """
            Compute the invariant for extrapolated data at high q range.
            
            Implementation:
                data = self.get_extra_data_high()
                return self._get_qstar()
                
            @return q_star: the invariant for data extrapolated at high q.
        """
        
    def _get_extra_data_low(self):
        """
            This method creates a new data set from the invariant calculator.
            
            It will use the extrapolation parameters kept as private data members.
            
            self._low_extrapolation_npts is the number of data points to use in to fit.
            self._low_extrapolation_function will be used as the fit function.
            
            
            
            It takes npts first points of data, fits them with a given model
            then uses the new parameters resulting from the fit to create a new data set.
            
            The new data first point is Q_MINIMUM.
            
            The last point of the new data is the first point of the original data.
            the number of q points of this data is INTEGRATION_NSTEPS.
            
            @return: a new data of type Data1D
        """
        
    def _get_extra_data_high(self):
        """
            This method creates a new data from the invariant calculator.
            
            It takes npts last points of data, fits them with a given model
            (for this function only power_law will be use), then uses
            the new parameters resulting from the fit to create a new data set.
            The first point is the last point of data.
            The last point of the new data is Q_MAXIMUM.
            The number of q points of this data is INTEGRATION_NSTEPS.

            
            @return: a new data of type Data1D
        """
        
    def get_qstar_with_error(self):
        """
            Compute the invariant uncertainty.
            This uncertainty computation depends on whether or not the data is
            smeared.
            @return dq_star:
                if slit smear:
                    return self._get_qstar(), self._get_qstar_smear_uncertainty()
                else:
                    return self._get_qstar(), self._get_qstar_unsmear_uncertainty()
        """
        
    def get_volume_fraction_with_error(self, contrast):
        """
            Compute uncertainty on volume value.
            This uncertainty is given by the following equation:
            dV = 0.5 * (4*k* dq_star) /(2* math.sqrt(1-k* q_star))
                                 
            for k = 10^(8)*q_star/(2*(pi*|contrast|)**2)
            q_star: the invariant value including extrapolated value if existing
            dq_star: the invariant uncertainty
            dV: the volume uncertainty
            @param contrast: contrast value 
            @return: v, dv
        """
        
    def get_surface_with_error(self, contrast, porod_const):
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
            @return S, dS: the surface, with its uncertainty
        """
        
    