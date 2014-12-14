# This program is public domain
"""
An assembly is a collection of fitting functions.  This provides
the model representation that is the basis of the park fitting engine.

Models can range from very simple one dimensional theory functions
to complex assemblies of multidimensional datasets from different
experimental techniques, each with their own theory function and
a common underlying physical model.

Usage
=====

First define the models you want to work with.  In the example
below we will use an example of a simple multilayer system measured by
specular reflection of xrays and neutrons.  The gold depth is the only
fitting parameter, ranging from 10-30 A.  The interface depths are
tied together using expressions.  In this case the expression is
a simple copy, but any standard math functions can be used.  Some
model developers may provide additional functions for use with the
expression.

Example models::

    import reflectometry.model1d as refl
    xray = refl.model('xray')
    xray.incident('Air',rho=0)
    xray.interface('iAu',sigma=5)
    xray.layer('Au',rho=124.68,depth=[10,30])
    xray.interface('iSi',sigma=5)
    xray.substrate('Si',rho=20.07)
    datax = refl.data('xray.dat')

    neutron = refl.model('neutron')
    neutron.incident('Air',rho=0)
    neutron.interface('iAu',sigma='xray.iAu')
    neutron.layer('Au',rho=4.66,depth='xray.Au.depth')
    neutron.interface('iSi',sigma='xray.iSi')
    neutron.substrate('Si',rho=2.07)
    datan = refl.data('neutron.dat')

As you can see from the above, parameters can be set to a value if
the parameter is fixed, to a range if the parametemr is fitted, or
to a string expression if the parameter is calculated from other
parameters.  See park.Parameter.set for further details.

Having constructed the models, we can now create an assembly::

    import park
    assembly = park.Assembly([(xray,datax), (neutron,datan)])

Note: this would normally be done in the context of a fit
using fit = park.Fit([(xray,datax), (neutron,datan)]), and later referenced
using fit.assembly.

Individual parts of the assembly are accessable using the
model number 0, 1, 2... or by the model name.  In the above,
assembly[0] and assembly['xray'] refer to the same model.
Assemblies have insert and append functions for adding new
models, and "del model[idx]" for removing them.

Once the assembly is created computing the values for the system
is a matter of calling::

    assembly.eval()
    print "Chi**2",assembly.chisq
    print "Reduced chi**2",assembly.chisq/assembly.degrees_of_freedom
    plot(arange(len(assembly.residuals)), assembly.residuals)

This defines the attributes residuals, degrees_of_freedom and chisq,
which is what the optimizer uses as the cost function to minimize.

assembly.eval uses the current values for the parameters in the
individual models.  These parameters can be changed directly
in the model.  In the reflectometry example above, you could
set the gold thickness using xray.layer.Au.depth=156, or
something similar (the details are model specific).  Parameters
can also be changed through the assembly parameter set.  In the same
example, this would be assembly.parameterset['xray']['Au']['depth'].
See parameter set for details.

In the process of modeling data, particularly with multiple
datasets, you will sometimes want to temporarily ignore
how well one of the datasets matches so that you
can more quickly refine the model for the other datasets,
or see how particular models are influencing the fit.  To
temporarily ignore the xray data in the example above use::

    assembly.parts[0].isfitted = False

The model itself isn't ignored since its parameters may be
needed to compute the parameters for other models.  To
reenable checking against the xray data, you would assign
a True value instead.  More subtle weighting of the models
can be controlled using assembly.parts[idx].weight, but
see below for a note on model weighting.

A note on model weighting
-------------------------

Changing the weight is equivalent to scaling the error bars
on the given model by a factor of weight/n where n is the
number of data points.  It is better to set the correct error
bars on your data in the first place than to adjust the weights.
If you have the correct error bars, then you should expect
roughly 2/3 of the data points to lie within one error bar of
the theory curve.  If consecutive data points have largely
overlapping errorbars, then your uncertainty is overestimated.

Another case where weights are adjusted (abused?) is to
compensate for systematic errors in the data by forcing the
errorbars to be large enough to cover the systematic bias.
This is a poor approach to the problem.  A better strategy
is to capture the systematic effects in the model, and treat
the measurement of the independent variable as an additional
data point in the fit.  This is still not statistically sound
as there is likely to be a large correlation between the
uncertainty of the measurement and the values of all the
other variables.

That said, adjusting the weight on a dataset is a quick way
of reducing its influence on the entire fit.  Please use it
with care.
"""

