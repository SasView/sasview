# This program is public domain
"""
Error propogation algorithms for simple arithmetic

Warning: like the underlying numpy library, the inplace operations
may return values of the wrong type if some of the arguments are
integers, so be sure to create them with floating point inputs.
"""
from __future__ import division  # Get true division
import numpy


def div(X, varX, Y, varY):
    """Division with error propagation"""
    # Direct algorithm:
    #   Z = X/Y
    #   varZ = (varX/X**2 + varY/Y**2) * Z**2
    #        = (varX + varY * Z**2) / Y**2
    # Indirect algorithm to minimize intermediates
    Z = X/Y      # truediv => Z is a float
    varZ = Z**2  # Z is a float => varZ is a float
    varZ *= varY
    varZ += varX
    T = Y**2     # Doesn't matter if T is float or int
    varZ /= T
    return Z, varZ


def mul(X, varX, Y, varY):
    """Multiplication with error propagation"""
    # Direct algorithm:
    Z = X * Y
    varZ = Y**2 * varX + X**2 * varY
    # Indirect algorithm won't ensure floating point results
    #   varZ = Y**2
    #   varZ *= varX
    #   Z = X**2   # Using Z to hold the temporary
    #   Z *= varY
    #   varZ += Z
    #   Z[:] = X
    #   Z *= Y
    return Z, varZ


def sub(X, varX, Y, varY):
    """Subtraction with error propagation"""
    Z = X - Y
    varZ = varX + varY
    return Z, varZ


def add(X, varX, Y, varY):
    """Addition with error propagation"""
    Z = X + Y
    varZ = varX + varY
    return Z, varZ


def exp(X, varX):
    """Exponentiation with error propagation"""
    Z = numpy.exp(X)
    varZ = varX * Z**2
    return Z, varZ


def log(X, varX):
    """Logarithm with error propagation"""
    Z = numpy.log(X)
    varZ = varX / X**2
    return Z, varZ

# Confirm this formula before using it
# def pow(X,varX, Y,varY):
#    Z = X**Y
#    varZ = (Y**2 * varX/X**2 + varY * numpy.log(X)**2) * Z**2
#    return Z,varZ
#


def pow(X, varX, n):
    """X**n with error propagation"""
    # Direct algorithm
    #   Z = X**n
    #   varZ = n*n * varX/X**2 * Z**2
    # Indirect algorithm to minimize intermediates
    Z = X**n
    varZ = varX / X
    varZ /= X
    varZ *= Z
    varZ *= Z
    varZ *= n**2
    return Z, varZ


def div_inplace(X, varX, Y, varY):
    """In-place division with error propagation"""
    # Z = X/Y
    # varZ = (varX + varY * (X/Y)**2) / Y**2 = (varX + varY * Z**2) / Y**2
    X /= Y     # X now has Z = X/Y
    T = X**2   # create T with Z**2
    T *= varY  # T now has varY * Z**2
    varX += T  # varX now has varX + varY*Z**2
    del T   # may want to use T[:] = Y for vectors
    T = Y   # reuse T for Y
    T **= 2     # T now has Y**2
    varX /= T  # varX now has varZ
    return X, varX


def mul_inplace(X, varX, Y, varY):
    """In-place multiplication with error propagation"""
    # Z = X * Y
    # varZ = Y**2 * varX + X**2 * varY
    T = Y**2   # create T with Y**2
    varX *= T  # varX now has Y**2 * varX
    del T   # may want to use T[:] = X for vectors
    T = X   # reuse T for X**2 * varY
    T **=2     # T now has X**2
    T *= varY  # T now has X**2 * varY
    varX += T  # varX now has varZ
    X *= Y     # X now has Z
    return X, varX


def sub_inplace(X, varX, Y, varY):
    """In-place subtraction with error propagation"""
    # Z = X - Y
    # varZ = varX + varY
    X -= Y
    varX += varY
    return X, varX


def add_inplace(X, varX, Y, varY):
    """In-place addition with error propagation"""
    # Z = X + Y
    # varZ = varX + varY
    X += Y
    varX += varY
    return X, varX


def pow_inplace(X, varX, n):
    """In-place X**n with error propagation"""
    # Direct algorithm
    #   Z = X**n
    #   varZ = abs(n) * varX/X**2 * Z**2
    # Indirect algorithm to minimize intermediates
    varX /= X
    varX /= X     # varX now has varX/X**2
    X **= n       # X now has Z = X**n
    varX *= X
    varX *= X     # varX now has varX/X**2 * Z**2
    varX *= n**2  # varX now has varZ
    return X, varX
