# A sample of an experimental model function for Sum(APmodel1,(1-A)Pmodel2)
import copy
from sas.models.pluginmodel import Model1DPlugin
import os
import sys
"""
## *****************************************************************************
Please select the 'Compile' from the menubar after the modification and saving.
Note that we recommend to save the file as a different file name.
Otherwise, it could be removed in the future on re-installation of the SasView.
## *****************************************************************************
"""

# Available model names for this sum model
"""
BCCrystalModel, BEPolyelectrolyte, BarBellModel, BinaryHSModel, BroadPeakModel,
CSParallelepipedModel, CappedCylinderModel, CoreShellCylinderModel,
CoreShellEllipsoidModel, CoreShellModel, CorrLengthModel, CylinderModel, 
DABModel, DebyeModel, EllipsoidModel, EllipticalCylinderModel, FCCrystalModel,
FlexCylEllipXModel, FlexibleCylinderModel, FractalCoreShellModel, FractalModel,
FuzzySphereModel, GaussLorentzGelModel, GuinierModel, GuinierPorodModel,
HardsphereStructure, HayterMSAStructure, HollowCylinderModel, LamellarFFHGModel,
LamellarModel, LamellarPCrystalModel, LamellarPSHGModel, LamellarPSModel,
LineModel, LorentzModel, MultiShellModel, ParallelepipedModel, PeakGaussModel,
PeakLorentzModel, PearlNecklaceModel, Poly_GaussCoil, PolymerExclVolume,
PorodModel, PowerLawAbsModel, SCCrystalModel, SphereModel, SquareWellStructure,
StackedDisksModel, StickyHSStructure, TeubnerStreyModel, TriaxialEllipsoidModel,
TwoLorentzianModel, TwoPowerLawModel, VesicleModel
"""
## This model is DIFFERENT from the Easy Custom Sum(p1 + p2) 
## by definition of the scale factor *****************************************
#
#     Custom model = scale_factor * P1 + (1 - scale_factor) * P2
#
## User can REPLACE model names below arrowed two lines (twice per line)
from sas.models.CylinderModel import CylinderModel as P1          #<========
from sas.models.PolymerExclVolume import PolymerExclVolume as P2  #<========

