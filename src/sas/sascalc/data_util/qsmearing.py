"""
    Handle Q smearing
"""
#####################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation. 
#See the license text in license.txt
#copyright 2008, University of Tennessee
######################################################################
import numpy
import math
import logging
import sys

from sasmodels.resolution import Slit1D, Pinhole1D
from sasmodels.resolution2d import Pinhole2D

def smear_selection(data, model = None):
    """
    Creates the right type of smearer according
    to the data.
    The canSAS format has a rule that either
    slit smearing data OR resolution smearing data
    is available.

    For the present purpose, we choose the one that
    has none-zero data. If both slit and resolution
    smearing arrays are filled with good data
    (which should not happen), then we choose the
    resolution smearing data.

    :param data: Data1D object
    :param model: sas.model instance
    """
    # Sanity check. If we are not dealing with a SAS Data1D
    # object, just return None
    if  data.__class__.__name__ not in ['Data1D', 'Theory1D']:
        if data == None:
            return None
        elif data.dqx_data == None or data.dqy_data == None:
            return None
        return PySmear2D(data, model)

    if  not hasattr(data, "dx") and not hasattr(data, "dxl")\
         and not hasattr(data, "dxw"):
        return None

    # Look for resolution smearing data
    _found_resolution = False
    if data.dx is not None and len(data.dx) == len(data.x):

        # Check that we have non-zero data
        if data.dx[0] > 0.0:
            _found_resolution = True
            #print "_found_resolution",_found_resolution
            #print "data1D.dx[0]",data1D.dx[0],data1D.dxl[0]
    # If we found resolution smearing data, return a QSmearer
    if _found_resolution == True:
         return pinhole_smear(data, model)

    # Look for slit smearing data
    _found_slit = False
    if data.dxl is not None and len(data.dxl) == len(data.x) \
        and data.dxw is not None and len(data.dxw) == len(data.x):

        # Check that we have non-zero data
        if data.dxl[0] > 0.0 or data.dxw[0] > 0.0:
            _found_slit = True

        # Sanity check: all data should be the same as a function of Q
        for item in data.dxl:
            if data.dxl[0] != item:
                _found_resolution = False
                break

        for item in data.dxw:
            if data.dxw[0] != item:
                _found_resolution = False
                break
    # If we found slit smearing data, return a slit smearer
    if _found_slit == True:
        return slit_smear(data, model)
    return None


class PySmear(object):
    """
    Wrapper for pure python sasmodels resolution functions.
    """
    def __init__(self, resolution, model):
        self.model = model
        self.resolution = resolution
        self.offset = numpy.searchsorted(self.resolution.q_calc, self.resolution.q[0])

    def apply(self, iq_in, first_bin=0, last_bin=None):
        """
        Apply the resolution function to the data.
        Note that this is called with iq_in matching data.x, but with
        iq_in[first_bin:last_bin] set to theory values for these bins,
        and the remainder left undefined.  The first_bin, last_bin values
        should be those returned from get_bin_range.
        The returned value is of the same length as iq_in, with the range
        first_bin:last_bin set to the resolution smeared values.
        """
        if last_bin is None: last_bin = len(iq_in)
        start, end = first_bin + self.offset, last_bin + self.offset
        q_calc = self.resolution.q_calc
        iq_calc = numpy.empty_like(q_calc)
        if start > 0 and self.model is not None:
            iq_calc[:start] = self.model.evalDistribution(q_calc[:start])
        if end+1 < len(q_calc) and self.model is not None:
            iq_calc[end+1:] = self.model.evalDistribution(q_calc[end+1:])
        iq_calc[start:end+1] = iq_in[first_bin:last_bin+1]
        smeared = self.resolution.apply(iq_calc)
        return smeared
    __call__ = apply

    def get_bin_range(self, q_min=None, q_max=None):
        """
        For a given q_min, q_max, find the corresponding indices in the data.
        Returns first, last.
        Note that these are indexes into q from the data, not the q_calc
        needed by the resolution function.  Note also that these are the
        indices, not the range limits.  That is, the complete range will be
        q[first:last+1].
        """
        q = self.resolution.q
        first = numpy.searchsorted(q, q_min)
        last = numpy.searchsorted(q, q_max)
        return first, min(last,len(q)-1)

def slit_smear(data, model=None):
    q = data.x
    width = data.dxw if data.dxw is not None else 0
    height = data.dxl if data.dxl is not None else 0
    # TODO: width and height seem to be reversed
    return PySmear(Slit1D(q, height, width), model)

def pinhole_smear(data, model=None):
    q = data.x
    width = data.dx if data.dx is not None else 0
    return PySmear(Pinhole1D(q, width), model)


class PySmear2D(object):
    """
    Q smearing class for SAS 2d pinhole data
    """

    def __init__(self, data=None, model=None):
        self.data = data
        self.model = model
        self.accuracy = 'Low'
        self.limit = 3.0
        self.index = None
        self.coords = 'polar'
        self.smearer = True

    def set_accuracy(self, accuracy='Low'):
        """
        Set accuracy.

        :param accuracy:  string
        """
        self.accuracy = accuracy

    def set_smearer(self, smearer=True):
        """
        Set whether or not smearer will be used

        :param smearer: smear object

        """
        self.smearer = smearer

    def set_data(self, data=None):
        """
        Set data.

        :param data: DataLoader.Data_info type
        """
        self.data = data

    def set_model(self, model=None):
        """
        Set model.

        :param model: sas.models instance
        """
        self.model = model

    def set_index(self, index=None):
        """
        Set index.

        :param index: 1d arrays
        """
        self.index = index

    def get_value(self):
        """
        Over sampling of r_nbins times phi_nbins, calculate Gaussian weights,
        then find smeared intensity
        """
        if self.smearer:
            res = Pinhole2D(data=self.data, index=self.index,
                            nsigma=3.0, accuracy=self.accuracy,
                            coords=self.coords)
            val = self.model.evalDistribution(res.q_calc)
            return res.apply(val)
        else:
            index = self.index if self.index is not None else slice(None)
            qx_data = self.data.qx_data[index]
            qy_data = self.data.qy_data[index]
            q_calc = [qx_data, qy_data]
            val = self.model.evalDistribution(q_calc)
            return val

