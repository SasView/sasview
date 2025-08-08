"""
    Calculation thread for modeling
"""

import math
import time

import numpy

from sas import config
from sas.sascalc.data_util.calcthread import CalcThread
from sas.sascalc.fit.MultiplicationModel import MultiplicationModel


class Calc2D(CalcThread):
    """
    Compute 2D model
    This calculation assumes a 2-fold symmetry of the model
    where points are computed for one half of the detector
    and I(qx, qy) = I(-qx, -qy) is assumed.
    """
    def __init__(self, data, model, smearer, qmin, qmax, page_id,
                 state=None,
                 weight=None,
                 fid=None,
                 toggle_mode_on=False,
                 completefn=None,
                 updatefn=None,
                 update_chisqr=True,
                 source='model',
                 yieldtime=0.04,
                 worktime=0.04,
                 exception_handler=None,
                 ):
        CalcThread.__init__(self, completefn, updatefn, yieldtime, worktime,
                            exception_handler=exception_handler)
        self.qmin = qmin
        self.qmax = qmax
        self.weight = weight
        self.fid = fid
        #self.qstep = qstep
        self.toggle_mode_on = toggle_mode_on
        self.data = data
        self.page_id = page_id
        self.state = None
        # the model on to calculate
        self.model = model
        self.smearer = smearer
        self.starttime = 0
        self.update_chisqr = update_chisqr
        self.source = source

    def compute(self):
        """
        Compute the data given a model function
        """
        self.starttime = time.time()
        # Determine appropriate q range
        if self.qmin is None:
            self.qmin = 0
        if self.qmax is None:
            if self.data is not None:
                newx = math.pow(max(math.fabs(self.data.xmax),
                                   math.fabs(self.data.xmin)), 2)
                newy = math.pow(max(math.fabs(self.data.ymax),
                                   math.fabs(self.data.ymin)), 2)
                self.qmax = math.sqrt(newx + newy)

        if self.data is None:
            msg = "Compute Calc2D receive data = %s.\n" % str(self.data)
            raise ValueError(msg)

        # Define matrix where data will be plotted
        radius = numpy.sqrt((self.data.qx_data * self.data.qx_data) + \
                    (self.data.qy_data * self.data.qy_data))

        # For theory, qmax is based on 1d qmax
        # so that must be mulitified by sqrt(2) to get actual max for 2d
        index_model = (self.qmin <= radius) & (radius <= self.qmax)
        index_model = index_model & self.data.mask
        index_model = index_model & numpy.isfinite(self.data.data)

        if self.smearer is not None:
            # Set smearer w/ data, model and index.
            fn = self.smearer
            fn.set_model(self.model)
            fn.set_index(index_model)
            # Calculate smeared Intensity
            #(by Gaussian averaging): DataLoader/smearing2d/Smearer2D()
            value = fn.get_value()
        else:
            # calculation w/o smearing
            value = self.model.evalDistribution([
                self.data.qx_data[index_model],
                self.data.qy_data[index_model]
            ])
        output = numpy.zeros(len(self.data.qx_data))
        # output default is None
        # This method is to distinguish between masked
        #point(nan) and data point = 0.
        output = output / output
        # set value for self.mask==True, else still None to Plottools
        output[index_model] = value
        elapsed = time.time() - self.starttime

        res = dict(image = output, data = self.data, page_id = self.page_id,
            model = self.model, state = self.state,
            toggle_mode_on = self.toggle_mode_on, elapsed = elapsed,
            index = index_model, fid = self.fid,
            qmin = self.qmin, qmax = self.qmax,
            weight = self.weight, update_chisqr = self.update_chisqr,
            source = self.source)

        if config.USING_TWISTED:
            return res
        else:
            self.completefn(res)

