
import  copy
#import logging
import sys
import numpy
import math
import park
from sans.dataloader.data_info import Data1D
from sans.dataloader.data_info import Data2D
_SMALLVALUE = 1.0e-10    
    
class SansParameter(park.Parameter):
    """
    SANS model parameters for use in the PARK fitting service.
    The parameter attribute value is redirected to the underlying
    parameter value in the SANS model.
    """
    def __init__(self, name, model, data):
        """
            :param name: the name of the model parameter
            :param model: the sans model to wrap as a park model
        """
        park.Parameter.__init__(self, name)
        self._model, self._name = model, name
        self.data = data
        self.model = model
        #set the value for the parameter of the given name
        self.set(model.getParam(name))
         
    def _getvalue(self):
        """
        override the _getvalue of park parameter
        
        :return value the parameter associates with self.name
        
        """
        return self._model.getParam(self.name)
    
    def _setvalue(self, value):
        """
        override the _setvalue pf park parameter
        
        :param value: the value to set on a given parameter
        
        """
        self._model.setParam(self.name, value)
        
    value = property(_getvalue, _setvalue)
    
    def _getrange(self):
        """
        Override _getrange of park parameter
        return the range of parameter
        """
        #if not  self.name in self._model.getDispParamList():
        lo, hi = self._model.details[self.name][1:3]
        if lo is None: lo = -numpy.inf
        if hi is None: hi = numpy.inf
        if lo > hi:
            raise ValueError, "wrong fit range for parameters"
        
        return lo, hi
    
    def get_name(self):
        """
        """
        return self._getname()
    
    def _setrange(self, r):
        """
        override _setrange of park parameter
        
        :param r: the value of the range to set
        
        """
        self._model.details[self.name][1:3] = r
    range = property(_getrange, _setrange)
    
    
class Model(park.Model):
    """
    PARK wrapper for SANS models.
    """
    def __init__(self, sans_model, sans_data=None, **kw):
        """
        :param sans_model: the sans model to wrap using park interface
        
        """
        park.Model.__init__(self, **kw)
        self.model = sans_model
        self.name = sans_model.name
        self.data = sans_data
        #list of parameters names
        self.sansp = sans_model.getParamList()
        #list of park parameter
        self.parkp = [SansParameter(p, sans_model, sans_data) for p in self.sansp]
        #list of parameter set
        self.parameterset = park.ParameterSet(sans_model.name, pars=self.parkp)
        self.pars = []
  
    def get_params(self, fitparams):
        """
        return a list of value of paramter to fit
        
        :param fitparams: list of paramaters name to fit
        
        """
        list_params = []
        self.pars = []
        self.pars = fitparams
        for item in fitparams:
            for element in self.parkp:
                if element.name == str(item):
                    list_params.append(element.value)
        return list_params
    
    def set_params(self, paramlist, params):
        """
        Set value for parameters to fit
        
        :param params: list of value for parameters to fit
        
        """
        try:
            for i in range(len(self.parkp)):
                for j in range(len(paramlist)):
                    if self.parkp[i].name == paramlist[j]:
                        self.parkp[i].value = params[j]
                        self.model.setParam(self.parkp[i].name, params[j])
        except:
            raise
  
    def eval(self, x):
        """
            Override eval method of park model.
        
            :param x: the x value used to compute a function
        """
        try:
            return self.model.evalDistribution(x)
        except:
            raise
        
    def eval_derivs(self, x, pars=[]):
        """
        Evaluate the model and derivatives wrt pars at x.

        pars is a list of the names of the parameters for which derivatives
        are desired.

        This method needs to be specialized in the model to evaluate the
        model function.  Alternatively, the model can implement is own
        version of residuals which calculates the residuals directly
        instead of calling eval.
        """
        return []

    