#####DO NOT CHANGE ANYTHING BELOW THIS LINE 
#####---------------------------------------------------------------------------
class Model(Model1DPlugin):
    """
    Use for A*p1(Q)+(1-A)*p2(Q); 
    Note: P(Q) refers to 'form factor' model.
    """
    name = ""  
    def __init__(self):
        Model1DPlugin.__init__(self, name=self.name)
        """
        :param p_model1: a form factor, P(Q)
        :param p_model2: another form factor, P(Q)
        """
        p_model1 = P1()
        p_model2 = P2()
        ## Setting  model name model description
        self.description = ""
        self.fill_description(p_model1, p_model2)
        # Set the name same as the file name
        self.name = self.get_fname()     ##DO NOT CHANGE THIS LINE!!!
        ## Define parameters
        self.params = {}

        ## Parameter details [units, min, max]
        self.details = {}
        ## Magnetic Panrameters
        self.magnetic_params = []
        
        # non-fittable parameters
        self.non_fittable = p_model1.non_fittable  
        self.non_fittable += p_model2.non_fittable  
            
        ##models 
        self.p_model1= p_model1
        self.p_model2= p_model2
        
       
        ## dispersion
        self._set_dispersion()
        ## Define parameters
        self._set_params()
        ## New parameter:Scaling factor
        self.params['scale_factor'] = 0.5
        
        ## Parameter details [units, min, max]
        self._set_details()
        self.details['scale_factor'] = ['',     None, None]

        
        #list of parameter that can be fitted
        self._set_fixed_params()  
        ## parameters with orientation
        for item in self.p_model1.orientation_params:
            new_item = "p1_" + item
            if not new_item in self.orientation_params:
                self.orientation_params.append(new_item)
            
        for item in self.p_model2.orientation_params:
            new_item = "p2_" + item
            if not new_item in self.orientation_params:
                self.orientation_params.append(new_item)
        ## magnetic params
        for item in self.p_model1.magnetic_params:
            new_item = "p1_" + item
            if not new_item in self.magnetic_params:
                self.magnetic_params.append(new_item)
            
        for item in self.p_model2.magnetic_params:
            new_item = "p2_" + item
            if not new_item in self.magnetic_params:
                self.magnetic_params.append(new_item)
        # set multiplicity 1: muti_func Not supported.
        multiplicity1 = 1
        multiplicity2 = 1
        ## functional multiplicity of the model
        self.multiplicity1 = multiplicity1  
        self.multiplicity2 = multiplicity2    
        self.multiplicity_info = []   
        
    def _clone(self, obj):
        """
            Internal utility function to copy the internal
            data members to a fresh copy.
        """
        obj.params     = copy.deepcopy(self.params)
        obj.description     = copy.deepcopy(self.description)
        obj.details    = copy.deepcopy(self.details)
        obj.dispersion = copy.deepcopy(self.dispersion)
        obj.p_model1  = self.p_model1.clone()
        obj.p_model2  = self.p_model2.clone()
        #obj = copy.deepcopy(self)
        return obj
    
    def _get_name(self, name1, name2):
        """
        Get combined name from two model names
        """
        name = "A*"
        p1_name = self._get_upper_name(name1)
        if not p1_name:
            p1_name = name1
        name += p1_name
        name += "+(1-A)*"
        p2_name = self._get_upper_name(name2)
        if not p2_name:
            p2_name = name2
        name += p2_name
        return name
    
    def _get_upper_name(self, name=None):
        """
        Get uppercase string from model name
        """
        if name == None:
            return ""
        upper_name = ""
        str_name = str(name)
        for index in range(len(str_name)):
            if str_name[index].isupper():
                upper_name += str_name[index]
        return upper_name
        
    def _set_dispersion(self):
        """
           combined the two models dispersions
           Polydispersion should not be applied to s_model
        """
        ##set dispersion only from p_model 
        for name , value in self.p_model1.dispersion.iteritems():
            #if name.lower() not in self.p_model1.orientation_params:
            new_name = "p1_" + name
            self.dispersion[new_name]= value 
        for name , value in self.p_model2.dispersion.iteritems():
            #if name.lower() not in self.p_model2.orientation_params:
            new_name = "p2_" + name
            self.dispersion[new_name]= value 
            
    def function(self, x=0.0): 
        """
        """
        return 0
                               
    def getProfile(self):
        """
        Get SLD profile of p_model if exists
        
        : return: (r, beta) where r is a list of radius of the transition points
                beta is a list of the corresponding SLD values 
        : Note: This works only for func_shell# = 2 (exp function)
                and is not supporting for p2
        """
        try:
            x,y = self.p_model1.getProfile()
        except:
            x = None
            y = None
            
        return x, y
    
    def _set_params(self):
        """
            Concatenate the parameters of the two models to create
            this model parameters 
        """

        for name , value in self.p_model1.params.iteritems():
            # No 2D-supported
            #if name not in self.p_model1.orientation_params:
            new_name = "p1_" + name
            self.params[new_name]= value
            
        for name , value in self.p_model2.params.iteritems():
            # No 2D-supported
            #if name not in self.p_model2.orientation_params:
            new_name = "p2_" + name
            self.params[new_name]= value
                
        # Set "scale" as initializing
        self._set_scale_factor()
      
            
    def _set_details(self):
        """
            Concatenate details of the two models to create
            this model details 
        """
        for name ,detail in self.p_model1.details.iteritems():
            new_name = "p1_" + name
            #if new_name not in self.orientation_params:
            self.details[new_name]= detail
            
        for name ,detail in self.p_model2.details.iteritems():
            new_name = "p2_" + name
            #if new_name not in self.orientation_params:
            self.details[new_name]= detail
    
    def _set_scale_factor(self):
        """
        Not implemented
        """
        pass
        
                
    def setParam(self, name, value):
        """ 
        Set the value of a model parameter
    
        :param name: name of the parameter
        :param value: value of the parameter
        """
        # set param to p1+p2 model
        self._setParamHelper(name, value)
        
        ## setParam to p model 
        model_pre = name.split('_', 1)[0]
        new_name = name.split('_', 1)[1]
        if model_pre == "p1":
            if new_name in self.p_model1.getParamList():
                self.p_model1.setParam(new_name, value)
        elif model_pre == "p2":
             if new_name in self.p_model2.getParamList():
                self.p_model2.setParam(new_name, value)
        elif name.lower() == 'scale_factor':
            self.params['scale_factor'] = value
        else:
            raise ValueError, "Model does not contain parameter %s" % name
            
    def getParam(self, name):
        """ 
        Set the value of a model parameter

        :param name: name of the parameter
        
        """
        # Look for dispersion parameters
        toks = name.split('.')
        if len(toks)==2:
            for item in self.dispersion.keys():
                # 2D not supported
                if item.lower()==toks[0].lower():# and \
                            #item.lower() not in self.orientation_params \
                            #and toks[0].lower() not in self.orientation_params:
                    for par in self.dispersion[item]:
                        if par.lower() == toks[1].lower():
                            return self.dispersion[item][par]
        else:
            # Look for standard parameter
            for item in self.params.keys():
                if item.lower()==name.lower():#and \
                            #item.lower() not in self.orientation_params \
                            #and toks[0].lower() not in self.orientation_params:
                    return self.params[item]
        return  
        #raise ValueError, "Model does not contain parameter %s" % name
       
    def _setParamHelper(self, name, value):
        """
        Helper function to setparam
        """
        # Look for dispersion parameters
        toks = name.split('.')
        if len(toks)== 2:
            for item in self.dispersion.keys():
                if item.lower()== toks[0].lower():# and \
                            #item.lower() not in self.orientation_params:
                    for par in self.dispersion[item]:
                        if par.lower() == toks[1].lower():#and \
                                #item.lower() not in self.orientation_params:
                            self.dispersion[item][par] = value
                            return
        else:
            # Look for standard parameter
            for item in self.params.keys():
                if item.lower()== name.lower():#and \
                            #item.lower() not in self.orientation_params:
                    self.params[item] = value
                    return
            
        raise ValueError, "Model does not contain parameter %s" % name
             
   
    def _set_fixed_params(self):
        """
             fill the self.fixed list with the p_model fixed list
        """
        for item in self.p_model1.fixed:
            new_item = "p1" + item
            self.fixed.append(new_item)
        for item in self.p_model2.fixed:
            new_item = "p2" + item
            self.fixed.append(new_item)

        self.fixed.sort()
                
                    
    def run(self, x = 0.0):
        """ 
        Evaluate the model
        
        :param x: input q-value (float or [float, float] as [r, theta])
        :return: (scattering function value)
        """
        self._set_scale_factor()
        return (self.params['scale_factor'] * self.p_model1.run(x) + \
                (1 - self.params['scale_factor']) * self.p_model2.run(x))
    
    def runXY(self, x = 0.0):
        """ 
        Evaluate the model
        
        :param x: input q-value (float or [float, float] as [qx, qy])
        :return: scattering function value
        """  
        self._set_scale_factor()
        return (self.params['scale_factor'] * self.p_model1.runXY(x) + \
                (1 - self.params['scale_factor']) * self.p_model2.runXY(x))
    
    ## Now (May27,10) directly uses the model eval function 
    ## instead of the for-loop in Base Component.
    def evalDistribution(self, x = []):
        """ 
        Evaluate the model in cartesian coordinates
        
        :param x: input q[], or [qx[], qy[]]
        :return: scattering function P(q[])
        """
        self._set_scale_factor()
        return (self.params['scale_factor'] * self.p_model1.evalDistribution(x) + \
                (1 - self.params['scale_factor']) * self.p_model2.evalDistribution(x))

    def set_dispersion(self, parameter, dispersion):
        """
        Set the dispersion object for a model parameter
        
        :param parameter: name of the parameter [string]
        :dispersion: dispersion object of type DispersionModel
        """
        value= None
        new_pre = parameter.split("_", 1)[0]
        new_parameter = parameter.split("_", 1)[1]
        try:
            if new_pre == 'p1' and \
                            new_parameter in self.p_model1.dispersion.keys():
                value= self.p_model1.set_dispersion(new_parameter, dispersion)
            if new_pre == 'p2' and \
                             new_parameter in self.p_model2.dispersion.keys():
                value= self.p_model2.set_dispersion(new_parameter, dispersion)
            self._set_dispersion()
            return value
        except:
            raise 

    def fill_description(self, p_model1, p_model2):
        """
        Fill the description for P(Q)+P(Q)
        """
        description = ""
        description +="This model gives the summation of (A*%s) and ((1-A)*%s).\n"% \
                                        ( p_model1.name, p_model2.name )
        self.description += description
    
    ## DO NOT MODIFY THE FOLLOWING LINES!!!!!!!!!!!!!!!!       
    def get_fname(self):
        """
        Get the model name same as the file name
        """
        path = sys._getframe().f_code.co_filename
        basename  = os.path.basename(path)
        name, _ = os.path.splitext(basename)
        return name
            
### FOR TEST                
if __name__ == "__main__": 
    m1= Model() 
    out1 = m1.runXY(0.01)
    m2= Model()
    out2 = 0.5 * m2.p_model1.runXY(0.01) + 0.5 * m2.p_model2.runXY(0.01)
    print "Testing at Q = 0.01:"
    print out1, " = ", out2
    if out1 == out2:
        print "===> Simple Test: Passed!"
    else:
        print "===> Simple Test: Failed!"
