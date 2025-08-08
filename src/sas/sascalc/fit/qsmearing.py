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

import numpy as np  # type: ignore

from sasdata.data_util.nxsunit import Converter
from sasmodels.resolution import Pinhole1D, Slit1D
from sasmodels.resolution2d import Pinhole2D
from sasmodels.sesans import SesansTransform


def smear_selection(data, model=None):
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
    # This checks for 2D data (does not throw exception because fail is common)
    if data.__class__.__name__ not in ['Data1D', 'Theory1D']:
        if data is None:
            return None
        elif data.dqx_data is None or data.dqy_data is None:
            return None
        return PySmear2D(data)
    # This checks for 1D data with smearing info in the data itself (again, fail is likely; no exceptions)
    if not hasattr(data, "dx") and not hasattr(data, "dxl") and not hasattr(data, "dxw"):
        return None

    # Look for resolution smearing data
    # Check if the loader flagged this as SESANS data and use Hankel transform as the resolution
    if data.isSesans:  # data.dx data is not required in the Hankel transform for SESANS data
        # Pre-compute the Hankel matrix (H)
        SElength = Converter(data._xunit)(data.x, "A")

        theta_max = Converter("radians")(data.sample.zacceptance)[0]
        q_max = 2 * np.pi / np.max(data.source.wavelength) * np.sin(theta_max)
        zaccept = Converter("1/A")(q_max, "1/" + data.source.wavelength_unit),

        Rmax = 10000000
        hankel = SesansTransform(data.x, SElength,
                                 data.source.wavelength,
                                 zaccept, Rmax)
        # Then return the actual transform, as if it were a smearing function
        return PySmear(hankel, model, offset=0)

    # Only return pinhole resolution if there is at least one resolution point greater than 0
    #  This eliminates edge cases where dQ is reported as 0.0 for *all* data points
    if data.dx is not None and len(data.dx) == len(data.x) and np.any(data.dx[data.dx > 0]):
        # Check for negative resolution values and throw an error if present
        if np.min(data.dx) < 0:
            raise ValueError('one or more of your dx values are negative, please check the data file!')
        return pinhole_smear(data, model)

    # Look for slit smeared data
    if (data.dxl is not None and len(data.dxl) == len(data.x)
            and data.dxw is not None and len(data.dxw) == len(data.x)):

        # Check that we have non-zero data in either of the slit-smeared resolutions.
        #  Note - All resolutions are assumed to be the same value for slit smeared data
        if ((np.any(data.dxl[data.dxl > 0]) and len(data.dxl) == len([dxl for dxl in data.dxl if dxl == data.dxl[0]]))
                or np.any(data.dxw[data.dxw > 0]) and len(data.dxw) == len([dxw for dxw in data.dxw if dxw == data.dxw[0]])):
            return slit_smear(data, model)

    # Getting here means no viable resolution was provided with the data set - No resolution should be applied
    return None


class PySmear:
    """
    Wrapper for pure python sasmodels resolution functions.
    """
    def __init__(self, resolution, model, offset=None):
        self.model = model
        self.resolution = resolution
        if offset is None:
            offset = np.searchsorted(self.resolution.q_calc, self.resolution.q[0])
        self.offset = offset

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
        if last_bin is None:
            last_bin = len(iq_in)
        start, end = first_bin + self.offset, last_bin + self.offset
        q_calc = self.resolution.q_calc
        iq_calc = np.empty_like(q_calc)
        if start > 0:
            iq_calc[:start] = self.model.evalDistribution(q_calc[:start])
        if end+1 < len(q_calc):
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
        first = np.searchsorted(q, q_min)
        last = np.searchsorted(q, q_max)
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


class PySmear2D:
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