__all__ = ['Assembly', 'Fitness']
import numpy

import park
from park.parameter import Parameter,ParameterSet
from park.fitresult import FitParameter
import park.expression



class Fitness(object):
    """
    Container for theory and data.

    The fit object compares theory with data.

    TODO: what to do with fittable metadata (e.g., footprint correction)?
    """
    data = None
    model = None
    def __init__(self, model=None,data=None):
        self.data,self.model = data,model
    def _parameterset(self):
        return self.model.parameterset
    parameterset = property(_parameterset)
    def residuals(self):
        return self.data.residuals(self.model.eval)
    def residuals_deriv(self, pars=[]):
        return self.data.residuals_deriv(self.model.eval_derivs,pars=pars)
    def set(self, **kw):
        """
        Set parameters in the model.

        User convenience function.  This allows a user with an assembly
        of models in a script to for example set the fit range for
        parameter 'a' of the model::

            assembly[0].set(a=[5,6])

        Raises KeyError if the parameter is not in parameterset.
        """
        self.model.set(**kw)
    def abort(self):
        if hasattr(self.model,'abort'): self.model.abort()

class Part(object):
    """
    Part of a fitting assembly.  Part holds the model itself and
    associated data.  The part can be initialized with a fitness
    object or with a pair (model,data) for the default fitness function.

    fitness (Fitness)
        object implementing the `park.assembly.Fitness` interface.  In
        particular, fitness should provide a parameterset attribute
        containing a ParameterSet and a residuals method returning a vector
        of residuals.
    weight (dimensionless)
        weight for the model.  See comments in assembly.py for details.
    isfitted (boolean)
        True if the model residuals should be included in the fit.
        The model parameters may still be used in parameter
        expressions, but there will be no comparison to the data.
    residuals (vector)
        Residuals for the model if they have been calculated, or None
    degrees_of_freedom
        Number of residuals minus number of fitted parameters.
        Degrees of freedom for individual models does not make
        sense in the presence of expressions combining models,
        particularly in the case where a model has many parameters
        but no data or many computed parameters.  The degrees of
        freedom for the model is set to be at least one.
    chisq
        sum(residuals**2); use chisq/degrees_of_freedom to
        get the reduced chisq value.

        Get/set the weight on the given model.

        assembly.weight(3) returns the weight on model 3 (0-origin)
        assembly.weight(3,0.5) sets the weight on model 3 (0-origin)
    """

    def __init__(self, fitness, weight=1., isfitted=True):
        if isinstance(fitness, tuple):
            fitness = park.Fitness(*fitness)
        self.fitness = fitness
        self.weight = weight
        self.isfitted = isfitted
        self.residuals = None
        self.chisq = numpy.Inf
        self.degrees_of_freedom = 1


