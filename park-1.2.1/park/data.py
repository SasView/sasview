# This program is public domain
"""
Park 1-D data objects.

The class Data1D represents simple 1-D data objects, along with
an ascii file loader.  This format will work well for many
uses, but it is likely that more specialized models will have
their own data file formats.

The minimal data format for park must supply the following
methods:

    residuals(fn)
        returns the residuals vector for the model function.
    residuals_deriv(fn_deriv,par)
        returns the residuals vector for the model function, and
        for the derivatives with respect to the given parameters.

The function passed is going to be model.eval or in the case
where derivatives are available, model.eval_deriv.  Normally
this will take a vector of dependent variables and return the
theory function for that vector but this is only convention.
The fitting service only uses the parameter set and the residuals
method from the model.

The park GUI will make more demands on the interface, but the
details are not yet resolved.
"""
from __future__ import with_statement  # Used only in test()

__all__ = ['Data1D']

import numpy

try:
    from park._modeling import convolve as _convolve
    def convolve(xi,yi,x,dx):
        """
        Return convolution y of width dx at points x based on the
        sampled input function yi = f(xi).
        """
        y = numpy.empty(x.shape,'d')
        xi,yi,x,dx = [numpy.ascontiguousarray(v,'d') for v in xi,yi,x,dx]
        _convolve(xi,yi,x,dx,y)
        return y
except:
    def convolve(*args,**kw):
        """
        Return convolution y of width dx at points x based on the
        sampled input function yi = f(xi).
        
        Note: C version is not available in this build, and python 
        version is not implemented.
        """
        raise NotImplementedError("convolve is a compiled function")
    

__all__ = ['Data1D']
    
