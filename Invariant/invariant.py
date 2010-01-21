"""
    This module implements invariant and its related computations.
    @author: Gervaise B. Alina/UTK
"""
#TODO: Need to decide if/how to use smearing for extrapolation
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

class Transform(object):
    """
        Define interface that need to compute a function or an inverse
        function given some x, y 
    """
    
    def linearize_data(self, data):
        """
            Linearize data so that a linear fit can be performed. 
            Filter out the data that can't be transformed.
            @param data : LoadData1D instance
        """
        # Check that the vector lengths are equal
        assert(len(data.x)==len(data.y))
        if data.dy is not None:
            assert(len(data.x)==len(data.dy))
            dy = data.dy
        else:
            dy = numpy.array([math.sqrt(math.fabs(j)) for j in data.y])
        # Transform smear info 
        dxl_out = None
        dxw_out = None
        dx_out = None
        first_x = data.x#[0] 
        #if first_x == 0:
        #    first_x = data.x[1]
            
           
        data_points = zip(data.x, data.y, dy)
        
        # Transform the data
        output_points = [(self.linearize_q_value(p[0]),
                          math.log(p[1]),
                          p[2]/p[1]) for p in data_points if p[0]>0 and p[1]>0]
        
        x_out, y_out, dy_out = zip(*output_points)
       
        #Transform smear info    
        if data.dxl is not None  and len(data.dxl)>0:
            dxl_out = self.linearize_dq_value(x=x_out, dx=data.dxl[:len(x_out)])
        if data.dxw is not None and len(data.dxw)>0:
            dxw_out = self.linearize_dq_value(x=x_out, dx=data.dxw[:len(x_out)])
        if data.dx is not None  and len(data.dx)>0:
            dx_out = self.linearize_dq_value(x=x_out, dx=data.dx[:len(x_out)])
        x_out = numpy.asarray(x_out)
        y_out = numpy.asarray(y_out)
        dy_out = numpy.asarray(dy_out)
        linear_data = LoaderData1D(x=x_out, y=y_out, dx=dx_out, dy=dy_out)
        linear_data.dxl = dxl_out
        linear_data.dxw = dxw_out
        
        return linear_data
    def linearize_dq_value(self, x, dx):
        """
            Transform the input dq-value for linearization
        """
        return NotImplemented

    def linearize_q_value(self, value):
        """
            Transform the input q-value for linearization
        """
        return NotImplemented

    def extract_model_parameters(self, a, b):
        """
            set private member
        """
        return NotImplemented
     
    def evaluate_model(self, x):
        """
            Returns an array f(x) values where f is the Transform function.
        """
        return NotImplemented
    
class Guinier(Transform):
    """
        class of type Transform that performs operations related to guinier 
        function
    """
    def __init__(self, scale=1, radius=60):
        Transform.__init__(self)
        self.scale = scale
        self.radius = radius
        
    def linearize_dq_value(self, x, dx):
        """
            Transform the input dq-value for linearization
        """
        return numpy.array([2*x[0]*dx[0] for i in xrange(len(x))]) 
    
    def linearize_q_value(self, value):
        """
            Transform the input q-value for linearization
            @param value: q-value
            @return: q*q
        """
        return value * value
    
    def extract_model_parameters(self, a, b):
    	"""
    	   assign new value to the scale and the radius
    	"""
     	b = math.sqrt(-3 * b)
        a = math.exp(a)
        self.scale = a
        self.radius = b
        return a, b
        
    def evaluate_model(self, x):
        """
            return F(x)= scale* e-((radius*x)**2/3)
        """
        return self._guinier(x)
             
    def _guinier(self, x):
        """
            Retrive the guinier function after apply an inverse guinier function
            to x
            Compute a F(x) = scale* e-((radius*x)**2/3).
            @param x: a vector of q values 
            @param scale: the scale value
            @param radius: the guinier radius value
            @return F(x)
        """   
        # transform the radius of coming from the inverse guinier function to a 
        # a radius of a guinier function
        if self.radius <= 0:
            raise ValueError("Rg expected positive value, but got %s"%self.radius)  
        value = numpy.array([math.exp(-((self.radius * i)**2/3)) for i in x ]) 
        return self.scale * value

