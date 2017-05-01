#!/usr/bin/env python

"""
Provide base functionality for all model components
"""

# imports
import copy
from collections import OrderedDict

import numpy as np
#TO DO: that about a way to make the parameter
#is self return if it is fittable or not

class BaseComponent:
    """
    Basic model component

    Since version 0.5.0, basic operations are no longer supported.
    """

    def __init__(self):
        """ Initialization"""

        ## Name of the model
        self.name = "BaseComponent"

        ## Parameters to be accessed by client
        self.params = {}
        self.details = {}
        ## Dictionary used to store the dispersity/averaging
        #  parameters of dispersed/averaged parameters.
        self.dispersion = {}
        # string containing information about the model such as the equation
        #of the given model, exception or possible use
        self.description = ''
        #list of parameter that can be fitted
        self.fixed = []
        #list of non-fittable parameter
        self.non_fittable = []
        ## parameters with orientation
        self.orientation_params = []
        ## magnetic parameters
        self.magnetic_params = []
        ## store dispersity reference
        self._persistency_dict = {}
        ## independent parameter name and unit [string]
        self.input_name = "Q"
        self.input_unit = "A^{-1}"
        ## output name and unit  [string]
        self.output_name = "Intensity"
        self.output_unit = "cm^{-1}"

        self.is_multiplicity_model = False
        self.is_structure_factor = False
        self.is_form_factor = False

    def __str__(self):
        """
        :return: string representatio
        """
        return self.name

    def is_fittable(self, par_name):
        """
        Check if a given parameter is fittable or not

        :param par_name: the parameter name to check

        """
        return par_name.lower() in self.fixed
        #For the future
        #return self.params[str(par_name)].is_fittable()

    def run(self, x):
        """
        run 1d
        """
        return NotImplemented

    def runXY(self, x):
        """
        run 2d
        """
        return NotImplemented

    def calculate_ER(self):
        """
        Calculate effective radius
        """
        return NotImplemented

    def calculate_VR(self):
        """
        Calculate volume fraction ratio
        """
        return NotImplemented

    def evalDistribution(self, qdist):
        """
        Evaluate a distribution of q-values.

        * For 1D, a numpy array is expected as input: ::

            evalDistribution(q)

          where q is a numpy array.


        * For 2D, a list of numpy arrays are expected: [qx_prime,qy_prime],
          where 1D arrays, ::

              qx_prime = [ qx[0], qx[1], qx[2], ....]

          and ::

              qy_prime = [ qy[0], qy[1], qy[2], ....]

        Then get ::

            q = np.sqrt(qx_prime^2+qy_prime^2)

        that is a qr in 1D array; ::

            q = [q[0], q[1], q[2], ....]

        .. note:: Due to 2D speed issue, no anisotropic scattering
                  is supported for python models, thus C-models should have
                  their own evalDistribution methods.

        The method is then called the following way: ::

            evalDistribution(q)

        where q is a numpy array.

        :param qdist: ndarray of scalar q-values or list [qx,qy] where qx,qy are 1D ndarrays
        """
        if qdist.__class__.__name__ == 'list':
            # Check whether we have a list of ndarrays [qx,qy]
            if len(qdist)!=2 or \
                qdist[0].__class__.__name__ != 'ndarray' or \
                qdist[1].__class__.__name__ != 'ndarray':
                msg = "evalDistribution expects a list of 2 ndarrays"
                raise RuntimeError(msg)

            # Extract qx and qy for code clarity
            qx = qdist[0]
            qy = qdist[1]

            # calculate q_r component for 2D isotropic
            q = np.sqrt(qx**2+qy**2)
            # vectorize the model function runXY
            v_model = np.vectorize(self.runXY, otypes=[float])
            # calculate the scattering
            iq_array = v_model(q)

            return iq_array

        elif qdist.__class__.__name__ == 'ndarray':
            # We have a simple 1D distribution of q-values
            v_model = np.vectorize(self.runXY, otypes=[float])
            iq_array = v_model(qdist)
            return iq_array

        else:
            mesg = "evalDistribution is expecting an ndarray of scalar q-values"
            mesg += " or a list [qx,qy] where qx,qy are 2D ndarrays."
            raise RuntimeError(mesg)



    def clone(self):
        """ Returns a new object identical to the current object """
        obj = copy.deepcopy(self)
        return self._clone(obj)

    def _clone(self, obj):
        """
        Internal utility function to copy the internal
        data members to a fresh copy.
        """
        obj.params     = copy.deepcopy(self.params)
        obj.details    = copy.deepcopy(self.details)
        obj.dispersion = copy.deepcopy(self.dispersion)
        obj._persistency_dict = copy.deepcopy( self._persistency_dict)
        return obj

    def set_dispersion(self, parameter, dispersion):
        """
        model dispersions
        """
        ##Not Implemented
        return None

    def getProfile(self):
        """
        Get SLD profile

        : return: (z, beta) where z is a list of depth of the transition points
                beta is a list of the corresponding SLD values
        """
        #Not Implemented
        return None, None

    def setParam(self, name, value):
        """
        Set the value of a model parameter

        :param name: name of the parameter
        :param value: value of the parameter

        """
        # Look for dispersion parameters
        toks = name.split('.')
        if len(toks)==2:
            for item in self.dispersion.keys():
                if item.lower()==toks[0].lower():
                    for par in self.dispersion[item]:
                        if par.lower() == toks[1].lower():
                            self.dispersion[item][par] = value
                            return
        else:
            # Look for standard parameter
            for item in self.params.keys():
                if item.lower()==name.lower():
                    self.params[item] = value
                    return

        raise ValueError("Model does not contain parameter %s" % name)

    def getParam(self, name):
        """
        Set the value of a model parameter
        :param name: name of the parameter

        """
        # Look for dispersion parameters
        toks = name.split('.')
        if len(toks)==2:
            for item in self.dispersion.keys():
                if item.lower()==toks[0].lower():
                    for par in self.dispersion[item]:
                        if par.lower() == toks[1].lower():
                            return self.dispersion[item][par]
        else:
            # Look for standard parameter
            for item in self.params.keys():
                if item.lower()==name.lower():
                    return self.params[item]

        raise ValueError("Model does not contain parameter %s" % name)

    def getParamList(self):
        """
        Return a list of all available parameters for the model
        """
        list = _ordered_keys(self.params)
        # WARNING: Extending the list with the dispersion parameters
        list.extend(self.getDispParamList())
        return list

    def getDispParamList(self):
        """
        Return a list of all available parameters for the model
        """
        list = []
        for item in _ordered_keys(self.dispersion):
            for p in _ordered_keys(self.dispersion[item]):
                if p not in ['type']:
                    list.append('%s.%s' % (item.lower(), p.lower()))

        return list

    # Old-style methods that are no longer used
    def setParamWithToken(self, name, value, token, member):
        """
        set Param With Token
        """
        return NotImplemented
    def getParamWithToken(self, name, token, member):
        """
        get Param With Token
        """
        return NotImplemented

    def getParamListWithToken(self, token, member):
        """
        get Param List With Token
        """
        return NotImplemented
    def __add__(self, other):
        """
        add
        """
        raise ValueError("Model operation are no longer supported")
    def __sub__(self, other):
        """
        sub
        """
        raise ValueError("Model operation are no longer supported")
    def __mul__(self, other):
        """
        mul
        """
        raise ValueError("Model operation are no longer supported")
    def __div__(self, other):
        """
        div
        """
        raise ValueError("Model operation are no longer supported")


def _ordered_keys(d):
    keys = list(d.keys())
    if not isinstance(d, OrderedDict):
        keys.sort()
    return keys