class Assembly(object):
    """
    Collection of fit models.

    Assembly implements the `park.fit.Objective` interface.

    See `park.assembly` for usage.

    Instance variables:

    residuals : array
        a vector of residuals spanning all models, with model
        weights applied as appropriate.
    degrees_of_freedom : integer
        length of the residuals - number of fitted parameters
    chisq : float
        sum squared residuals; this is not the reduced chisq, which
        you can get using chisq/degrees_of_freedom

    These fields are defined for the individual models as well, with
    degrees of freedom adjusted to the length of the individual data
    set.  If the model is not fitted or the weight is zero, the residual
    will not be calculated.

    The residuals fields are available only after the model has been
    evaluated.
    """

    def __init__(self, models=[]):
        """Build an assembly from a list of models."""
        self.parts = []
        for m in models:
            self.parts.append(Part(m))
        self._reset()

    def __iter__(self):
        """Iterate through the models in order"""
        for m in self.parts: yield m

    def __getitem__(self, n):
        """Return the nth model"""
        return self.parts[n].fitness

    def __setitem__(self, n, fitness):
        """Replace the nth model"""
        self.parts[n].fitness = fitness
        self._reset()

    def __delitem__(self, n):
        """Delete the nth model"""
        del self.parts[n]
        self._reset()

    def weight(self, idx, value=None):
        """
        Query the weight on a particular model.

        Set weight to value if value is supplied.

        :Parameters:
         idx : integer
           model number
         value : float
           model weight
        :return: model weight
        """
        if value is not None:
            self.parts[idx].weight = value
        return self.parts[idx].weight

    def isfitted(self, idx, value=None):
        """
        Query if a particular model is fitted.

        Set isfitted to value if value is supplied.

        :param idx: model number
        :type idx: integer
        :param value:
        """
        if value is not None:
            self.parts[idx].isfitted = value
        return self.parts[idx].isfitted

    def append(self, fitness, weight=1.0, isfitted=True):
        """
        Add a model to the end of set.

        :param fitness: the fitting model
            The fitting model can be an instance of `park.assembly.Fitness`,
            or a tuple of (`park.model.Model`,`park.data.Data1D`)
        :param weight: model weighting (usually 1.0)
        :param isfitted: whether model should be fit (equivalent to weight 0.)
        """
        self.parts.append(Part(fitness,weight,isfitted))
        self._reset()

    def insert(self, idx, fitness, weight=1.0, isfitted=True):
        """Add a model to a particular position in the set."""
        self.parts.insert(idx,Part(fitness,weight,isfitted))
        self._reset()

    def _reset(self):
        """Adjust the parameter set after the addition of a new model."""
        subsets = [m.fitness.parameterset for m in self]
        self.parameterset = ParameterSet('root',subsets)
        self.parameterset.setprefix()
        #print [p.path for p in self.parameterset.flatten()]

    def eval(self):
        """
        Recalculate the theory functions, and from them, the
        residuals and chisq.

        :note: Call this after the parameters have been updated.
        """
        # Handle abort from a separate thread.
        self._cancel = False

        # Evaluate the computed parameters
        self._fitexpression()

        # Check that the resulting parameters are in a feasible region.
        if not self.isfeasible(): return numpy.inf

        resid = []
        k = len(self._fitparameters)
        for m in self.parts:
            # In order to support abort, need to be able to propagate an
            # external abort signal from self.abort() into an abort signal
            # for the particular model.  Can't see a way to do this which
            # doesn't involve setting a state variable.
            self._current_model = m
            if self._cancel: return numpy.inf
            if m.isfitted and m.weight != 0:
                m.residuals = m.fitness.residuals()
                N = len(m.residuals)
                m.degrees_of_freedom = N-k if N>k else 1
                m.chisq = numpy.sum(m.residuals**2)
                resid.append(m.weight*m.residuals)
        self.residuals = numpy.hstack(resid)
        N = len(self.residuals)
        self.degrees_of_freedom = N-k if N>k else 1
        self.chisq = numpy.sum(self.residuals**2)
        return self.chisq

    def jacobian(self, pvec, step=1e-8):
        """
        Returns the derivative wrt the fit parameters at point p.

        Numeric derivatives are calculated based on step, where step is
        the portion of the total range for parameter j, or the portion of
        point value p_j if the range on parameter j is infinite.
        """
        # Make sure the input vector is an array
        pvec = numpy.asarray(pvec)
        # We are being lazy here.  We can precompute the bounds, we can
        # use the residuals_deriv from the sub-models which have analytic
        # derivatives and we need only recompute the models which depend
        # on the varying parameters.
        # Meanwhile, let's compute the numeric derivative using the
        # three point formula.
        # We are not checking that the varied parameter in numeric
        # differentiation is indeed feasible in the interval of interest.
        range = zip(*[p.range for p in self._fitparameters])
        lo,hi = [numpy.asarray(v) for v in range]
        delta = (hi-lo)*step
        # For infinite ranges, use p*1e-8 for the step size
        idx = numpy.isinf(delta)
        #print "J",idx,delta,pvec,type(idx),type(delta),type(pvec)
        delta[idx] = pvec[idx]*step
        delta[delta==0] = step

        # Set the initial value
        for k,v in enumerate(pvec):
            self._fitparameters[k].value = v
        # Gather the residuals
        r = []
        for k,v in enumerate(pvec):
            # Center point formula:
            #     df/dv = lim_{h->0} ( f(v+h)-f(v-h) ) / ( 2h )
            h = delta[k]
            self._fitparameters[k].value = v + h
            self.eval()
            rk = self.residuals
            self._fitparameters[k].value = v - h
            self.eval()
            rk -= self.residuals
            self._fitparameters[k].value = v
            r.append(rk/(2*h))
        # return the jacobian
        return numpy.vstack(r).T


    def cov(self, pvec):
        """
        Return the covariance matrix inv(J'J) at point p.
        """

        # Find cov of f at p
        #     cov(f,p) = inv(J'J)
        # Use SVD
        #     J = U S V'
        #     J'J = (U S V')' (U S V')
        #         = V S' U' U S V'
        #         = V S S V'
        #     inv(J'J) = inv(V S S V')
        #              = inv(V') inv(S S) inv(V)
        #              = V inv (S S) V'
        J = self.jacobian(pvec)
        u,s,vh = numpy.linalg.svd(J,0)
        JTJinv = numpy.dot(vh.T.conj()/s**2,vh)
        return JTJinv

    def stderr(self, pvec):
        """
        Return parameter uncertainty.

        This is just the sqrt diagonal of covariance matrix inv(J'J) at point p.
        """
        return numpy.sqrt(numpy.diag(self.cov(pvec)))

    def isfeasible(self):
        """
        Returns true if the parameter set is in a feasible region of the
        modeling space.
        """
        return True

    # Fitting service interface
    def fit_parameters(self):
        """
        Return an alphabetical list of the fitting parameters.

        This function is called once at the beginning of a fit,
        and serves as a convenient place to precalculate what
        can be precalculated such as the set of fitting parameters
        and the parameter expressions evaluator.
        """
        self.parameterset.setprefix()
        self._fitparameters = self.parameterset.fitted
        self._restraints = self.parameterset.restrained
        pars = self.parameterset.flatten()
        context = self.parameterset.gather_context()
        self._fitexpression = park.expression.build_eval(pars,context)
        #print "constraints",self._fitexpression.__doc__

        self._fitparameters.sort(lambda a,b: cmp(a.path,b.path))
        # Convert to fitparameter a object
        fitpars = [FitParameter(p.path,p.range,p.value)
                   for p in self._fitparameters]
        return fitpars

    def set_result(self, result):
        """
        Set the parameters resulting from the fit into the parameter set,
        and update the calculated expression.

        The parameter values may be retrieved by walking the assembly.parameterset
        tree, checking each parameter for isfitted, iscomputed, or isfixed.
        For example::

            assembly.set_result(result)
            for p in assembly.parameterset.flatten():
                if p.isfitted():
                    print "%s %g in [%g,%g]"%(p.path,p.value,p.range[0],p.range[1])
                elif p.iscomputed():
                    print "%s computed as %g"%(p.path.p.value)

        This does not calculate the function or the residuals for these parameters.
        You can call assembly.eval() to do this.  The residuals will be set in
        assembly[i].residuals.  The theory and data are model specific, and can
        be found in assembly[i].fitness.data.
        """
        for n,p in enumerate(result.parameters):
            self._fitparameters[n] = p.value
        self._fitexpression()

    def all_results(self, result):
        """
        Extend result from the fit with the calculated parameters.
        """
        calcpars = [FitParameter(p.path,p.range,p.value)
                    for p in self.parameterset.computed]
        result.parameters += calcpars

    def result(self, status='step'):
        """
        Details to send back to the fitting client on an improved fit.

        status is 'start', 'step' or 'end' depending if this is the
        first result to return, an improved result, or the final result.

        [Not implemented]
        """
        return None

    def fresiduals(self, pvec):
        chisq = self.__call__(pvec)
        return self.residuals

    def __call__(self, pvec):
        """
        Cost function.

        Evaluate the system for the parameter vector pvec, returning chisq
        as the cost function to be minimized.

        Raises a runtime error if the number of fit parameters is
        different than the length of the vector.
        """
        # Plug fit parameters into model
        #print "Trying",pvec
        pars = self._fitparameters
        if len(pvec) != len(pars):
            raise RuntimeError("Unexpected number of parameters")
        for n,value in enumerate(pvec):
            pars[n].value = value
        # Evaluate model
        chisq = self.eval()
        # Evaluate additional restraints based on parameter value
        # likelihood
        restraints_penalty = 0
        for p in self._restraints:
            restraints_penalty += p.likelihood(p.value)
        # Return total cost function
        return self.chisq + restraints_penalty

    def abort(self):
        """
        Interrupt the current function evaluation.

        Forward this to the currently executing model if possible.
        """
        self._cancel = True
        if hasattr(self._current_model,'abort'):
            self._current_model.abort()