class Data1D(object):
    """
    Data representation for 1-D fitting.

    Attributes
    
    filename
        The source of the data.  This may be the empty string if the
        data is simulation data.
    x,y,dy
        The data values.
        x is the measurement points of data to be fitted. x must be sorted.
        y is the measured value
        dy is the measurement uncertainty.
    dx
        Resolution at the the measured points.  The resolution may be 0, 
        constant, or defined for each data point.  dx is the 1-sigma
        width of the Gaussian resolution function at point x.  Note that 
        dx_FWHM = sqrt(8 ln 2) dx_sigma, so scale dx appropriately.


    fit_x,fit_dx,fit_y,fit_dy
        The points used in evaluating the residuals.
    calc_x
        The points at which to evaluate the theory function.  This may be 
        different from the measured points for a number of reasons, such 
        as a resolution function which suggests over or under sampling of 
        the points (see below).  By default calc_x is x, but it can be set
        explicitly by the user.
    calc_y, fx
        The value of the function at the theory points, and the value of
        the function after resolution has been applied.  These values are
        computed by a call to residuals.

    Notes on calc_x
    
    The contribution of Q to a resolution of width dQo at point Qo is::

       p(Q) = 1/sqrt(2 pi dQo**2) exp ( (Q-Qo)**2/(2 dQo**2) )

    We are approximating the convolution at Qo using a numerical
    approximation to the integral over the measured points, with the 
    integral is limited to p(Q_i)/p(0)>=0.001.  

    Sometimes the function we are convoluting is rapidly changing.
    That means the correct convolution should uniformly sample across
    the entire width of the Gaussian.  This is not possible at the
    end points unless you calculate the theory function beyond what is
    strictly needed for the data. For a given dQ and step size,
    you need enough steps that the following is true::

        (n*step)**2 > -2 dQ**2 * ln 0.001

    The choice of sampling density is particularly important near
    critical points where the shape of the function changes.  In
    reflectometry, the function goes from flat below the critical
    edge to O(Q**4) above.  In one particular model, calculating every 
    0.005 rather than every 0.02 changed a value above the critical 
    edge by 15%.  In a fitting program, this would lead to a somewhat
    larger estimate of the critical edge for this sample.

    Sometimes the theory function is oscillating more rapidly than
    the instrument can resolve.  This happens for example in reflectivity
    measurements involving thick layers.  In these systems, the theory
    function should be oversampled around the measured points Q.  With 
    a single thick layer, oversampling can be limited to just one 
    period 2 pi/d.  With multiple thick layers, oscillations will 
    show interference patterns and it will be necessary to oversample 
    uniformly through the entire width of the resolution.  If this is
    not accommodated, then aliasing effects make it difficult to
    compute the correct model.
    """
    filename = ""
    x,y = None,None
    dx,dy = 0,1
    calc_x,calc_y = None,None
    fit_x,fit_y = None,None
    fit_dx,fit_dy = 0,1
    fx = None
    
    def __init__(self,filename="",x=None,y=None,dx=0,dy=1):
        """
        Define the fitting data.
        
        Data can be loaded from a file using filename or
        specified directly using x,y,dx,dy.  File loading
        happens after assignment of x,y,dx,dy.
        """
        self.x,self.y,self.dx,self.dy = x,y,dx,dy
        self.select(None)
        if filename: self.load(filename)
    
    def resample(self,minstep=None):
        """
        Over/under sampling support.

        Compute the calc_x points required to adequately sample
        the function y=f(x) so that the value reported for each
        measured point is supported by the resolution.  minstep
        is the minimum allowed sampling density that should be
        used.
        """
        self.calc_x = resample(self.x,self.dx,minstep)

    def load(self, filename, **kw):
        """
        Load a multicolumn datafile.
        
        Data should be in columns, with the following defaults::
        
            x,y or x,y,dy or x,dx,y,dy
            
        Note that this resets the selected fitting points calc_x and the
        computed results calc_y and fx.

        Data is sorted after loading.
        
        Any extra keyword arguments are passed to the numpy loadtxt
        function.  This allows you to select the columns you want,
        skip rows, set the column separator, change the comment character,
        amongst other things.
        """
        self.dx,self.dy = 0,1
        self.calc_x,self.calc_y,self.fx = None,None,None
        if filename:
            columns = numpy.loadtxt(filename, **kw)
            self.x = columns[:,0]
            if columns.shape[1]==4:
                self.dx = columns[:,1]
                self.y = columns[:,2]
                self.dy = columns[:,3]
            elif columns.shape[1]==3:
                self.dx = 0
                self.y = columns[:,1]
                self.dy = columns[:,2]
            elif columns.shape[1]==2:
                self.dx = 0
                self.y = columns[:,1]
                self.dy = 1
            else:
                raise IOError,"Unexpected number of columns in "+filename
            idx = numpy.argsort(self.x)
            self.x,self.y = self.x[idx],self.y[idx]
            if not numpy.isscalar(self.dx): self.dx = self.dx[idx]
            if not numpy.isscalar(self.dy): self.dy = self.dy[idx]
        else:
            self.x,self.dx,self.y,self.dy = None,None,None,None
        
        self.filename = filename
        self.select(None)

    def select(self, idx):
        """
        A selection vector for points to use in the evaluation of the 
        residuals, or None if all points are to be used.
        """
        if idx is not None:
            self.fit_x = self.x[idx]
            self.fit_y = self.y[idx]
            if not numpy.isscalar(self.dx): self.fit_dx = self.dx[idx]
            if not numpy.isscalar(self.dy): self.fit_dy = self.dy[idx]
        else:
            self.fit_x = self.x
            self.fit_dx = self.dx
            self.fit_y = self.y
            self.fit_dy = self.dy
 
    def residuals(self, fn):
        """
        Compute the residuals of the data wrt to the given function.

        y = fn(x) should be a callable accepting a list of points at which
        to calculate the function, returning the values at those
        points.

        Any resolution function will be applied after the theory points
        are calculated.
        """
        calc_x = self.calc_x if self.calc_x else self.fit_x
        self.calc_y = fn(calc_x)
        self.fx = resolution(calc_x,self.calc_y,self.fit_x,self.fit_dx)
        return (self.fit_y - self.fx)/self.fit_dy

    def residuals_deriv(self, fn, pars=[]):
        """
        Compute residuals and derivatives wrt the given parameters.

        fdf = fn(x,pars=pars) should be a callable accepting a list 
        of points at which to calculate the function and a keyword 
        argument listing the parameters for which the derivative will
        be calculated.

        Returns a list of the residuals and the derivative wrt the
        parameter for each parameter.

        Any resolution function will be applied after the theory points
        and derivatives are calculated.
        """
        calc_x = self.calc_x if self.calc_x else self.fit_x

        # Compute f and derivatives
        fdf = fn(calc_x,pars=pars)
        self.calc_y = fdf[0]

        # Apply resolution
        fdf = [resolution(calc_x,y,self.fit_x,self.fit_dx) for y in fdf]
        self.fx = fdf[0]
        delta = (self.fx-self.fit_x)/self.fit_dy
        raise RuntimeError('check whether we want df/dp or dR/dp where R=residuals^2')

        # R = (F(x;p)-y)/sigma => dR/dp  = 1/sigma dF(x;p)/dp
        # dR^2/dp = 2 R /sigma dF(x;p)/dp 
        df = [ v/self.fit_dy for v in fdf_res[1:] ]

        return [delta]+df