class FitData1D(Data1D):
    """
        Wrapper class  for SANS data
        FitData1D inherits from DataLoader.data_info.Data1D. Implements
        a way to get residuals from data.
    """
    def __init__(self, x, y, dx=None, dy=None, smearer=None, data=None):
        """
            :param smearer: is an object of class QSmearer or SlitSmearer
               that will smear the theory data (slit smearing or resolution
               smearing) when set.
            
            The proper way to set the smearing object would be to
            do the following: ::
            
                from DataLoader.qsmearing import smear_selection
                smearer = smear_selection(some_data)
                fitdata1d = FitData1D( x= [1,3,..,],
                                        y= [3,4,..,8],
                                        dx=None,
                                        dy=[1,2...], smearer= smearer)
           
            :Note: that some_data _HAS_ to be of
                class DataLoader.data_info.Data1D
                Setting it back to None will turn smearing off.
                
        """
        Data1D.__init__(self, x=x, y=y, dx=dx, dy=dy)
        self.sans_data = data
        self.smearer = smearer
        self._first_unsmeared_bin = None
        self._last_unsmeared_bin = None
        # Check error bar; if no error bar found, set it constant(=1)
        # TODO: Should provide an option for users to set it like percent,
        # constant, or dy data
        if dy == None or dy == [] or dy.all() == 0:
            self.dy = numpy.ones(len(y))
        else:
            self.dy = numpy.asarray(dy).copy()

        ## Min Q-value
        #Skip the Q=0 point, especially when y(q=0)=None at x[0].
        if min(self.x) == 0.0 and self.x[0] == 0 and\
                     not numpy.isfinite(self.y[0]):
            self.qmin = min(self.x[self.x != 0])
        else:
            self.qmin = min(self.x)
        ## Max Q-value
        self.qmax = max(self.x)
        
        # Range used for input to smearing
        self._qmin_unsmeared = self.qmin
        self._qmax_unsmeared = self.qmax
        # Identify the bin range for the unsmeared and smeared spaces
        self.idx = (self.x >= self.qmin) & (self.x <= self.qmax)
        self.idx_unsmeared = (self.x >= self._qmin_unsmeared) \
                            & (self.x <= self._qmax_unsmeared)
  
    def set_fit_range(self, qmin=None, qmax=None):
        """ to set the fit range"""
        # Skip Q=0 point, (especially for y(q=0)=None at x[0]).
        # ToDo: Find better way to do it.
        if qmin == 0.0 and not numpy.isfinite(self.y[qmin]):
            self.qmin = min(self.x[self.x != 0])
        elif qmin != None:
            self.qmin = qmin
        if qmax != None:
            self.qmax = qmax
        # Determine the range needed in unsmeared-Q to cover
        # the smeared Q range
        self._qmin_unsmeared = self.qmin
        self._qmax_unsmeared = self.qmax
        
        self._first_unsmeared_bin = 0
        self._last_unsmeared_bin = len(self.x) - 1
        
        if self.smearer != None:
            self._first_unsmeared_bin, self._last_unsmeared_bin = \
                    self.smearer.get_bin_range(self.qmin, self.qmax)
            self._qmin_unsmeared = self.x[self._first_unsmeared_bin]
            self._qmax_unsmeared = self.x[self._last_unsmeared_bin]
            
        # Identify the bin range for the unsmeared and smeared spaces
        self.idx = (self.x >= self.qmin) & (self.x <= self.qmax)
        ## zero error can not participate for fitting
        self.idx = self.idx & (self.dy != 0)
        self.idx_unsmeared = (self.x >= self._qmin_unsmeared) \
                            & (self.x <= self._qmax_unsmeared)

    def get_fit_range(self):
        """
            Return the range of data.x to fit
        """
        return self.qmin, self.qmax
        
    def residuals(self, fn):
        """
            Compute residuals.
            
            If self.smearer has been set, use if to smear
            the data before computing chi squared.
            
            :param fn: function that return model value
            
            :return: residuals
        """
        # Compute theory data f(x)
        fx = numpy.zeros(len(self.x))
        fx[self.idx_unsmeared] = fn(self.x[self.idx_unsmeared])
       
        ## Smear theory data
        if self.smearer is not None:
            fx = self.smearer(fx, self._first_unsmeared_bin,
                              self._last_unsmeared_bin)
        ## Sanity check
        if numpy.size(self.dy) != numpy.size(fx):
            msg = "FitData1D: invalid error array "
            msg += "%d <> %d" % (numpy.shape(self.dy), numpy.size(fx))
            raise RuntimeError, msg
        return (self.y[self.idx] - fx[self.idx]) / self.dy[self.idx], fx[self.idx]
            
    def residuals_deriv(self, model, pars=[]):
        """
            :return: residuals derivatives .
            
            :note: in this case just return empty array 
        """
        return []
    
    
