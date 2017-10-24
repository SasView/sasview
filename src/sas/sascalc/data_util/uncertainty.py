r"""
Uncertainty propagation class for arithmetic, log and exp.

Based on scalars or numpy vectors, this class allows you to store and
manipulate values+uncertainties, with propagation of gaussian error for
addition, subtraction, multiplication, division, power, exp and log.

Storage properties are determined by the numbers used to set the value
and uncertainty.  Be sure to use floating point uncertainty vectors
for inplace operations since numpy does not do automatic type conversion.
Normal operations can use mixed integer and floating point.  In place
operations such as *a \*= b* create at most one extra copy for each operation.
By contrast, *c = a\*b* uses four intermediate vectors, so shouldn't be used
for huge arrays.
"""

from __future__ import division

import numpy as np

from .import err1d
from .formatnum import format_uncertainty

__all__ = ['Uncertainty']

# TODO: rename to Measurement and add support for units?
# TODO: C implementation of *,/,**?
class Uncertainty(object):
    # Make standard deviation available
    def _getdx(self): return np.sqrt(self.variance)
    def _setdx(self,dx):
        # Direct operation
        #    variance = dx**2
        # Indirect operation to avoid temporaries
        self.variance[:] = dx
        self.variance **= 2
    dx = property(_getdx,_setdx,doc="standard deviation")

    # Constructor
    def __init__(self, x, variance=None):
        self.x, self.variance = x, variance

    # Numpy array slicing operations
    def __len__(self):
        return len(self.x)
    def __getitem__(self,key):
        return Uncertainty(self.x[key],self.variance[key])
    def __setitem__(self,key,value):
        self.x[key] = value.x
        self.variance[key] = value.variance
    def __delitem__(self, key):
        del self.x[key]
        del self.variance[key]
    #def __iter__(self): pass # Not sure we need iter

    # Normal operations: may be of mixed type
    def __add__(self, other):
        if isinstance(other,Uncertainty):
            return Uncertainty(*err1d.add(self.x,self.variance,other.x,other.variance))
        else:
            return Uncertainty(self.x+other, self.variance+0) # Force copy
    def __sub__(self, other):
        if isinstance(other,Uncertainty):
            return Uncertainty(*err1d.sub(self.x,self.variance,other.x,other.variance))
        else:
            return Uncertainty(self.x-other, self.variance+0) # Force copy
    def __mul__(self, other):
        if isinstance(other,Uncertainty):
            return Uncertainty(*err1d.mul(self.x,self.variance,other.x,other.variance))
        else:
            return Uncertainty(self.x*other, self.variance*other**2)
    def __truediv__(self, other):
        if isinstance(other,Uncertainty):
            return Uncertainty(*err1d.div(self.x,self.variance,other.x,other.variance))
        else:
            return Uncertainty(self.x/other, self.variance/other**2)
    def __pow__(self, other):
        if isinstance(other,Uncertainty):
            # Haven't calcuated variance in (a+/-da) ** (b+/-db)
            return NotImplemented
        else:
            return Uncertainty(*err1d.pow(self.x,self.variance,other))

    # Reverse operations
    def __radd__(self, other):
        return Uncertainty(self.x+other, self.variance+0) # Force copy
    def __rsub__(self, other):
        return Uncertainty(other-self.x, self.variance+0)
    def __rmul__(self, other):
        return Uncertainty(self.x*other, self.variance*other**2)
    def __rtruediv__(self, other):
        x,variance = err1d.pow(self.x,self.variance,-1)
        return Uncertainty(x*other,variance*other**2)
    def __rpow__(self, other): return NotImplemented

    # In-place operations: may be of mixed type
    def __iadd__(self, other):
        if isinstance(other,Uncertainty):
            self.x,self.variance \
                = err1d.add_inplace(self.x,self.variance,other.x,other.variance)
        else:
            self.x+=other
        return self
    def __isub__(self, other):
        if isinstance(other,Uncertainty):
            self.x,self.variance \
                = err1d.sub_inplace(self.x,self.variance,other.x,other.variance)
        else:
            self.x-=other
        return self
    def __imul__(self, other):
        if isinstance(other,Uncertainty):
            self.x, self.variance \
                = err1d.mul_inplace(self.x,self.variance,other.x,other.variance)
        else:
            self.x *= other
            self.variance *= other**2
        return self
    def __itruediv__(self, other):
        if isinstance(other,Uncertainty):
            self.x,self.variance \
                = err1d.div_inplace(self.x,self.variance,other.x,other.variance)
        else:
            self.x /= other
            self.variance /= other**2
        return self
    def __ipow__(self, other):
        if isinstance(other,Uncertainty):
            # Haven't calcuated variance in (a+/-da) ** (b+/-db)
            return NotImplemented
        else:
            self.x,self.variance = err1d.pow_inplace(self.x, self.variance, other)
        return self

    # Use true division instead of integer division
    def __div__(self, other): return self.__truediv__(other)
    def __rdiv__(self, other): return self.__rtruediv__(other)
    def __idiv__(self, other): return self.__itruediv__(other)


    # Unary ops
    def __neg__(self):
        return Uncertainty(-self.x,self.variance)
    def __pos__(self):
        return self
    def __abs__(self):
        return Uncertainty(np.abs(self.x),self.variance)

    def __str__(self):
        #return str(self.x)+" +/- "+str(np.sqrt(self.variance))
        if np.isscalar(self.x):
            return format_uncertainty(self.x,np.sqrt(self.variance))
        else:
            return [format_uncertainty(v,dv)
                    for v,dv in zip(self.x,np.sqrt(self.variance))]
    def __repr__(self):
        return "Uncertainty(%s,%s)"%(str(self.x),str(self.variance))

    # Not implemented
    def __floordiv__(self, other): return NotImplemented
    def __mod__(self, other): return NotImplemented
    def __divmod__(self, other): return NotImplemented
    def __mod__(self, other): return NotImplemented
    def __lshift__(self, other): return NotImplemented
    def __rshift__(self, other): return NotImplemented
    def __and__(self, other): return NotImplemented
    def __xor__(self, other): return NotImplemented
    def __or__(self, other): return NotImplemented

    def __rfloordiv__(self, other): return NotImplemented
    def __rmod__(self, other): return NotImplemented
    def __rdivmod__(self, other): return NotImplemented
    def __rmod__(self, other): return NotImplemented
    def __rlshift__(self, other): return NotImplemented
    def __rrshift__(self, other): return NotImplemented
    def __rand__(self, other): return NotImplemented
    def __rxor__(self, other): return NotImplemented
    def __ror__(self, other): return NotImplemented

    def __ifloordiv__(self, other): return NotImplemented
    def __imod__(self, other): return NotImplemented
    def __idivmod__(self, other): return NotImplemented
    def __imod__(self, other): return NotImplemented
    def __ilshift__(self, other): return NotImplemented
    def __irshift__(self, other): return NotImplemented
    def __iand__(self, other): return NotImplemented
    def __ixor__(self, other): return NotImplemented
    def __ior__(self, other): return NotImplemented

    def __invert__(self): return NotImplmented  # For ~x
    def __complex__(self): return NotImplmented
    def __int__(self): return NotImplmented
    def __long__(self): return NotImplmented
    def __float__(self): return NotImplmented
    def __oct__(self): return NotImplmented
    def __hex__(self): return NotImplmented
    def __index__(self): return NotImplmented
    def __coerce__(self): return NotImplmented

    def log(self):
        return Uncertainty(*err1d.log(self.x,self.variance))

    def exp(self):
        return Uncertainty(*err1d.exp(self.x,self.variance))