class Calc1D(CalcThread):
    """
    Compute 1D data
    """
    def __init__(self, model,
                 page_id,
                 data,
                 fid=None,
                 qmin=None,
                 qmax=None,
                 weight=None,
                 smearer=None,
                 toggle_mode_on=False,
                 state=None,
                 completefn=None,
                 update_chisqr=True,
                 source='model',
                 updatefn=None,
                 yieldtime=0.01,
                 worktime=0.01,
                 exception_handler=None,
                 ):
        """
        """
        CalcThread.__init__(self, completefn, updatefn, yieldtime, worktime,
                            exception_handler=exception_handler)
        self.fid = fid
        self.data = data
        self.qmin = qmin
        self.qmax = qmax
        self.model = model
        self.weight = weight
        self.toggle_mode_on = toggle_mode_on
        self.state = state
        self.page_id = page_id
        self.smearer = smearer
        self.starttime = 0
        self.update_chisqr = update_chisqr
        self.source = source
        self.out = None
        self.index = None

    def compute(self):
        """
        Compute model 1d value given qmin , qmax , x value
        """
        self.starttime = time.time()
        output = numpy.zeros(len(self.data.x))
        index = (self.qmin <= self.data.x) & (self.data.x <= self.qmax)

        intermediate_results = None

        # If we use a smearer, also return the unsmeared model
        unsmeared_output = None
        unsmeared_data = None
        unsmeared_error = None
        ##smearer the ouput of the plot
        if self.smearer is not None:
            if self.data.isSesans:
                # For SESANS, data.x, qmin and qmax, and therefore get_bin_range are in real space, and
                # the Hankel transform from q space to real space is set up as a resolution function, i.e.,
                # the "unsmeared" data is in q space and the "smeared" data is in real space.
                # Therefore, q_calc needs to be used here to calculate the unsmeared_out rather than data.x.
                mask = self.smearer.resolution.q_calc
                first_bin = 0
                last_bin = len(mask)
                unsmeared_output = numpy.zeros(len(mask))
            else:
                first_bin, last_bin = self.smearer.get_bin_range(self.qmin,
                                                                 self.qmax)
                mask = self.data.x[first_bin:last_bin+1]
                unsmeared_output = numpy.zeros(len(self.data.x))

            return_data = self.model.calculate_Iq(mask)
            if isinstance(return_data, tuple):
                # see sasmodels beta_approx: SasviewModel.calculate_Iq
                # TODO: implement intermediate results in smearers
                return_data, intermediate_results = return_data
            unsmeared_output[first_bin:last_bin+1] = return_data
            output = self.smearer(unsmeared_output, first_bin, last_bin)
            # Rescale data to unsmeared model
            # Check that the arrays are compatible. If we only have a model but no data,
            # the length of data.y will be zero.
            # does not apply to SESANS where Hankel was implemented as resolution function
            if isinstance(self.data.y, numpy.ndarray) and output.shape == self.data.y.shape and not self.data.isSesans:
                unsmeared_data = numpy.zeros(len(self.data.x))
                unsmeared_error = numpy.zeros(len(self.data.x))
                unsmeared_data[first_bin:last_bin+1] = self.data.y[first_bin:last_bin+1]\
                                                        * unsmeared_output[first_bin:last_bin+1]\
                                                        / output[first_bin:last_bin+1]
                unsmeared_error[first_bin:last_bin+1] = self.data.dy[first_bin:last_bin+1]\
                                                        * unsmeared_output[first_bin:last_bin+1]\
                                                        / output[first_bin:last_bin+1]
                unsmeared_output=unsmeared_output[index]
                unsmeared_data=unsmeared_data[index]
                unsmeared_error=unsmeared_error
        else:
            return_data = self.model.calculate_Iq(self.data.x[index])
            if isinstance(return_data, tuple):
                # see sasmodels beta_approx: SasviewModel.calculate_Iq
                return_data, intermediate_results = return_data
            output[index] = return_data

        if intermediate_results:
            if isinstance(intermediate_results, list):
                # the model returns an ordered dictionary
                if len(intermediate_results) == 2:
                    intermediate_results  = {
                        "P(Q)": intermediate_results[0],
                        "S(Q)": intermediate_results[1]
                    }
            else:
                # the model returns a callable which is then used to retrieve the data
                try:
                    intermediate_results = intermediate_results()
                except:
                    intermediate_results = {}

        else:
            # TODO: this conditional branch needs refactoring
            sq_values = None
            pq_values = None
            s_model = None
            p_model = None

            if isinstance(self.model, MultiplicationModel):
                s_model = self.model.s_model
                p_model = self.model.p_model

            elif hasattr(self.model, "calc_composition_models"):
                results = self.model.calc_composition_models(self.data.x[index])
                if results is not None:
                    pq_values, sq_values = results

            if pq_values is None or sq_values is None:
                if p_model is not None and s_model is not None:
                    sq_values = numpy.zeros(len(self.data.x))
                    pq_values = numpy.zeros(len(self.data.x))
                    sq_values[index] = s_model.evalDistribution(self.data.x[index])
                    pq_values[index] = p_model.evalDistribution(self.data.x[index])

            if pq_values is not None and sq_values is not None:
                intermediate_results  = {
                    "P(Q)": pq_values,
                    "S(Q)": sq_values
                }
            else:
                intermediate_results = {}

        elapsed = time.time() - self.starttime

        res = dict(x = self.data.x[index], y = output[index],
            page_id = self.page_id, state = self.state, weight = self.weight,
            fid = self.fid, toggle_mode_on = self.toggle_mode_on,
            elapsed = elapsed, index = index, model = self.model,
            data = self.data, update_chisqr = self.update_chisqr,
            source = self.source, unsmeared_output = unsmeared_output,
            unsmeared_data = unsmeared_data, unsmeared_error = unsmeared_error,
            intermediate_results = intermediate_results)

        if config.USING_TWISTED:
            return res
        else:
            self.completefn(res)

    def results(self):
        """
        Send resuts of the computation
        """
        return [self.out, self.index]