class FitData2D(Data2D):
    """
        Wrapper class  for SANS data
    """
    def __init__(self, sans_data2d, data=None, err_data=None):
        Data2D.__init__(self, data=data, err_data=err_data)
        """
            Data can be initital with a data (sans plottable)
            or with vectors.
        """
        self.res_err_image = []
        self.idx = []
        self.qmin = None
        self.qmax = None
        self.smearer = None
        self.radius = 0
        self.res_err_data = []
        self.sans_data = sans_data2d
        self.set_data(sans_data2d)

    def set_data(self, sans_data2d, qmin=None, qmax=None):
        """
            Determine the correct qx_data and qy_data within range to fit
        """
        self.data = sans_data2d.data
        self.err_data = sans_data2d.err_data
        self.qx_data = sans_data2d.qx_data
        self.qy_data = sans_data2d.qy_data
        self.mask = sans_data2d.mask

        x_max = max(math.fabs(sans_data2d.xmin), math.fabs(sans_data2d.xmax))
        y_max = max(math.fabs(sans_data2d.ymin), math.fabs(sans_data2d.ymax))
        
        ## fitting range
        if qmin == None:
            self.qmin = 1e-16
        if qmax == None:
            self.qmax = math.sqrt(x_max * x_max + y_max * y_max)
        ## new error image for fitting purpose
        if self.err_data == None or self.err_data == []:
            self.res_err_data = numpy.ones(len(self.data))
        else:
            self.res_err_data = copy.deepcopy(self.err_data)
        #self.res_err_data[self.res_err_data==0]=1
        
        self.radius = numpy.sqrt(self.qx_data**2 + self.qy_data**2)
        
        # Note: mask = True: for MASK while mask = False for NOT to mask
        self.idx = ((self.qmin <= self.radius) &\
                            (self.radius <= self.qmax))
        self.idx = (self.idx) & (self.mask)
        self.idx = (self.idx) & (numpy.isfinite(self.data))

    def set_smearer(self, smearer):
        """
            Set smearer
        """
        if smearer == None:
            return
        self.smearer = smearer
        self.smearer.set_index(self.idx)
        self.smearer.get_data()

    def set_fit_range(self, qmin=None, qmax=None):
        """
            To set the fit range
        """
        if qmin == 0.0:
            self.qmin = 1e-16
        elif qmin != None:
            self.qmin = qmin
        if qmax != None:
            self.qmax = qmax
        self.radius = numpy.sqrt(self.qx_data**2 + self.qy_data**2)
        self.idx = ((self.qmin <= self.radius) &\
                            (self.radius <= self.qmax))
        self.idx = (self.idx) & (self.mask)
        self.idx = (self.idx) & (numpy.isfinite(self.data))
        self.idx = (self.idx) & (self.res_err_data != 0)

    def get_fit_range(self):
        """
        return the range of data.x to fit
        """
        return self.qmin, self.qmax
     
    def residuals(self, fn):
        """
        return the residuals
        """
        if self.smearer != None:
            fn.set_index(self.idx)
            # Get necessary data from self.data and set the data for smearing
            fn.get_data()

            gn = fn.get_value()
        else:
            gn = fn([self.qx_data[self.idx],
                     self.qy_data[self.idx]])
        # use only the data point within ROI range
        res = (self.data[self.idx] - gn) / self.res_err_data[self.idx]

        return res, gn
        
    def residuals_deriv(self, model, pars=[]):
        """
        :return: residuals derivatives .
        
        :note: in this case just return empty array
        
        """
        return []
    
    