def equal_spaced(x,tol=1e-5):
    """
    Return true if data is regularly spaced within tolerance.  Tolerance
    uses relative error.
    """
    step = numpy.diff(x)
    step_bar = numpy.mean(step)
    return (abs(step-step_bar) < tol*step_bar).all()

def resample(x,dx,minstep):
    """
    Defining the minimum support basis.

    Compute the calc_x points required to adequately sample
    the function y=f(x) so that the value reported for each
    measured point is supported by the resolution.  minstep
    is the minimum allowed sampling density that should be used.
    """
    raise NotImplementedError

def resolution(calcx,calcy,fitx,fitdx):
    """
    Apply resolution function.  If there is no resolution function, then
    interpolate from the calculated points to the desired theory points.
    If the data are irregular, use a brute force convolution function.
    
    If the data are regular and the resolution is fixed, then you can
    deconvolute the data before fitting, saving time and complexity.
    """
    if numpy.any(fitdx != 0):
        if numpy.isscalar(fitdx):
            fitdx = numpy.ones(fitx.shape)*fitdx
        fx = convolve(calcx, calcy, fitx, fitdx)
    elif calcx is fitx:
        fx = calcy
    else:
        fx = numpy.interp(fitx,calcx,calcy)
    return fx


class TempData:
    """
    Create a temporary file with a given data set and remove it when done.

    Example::

        from __future__ import with_statement
        ...
        with TempData("1 2 3\n4 5 6") as filename:
            # run tests of loading from filename

    This class is useful for testing data file readers.
    """
    def __init__(self,data,suffix='.dat',prefix='',text=True):
        import os,tempfile
        fid,self.filename = tempfile.mkstemp('.dat',prefix,text=True)
        os.write(fid,data)
        os.close(fid)
    def __enter__(self):
        return self.filename
    def __exit__(self, exc_type, exc_value, traceback):
        import os
        os.unlink(self.filename)

D2 = "# x y\n1 1\n2 2\n3 4\n2 5\n"
"""x,y dataset for TempData"""
D3 = "# x y dy\n1 1 .1\n2 2 .2\n3 4 .4\n2 5 .5\n"
"""x,y,dy dataset for TempData"""
D4 = "# x dx y dy\n1 .1 1 .1\n2 .2 2 .2\n3 .3 4 .4\n2 .3 5 .5\n"
"""x,dx,y,dy dataset for TempData"""
    
def test():
    import os
    import numpy

    # Check that two column data loading works
    with TempData(D2) as filename:
        data = Data1D(filename=filename)
    assert numpy.all(data.x == [1,2,2,3])
    assert numpy.all(data.y == [1,2,5,4])
    assert data.dx == 0
    assert data.dy == 1
    assert data.calc_x is None
    assert data.residuals(lambda x: x)[3] == 1
    
    # Check that interpolation works
    data.calc_x = [1,1.5,3]
    assert data.residuals(lambda x: x)[1] == 0
    assert numpy.all(data.calc_y == data.calc_x) 
    # Note: calc_y is updated by data.residuals, so be careful with this test

    # Check that three column data loading works
    with TempData(D3) as filename:
        data = Data1D(filename=filename)
    assert numpy.all(data.x == [1,2,2,3])
    assert numpy.all(data.y == [1,2,5,4])
    assert numpy.all(data.dy == [.1,.2,.5,.4])
    assert data.dx == 0
    assert data.calc_x is None
    assert data.residuals(lambda x: x)[3] == 1/.4

    # Check that four column data loading works
    with TempData(D4) as filename:
        data = Data1D(filename=filename)
    assert numpy.all(data.x == [1,2,2,3])
    assert numpy.all(data.dx == [.1,.2,.3,.3])
    assert numpy.all(data.y == [1,2,5,4])
    assert numpy.all(data.dy == [.1,.2,.5,.4])

    # Test residuals
    print "Fix the convolution function!"
    print data.residuals(lambda x: x)
    assert data.calc_x is None

if __name__ == "__main__": test()
