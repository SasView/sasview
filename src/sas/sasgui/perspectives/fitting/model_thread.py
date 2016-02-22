"""
    Calculation thread for modeling
"""

import time
import numpy
import math
from sas.sascalc.data_util.calcthread import CalcThread

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
                 worktime=0.04
                 ):
        CalcThread.__init__(self, completefn, updatefn, yieldtime, worktime)
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
        if self.qmin == None:
            self.qmin = 0
        if self.qmax == None:
            if self.data != None:
                newx = math.pow(max(math.fabs(self.data.xmax),
                                   math.fabs(self.data.xmin)), 2)
                newy = math.pow(max(math.fabs(self.data.ymax),
                                   math.fabs(self.data.ymin)), 2)
                self.qmax = math.sqrt(newx + newy)

        if self.data is None:
            msg = "Compute Calc2D receive data = %s.\n" % str(self.data)
            raise ValueError, msg

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
            # Get necessary data from self.data and set the data for smearing
            fn.get_data()
            # Calculate smeared Intensity
            #(by Gaussian averaging): DataLoader/smearing2d/Smearer2D()
            value = fn.get_value()
        else:
            # calculation w/o smearing
            value = self.model.evalDistribution(\
                [self.data.qx_data[index_model],
                 self.data.qy_data[index_model]])
        output = numpy.zeros(len(self.data.qx_data))
        # output default is None
        # This method is to distinguish between masked
        #point(nan) and data point = 0.
        output = output / output
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
                 worktime=0.01
                 ):
        """
        """
        CalcThread.__init__(self, completefn,
                 updatefn,
                 yieldtime,
                 worktime)
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
        output = numpy.zeros((len(self.data.x)))
        index = (self.qmin <= self.data.x) & (self.data.x <= self.qmax)

        ##smearer the ouput of the plot
        if self.smearer is not None:
            first_bin, last_bin = self.smearer.get_bin_range(self.qmin,
                                                             self.qmax)
            mask = self.data.x[first_bin:last_bin+1]
            output[first_bin:last_bin+1] = self.model.evalDistribution(mask)
            output = self.smearer(output, first_bin, last_bin)
        else:
            output[index] = self.model.evalDistribution(self.data.x[index])

        elapsed = time.time() - self.starttime

        self.complete(x=self.data.x[index], y=output[index],
                      page_id=self.page_id,
                      state=self.state,
                      weight=self.weight,
                      fid=self.fid,
                      toggle_mode_on=self.toggle_mode_on,
                      elapsed=elapsed, index=index, model=self.model,
                      data=self.data,
                      update_chisqr=self.update_chisqr,
                      source=self.source)

    def results(self):
        """
        Send resuts of the computation
        """
        return [self.out, self.index]

"""
Example: ::

    class CalcCommandline:
        def __init__(self, n=20000):
            #print thread.get_ident()
            from sas.models.CylinderModel import CylinderModel

            model = CylinderModel()


            print model.runXY([0.01, 0.02])

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
            print "update"

        def complete(self, image, data, model, elapsed, qmin, qmax,index, qstep ):
            print "complete"
            self.done = True

    if __name__ == "__main__":
        CalcCommandline()
"""
