# This program is public domain
"""
Define a park fitting model.

Usage
-----

The simplest sort of fitting model is something like the following::

    import numpy
    import park
    def G(x,mu,sigma):
        return numpy.exp(-0.5*(x-mu)**2/sigma**2)

    class Gauss(park.Model):
        parameters = ['center','width','scale']
        def eval(self,x):
            return self.scale * G(x,self.center,self.width)

It has a function which is evaluated at a series of x values and
a set of adjustable parameters controlling the shape of f(x).

You can check your module with something like the following::

    $ ipython -pylab

    from gauss import Gauss

    g = Gauss(center=5,width=1,scale=10)
    x = asarray([1,2,3,4,5])
    y = g(x)
    plot(x,y)

This should produce a plot of the Gaussian peak.

You will then want to try your model with some data.  Create a file
with some dummy data, such as gauss.dat::

    # x y
    4 2
    5 6
    6 7
    7 3

In order to match the model to data, you need to define a fitness
object.  This shows the difference between the model and the data,
which you can then plot or sum to create a weighted chisq value::

    f = park.Fitness(g, 'gauss.dat')
    plot(f.data.fit_x, f.residuals())

The data file can have up to four columns, either x,y or x,y,dy
or x,dx,y,dy where x,y are the measurement points and values,
dx is the instrument resolution in x and dy is the uncertainty
in the measurement value y.  You can pass any keyword arguments
to data.load that are accepted by numpy.loadtxt.  For example,
you can reorder columns or skip rows.  Additionally, you can modify
data attributes directly x,y,dx,dy and calc_x.  See help on park.Data1D
for details.

Once you have your model debugged you can use it in a fit::

    g = Gauss(center=[3,5],scale=7.2,width=[1,3])
    result = park.fit((g, 'gauss.dat'))
    result.plot()

In this example, center and width are allowed to vary but scale is fixed.

Existing models can be readily adapted to Park::

    class Gauss(object):
        "Existing model"
        center,width,scale = 0,1,1
        def __init__(self,**kw):
            for k,v in kw.items(): setattr(self,k,v)
        def eval(self,x):
            return self.scale *G(x,self.center,self.width)

    class GaussAdaptor(Gauss,Model):
        "PARK adaptor"
        parameters = ['center','width','scale']
        def __init__(self,*args,**kw):
            Model.__init__(self,*args)
            Gauss.__init__(self,**kw)

    g = GaussAdaptor(center=[3,5],scale=7.2,width=[1,3])
    result = park.fit((g, 'gauss.dat'))
    result.plot()

Models can become much more complex than the ones described above,
including multilevel models where fitting parameters can be added
and removed dynamically.

In many cases the park optimizer will need an adaptor for pre-existing
models.  The adaptor above relies on python properties to translate
model.par access into model._par.get() and model._par.set() where _par
is the internal name for par.  This technique works for simple static
models, but will not work well for sophisticated models which have,
for example, a dynamic parameter set where the model parameters cannot
be set as properties.  A solution to this problem is to subclass the
park.Parameter and override the value attribute as a property.

Once models are defined they can be used in a variety of contexts, such
as simultaneous fitting with constraints between the parameters.  With
some care in defining the model, computationally intensive fits can
be distributed across multiple processors.  We provide a simple user
interface for interacting with the model parameters and managing fits.
This can be extended with model specialized model editors which format
the parameters in a sensible way for the model, or allow direct manipulation
of the model structure.  The underlying fitting engine can also be
used directly from your own user interface.

"""

__all__ = ['Model']

import park
from park.parameter import Parameter, ParameterSet
from copy import copy, deepcopy