class PowerLaw(Transform):
    """
        class of type transform that perform operation related to power_law 
        function
    """
    def __init__(self, scale=1, power=4):
        Transform.__init__(self)
        self.scale = scale
        self.power = power
   
    def linearize_dq_value(self, x, dx):
        """
            Transform the input dq-value for linearization
        """
        return  numpy.array([dx[0]/x[0] for i in xrange(len(x))]) 
    
    def linearize_q_value(self, value):
        """
            Transform the input q-value for linearization
            @param value: q-value
            @return: log(q)
        """
        return math.log(value)
    
    def extract_model_parameters(self, a, b):
        """
            Assign new value to the scale and the power 
        """
        b = -1 * b
        a = math.exp(a)
        self.power = b
        self.scale = a
        return a, b
        
    def evaluate_model(self, x):
        """
            given a scale and a radius transform x, y using a power_law
            function
        """
        return self._power_law(x)
       
    def _power_law(self, x):
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
        if self.power <= 0:
            raise ValueError("Power_law function expected positive power, but got %s"%self.power)
        if self.scale <= 0:
            raise ValueError("scale expected positive value, but got %s"%self.scale) 
       
        value = numpy.array([ math.pow(i, -self.power) for i in x ])  
        return self.scale * value

class Extrapolator:
    """
        Extrapolate I(q) distribution using a given model
    """
    def __init__(self, data):
        """
            Determine a and b given a linear equation y = ax + b
            @param Data: data containing x and y  such as  y = ax + b 
        """
        self.data  = data
       
        # Set qmin as the lowest non-zero value
        self.qmin = Q_MINIMUM
        for q_value in self.data.x:
            if q_value > 0: 
                self.qmin = q_value
                break
        self.qmax = max(self.data.x)
       
        #get the smear object of data
        self.smearer = smear_selection(self.data)
        # Set the q-range information to allow smearing
        self.set_fit_range()
      
    def set_fit_range(self, qmin=None, qmax=None):
        """ to set the fit range"""
        if qmin is not None:
            self.qmin = qmin
        if qmax is not None:
            self.qmax = qmax
            
        # Determine the range needed in unsmeared-Q to cover
        # the smeared Q range
        self._qmin_unsmeared = self.qmin
        self._qmax_unsmeared = self.qmax    
        
        if self.smearer is not None:
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
        fx = numpy.zeros(len(self.data.x))

         # Uncertainty
        if type(self.data.dy)==numpy.ndarray and len(self.data.dy)==len(self.data.x):
            sigma = self.data.dy
        else:
            sigma = numpy.ones(len(self.data.x))
            
        # Compute theory data f(x)
        fx[self.idx_unsmeared] = self.data.y[self.idx_unsmeared]
        ## Smear theory data
        if self.smearer is not None:
            fx = self.smearer(fx, self._first_unsmeared_bin,self._last_unsmeared_bin)
        
        fx[self.idx_unsmeared] = fx[self.idx_unsmeared]/sigma[self.idx_unsmeared]
        
        ##power is given only for function = power_law    
        if power != None:
            sigma2 = sigma * sigma
            a = -(power)
            b = (numpy.sum(fx[self.idx]/sigma[self.idx]) - a*numpy.sum(self.data.x[self.idx]/sigma2[self.idx]))/numpy.sum(numpy.ones(len(sigma2[self.idx]))/sigma2[self.idx])
            return a, b
        else:
            A = numpy.vstack([ self.data.x[self.idx]/sigma[self.idx],
                               numpy.ones(len(self.data.x[self.idx]))/sigma[self.idx]]).T
           
            a, b = numpy.linalg.lstsq(A, fx[self.idx])[0]
            
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
            @param background: Background value. The data will be corrected before processing
            @param scale: Scaling factor for I(q). The data will be corrected before processing
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
        self._low_extrapolation_function = Guinier()
        self._low_extrapolation_power = None
   
        self._high_extrapolation_npts = 4
        self._high_extrapolation_function = PowerLaw()
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
        new_data = (self._scale * data) - self._background   
        new_data.dxl = data.dxl
        new_data.dxw = data.dxw 
        return  new_data
     
    def _fit(self, model, qmin=Q_MINIMUM, qmax=Q_MAXIMUM, power=None):
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
        # Linearize the data in preparation for fitting
        fit_data = model.linearize_data(self._data)
        qmin = model.linearize_q_value(qmin)
        qmax = model.linearize_q_value(qmax)
        # Get coefficient cmoning out of the  fit
        extrapolator = Extrapolator(data=fit_data)
        extrapolator.set_fit_range(qmin=qmin, qmax=qmax)
        b, a = extrapolator.fit(power=power) 
        
        return model.extract_model_parameters(a=a, b=b)
    
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
            msg +=" len x=%s, y=%s, dxl=%s"%(len(data.x),len(data.y),len(data.dxl))
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
            data = self._data
        if data.is_slit_smeared():
            return self._get_qstar_smear_uncertainty(data)
        else:
            return self._get_qstar_unsmear_uncertainty(data)
        
    def _get_qstar_unsmear_uncertainty(self, data):
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
        
    def _get_qstar_smear_uncertainty(self, data):
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
        
    def _get_extrapolated_data(self, model, npts=INTEGRATION_NSTEPS,
                              q_start=Q_MINIMUM, q_end=Q_MAXIMUM):
        """
            @return extrapolate data create from data
        """
        #create new Data1D to compute the invariant
        q = numpy.linspace(start=q_start,
                               stop=q_end,
                               num=npts,
                               endpoint=True)
        iq = model.evaluate_model(q)
         
        # Determine whether we are extrapolating to high or low q-values
        # If the data is slit smeared, get the index of the slit dimension array entry
        # that we will use to smear the extrapolated data.
        dxl = None
        dxw = None

        if self._data.is_slit_smeared():
            if q_start<min(self._data.x):
                smear_index = 0
            elif q_end>max(self._data.x):
                smear_index = len(self._data.x)-1
            else:
                raise RuntimeError, "Extrapolation can only be evaluated for points outside the data Q range"
            
            if self._data.dxl is not None :
                dxl = numpy.ones(INTEGRATION_NSTEPS)
                dxl = dxl * self._data.dxl[smear_index]
               
            if self._data.dxw is not None :
                dxw = numpy.ones(INTEGRATION_NSTEPS)
                dxw = dxw * self._data.dxw[smear_index]
             
        result_data = LoaderData1D(x=q, y=iq)
        result_data.dxl = dxl
        result_data.dxw = dxw
        return result_data
    
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
        
        # Data boundaries for fitting
        qmin = self._data.x[0]
        qmax = self._data.x[self._low_extrapolation_npts - 1]
        
        # Extrapolate the low-Q data
        a, b = self._fit(model=self._low_extrapolation_function,
                         qmin=qmin,
                         qmax=qmax,
                         power=self._low_extrapolation_power)
        q_start = Q_MINIMUM
        #q_start point
        if Q_MINIMUM >= qmin:
            q_start = qmin/10
        
        data_min = self._get_extrapolated_data(model=self._low_extrapolation_function,
                                               npts=INTEGRATION_NSTEPS,
                                               q_start=q_start, q_end=qmin)
        return data_min
          
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
        # Data boundaries for fitting
        x_len = len(self._data.x) - 1
        qmin = self._data.x[x_len - (self._high_extrapolation_npts - 1)]
        qmax = self._data.x[x_len]
        q_end = Q_MAXIMUM
        
        # fit the data with a model to get the appropriate parameters
        a, b = self._fit(model=self._high_extrapolation_function,
                         qmin=qmin,
                         qmax=qmax,
                         power=self._high_extrapolation_power)
        
        #create new Data1D to compute the invariant
        data_max = self._get_extrapolated_data(model=self._high_extrapolation_function,
                                               npts=INTEGRATION_NSTEPS,
                                               q_start=qmax, q_end=q_end)
        return data_max
         
    def get_qstar_low(self):
        """
            Compute the invariant for extrapolated data at low q range.
            
            Implementation:
                data = self._get_extra_data_low()
                return self._get_qstar()
                
            @return q_star: the invariant for data extrapolated at low q.
        """
        data = self._get_extra_data_low()
        
        return self._get_qstar(data=data)
        
    def get_qstar_high(self):
        """
            Compute the invariant for extrapolated data at high q range.
            
            Implementation:
                data = self._get_extra_data_high()
                return self._get_qstar()
                
            @return q_star: the invariant for data extrapolated at high q.
        """
        data = self._get_extra_data_high()
        return self._get_qstar(data=data)
    
    def get_extra_data_low(self, npts_in=None, q_start=Q_MINIMUM, nsteps=INTEGRATION_NSTEPS):
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
        #Create a data from result of the fit for a range outside of the data
        # at low q range
        data_out_range = self._get_extra_data_low()
        
        if  q_start != Q_MINIMUM or nsteps != INTEGRATION_NSTEPS:
            qmin = min(self._data.x)
            if q_start < Q_MINIMUM:
                q_start = Q_MINIMUM
            elif q_start >= qmin:
                q_start = qmin/10
                
            #compute the new data with the proper result of the fit for different
            #boundary and step, outside of data
            data_out_range = self._get_extrapolated_data(model=self._low_extrapolation_function,
                                               npts=nsteps,
                                               q_start=q_start, q_end=qmin)
        #Create data from the result of the fit for a range inside data q range for
        #low q
        if npts_in is None :
            npts_in = self._low_extrapolation_npts

        x = self._data.x[:npts_in]
        y = self._low_extrapolation_function.evaluate_model(x=x)
        dy = None
        dx = None
        dxl = None
        dxw = None
        if self._data.dx is not None:
            dx = self._data.dx[:npts_in]
        if self._data.dy is not None:
            dy = self._data.dy[:npts_in]
        if self._data.dxl is not None and len(self._data.dxl)>0:
            dxl = self._data.dxl[:npts_in]
        if self._data.dxw is not None and len(self._data.dxw)>0:
            dxw = self._data.dxw[:npts_in]
        #Crate new data 
        data_in_range = LoaderData1D(x=x, y=y, dx=dx, dy=dy)
        data_in_range.clone_without_data(clone=self._data)
        data_in_range.dxl = dxl
        data_in_range.dxw = dxw
        
        return data_out_range, data_in_range
          
    def get_extra_data_high(self, npts_in=None, q_end=Q_MAXIMUM, nsteps=INTEGRATION_NSTEPS ):
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
        #Create a data from result of the fit for a range outside of the data
        # at low q range
        data_out_range = self._get_extra_data_high()
        qmax = max(self._data.x)
        if  q_end != Q_MAXIMUM or nsteps != INTEGRATION_NSTEPS:
            if q_end > Q_MAXIMUM:
               q_end = Q_MAXIMUM
            elif q_end <= qmax:
                q_end = qmax * 10
                
            #compute the new data with the proper result of the fit for different
            #boundary and step, outside of data
            data_out_range = self._get_extrapolated_data(model=self._high_extrapolation_function,
                                               npts=nsteps,
                                               q_start=qmax, q_end=q_end)
        #Create data from the result of the fit for a range inside data q range for
        #high q
        if npts_in is None :
            npts_in = self._high_extrapolation_npts
            
        x_len = len(self._data.x)
        x = self._data.x[(x_len-npts_in):]
        y = self._high_extrapolation_function.evaluate_model(x=x)
        dy = None
        dx = None
        dxl = None
        dxw = None
        
        if self._data.dx is not None:
            dx = self._data.dx[(x_len-npts_in):]
        if self._data.dy is not None:
            dy = self._data.dy[(x_len-npts_in):]
        if self._data.dxl is not None and len(self._data.dxl)>0:
            dxl = self._data.dxl[(x_len-npts_in):]
        if self._data.dxw is not None and len(self._data.dxw)>0:
            dxw = self._data.dxw[(x_len-npts_in):]
        #Crate new data 
        data_in_range = LoaderData1D(x=x, y=y, dx=dx, dy=dy)
        data_in_range.clone_without_data(clone=self._data)
        data_in_range.dxl = dxl
        data_in_range.dxw = dxw
        
        return data_out_range, data_in_range
          
     
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
                self._low_extrapolation_function = PowerLaw()
            else:
                self._low_extrapolation_function = Guinier()
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
