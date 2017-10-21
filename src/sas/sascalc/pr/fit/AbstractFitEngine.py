from __future__ import print_function

import  copy
#import logging
import sys
import math
import numpy as np

from sas.sascalc.dataloader.data_info import Data1D
from sas.sascalc.dataloader.data_info import Data2D
_SMALLVALUE = 1.0e-10

class FitHandler(object):
    """
    Abstract interface for fit thread handler.

    The methods in this class are called by the optimizer as the fit
    progresses.

    Note that it is up to the optimizer to call the fit handler correctly,
    reporting all status changes and maintaining the 'done' flag.
    """
    done = False
    """True when the fit job is complete"""
    result = None
    """The current best result of the fit"""

    def improvement(self):
        """
        Called when a result is observed which is better than previous
        results from the fit.

        result is a FitResult object, with parameters, #calls and fitness.
        """
    def error(self, msg):
        """
        Model had an error; print traceback
        """
    def progress(self, current, expected):
        """
        Called each cycle of the fit, reporting the current and the
        expected amount of work.   The meaning of these values is
        optimizer dependent, but they can be converted into a percent
        complete using (100*current)//expected.

        Progress is updated each iteration of the fit, whatever that
        means for the particular optimization algorithm.  It is called
        after any calls to improvement for the iteration so that the
        update handler can control I/O bandwidth by suppressing
        intermediate improvements until the fit is complete.
        """
    def finalize(self):
        """
        Fit is complete; best results are reported
        """
    def abort(self):
        """
        Fit was aborted.
        """

    # TODO: not sure how these are used, but they are needed for running the fit
    def update_fit(self, last=False): pass
    def set_result(self, result=None): self.result = result

class Model:
    """
    Fit wrapper for SAS models.
    """
    def __init__(self, sas_model, sas_data=None, **kw):
        """
        :param sas_model: the sas model to wrap for fitting

        """
        self.model = sas_model
        self.name = sas_model.name
        self.data = sas_data

    def get_params(self, fitparams):
        """
        return a list of value of paramter to fit

        :param fitparams: list of paramaters name to fit

        """
        return [self.model.getParam(k) for k in fitparams]

    def set_params(self, paramlist, params):
        """
        Set value for parameters to fit

        :param params: list of value for parameters to fit

        """
        for k,v in zip(paramlist, params):
            self.model.setParam(k,v)

    def set(self, **kw):
        self.set_params(*zip(*kw.items()))

    def eval(self, x):
        """
            Override eval method of model.

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
        raise NotImplementedError('no derivatives available')

    def __call__(self, x):
        return self.eval(x)

class FitData1D(Data1D):
    """
        Wrapper class  for SAS data
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

                from sas.sascalc.fit.qsmearing import smear_selection
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
        self.num_points = len(x)
        self.sas_data = data
        self.smearer = smearer
        self._first_unsmeared_bin = None
        self._last_unsmeared_bin = None
        # Check error bar; if no error bar found, set it constant(=1)
        # TODO: Should provide an option for users to set it like percent,
        # constant, or dy data
        if dy is None or dy == [] or dy.all() == 0:
            self.dy = np.ones(len(y))
        else:
            self.dy = np.asarray(dy).copy()

        ## Min Q-value
        #Skip the Q=0 point, especially when y(q=0)=None at x[0].
        if min(self.x) == 0.0 and self.x[0] == 0 and\
                     not np.isfinite(self.y[0]):
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
        if qmin == 0.0 and not np.isfinite(self.y[qmin]):
            self.qmin = min(self.x[self.x != 0])
        elif qmin is not None:
            self.qmin = qmin
        if qmax is not None:
            self.qmax = qmax
        # Determine the range needed in unsmeared-Q to cover
        # the smeared Q range
        self._qmin_unsmeared = self.qmin
        self._qmax_unsmeared = self.qmax

        self._first_unsmeared_bin = 0
        self._last_unsmeared_bin = len(self.x) - 1

        if self.smearer is not None:
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

    def size(self):
        """
        Number of measurement points in data set after masking, etc.
        """
        return len(self.x)

    def residuals(self, fn):
        """
            Compute residuals.

            If self.smearer has been set, use if to smear
            the data before computing chi squared.

            :param fn: function that return model value

            :return: residuals
        """
        # Compute theory data f(x)
        fx = np.zeros(len(self.x))
        fx[self.idx_unsmeared] = fn(self.x[self.idx_unsmeared])

        ## Smear theory data
        if self.smearer is not None:
            fx = self.smearer(fx, self._first_unsmeared_bin,
                              self._last_unsmeared_bin)
        ## Sanity check
        if np.size(self.dy) != np.size(fx):
            msg = "FitData1D: invalid error array "
            msg += "%d <> %d" % (np.shape(self.dy), np.size(fx))
            raise RuntimeError(msg)
        return (self.y[self.idx] - fx[self.idx]) / self.dy[self.idx], fx[self.idx]

    def residuals_deriv(self, model, pars=[]):
        """
            :return: residuals derivatives .

            :note: in this case just return empty array
        """
        return []