class ParameterProperty(object):
    """
    Attribute accessor for a named parameter.

    Objects of class ParameterProperty act similarly to normal property
    objects in that assignment to object.attr triggers the __set__
    method of ParameterProperty and queries of the value object.attr
    triggers the __get__ method.  These methods look up the actual
    parameter in the dictionary model.parameterset, delegating the
    the set/get methods of the underlying parameter object.

    For example::

        model.P1 = 5
        print model.P1

    is equivalent to::

        model.parameterset['P1'].set(5)
        print model.parameterset['P1'].get()

    To enable this behaviour, the model developer must assign a
    ParameterProperty object to a class attribute of the model.  It
    must be a class attribute.  Properties assigned as an instance
    attribute in the __init__ of the class will not be recognized
    as properties.

    An example model will look something like the following::

        class MyModel:
            # A property must be assigned as a class attribute!
            P1 = ParameterProperty('P1')
            P2 = ParameterProperty('P2')
            def __init__(self, P1=None, P2=None):
                parP1 = Parameter('P1')
                if P1 is not None: parP1.set(P1)
                parP2 = Parameter('P2')
                if P2 is not None: parP2.set(P2)
                self.parameterset = { 'P1': parP1, 'P2': parP2 }

    This work is done implicitly by MetaModel, and by subclassing
    the class Model, the model developer does not ever need to
    use ParameterProperty.
    """
    def __init__(self,name,**kw):
        self.name = name
    def __get__(self,instance,cls):
        return instance.parameterset[self.name].get()
    def __set__(self,instance,value):
        instance.parameterset[self.name].set(value)


class MetaModel(type):
    """
    Interpret parameters.

    This is a meta class, and the usual meta class rules apply.  That is,
    the Model base class should be defined like::

        class Model(object):
            __metaclass__ = MetaModel
            ...

    The MetaModel.__new__ method is called whenever a new Model
    class is created.  The name of the model, its superclasses and
    its attributes are passed to MetaModel.__new__ which creates the
    actual class.  It is not called for new instances of the model.

    MetaModel is designed to simplify the definition of parameters for
    the model.  When processing the class, MetaModel defines
    parameters which is a list of names of all the parameters in the
    model, and parameterset, which is a dictionary of the actual
    parameters and any parameter sets in the model.

    Parameters can be defined using a list of names in the parameter
    attribute, or by defining the individual parameters as separate
    attributes of class Parameter.

    For example, the following defines parameters P1, P2, and P3::

        class MyModel(Model):
            parameters = ['P1','P2']
            P2 = Parameter(range=[0,inf])
            P3 = Parameter()

    For each parameter, MetaModel will define a parameter accessor,
    and add the parameter definition to the parameter set. The accessor
    delegates query and assignment to the Parameter get/set methods. The
    attributes of the particular parameter instance can be
    adjusted using model.parameterset['name'].attribute = value.
    """
    def __new__(cls, name, bases, vars):
        #print 'calling model meta',vars

        # Find all the parameters for the model.  The listed parameters
        # are defined using::
        #    parameters = ['P1', 'P2', ...]
        # The remaining parameters are defined individually::
        #    P3 = Parameter()
        #    P4 = Parameter()
        # The undefined parameters are those that are listed but not defined.
        listed = vars.get('parameters',[])
        defined = [k for k,v in vars.items() if isinstance(v,Parameter)]
        undefined = [k for k in listed if k not in defined]
        #print listed,defined,undefined

        # Define a getter/setter for every parameter so that the user
        # can say model.name to access parameter name.
        #
        # Create a parameter object for every undefined parameter.
        # Check if the base class defines a default value, and use
        # that for the initial value.  We don't want to do this for
        # parameters explicitly defined since the user may have
        # given them a default value already.
        #
        # For predefined parameters we must set the name explicitly.
        # This saves the user from having to use, e.g.::
        #     P1 = Parameter('P1')
        pars = []
        for p in undefined:
            # Check if the attribute value is initialized in a base class
            for b in bases:
                if hasattr(b,p):
                    value = getattr(b,p)
                    break
            else:
                value = 0.
            #print "looking up value in base as",value
            pars.append(Parameter(name=p,value=value))
            vars[p] = ParameterProperty(p)
        for p in defined:
            # Make sure parameter name is correct.  Note that we are using
            # _name rather than .name to access the name attribute since
            # name is a read-only parameter.
            vars[p]._name = p
            pars.append(vars[p])
            vars[p] = ParameterProperty(p)

        # Construct the class attributes 'parameters' and 'parameterset'.
        # Listed parameters are given first, with unlisted parameters
        # following alphabetically.  For hierarchical parameter sets,
        # we also need to include the defined sets.
        unlisted = list(set(defined+undefined) - set(listed))
        unlisted.sort()
        parameters = listed + unlisted
        parsets = [k for k,v in vars.items() if isinstance(v,ParameterSet)]
        vars['parameters'] = parameters
        vars['parameterset'] = ParameterSet(pars=pars+parsets)
        #print 'pars',vars['parameters']
        #print 'parset',vars['parameterset']

        # Return a new specialized instance of the class with parameters
        # and parameterset made explicit.
        return type.__new__(cls, name, bases, vars)

