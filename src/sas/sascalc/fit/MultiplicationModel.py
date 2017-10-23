import copy

import numpy as np

from sas.sascalc.calculator.BaseComponent import BaseComponent

class MultiplicationModel(BaseComponent):
    r"""
        Use for P(Q)\*S(Q); function call must be in the order of P(Q) and then S(Q):
        The model parameters are combined from both models, P(Q) and S(Q), except 1) 'radius_effective' of S(Q)
        which will be calculated from P(Q) via calculate_ER(),
        and 2) 'scale' in P model which is synchronized w/ volfraction in S
        then P*S is multiplied by a new parameter, 'scale_factor'.
        The polydispersion is applicable only to P(Q), not to S(Q).

        .. note:: P(Q) refers to 'form factor' model while S(Q) does to 'structure factor'.
    """
    def __init__(self, p_model, s_model ):
        BaseComponent.__init__(self)
        """
        :param p_model: form factor, P(Q)
        :param s_model: structure factor, S(Q)
        """

        ## Setting  model name model description
        self.description = ""
        self.name = p_model.name +" * "+ s_model.name
        self.description= self.name + "\n"
        self.fill_description(p_model, s_model)

        ## Define parameters
        self.params = {}

        ## Parameter details [units, min, max]
        self.details = {}

        ## Define parameters to exclude from multiplication model
        self.excluded_params={'radius_effective','scale','background'}

        ##models
        self.p_model = p_model
        self.s_model = s_model
        self.magnetic_params = []
        ## dispersion
        self._set_dispersion()
        ## Define parameters
        self._set_params()
        ## New parameter:Scaling factor
        self.params['scale_factor'] = 1
        self.params['background']  = 0

        ## Parameter details [units, min, max]
        self._set_details()
        self.details['scale_factor'] = ['', 0.0, np.inf]
        self.details['background'] = ['',-np.inf,np.inf]

        #list of parameter that can be fitted
        self._set_fixed_params()
        ## parameters with orientation
        for item in self.p_model.orientation_params:
            self.orientation_params.append(item)
        for item in self.p_model.magnetic_params:
            self.magnetic_params.append(item)
        for item in self.s_model.orientation_params:
            if not item in self.orientation_params:
                self.orientation_params.append(item)
        # get multiplicity if model provide it, else 1.
        try:
            multiplicity = p_model.multiplicity
        except:
            multiplicity = 1
        ## functional multiplicity of the model
        self.multiplicity = multiplicity

        # non-fittable parameters
        self.non_fittable = p_model.non_fittable
        self.multiplicity_info = []
        self.fun_list = {}
        if self.non_fittable > 1:
            try:
                self.multiplicity_info = p_model.multiplicity_info
                self.fun_list = p_model.fun_list
                self.is_multiplicity_model = True
            except:
                pass
        else:
            self.is_multiplicity_model = False
            self.multiplicity_info = [0]

    def _clone(self, obj):
        """
        Internal utility function to copy the internal data members to a
        fresh copy.
        """
        obj.params     = copy.deepcopy(self.params)
        obj.description     = copy.deepcopy(self.description)
        obj.details    = copy.deepcopy(self.details)
        obj.dispersion = copy.deepcopy(self.dispersion)
        obj.p_model  = self.p_model.clone()
        obj.s_model  = self.s_model.clone()
        #obj = copy.deepcopy(self)
        return obj


    def _set_dispersion(self):
        """
        combine the two models' dispersions. Polydispersity should not be
        applied to s_model
        """
        ##set dispersion only from p_model
        for name , value in self.p_model.dispersion.items():
            self.dispersion[name] = value

    def getProfile(self):
        """
        Get SLD profile of p_model if exists

        :return: (r, beta) where r is a list of radius of the transition points\
                beta is a list of the corresponding SLD values

        .. note:: This works only for func_shell num = 2 (exp function).
        """
        try:
            x, y = self.p_model.getProfile()
        except:
            x = None
            y = None

        return x, y

    def _set_params(self):
        """
        Concatenate the parameters of the two models to create
        these model parameters
        """

        for name , value in self.p_model.params.items():
            if not name in self.params.keys() and name not in self.excluded_params:
                self.params[name] = value

        for name , value in self.s_model.params.items():
            #Remove the radius_effective from the (P*S) model parameters.
            if not name in self.params.keys() and name not in self.excluded_params:
                self.params[name] = value

        # Set "scale and effec_radius to P and S model as initializing
        # since run P*S comes from P and S separately.
        self._set_backgrounds()
        self._set_scale_factor()
        self._set_radius_effective()

    def _set_details(self):
        """
        Concatenate details of the two models to create
        this model's details
        """
        for name, detail in self.p_model.details.items():
            if name not in self.excluded_params:
                self.details[name] = detail

        for name , detail in self.s_model.details.items():
            if not name in self.details.keys() or name not in self.exluded_params:
                self.details[name] = detail

    def _set_backgrounds(self):
        """
        Set component backgrounds to zero
        """
        if 'background' in self.p_model.params:
            self.p_model.setParam('background',0)
        if 'background' in self.s_model.params:
            self.s_model.setParam('background',0)


    def _set_scale_factor(self):
        """
        Set scale=volfraction for P model
        """
        value = self.params['volfraction']
        if value is not None:
            factor = self.p_model.calculate_VR()
            if factor is None or factor == NotImplemented or factor == 0.0:
                val = value
            else:
                val = value / factor
            self.p_model.setParam('scale', value)
            self.s_model.setParam('volfraction', val)

    def _set_radius_effective(self):
        """
        Set effective radius to S(Q) model
        """
        if not 'radius_effective' in self.s_model.params.keys():
            return
        effective_radius = self.p_model.calculate_ER()
        #Reset the effective_radius of s_model just before the run
        if effective_radius is not None and effective_radius != NotImplemented:
            self.s_model.setParam('radius_effective', effective_radius)

    def setParam(self, name, value):
        """
        Set the value of a model parameter

        :param name: name of the parameter
        :param value: value of the parameter
        """
        # set param to P*S model
        self._setParamHelper( name, value)

        ## setParam to p model
        # set 'scale' in P(Q) equal to volfraction
        if name == 'volfraction':
            self._set_scale_factor()
        elif name in self.p_model.getParamList() and name not in self.excluded_params:
            self.p_model.setParam( name, value)

        ## setParam to s model
        # This is a little bit abundant: Todo: find better way
        self._set_radius_effective()
        if name in self.s_model.getParamList() and name not in self.excluded_params:
            if name != 'volfraction':
                self.s_model.setParam( name, value)


        #self._setParamHelper( name, value)

    def _setParamHelper(self, name, value):
        """
        Helper function to setparam
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
                if item.lower() == name.lower():
                    self.params[item] = value
                    return

        raise ValueError("Model does not contain parameter %s" % name)


    def _set_fixed_params(self):
        """
        Fill the self.fixed list with the p_model fixed list
        """
        for item in self.p_model.fixed:
            self.fixed.append(item)

        self.fixed.sort()


    def run(self, x = 0.0):
        """
        Evaluate the model

        :param x: input q-value (float or [float, float] as [r, theta])
        :return: (scattering function value)
        """
        # set effective radius and scaling factor before run
        self._set_radius_effective()
        self._set_scale_factor()
        return self.params['scale_factor'] * self.p_model.run(x) * \
                            self.s_model.run(x) + self.params['background']

    def runXY(self, x = 0.0):
        """
        Evaluate the model

        :param x: input q-value (float or [float, float] as [qx, qy])
        :return: scattering function value
        """
        # set effective radius and scaling factor before run
        self._set_radius_effective()
        self._set_scale_factor()
        out = self.params['scale_factor'] * self.p_model.runXY(x) * \
                        self.s_model.runXY(x) + self.params['background']
        return out

    ## Now (May27,10) directly uses the model eval function
    ## instead of the for-loop in Base Component.
    def evalDistribution(self, x = []):
        """
        Evaluate the model in cartesian coordinates

        :param x: input q[], or [qx[], qy[]]
        :return: scattering function P(q[])
        """
        # set effective radius and scaling factor before run
        self._set_radius_effective()
        self._set_scale_factor()
        out = self.params['scale_factor'] * self.p_model.evalDistribution(x) * \
                        self.s_model.evalDistribution(x) + self.params['background']
        return out

    def set_dispersion(self, parameter, dispersion):
        """
        Set the dispersion object for a model parameter

        :param parameter: name of the parameter [string]
        :dispersion: dispersion object of type DispersionModel
        """
        value = None
        try:
            if parameter in self.p_model.dispersion.keys():
                value = self.p_model.set_dispersion(parameter, dispersion)
            self._set_dispersion()
            return value
        except:
            raise

    def fill_description(self, p_model, s_model):
        """
        Fill the description for P(Q)*S(Q)
        """
        description = ""
        description += "Note:1) The radius_effective (effective radius) of %s \n"%\
                                                                (s_model.name)
        description += "             is automatically calculated "
        description += "from size parameters (radius...).\n"
        description += "         2) For non-spherical shape, "
        description += "this approximation is valid \n"
        description += "            only for limited systems. "
        description += "Thus, use it at your own risk.\n"
        description += "See %s description and %s description \n"% \
                                                ( p_model.name, s_model.name )
        description += "        for details of individual models."
        self.description += description