class FitData2D(Data2D):
    """
        Wrapper class  for SAS data
    """
    def __init__(self, sas_data2d, data=None, err_data=None):
        Data2D.__init__(self, data=data, err_data=err_data)
        # Data can be initialized with a sas plottable or with vectors.
        self.res_err_image = []
        self.num_points = 0 # will be set by set_data
        self.idx = []
        self.qmin = None
        self.qmax = None
        self.smearer = None
        self.radius = 0
        self.res_err_data = []
        self.sas_data = sas_data2d
        self.set_data(sas_data2d)

    def set_data(self, sas_data2d, qmin=None, qmax=None):
        """
            Determine the correct qx_data and qy_data within range to fit
        """
        self.data = sas_data2d.data
        self.err_data = sas_data2d.err_data
        self.qx_data = sas_data2d.qx_data
        self.qy_data = sas_data2d.qy_data
        self.mask = sas_data2d.mask

        x_max = max(math.fabs(sas_data2d.xmin), math.fabs(sas_data2d.xmax))
        y_max = max(math.fabs(sas_data2d.ymin), math.fabs(sas_data2d.ymax))

        ## fitting range
        if qmin is None:
            self.qmin = 1e-16
        if qmax is None:
            self.qmax = math.sqrt(x_max * x_max + y_max * y_max)
        ## new error image for fitting purpose
        if self.err_data is None or self.err_data == []:
            self.res_err_data = np.ones(len(self.data))
        else:
            self.res_err_data = copy.deepcopy(self.err_data)
        #self.res_err_data[self.res_err_data==0]=1

        self.radius = np.sqrt(self.qx_data**2 + self.qy_data**2)

        # Note: mask = True: for MASK while mask = False for NOT to mask
        self.idx = ((self.qmin <= self.radius) &\
                            (self.radius <= self.qmax))
        self.idx = (self.idx) & (self.mask)
        self.idx = (self.idx) & (np.isfinite(self.data))
        self.num_points = np.sum(self.idx)

    def set_smearer(self, smearer):
        """
            Set smearer
        """
        if smearer is None:
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
        elif qmin is not None:
            self.qmin = qmin
        if qmax is not None:
            self.qmax = qmax
        self.radius = np.sqrt(self.qx_data**2 + self.qy_data**2)
        self.idx = ((self.qmin <= self.radius) &\
                            (self.radius <= self.qmax))
        self.idx = (self.idx) & (self.mask)
        self.idx = (self.idx) & (np.isfinite(self.data))
        self.idx = (self.idx) & (self.res_err_data != 0)

    def get_fit_range(self):
        """
        return the range of data.x to fit
        """
        return self.qmin, self.qmax

    def size(self):
        """
        Number of measurement points in data set after masking, etc.
        """
        return np.sum(self.idx)

    def residuals(self, fn):
        """
        return the residuals
        """
        if self.smearer is not None:
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



class FitEngine:
    def __init__(self):
        """
        Base class for the fit engine
        """
        #Dictionnary of fitArrange element (fit problems)
        self.fit_arrange_dict = {}
        self.fitter_id = None

    def set_model(self, model, id, pars=[], constraints=[], data=None):
        """
        set a model on a given  in the fit engine.

        :param model: sas.models type
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
        if not pars:
            raise ValueError("no fitting parameters")

        if model is None:
            raise ValueError("no model to fit")

        if not issubclass(model.__class__, Model):
            model = Model(model, data)

        sasmodel = model.model
        available_parameters = sasmodel.getParamList()
        for p in pars:
            if p not in available_parameters:
                raise ValueError("parameter %s not available in model %s; use one of [%s] instead"
                                 %(p, sasmodel.name, ", ".join(available_parameters)))

        if id not in self.fit_arrange_dict:
            self.fit_arrange_dict[id] = FitArrange()

        self.fit_arrange_dict[id].set_model(model)
        self.fit_arrange_dict[id].pars = pars
        self.fit_arrange_dict[id].vals = [sasmodel.getParam(name) for name in pars]
        self.fit_arrange_dict[id].constraints = constraints

    def set_data(self, data, id, smearer=None, qmin=None, qmax=None):
        """
        Receives plottable, creates a list of data to fit,set data
        in a FitArrange object and adds that object in a dictionary
        with key id.

        :param data: data added
        :param id: unique key corresponding to a fitArrange object with data
        """
        if data.__class__.__name__ == 'Data2D':
            fitdata = FitData2D(sas_data2d=data, data=data.data,
                                 err_data=data.err_data)
        else:
            fitdata = FitData1D(x=data.x, y=data.y,
                                 dx=data.dx, dy=data.dy, smearer=smearer)
        fitdata.sas_data = data

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

class FResult(object):
    """
    Storing fit result
    """
    def __init__(self, model=None, param_list=None, data=None):
        self.calls = None
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
        if self.pvec is None and self.model is None and self.param_list is None:
            return "No results"

        sasmodel = self.model.model
        pars = enumerate(sasmodel.getParamList())
        msg1 = "[Iteration #: %s ]" % self.iterations
        msg3 = "=== goodness of fit: %s ===" % (str(self.fitness))
        msg2 = ["P%-3d  %s......|.....%s" % (i, v, sasmodel.getParam(v))
                for i,v in pars if v in self.param_list]
        msg = [msg1, msg3] + msg2
        return "\n".join(msg)

    def print_summary(self):
        """
        """
        print(str(self))