class FitAbort(Exception):
    """
    Exception raise to stop the fit
    """
    #pass
    #print"Creating fit abort Exception"


class SansAssembly:
    """
    Sans Assembly class a class wrapper to be call in optimizer.leastsq method
    """
    def __init__(self, paramlist, model=None, data=None, fitresult=None,
                 handler=None, curr_thread=None, msg_q=None):
        """
        :param Model: the model wrapper fro sans -model
        :param Data: the data wrapper for sans data
        
        """
        self.model = model
        self.data = data
        self.paramlist = paramlist
        self.msg_q = msg_q
        self.curr_thread = curr_thread
        self.handler = handler
        self.fitresult = fitresult
        self.res = []
        self.true_res = []
        self.func_name = "Functor"
        self.theory = None
        
    def chisq(self):
        """
        Calculates chi^2
        
        :param params: list of parameter values
        
        :return: chi^2
        
        """
        total = 0
        for item in self.true_res:
            total += item * item
        if len(self.true_res) == 0:
            return None
        return total / len(self.true_res)
    
    def __call__(self, params):
        """
            Compute residuals
            :param params: value of parameters to fit
        """
        #import thread
        self.model.set_params(self.paramlist, params)
        #print "params", params
        self.true_res, theory = self.data.residuals(self.model.eval)
        self.theory = copy.deepcopy(theory)
        # check parameters range
        if self.check_param_range():
            # if the param value is outside of the bound
            # just silent return res = inf
            return self.res
        self.res = self.true_res
        
        if self.fitresult is not None:
            self.fitresult.set_model(model=self.model)
            self.fitresult.residuals = self.true_res
            self.fitresult.iterations += 1
            self.fitresult.theory = theory
           
            #fitness = self.chisq(params=params)
            fitness = self.chisq()
            self.fitresult.pvec = params
            self.fitresult.set_fitness(fitness=fitness)
            if self.msg_q is not None:
                self.msg_q.put(self.fitresult)
                
            if self.handler is not None:
                self.handler.set_result(result=self.fitresult)
                self.handler.update_fit()

            if self.curr_thread != None:
                try:
                    self.curr_thread.isquit()
                except:
                    #msg = "Fitting: Terminated...       Note: Forcing to stop "
                    #msg += "fitting may cause a 'Functor error message' "
                    #msg += "being recorded in the log file....."
                    #self.handler.stop(msg)
                    raise
         
        return self.res
    
    def check_param_range(self):
        """
        Check the lower and upper bound of the parameter value
        and set res to the inf if the value is outside of the
        range
        :limitation: the initial values must be within range.
        """

        #time.sleep(0.01)
        is_outofbound = False
        # loop through the fit parameters
        for p in self.model.parameterset:
            param_name = p.get_name()
            if param_name in self.paramlist:
                
                # if the range was defined, check the range
                if numpy.isfinite(p.range[0]):
                    if p.value == 0:
                        # This value works on Scipy
                        # Do not change numbers below
                        value = _SMALLVALUE
                    else:
                        value = p.value
                    # For leastsq, it needs a bit step back from the boundary
                    val = p.range[0] - value * _SMALLVALUE
                    if p.value < val:
                        self.res *= 1e+6
                        
                        is_outofbound = True
                        break
                if numpy.isfinite(p.range[1]):
                    # This value works on Scipy
                    # Do not change numbers below
                    if p.value == 0:
                        value = _SMALLVALUE
                    else:
                        value = p.value
                    # For leastsq, it needs a bit step back from the boundary
                    val = p.range[1] + value * _SMALLVALUE
                    if p.value > val:
                        self.res *= 1e+6
                        is_outofbound = True
                        break

        return is_outofbound
    
    