class Model(object):
    """
    Model definition.

    The model manages attribute access to the fitting parameters and
    also manages the dataset.

    derivatives ['p1','p2',...]
        List of parameters for which the model can calculate
        derivatives.  The derivs
        The model function can compute the derivative with respect
        to this parameter.  The function model.derivs(x,[p1,p2,...])
        will return (f(x),df/dp1(x), ...).  The parameters and their
        order are determined by the fitting engine.

        Note: This is a property of the model, not the fit.
        Numerical derivatives will be used if the parameter is
        used in an expression or if no analytic derivative is
        available for the parameter.  Automatic differentiation
        on parameter expressions is possible, but beyond the scope
        of this project.

    eval(x)
        Evaluate the model at x.  This must be defined by the subclass.

    eval_deriv(x,pars=[])
        Evaluate the model and the derivatives at x.  This must be
        defined by the subclass.

    parameters
        The names of the model parameters.  If this is not provided, then
        the model will search the subclass for park.Parameter attributes
        and construct the list of names from that.  Any parameters in the
        list not already defined as park.Parameter attributes will be
        defined as parameters with a default of 0.

    parameterset
        The set of parameters defined by the model.  These are the
        parameters themselves, gathered into a park.ParameterSet.

    The minimum fittng model if you choose not to subclass park.Model
    requires parameterset and a residuals() method.
    """
    __metaclass__ = MetaModel
    derivatives = []
    def __init__(self,*args,**kw):
        """
        Initialize the model.

        Model('name',P1=value, P2=Value, ...)

        When overriding __init__ in the subclass be sure to call
        Model.__init__(self, *args, **kw).  This makes a private
        copy of the parameterset for the model and initializes
        any parameters set using keyword arguments.
        """
        #print 'calling model init on',id(self)
        # To avoid trashing the Model.parname = Parameter() template
        # when we create an instance and accessor for the parameter
        # we need to make sure that we are using our own copy of the
        # model dictionary stored in vars
        if len(args)>1: raise TypeError("expect name as model parameter")
        name = args[0] if len(args)>=1 else 'unknown'
        self.parameterset = deepcopy(self.parameterset)
        for k,v in kw.items():
            self.parameterset[k].set(v)
        self.parameterset._name = name
        #print 'done',id(self)

    def __call__(self, x, pars=[]):
        return self.eval(x)

    def eval(self, x):
        """
        Evaluate the model at x.

        This method needs to be specialized in the model to evaluate the
        model function.  Alternatively, the model can implement is own
        version of residuals which calculates the residuals directly
        instead of calling eval.
        """
        raise NotImplementedError('Model needs to implement eval')

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
        raise NotImplementedError('Model needs to implement eval_derivs')

    def set(self, **kw):
        """
        Set the initial value for a set of parameters.

        E.g., model.set(width=3,center=5)
        """
        # This is a convenience funciton for the user.
        #
        for k,v in kw.items():
            self.parameterset[k].set(v)