class _Exp(park.Model):
    """
    Sample model for testing assembly.
    """
    parameters = ['a','c']
    def eval(self,x):
        return self.a*numpy.exp(self.c*x)
class _Linear(park.Model):
    parameters = ['a','c']
    def eval(self,x):
        #print "eval",self.a,self.c,x,self.a*x+self.c
        return self.a*x+self.c
def example():
    """
    Return an example assembly consisting of a pair of functions,
        M1.a*exp(M1.c*x), M2.a*exp(2*M1.c*x)
    and ideal data for
        M1.a=1, M1.c=1.5, M2.a=2.5
    """
    import numpy
    import park
    from numpy import inf
    # Make some fake data
    x1 = numpy.linspace(0,1,11)
    x2 = numpy.linspace(0,1,12)
    # Define a shared model
    if True: # Exp model
        y1,y2 = numpy.exp(1.5*x1),2.5*numpy.exp(3*x2)
        M1 = _Exp('M1',a=[1,3],c=[1,3])
        M2 = _Exp('M2',a=[1,3],c='2*M1.c')
        #M2 = _Exp('M2',a=[1,3],c=3)
    else:  # Linear model
        y1,y2 = x1+1.5, 2.5*x2+3
        M1 = _Linear('M1',a=[1,3],c=[1,3])
        M2 = _Linear('M2',a=[1,3],c='2*M1.c')
    if False: # Unbounded
        M1.a = [-inf,inf]
        M1.c = [-inf,inf]
        M2.a = [-inf,inf]
    D1 = park.Data1D(x=x1, y=y1)
    D2 = park.Data1D(x=x2, y=y2)
    # Construct the assembly
    assembly = park.Assembly([(M1,D1),(M2,D2)])
    return assembly