class FitEngine:
    def __init__(self):
        """
        Base class for scipy and park fit engine
        """
        #List of parameter names to fit
        self.param_list = []
        #Dictionnary of fitArrange element (fit problems)
        self.fit_arrange_dict = {}
        self.fitter_id = None
        
    def set_model(self, model, id, pars=[], constraints=[], data=None):
        """
        set a model on a given  in the fit engine.
        
        :param model: sans.models type 
        :param id: is the key of the fitArrange dictionary where model is saved as a value
        :param pars: the list of parameters to fit 
        :param constraints: list of 
            tuple (name of parameter, value of parameters)
            the value of parameter must be a string to constraint 2 different
            parameters.
            Example:  
            we want to fit 2 model M1 and M2 both have parameters A and B.
            constraints can be ``constraints = [(M1.A, M2.B+2), (M1.B= M2.A *5),...,]``
            
             
        :note: pars must contains only name of existing model's parameters
        
        """
        if model == None:
            raise ValueError, "AbstractFitEngine: Need to set model to fit"
        
        new_model = model
        if not issubclass(model.__class__, Model):
            new_model = Model(model, data)
        
        if len(constraints) > 0:
            for constraint in constraints:
                name, value = constraint
                try:
                    new_model.parameterset[str(name)].set(str(value))
                except:
                    msg = "Fit Engine: Error occurs when setting the constraint"
                    msg += " %s for parameter %s " % (value, name)
                    raise ValueError, msg
                
        if len(pars) > 0:
            temp = []
            for item in pars:
                if item in new_model.model.getParamList():
                    temp.append(item)
                    self.param_list.append(item)
                else:
                    
                    msg = "wrong parameter %s used" % str(item)
                    msg += "to set model %s. Choose" % str(new_model.model.name)
                    msg += "parameter name within %s" % \
                                str(new_model.model.getParamList())
                    raise ValueError, msg
              
            #A fitArrange is already created but contains data_list only at id
            if self.fit_arrange_dict.has_key(id):
                self.fit_arrange_dict[id].set_model(new_model)
                self.fit_arrange_dict[id].pars = pars
            else:
            #no fitArrange object has been create with this id
                fitproblem = FitArrange()
                fitproblem.set_model(new_model)
                fitproblem.pars = pars
                self.fit_arrange_dict[id] = fitproblem
                vals = []
                for name in pars:
                    vals.append(new_model.model.getParam(name))
                self.fit_arrange_dict[id].vals = vals
        else:
            raise ValueError, "park_integration:missing parameters"
    
    def set_data(self, data, id, smearer=None, qmin=None, qmax=None):
        """
        Receives plottable, creates a list of data to fit,set data
        in a FitArrange object and adds that object in a dictionary
        with key id.
        
        :param data: data added
        :param id: unique key corresponding to a fitArrange object with data
        """
        if data.__class__.__name__ == 'Data2D':
            fitdata = FitData2D(sans_data2d=data, data=data.data,
                                 err_data=data.err_data)
        else:
            fitdata = FitData1D(x=data.x, y=data.y,
                                 dx=data.dx, dy=data.dy, smearer=smearer)
        fitdata.sans_data = data
       
        fitdata.set_fit_range(qmin=qmin, qmax=qmax)
        #A fitArrange is already created but contains model only at id
        if id in self.fit_arrange_dict:
            self.fit_arrange_dict[id].add_data(fitdata)
        else:
        #no fitArrange object has been create with this id
            fitproblem = FitArrange()
            fitproblem.add_data(fitdata)
            self.fit_arrange_dict[id] = fitproblem
   
    def get_model(self, id):
        """
        :param id: id is key in the dictionary containing the model to return
        
        :return:  a model at this id or None if no FitArrange element was
            created with this id
        """
        if id in self.fit_arrange_dict:
            return self.fit_arrange_dict[id].get_model()
        else:
            return None
    
    def remove_fit_problem(self, id):
        """remove   fitarrange in id"""
        if id in self.fit_arrange_dict:
            del self.fit_arrange_dict[id]
            
    def select_problem_for_fit(self, id, value):
        """
        select a couple of model and data at the id position in dictionary
        and set in self.selected value to value
        
        :param value: the value to allow fitting.
                can only have the value one or zero
        """
        if id in self.fit_arrange_dict:
            self.fit_arrange_dict[id].set_to_fit(value)
             
    def get_problem_to_fit(self, id):
        """
        return the self.selected value of the fit problem of id
        
        :param id: the id of the problem
        """
        if id in self.fit_arrange_dict:
            self.fit_arrange_dict[id].get_to_fit()
    
    
