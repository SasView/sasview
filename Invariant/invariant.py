"""
    This module implements invariant and its related computations.
    @author: Gervaise B. Alina/UTK
"""

import math 
import numpy

from DataLoader.data_info import Data1D as LoaderData1D
from DataLoader.qsmearing import smear_selection


# The minimum q-value to be used when extrapolating
Q_MINIMUM  = 1e-5

# The maximum q-value to be used when extrapolating
Q_MAXIMUM  = 10

# Number of steps in the extrapolation
INTEGRATION_NSTEPS = 1000

def guinier(x, scale=1, radius=60):
    """
        Compute a F(x) = scale* e-((radius*x)**2/3).
        @param x: a vector of q values 
        @param scale: the scale value
        @param radius: the guinier radius value
        @return F(x)
    """   
    if radius <= 0:
        raise ValueError("Rg expected positive value, but got %s"%radius)  
    value = numpy.array([math.exp(-((radius * i)**2/3)) for i in x ]) 
    scale = numpy.sqrt(scale*scale)      
    if scale == 0:
        raise ValueError("scale expected positive value, but got %s"%scale) 
    return scale * value

def power_law(x, scale=1, power=4):
    """
        F(x) = scale* (x)^(-power)
            when power= 4. the model is porod 
            else power_law
        The model has three parameters: 
        @param x: a vector of q values
        @param power: power of the function
        @param scale : scale factor value
        @param F(x)
    """  
    if power <=0:
        raise ValueError("Power_law function expected positive power, but got %s"%power)
    
    value = numpy.array([ math.pow(i, -power) for i in x ])  
    scale = numpy.sqrt(scale*scale)
    if scale == 0:
        raise ValueError("scale expected positive value, but got %s"%scale) 
    return scale * value

