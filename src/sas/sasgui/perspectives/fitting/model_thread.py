"""
Calculation thread for modeling
"""

import time
import math

import numpy as np

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
                newx = max(math.fabs(self.data.xmax), math.fabs(self.data.xmin))
                newy = max(math.fabs(self.data.ymax), math.fabs(self.data.ymin))
                self.qmax = math.sqrt(newx**2 + newy**2)

        if self.data is None:
            msg = "Compute Calc2D receive data = %s.\n" % str(self.data)
            raise ValueError, msg

        # Define matrix where data will be plotted
        radius = np.sqrt(self.data.qx_data**2 + self.data.qy_data**2)

        # For theory, qmax is based on 1d qmax
        # so that must be mulitified by sqrt(2) to get actual max for 2d
        index_model = (self.qmin <= radius) & (radius <= self.qmax)
        index_model &= self.data.mask
        index_model &= np.isfinite(self.data.data)

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
        # Initialize output to NaN so masked elements do not get plotted.
        output = np.empty_like(self.data.qx_data)
        # output default is None
        # This method is to distinguish between masked
        #point(nan) and data point = 0.
        output[:] = np.NaN
        # set value for self.mask==True, else still None to Plottools
        output[index_model] = value
        elapsed = time.time() - self.starttime
        self.complete(image=output,
                      data=self.data,
                      page_id=self.page_id,
                      model=self.model,
                      state=self.state,
                      toggle_mode_on=self.toggle_mode_on,
                      elapsed=elapsed,
                      index=index_model,
                      fid=self.fid,
                      qmin=self.qmin,
                      qmax=self.qmax,
                      weight=self.weight,
                      #qstep=self.qstep,
                      update_chisqr=self.update_chisqr,
                      source=self.source)


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
        output = np.zeros((len(self.data.x)))
        index = (self.qmin <= self.data.x) & (self.data.x <= self.qmax)

        # If we use a smearer, also return the unsmeared model
        unsmeared_output = None
        unsmeared_data = None
        unsmeared_error = None
        ##smearer the ouput of the plot
        if self.smearer is not None:
            first_bin, last_bin = self.smearer.get_bin_range(self.qmin,
                                                             self.qmax)
            mask = self.data.x[first_bin:last_bin+1]
            unsmeared_output = np.zeros((len(self.data.x)))
            unsmeared_output[first_bin:last_bin+1] = self.model.evalDistribution(mask)
            self.smearer.model = self.model
            output = self.smearer(unsmeared_output, first_bin, last_bin)

            # Rescale data to unsmeared model
            # Check that the arrays are compatible. If we only have a model but no data,
            # the length of data.y will be zero.
            if isinstance(self.data.y, np.ndarray) and output.shape == self.data.y.shape:
                unsmeared_data = np.zeros((len(self.data.x)))
                unsmeared_error = np.zeros((len(self.data.x)))
                unsmeared_data[first_bin:last_bin+1] = self.data.y[first_bin:last_bin+1]\
                                                        * unsmeared_output[first_bin:last_bin+1]\
                                                        / output[first_bin:last_bin+1]
                unsmeared_error[first_bin:last_bin+1] = self.data.dy[first_bin:last_bin+1]\
                                                        * unsmeared_output[first_bin:last_bin+1]\
                                                        / output[first_bin:last_bin+1]
                unsmeared_output = unsmeared_output[index]
                unsmeared_data = unsmeared_data[index]
                unsmeared_error = unsmeared_error
        else:
            output[index] = self.model.evalDistribution(self.data.x[index])

        x=self.data.x[index]
        y=output[index]
        sq_values = None
        pq_values = None
        if isinstance(self.model, MultiplicationModel):
            s_model = self.model.s_model
            p_model = self.model.p_model
            sq_values = s_model.evalDistribution(x)
            pq_values = p_model.evalDistribution(x)
        elif hasattr(self.model, "calc_composition_models"):
            results = self.model.calc_composition_models(x)
            if results is not None:
                pq_values, sq_values = results


        elapsed = time.time() - self.starttime

        self.complete(x=x, y=y,
                      page_id=self.page_id,
                      state=self.state,
                      weight=self.weight,
                      fid=self.fid,
                      toggle_mode_on=self.toggle_mode_on,
                      elapsed=elapsed, index=index, model=self.model,
                      data=self.data,
                      update_chisqr=self.update_chisqr,
                      source=self.source,
                      unsmeared_model=unsmeared_output,
                      unsmeared_data=unsmeared_data,
                      unsmeared_error=unsmeared_error,
                      pq_model=pq_values,
                      sq_model=sq_values)

    def results(self):
        """
        Send resuts of the computation
        """
        return [self.out, self.index]

"""
Example: ::

    class CalcCommandline:
        def __init__(self, n=20000):
            #print(thread.get_ident())

            from sasmodels.sasview_model import _make_standard_model
            cylinder = _make_standard_model('cylinder')
            model = cylinder()

            print(model.runXY([0.01, 0.02]))

            qmax = 0.01
            qstep = 0.0001
            self.done = False

            x = numpy.arange(-qmax, qmax+qstep*0.01, qstep)
            y = numpy.arange(-qmax, qmax+qstep*0.01, qstep)

            calc_thread_2D = Calc2D(x, y, None, model.clone(),None,
                                    -qmax, qmax,qstep,
                                    completefn=self.complete,
                                    updatefn=self.update ,
                                    yieldtime=0.0)

            calc_thread_2D.queue()
            calc_thread_2D.ready(2.5)

            while not self.done:
                time.sleep(1)

        def update(self,output):
            print("update")

        def complete(self, image, data, model, elapsed, qmin, qmax,index, qstep ):
            print("complete")
            self.done = True

    if __name__ == "__main__":
        CalcCommandline()
"""