def add_parameter(model, name, **kw):
    """
    Add a parameter to an existing park model.

    Note: this may not work if it is operating on a BaseModel.
    """
    setattr(model.__class__, name, park.model.ParameterProperty(name))
    model.parameterset.append(park.Parameter(name=name, **kw))


def test():
    # Gauss theory function
    import numpy
    eps,inf = numpy.finfo('d').eps,numpy.inf
    def G(x,mu,sigma):
        mu,sigma = numpy.asarray(mu),numpy.asarray(sigma)
        return numpy.exp(-0.5*(x-mu)**2/sigma**2)

    # === Minimal model ===
    # just list the fitting parameters and define the function.
    class Gauss(Model):
        parameters = ['center','width','scale']
        def eval(self,x):
            return self.scale * G(x,self.center,self.width)

    # Create a couple of models and make sure they don't conflict
    g1 = Gauss(center=5,width=1,scale=2)
    assert g1.center == 5
    g2 = Gauss(center=6,width=1)
    assert g1.center == 5
    assert g2.center == 6
    assert g1(5) == 2
    assert g2(6) == 0

    # === explore parameters ===
    # dedicated model using park parameters directly, and defining derivatives
    class Gauss(Model):
        center = Parameter(value=0,
                           tip='Peak center')
        width = Parameter(value=1,
                          limits=(eps,inf),
                          tip='Peak width (1-sigma)')
        scale = Parameter(value=1,
                          limits=(0,inf),
                          tip='Peak scale (>0)')
        def eval(self,x):
            return self.scale * G(x,self.center,self.width)

        # Derivatives
        derivatives = ['center','width','scale']
        def dscale(self, g, x):
            return g/self.scale
        def dcenter(self, g, x):
            return 2*(x-self.center)/self.width*g
        def dwidth(self, g, x):
            return 2*(x-self.center)/self.width**3*g
        dmap = dict(scale=dscale,center=dcenter,width=dwidth)
        def eval_derivs(self,x,pars=[]):
            """
            Calculate function value and derivatives wrt to the parameters.

            pars is a list of parameter names, possibly consisting of any
            parameter with deriv=True.
            """
            g = self.eval(x)
            dg = [self.dmap[p](self,g,x) for p in pars]
            return [g]+dg

    g1 = Gauss(center=5)
    g1.parameterset['center'].tip = 'This is the center'
    assert g1.center == 5
    g2 = Gauss(center=6)
    assert g1.center == 5
    assert g2.center == 6
    assert g1(5) == 1
    assert g2(6) == 1

    # ====== Test wrapper =======
    # delegate to existing model via inheritence
    class Gauss(object):
        """Pre-existing model"""
        center,width,scale = 0,1,1
        def __init__(self,**kw):
            #print "calling BaseGauss init on",id(self)
            for k,v in kw.items(): setattr(self,k,v)
            #print "done",id(self)
        def eval(self,x):
            return self.scale *G(x,self.center,self.width)

    class GaussAdaptor(Gauss,Model):
        """PARK wrapper"""
        parameters = ['center','width','scale']
        def __init__(self,*args,**kw):
            #print "calling Gauss init on",id(self)
            Model.__init__(self,*args)
            Gauss.__init__(self,**kw)
            #print "done",id(self)

    g1 = GaussAdaptor(center=5)
    g2 = GaussAdaptor(center=6)
    g3 = GaussAdaptor()
    assert g1.center == 5
    assert g2.center == 6
    assert g3.scale == 1
    assert g1(5) == 1
    assert g2(6) == 1

    g4 = GaussAdaptor('M3',center=6)
    assert g4.parameterset.name == 'M3'

    # dedicated multilevel model using park parameters directly
    class MultiGauss(Model):
        def add(self,name,model):
            pass

    # wrapped model using park parameters indirectly
    class BaseMultiGauss(object):
        def __init__(self):
            self.models = []
        def add(self,**kw):
            self.models.append(BaseGauss(**kw))
    class WrapMultiGauss(BaseMultiGauss,Model):
        def __init__(self):
            pass

if __name__ == "__main__": test()