class FitFunctor:
    """
        compute f(x)
    """
    def __init__(self, data):
        """
            Determine a and b given a linear equation y = ax + b
            @param Data: data containing x and y  such as  y = ax + b 
        """
        self.data  = data
        x_len = len(self.data.x) -1
        #fitting range 
        self.qmin =  self.data.x[0]    
        if self.qmin == 0:
            self.qmin = Q_MINIMUM 
    
        self.qmax = self.data.x[x_len]
        #Unsmeared q range
        self._qmin_unsmeared = 0
        self._qmax_unsmeared = self.data.x[x_len]
        
        #bin for smear data
        self._first_unsmeared_bin = 0
        self._last_unsmeared_bin  = x_len
        
        # Identify the bin range for the unsmeared and smeared spaces
        self.idx = (self.data.x >= self.qmin) & (self.data.x <= self.qmax)
        self.idx_unsmeared = (self.data.x >= self._qmin_unsmeared) \
                            & (self.data.x <= self._qmax_unsmeared)
  
        #get the smear object of data
        self.smearer = smear_selection( self.data )
      
    def set_fit_range(self ,qmin=None, qmax=None):
        """ to set the fit range"""
        if qmin is not None:
            self.qmin = qmin
        if qmax is not None:
            self.qmax = qmax
            
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
        self.idx = (self.data.x >= self.qmin) & (self.data.x <= self.qmax)
        self.idx_unsmeared = (self.data.x >= self._qmin_unsmeared) \
                                & (self.data.x <= self._qmax_unsmeared)
  
    def fit(self, power=None):
        """
           Fit data for y = ax + b  return a and b
           @param power = a fixed, otherwise None
        """
        power = power
        fx = numpy.zeros(len(self.data.x))
        one = numpy.ones(len(self.data.x))

        #define dy^2
        try:
            sigma = self.data.dy[self.idx_unsmeared ]
        except:
            print "The dy data for Invariant calculation should be prepared before get to FitFunctor.fit()..."
            sigma = one[self.idx_unsmeared ]
        sigma2 = sigma * sigma

        # Compute theory data f(x)
        fx = self.data.y[self.idx_unsmeared ]/sigma
        ## Smear theory data
        if self.smearer is not None:
            fx = self.smearer(fx, self._first_unsmeared_bin,self._last_unsmeared_bin)
        
        ##power is given only for function = power_law    
        if power != None:
            a = -(power)
            b = (numpy.sum(fx/sigma) - a*numpy.sum(self.data.x[self.idx]/sigma2))/numpy.sum(numpy.ones(len(sigma2))/sigma2)
            return a, b
        else:
            A = numpy.vstack([ self.data.x[self.idx]/sigma,
                               numpy.ones(len(self.data.x[self.idx]))/sigma]).T
           
            a, b = numpy.linalg.lstsq(A, fx)[0]
            return a, b

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
        self._low_extrapolation_power = None
   
        self._high_extrapolation_npts = 4
        self._high_extrapolation_function = power_law
        self._high_extrapolation_power = None
        
    def _get_data(self, data):
        """
            @note this function must be call before computing any type
             of invariant
            @return data= self._scale *data - self._background
        """
        if not issubclass(data.__class__, LoaderData1D):
            #Process only data that inherited from DataLoader.Data_info.Data1D
            raise ValueError,"Data must be of type DataLoader.Data1D"
        new_data = self._scale * data - self._background
        try:
            #All data should pass here.
            new_data.dy = data.dy
            new_data.dxl = data.dxl
            new_data.dxw = data.dxw        
        except:
            #in case...
            new_data.dy = numpy.ones(len(data.x))
            new_data.dxl = numpy.zeros(len(data.x))
            new_data.dxw = numpy.zeros(len(data.x))       

        return new_data
        
    def _fit(self, function, qmin=Q_MINIMUM, qmax=Q_MAXIMUM, power=None):
        """
            fit data with function using 
            data= self._get_data()
            fx= Functor(data , function)
            y = data.y
            slope, constant = linalg.lstsq(y,fx)
            @param qmin: data first q value to consider during the fit
            @param qmax: data last q value to consider during the fit
            @param power : power value to consider for power-law 
            @param function: the function to use during the fit
            @return a: the scale of the function
            @return b: the other parameter of the function for guinier will be radius
                    for power_law will be the power value
        """
        #fit_x = numpy.array([math.log(x) for x in self._data.x])
        if function.__name__ == "guinier":   
            fit_x = numpy.array([x * x for x in self._data.x])     
            qmin = qmin**2
            qmax = qmax**2
            fit_y = numpy.array([math.log(y) for y in self._data.y])
            fit_dy = numpy.array([y for y in self._data.y])
            fit_dy = numpy.array([dy for dy in self._data.dy])/fit_dy

        elif function.__name__ == "power_law":
            fit_x = numpy.array([math.log(x) for x in self._data.x])
            qmin = math.log(qmin)
            qmax = math.log(qmax)
            fit_y = numpy.array([math.log(y) for y in self._data.y])
            fit_dy = numpy.array([y for y in self._data.y])
            fit_dy = numpy.array([dy for dy in self._data.dy])/fit_dy

        else:
            raise ValueError("Unknown function used to fit %s"%function.__name__)
       
        
        #else:
        fit_data = LoaderData1D(x=fit_x, y=fit_y, dy=fit_dy)
        fit_data.dxl = self._data.dxl
        fit_data.dxw = self._data.dxw   
        functor = FitFunctor(data=fit_data)
        functor.set_fit_range(qmin=qmin, qmax=qmax)
        b, a = functor.fit(power=power)         
      
                  
        if function.__name__ == "guinier":
            # b is the radius value of the guinier function
            if b>=0:
                raise ValueError("Guinier fit was not converged")
            else:
                b = math.sqrt(-3 * b)


        if function.__name__ == "power_law":
            b = -1 * b
            if b <= 0:
                raise ValueError("Power_law fit expected posive power, but got %s"%power)
        # a is the scale of the guinier function
        a = math.exp(a)

        return a, b
    
    def _get_qstar(self, data):
        """
            Compute invariant for data
            @param data: data to use to compute invariant.
              
        """
        if data is None:
            return 0
        if data.is_slit_smeared():
            return self._get_qstar_smear(data)
        else:
            return self._get_qstar_unsmear(data)
        
    def _get_qstar_unsmear(self, data):
        """
            Compute invariant for pinhole data.
            This invariant is given by:
        
                q_star = x0**2 *y0 *dx0 +x1**2 *y1 *dx1 
                            + ..+ xn**2 *yn *dxn 
                            
            where n >= len(data.x)-1
            dxi = 1/2*(xi+1 - xi) + (xi - xi-1)
            dx0 = (x1 - x0)/2
            dxn = (xn - xn-1)/2
            @param data: the data to use to compute invariant.
            @return q_star: invariant value for pinhole data. q_star > 0
        """
        if len(data.x) <= 1 or len(data.y) <= 1 or len(data.x)!= len(data.y):
            msg =  "Length x and y must be equal"
            msg += " and greater than 1; got x=%s, y=%s"%(len(data.x), len(data.y))
            raise ValueError, msg
        else:
            n = len(data.x)- 1
            #compute the first delta q
            dx0 = (data.x[1] - data.x[0])/2
            #compute the last delta q
            dxn = (data.x[n] - data.x[n-1])/2
            sum = 0
            sum += data.x[0] * data.x[0] * data.y[0] * dx0
            sum += data.x[n] * data.x[n] * data.y[n] * dxn
            
            if len(data.x) == 2:
                return sum
            else:
                #iterate between for element different from the first and the last
                for i in xrange(1, n-1):
                    dxi = (data.x[i+1] - data.x[i-1])/2
                    sum += data.x[i] * data.x[i] * data.y[i] * dxi
                return sum
            
    def _get_qstar_smear(self, data):
        """
            Compute invariant for slit-smeared data.
            This invariant is given by:
                q_star = x0*dxl *y0*dx0 + x1*dxl *y1 *dx1 
                            + ..+ xn*dxl *yn *dxn 
            where n >= len(data.x)-1
            dxi = 1/2*(xi+1 - xi) + (xi - xi-1)
            dx0 = (x1 - x0)/2
            dxn = (xn - xn-1)/2
            dxl: slit smear value
            
            @return q_star: invariant value for slit smeared data.
        """
        if not data.is_slit_smeared():
            msg = "_get_qstar_smear need slit smear data "
            msg += "Hint :dxl= %s , dxw= %s"%(str(data.dxl), str(data.dxw))
            raise ValueError, msg

        if len(data.x) <= 1 or len(data.y) <= 1 or len(data.x) != len(data.y)\
              or len(data.x)!= len(data.dxl):
            msg = "x, dxl, and y must be have the same length and greater than 1"
            raise ValueError, msg
        else:
            n = len(data.x)-1
            #compute the first delta
            dx0 = (data.x[1] - data.x[0])/2
            #compute the last delta
            dxn = (data.x[n] - data.x[n-1])/2
            sum = 0
            sum += data.x[0] * data.dxl[0] * data.y[0] * dx0
            sum += data.x[n] * data.dxl[n] * data.y[n] * dxn
            
            if len(data.x)==2:
                return sum
            else:
                #iterate between for element different from the first and the last
                for i in xrange(1, n-1):
                    dxi = (data.x[i+1] - data.x[i-1])/2
                    sum += data.x[i] * data.dxl[i] * data.y[i] * dxi
                return sum
        
    def _get_qstar_uncertainty(self, data=None):
        """
            Compute uncertainty of invariant value
            Implementation:
                if data is None:
                    data = self.data
            
                if data.slit smear:
                        return self._get_qstar_smear_uncertainty(data)
                    else:
                        return self._get_qstar_unsmear_uncertainty(data)
          
            @param: data use to compute the invariant which allow uncertainty
            computation.
            @return: uncertainty
        """
        if data is None:
            data = self.data
    
        if data.is_slit_smeared():
            return self._get_qstar_smear_uncertainty(data)
        else:
            return self._get_qstar_unsmear_uncertainty(data)
        
    def _get_qstar_unsmear_uncertainty(self, data=None):
        """
            Compute invariant uncertainty with with pinhole data.
            This uncertainty is given as follow:
               dq_star = math.sqrt[(x0**2*(dy0)*dx0)**2 +
                    (x1**2 *(dy1)*dx1)**2 + ..+ (xn**2 *(dyn)*dxn)**2 ]
            where n >= len(data.x)-1
            dxi = 1/2*(xi+1 - xi) + (xi - xi-1)
            dx0 = (x1 - x0)/2
            dxn = (xn - xn-1)/2
            dyn: error on dy
           
            @param data:
            note: if data doesn't contain dy assume dy= math.sqrt(data.y)
        """
        if data is None:
            data = self.data
            
        if len(data.x) <= 1 or len(data.y) <= 1 or \
            len(self.data.x) != len(self.data.y):
            msg = "Length of data.x and data.y must be equal"
            msg += " and greater than 1; got x=%s, y=%s"%(len(data.x),
                                                         len(data.y))
            raise ValueError, msg
        else:
            #Create error for data without dy error
            if (data.dy is None) or (not data.dy):
                dy = math.sqrt(y) 
            else:
                dy = data.dy
                
            n = len(data.x) - 1
            #compute the first delta
            dx0 = (data.x[1] - data.x[0])/2
            #compute the last delta
            dxn= (data.x[n] - data.x[n-1])/2
            sum = 0
            sum += (data.x[0] * data.x[0] * dy[0] * dx0)**2
            sum += (data.x[n] * data.x[n] * dy[n] * dxn)**2
            if len(data.x) == 2:
                return math.sqrt(sum)
            else:
                #iterate between for element different from the first and the last
                for i in xrange(1, n-1):
                    dxi = (data.x[i+1] - data.x[i-1])/2
                    sum += (data.x[i] * data.x[i] * dy[i] * dxi)**2
                return math.sqrt(sum)
        
    def _get_qstar_smear_uncertainty(self):
        """
            Compute invariant uncertainty with slit smeared data.
            This uncertainty is given as follow:
                dq_star = x0*dxl *dy0 *dx0 + x1*dxl *dy1 *dx1 
                            + ..+ xn*dxl *dyn *dxn 
            where n >= len(data.x)-1
            dxi = 1/2*(xi+1 - xi) + (xi - xi-1)
            dx0 = (x1 - x0)/2
            dxn = (xn - xn-1)/2
            dxl: slit smearing value
            dyn : error on dy
            @param data: data of type Data1D where the scale is applied
                        and the background is subtracted.
          
            note: if data doesn't contain dy assume dy= math.sqrt(data.y)
        """
        if data is None:
            data = self._data
            
        if not data.is_slit_smeared():
            msg = "_get_qstar_smear_uncertainty need slit smear data "
            msg += "Hint :dxl= %s , dxw= %s"%(str(data.dxl), str(data.dxw))
            raise ValueError, msg

        if len(data.x) <= 1 or len(data.y) <= 1 or len(data.x) != len(data.y)\
                or len(data.x) != len(data.dxl):
            msg = "x, dxl, and y must be have the same length and greater than 1"
            raise ValueError, msg
        else:
            #Create error for data without dy error
            if (data.dy is None) or (not data.dy):
                dy = math.sqrt(y)
            else:
                dy = data.dy
                
            n = len(data.x) - 1
            #compute the first delta
            dx0 = (data.x[1] - data.x[0])/2
            #compute the last delta
            dxn = (data.x[n] - data.x[n-1])/2
            sum = 0
            sum += (data.x[0] * data.dxl[0] * dy[0] * dx0)**2
            sum += (data.x[n] * data.dxl[n] * dy[n] * dxn)**2
            
            if len(data.x) == 2:
                return math.sqrt(sum)
            else:
                #iterate between for element different from the first and the last
                for i in xrange(1, n-1):
                    dxi = (data.x[i+1] - data.x[i-1])/2
                    sum += (data.x[i] * data.dxl[i] * dy[i] * dxi)**2
                return math.sqrt(sum)
   
    def get_qstar_low(self):
        """
            Compute the invariant for extrapolated data at low q range.
            
            Implementation:
                data = self.get_extra_data_low()
                return self._get_qstar()
                
            @return q_star: the invariant for data extrapolated at low q.
        """
        data = self.get_extra_data_low()
        return self._get_qstar(data=data)
        
    def get_qstar_high(self):
        """
            Compute the invariant for extrapolated data at high q range.
            
            Implementation:
                data = self.get_extra_data_high()
                return self._get_qstar()
                
            @return q_star: the invariant for data extrapolated at high q.
        """
        data = self.get_extra_data_high()
        return self._get_qstar(data=data)
        
    def get_extra_data_low(self):
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
        
        # Data boundaries for fiiting
        qmin = self._data.x[0]
        qmax = self._data.x[self._low_extrapolation_npts - 1]
        try:
            # fit the data with a model to get the appropriate parameters
            a, b = self._fit(function=self._low_extrapolation_function,
                              qmin=qmin,
                              qmax=qmax,
                              power=self._low_extrapolation_power)
        except:
            #raise
            return None
        
        #q_start point
        q_start = Q_MINIMUM
        if Q_MINIMUM >= qmin:
            q_start = qmin/10
            
        #create new Data1D to compute the invariant
        new_x = numpy.linspace(start=q_start,
                               stop=qmin,
                               num=INTEGRATION_NSTEPS,
                               endpoint=True)
        new_y = self._low_extrapolation_function(x=new_x, scale=a, radius=b)
        dxl = None
        dxw = None
        if self._data.dxl is not None:
            dxl = numpy.ones(INTEGRATION_NSTEPS)
            dxl = dxl * self._data.dxl[0]
        if self._data.dxw is not None:
            dxw = numpy.ones(INTEGRATION_NSTEPS)
            dxw = dxw * self._data.dxw[0]

        data_min = LoaderData1D(x=new_x, y=new_y)
        data_min.dxl = dxl
        data_min.dxw = dxw
        self._data.clone_without_data( clone= data_min)

        return data_min
          
    def get_extra_data_high(self):
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
        # Data boundaries for fiiting
        x_len = len(self._data.x) - 1
        qmin = self._data.x[x_len - (self._high_extrapolation_npts - 1)]
        qmax = self._data.x[x_len]
        
        try:
            # fit the data with a model to get the appropriate parameters
            a, b = self._fit(function=self._high_extrapolation_function,
                                   qmin=qmin,
                                    qmax=qmax,
                                    power=self._high_extrapolation_power)
        except:
            return None
       
        #create new Data1D to compute the invariant
        new_x = numpy.linspace(start=qmax,
                               stop=Q_MAXIMUM,
                               num=INTEGRATION_NSTEPS,
                               endpoint=True)
       
        new_y = self._high_extrapolation_function(x=new_x, scale=a, power=b)
        
        dxl = None
        dxw = None
        if self._data.dxl is not None:
            dxl = numpy.ones(INTEGRATION_NSTEPS)
            dxl = dxl * self._data.dxl[0]
        if self._data.dxw is not None:
            dxw = numpy.ones(INTEGRATION_NSTEPS)
            dxw = dxw * self._data.dxw[0]
            
        data_max = LoaderData1D(x=new_x, y=new_y)
        data_max.dxl = dxl
        data_max.dxw = dxw
        self._data.clone_without_data(clone=data_max)
    
        return data_max
     
    def set_extrapolation(self, range, npts=4, function=None, power=None):
        """
            Set the extrapolation parameters for the high or low Q-range.
            Note that this does not turn extrapolation on or off.
            @param range: a keyword set the type of extrapolation . type string
            @param npts: the numbers of q points of data to consider for extrapolation
            @param function: a keyword to select the function to use for extrapolation.
                of type string.
            @param power: an power to apply power_low function
                
        """
        range = range.lower()
        if range not in ['high', 'low']:
            raise ValueError, "Extrapolation range should be 'high' or 'low'"
        function = function.lower()
        if function not in ['power_law', 'guinier']:
            raise ValueError, "Extrapolation function should be 'guinier' or 'power_law'"
        
        if range == 'high':
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
        
    def get_qstar(self, extrapolation=None):
        """
            Compute the invariant of the local copy of data.
            Implementation:
                if slit smear:
                    qstar_0 = self._get_qstar_smear()
                else:
                    qstar_0 = self._get_qstar_unsmear()
                if extrapolation is None:
                    return qstar_0    
                if extrapolation==low:
                    return qstar_0 + self.get_qstar_low()
                elif extrapolation==high:
                    return qstar_0 + self.get_qstar_high()
                elif extrapolation==both:
                    return qstar_0 + self.get_qstar_low() + self.get_qstar_high()
           
            @param extrapolation: string to apply optional extrapolation    
            @return q_star: invariant of the data within data's q range
            
            @warning: When using setting data to Data1D , the user is responsible of
            checking that the scale and the background are properly apply to the data
            
            @warning: if error occur self.get_qstar_low() or self.get_qstar_low()
            their returned value will be ignored
        """
        qstar_0 = self._get_qstar(data=self._data)
        
        if extrapolation is None:
            self._qstar = qstar_0
            return self._qstar
        # Compute invariant plus invaraint of extrapolated data
        extrapolation = extrapolation.lower()    
        if extrapolation == "low":
            self._qstar = qstar_0 + self.get_qstar_low()
            return self._qstar
        elif extrapolation == "high":
            self._qstar = qstar_0 + self.get_qstar_high()
            return self._qstar
        elif extrapolation == "both":
            self._qstar = qstar_0 + self.get_qstar_low() + self.get_qstar_high()
            return self._qstar
       
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
        if contrast is None or porod_const is None:
            return 
        #Check whether we have Q star
        if self._qstar is None:
            self._qstar = self.get_star()
        if self._qstar == 0:
            raise RuntimeError("Cannot compute surface, invariant value is zero")
        # Compute the volume
        volume = self.get_volume_fraction(contrast)
        return 2 * math.pi * volume *(1 - volume) * float(porod_const)/self._qstar
        
    def get_volume_fraction(self, contrast):
        """
            Compute volume fraction is deduced as follow:
            
            q_star = 2*(pi*contrast)**2* volume( 1- volume)
            for k = 10^(-8)*q_star/(2*(pi*|contrast|)**2)
            we get 2 values of volume:
                 with   1 - 4 * k >= 0
                 volume1 = (1- sqrt(1- 4*k))/2
                 volume2 = (1+ sqrt(1- 4*k))/2
           
            q_star: the invariant value included extrapolation is applied
                         unit  1/A^(3)*1/cm
                    q_star = self.get_qstar()
                    
            the result returned will be 0<= volume <= 1
            
            @param contrast: contrast value provides by the user of type float.
                     contrast unit is 1/A^(2)= 10^(16)cm^(2)
            @return: volume fraction
            @note: volume fraction must have no unit
        """
        if contrast is None:
            return 
        if contrast < 0:
            raise ValueError, "contrast must be greater than zero"  
        
        if self._qstar is None:
            self._qstar = self.get_qstar()
        
        if self._qstar < 0:
            raise RuntimeError, "invariant must be greater than zero"
        
        # Compute intermediate constant
        k =  1.e-8 * self._qstar/(2 * (math.pi * math.fabs(float(contrast)))**2)
        #Check discriminant value
        discrim = 1 - 4 * k
        
        # Compute volume fraction
        if discrim < 0:
            raise RuntimeError, "could not compute the volume fraction: negative discriminant"
        elif discrim == 0:
            return 1/2
        else:
            volume1 = 0.5 * (1 - math.sqrt(discrim))
            volume2 = 0.5 * (1 + math.sqrt(discrim))
            
            if 0 <= volume1 and volume1 <= 1:
                return volume1
            elif 0 <= volume2 and volume2 <= 1: 
                return volume2 
            raise RuntimeError, "could not compute the volume fraction: inconsistent results"
    
    def get_qstar_with_error(self, extrapolation=None):
        """
            Compute the invariant uncertainty.
            This uncertainty computation depends on whether or not the data is
            smeared.
            @return: invariant,  the invariant uncertainty
                return self._get_qstar(), self._get_qstar_smear_uncertainty()   
        """
        if self._qstar is None:
            self._qstar = self.get_qstar(extrapolation=extrapolation)
        if self._qstar_err is None:
            self._qstar_err = self._get_qstar_smear_uncertainty()
            
        return self._qstar, self._qstar_err
    
    def get_volume_fraction_with_error(self, contrast):
        """
            Compute uncertainty on volume value as well as the volume fraction
            This uncertainty is given by the following equation:
            dV = 0.5 * (4*k* dq_star) /(2* math.sqrt(1-k* q_star))
                                 
            for k = 10^(-8)*q_star/(2*(pi*|contrast|)**2)
            
            q_star: the invariant value including extrapolated value if existing
            dq_star: the invariant uncertainty
            dV: the volume uncertainty
            @param contrast: contrast value 
            @return: V, dV = self.get_volume_fraction_with_error(contrast), dV
        """
        if contrast is None:
            return 
        self._qstar, self._qstar_err = self.get_qstar_with_error()
        
        volume = self.get_volume_fraction(contrast)
        if self._qstar < 0:
            raise ValueError, "invariant must be greater than zero"
        
        k =  1.e-8 * self._qstar /(2 * (math.pi* math.fabs(float(contrast)))**2)
        #check value inside the sqrt function
        value = 1 - k * self._qstar
        if (value) <= 0:
            raise ValueError, "Cannot compute incertainty on volume"
        # Compute uncertainty
        uncertainty = (0.5 * 4 * k * self._qstar_err)/(2 * math.sqrt(1 - k * self._qstar))
        
        return volume, math.fabs(uncertainty)
    
    def get_surface_with_error(self, contrast, porod_const):
        """
            Compute uncertainty of the surface value as well as thesurface value
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
        if contrast is None or porod_const is None:
            return 
        v, dv = self.get_volume_fraction_with_error(contrast)
        self._qstar, self._qstar_err = self.get_qstar_with_error()
        if self._qstar <= 0:
            raise ValueError, "invariant must be greater than zero"
        ds = porod_const * 2 * math.pi * (( dv - 2 * v * dv)/ self._qstar\
                 + self._qstar_err * ( v - v**2))
        s = self.get_surface(contrast=contrast, porod_const=porod_const)
        return s, ds