def log(val): return self.log()
def exp(val): return self.exp()

def test():
    a = Uncertainty(5,3)
    b = Uncertainty(4,2)

    # Scalar operations
    z = a+4
    assert z.x == 5+4 and z.variance == 3
    z = a-4
    assert z.x == 5-4 and z.variance == 3
    z = a*4
    assert z.x == 5*4 and z.variance == 3*4**2
    z = a/4
    assert z.x == 5./4 and z.variance == 3./4**2

    # Reverse scalar operations
    z = 4+a
    assert z.x == 4+5 and z.variance == 3
    z = 4-a
    assert z.x == 4-5 and z.variance == 3
    z = 4*a
    assert z.x == 4*5 and z.variance == 3*4**2
    z = 4/a
    assert z.x == 4./5 and abs(z.variance - 3./5**4 * 4**2) < 1e-15

    # Power operations
    z = a**2
    assert z.x == 5**2 and z.variance == 4*3*5**2
    z = a**1
    assert z.x == 5**1 and z.variance == 3
    z = a**0
    assert z.x == 5**0 and z.variance == 0
    z = a**-1
    assert z.x == 5**-1 and abs(z.variance - 3./5**4) < 1e-15

    # Binary operations
    z = a+b
    assert z.x == 5+4 and z.variance == 3+2
    z = a-b
    assert z.x == 5-4 and z.variance == 3+2
    z = a*b
    assert z.x == 5*4 and z.variance == (5**2*2 + 4**2*3)
    z = a/b
    assert z.x == 5./4 and abs(z.variance - (3./5**2 + 2./4**2)*(5./4)**2) < 1e-15

    # ===== Inplace operations =====
    # Scalar operations
    y = a+0; y += 4
    z = a+4
    assert y.x == z.x and abs(y.variance-z.variance) < 1e-15
    y = a+0; y -= 4
    z = a-4
    assert y.x == z.x and abs(y.variance-z.variance) < 1e-15
    y = a+0; y *= 4
    z = a*4
    assert y.x == z.x and abs(y.variance-z.variance) < 1e-15
    y = a+0; y /= 4
    z = a/4
    assert y.x == z.x and abs(y.variance-z.variance) < 1e-15

    # Power operations
    y = a+0; y **= 4
    z = a**4
    assert y.x == z.x and abs(y.variance-z.variance) < 1e-15

    # Binary operations
    y = a+0; y += b
    z = a+b
    assert y.x == z.x and abs(y.variance-z.variance) < 1e-15
    y = a+0; y -= b
    z = a-b
    assert y.x == z.x and abs(y.variance-z.variance) < 1e-15
    y = a+0; y *= b
    z = a*b
    assert y.x == z.x and abs(y.variance-z.variance) < 1e-15
    y = a+0; y /= b
    z = a/b
    assert y.x == z.x and abs(y.variance-z.variance) < 1e-15


    # =============== vector operations ================
    # Slicing
    z = Uncertainty(np.array([1,2,3,4,5]),np.array([2,1,2,3,2]))
    assert z[2].x == 3 and z[2].variance == 2
    assert (z[2:4].x == [3,4]).all()
    assert (z[2:4].variance == [2,3]).all()
    z[2:4] = Uncertainty(np.array([8,7]),np.array([4,5]))
    assert z[2].x == 8 and z[2].variance == 4
    A = Uncertainty(np.array([a.x]*2),np.array([a.variance]*2))
    B = Uncertainty(np.array([b.x]*2),np.array([b.variance]*2))

    # TODO complete tests of copy and inplace operations for vectors and slices.

    # Binary operations
    z = A+B
    assert (z.x == 5+4).all() and (z.variance == 3+2).all()
    z = A-B
    assert (z.x == 5-4).all() and (z.variance == 3+2).all()
    z = A*B
    assert (z.x == 5*4).all() and (z.variance == (5**2*2 + 4**2*3)).all()
    z = A/B
    assert (z.x == 5./4).all()
    assert (abs(z.variance - (3./5**2 + 2./4**2)*(5./4)**2) < 1e-15).all()

    # printing; note that sqrt(3) ~ 1.7
    assert str(Uncertainty(5,3)) == "5.0(17)"
    assert str(Uncertainty(15,3)) == "15.0(17)"
    assert str(Uncertainty(151.23356,0.324185**2)) == "151.23(32)"

if __name__ == "__main__": test()