class FitArrange:
    def __init__(self):
        """
        Class FitArrange contains a set of data for a given model
        to perform the Fit.FitArrange must contain exactly one model
        and at least one data for the fit to be performed.
        
        model: the model selected by the user
        Ldata: a list of data what the user wants to fit
            
        """
        self.model = None
        self.data_list = []
        self.pars = []
        self.vals = []
        self.selected = 0
        
    def set_model(self, model):
        """
        set_model save a copy of the model
        
        :param model: the model being set
        """
        self.model = model
        
    def add_data(self, data):
        """
        add_data fill a self.data_list with data to fit
        
        :param data: Data to add in the list
        """
        if not data in self.data_list:
            self.data_list.append(data)
            
    def get_model(self):
        """
        :return: saved model
        """
        return self.model
     
    def get_data(self):
        """
        :return: list of data data_list
        """
        return self.data_list[0]
      
    def remove_data(self, data):
        """
        Remove one element from the list
        
        :param data: Data to remove from data_list
        """
        if data in self.data_list:
            self.data_list.remove(data)
            
    def set_to_fit(self, value=0):
        """
        set self.selected to 0 or 1  for other values raise an exception
        
        :param value: integer between 0 or 1
        """
        self.selected = value
        
    def get_to_fit(self):
        """
        return self.selected value
        """
        return self.selected
    
    
IS_MAC = True
if sys.platform.count("win32") > 0:
    IS_MAC = False


class FResult(object):
    """
    Storing fit result
    """
    def __init__(self, model=None, param_list=None, data=None):
        self.calls = None
        self.pars = []
        self.fitness = None
        self.chisqr = None
        self.pvec = []
        self.cov = []
        self.info = None
        self.mesg = None
        self.success = None
        self.stderr = None
        self.residuals = []
        self.index = []
        self.parameters = None
        self.is_mac = IS_MAC
        self.model = model
        self.data = data
        self.theory = []
        self.param_list = param_list
        self.iterations = 0
        self.inputs = []
        self.fitter_id = None
        if self.model is not None and self.data is not None:
            self.inputs = [(self.model, self.data)]
     
    def set_model(self, model):
        """
        """
        self.model = model
        
    def set_fitness(self, fitness):
        """
        """
        self.fitness = fitness
        
    def __str__(self):
        """
        """
        if self.pvec == None and self.model is None and self.param_list is None:
            return "No results"
        n = len(self.model.parameterset)
        
        result_param = zip(xrange(n), self.model.parameterset)
        msg1 = ["[Iteration #: %s ]" % self.iterations]
        msg3 = ["=== goodness of fit: %s ===" % (str(self.fitness))]
        if not self.is_mac:
            msg2 = ["P%-3d  %s......|.....%s" % \
                (p[0], p[1], p[1].value)\
                  for p in result_param if p[1].name in self.param_list]
            msg = msg1 + msg3 + msg2
        else:
            msg = msg1 + msg3
        msg = "\n".join(msg)
        return msg
    
    def print_summary(self):
        """
        """
        print self