class _Sphere(park.Model):
    parameters = ['a','b','c','d','e']
    def eval(self,x):
        return self.a*x**2+self.b*x+self.c + exp(self.d) - 3*sin(self.e)

def example5():
    import numpy
    import park
    from numpy import inf
    # Make some fake data
    x = numpy.linspace(0,1,11)
    # Define a shared model
    S = _Sphere(a=1,b=2,c=3,d=4,e=5)
    y = S.eval(x1)
    Sfit = _Sphere(a=[-inf,inf],b=[-inf,inf],c=[-inf,inf],d=[-inf,inf],e=[-inf,inf])
    D = park.Data1D(x=x, y=y)
    # Construct the assembly
    assembly = park.Assembly([(Sfit,D)])
    return assembly

def test():
    assembly = example()
    assert assembly[0].parameterset.name == 'M1'

    # extract the fitting parameters
    pars = [p.name for p in assembly.fit_parameters()]
    assert set(pars) == set(['M1.a','M1.c','M2.a'])
    # Compute chisq and verify constraints are updated properly
    assert assembly([1,1.5,2.5]) == 0
    assert assembly[0].model.c == 1.5 and assembly[1].model.c == 3

    # Try without constraints
    assembly[1].set(c=3)
    assembly.fit_parameters()  # Fit parameters have changed
    assert assembly([1,1.5,2.5]) == 0

    # Check that assembly.cov runs ... still need to check that it is correct!
    C = assembly.cov(numpy.array([1,1.5,2.5]))

if __name__ == "__main__": test()
