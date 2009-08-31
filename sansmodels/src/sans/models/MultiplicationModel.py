
from sans.models.BaseComponent import BaseComponent
import numpy, math
import copy
from sans.models.pluginmodel import Model1DPlugin
from sans.models.DiamCylFunc import  DiamCylFunc
from sans.models.DiamEllipFunc import  DiamEllipFunc
class MultiplicationModel(BaseComponent):
    """
        Use for P(Q)*S(Q); function call maut be in order of P(Q) and then S(Q).
        Perform multplication of two models.
        Contains the models parameters combined.
    """
    def __init__(self, model1, model2 ):
        BaseComponent.__init__(self)

       
        ## Setting  model name model description
        self.description=""
        if  model1.name != "NoStructure" and  model2.name != "NoStructure":
             self.name = model1.name +" * "+ model2.name
             self.description= self.name+"\n"
             self.description +="see %s description and %s description"%( model1.name,
                                                                         model2.name )
        elif  model2.name != "NoStructure":
            self.name = model2.name
            self.description= model2.description
        else :
            self.name = model1.name
            self.description= model1.description
                        


        self.model1= model1
        self.model2= model2
              
        ## Define diaparams 
        self._set_diaparams()
        ## dispersion
        self._set_dispersion()
        ## Define parameters
        self._set_params()
        ## Parameter details [units, min, max]
        self._set_details()
        #list of parameter that can be fitted
        self._set_fixed_params()  
        ## parameters with orientation
        for item in self.model1.orientation_params:
            self.orientation_params.append(item)
            
        for item in self.model2.orientation_params:
            if not item in self.orientation_params:
                self.orientation_params.append(item)
                
         
    def _clone(self, obj):
        """
            Internal utility function to copy the internal
            data members to a fresh copy.
        """
        obj.params     = copy.deepcopy(self.params)
        obj.description     = copy.deepcopy(self.description)
        obj.details    = copy.deepcopy(self.details)
        obj.dispersion = copy.deepcopy(self.dispersion)
        obj.model1  = self.model1.clone()
        obj.model2  = self.model2.clone()
        
        return obj
    
    
    def _set_dispersion(self):
        """
           combined the two models dispersions
        """
        for name , value in self.model1.dispersion.iteritems():
            self.dispersion[name]= value
            
        for name , value in self.model2.dispersion.iteritems():
            # S(Q) has only 'radius' for dispersion.
            if not name in self.dispersion.keys()and name !='radius': 
                self.dispersion[name]= value

    
                
    def _set_params(self):
        """
            Concatenate the parameters of the two models to create
            this model parameters 
        """
        #Prepare for radius calculation for Diam** functions
        #Only allows two case of radius modifications (radius = core_radius + thickness or just radius =radius).
        dia_rad = 0
        
        for name , value in self.model1.params.iteritems():
            self.params[name]= value
            
            if self.model2.name != 'NoStructure':
                if len(self.diapara[self.para[0]])>1 and \
                        (name == self.diapara[self.para[0]][0] or \
                         name == self.diapara[self.para[0]][1]):
                    dia_rad += value
                    
                    if self.modelD !=None:
                        self.modelD.params[self.para[0]]= dia_rad
                    else:
                        self.model2.setParam("radius", dia_rad)
                    
                elif self.modelD !=None:
                    if name == self.diapara[self.para[0]]:
                        self.modelD.params[self.para[0]]= value
                    elif name == self.diapara[self.para[1]]:
                        self.modelD.params[self.para[1]]= value
                elif name in self.model2.getParamList():
                    self.model2.setParam( name, value)
                        
                        
            print "value=",dia_rad 
        if self.modelD !=None:
            self.model2.setParam('radius', self.modelD.run())
            
        for name , value in self.model2.params.iteritems():
            if not name in self.params.keys()and name != 'radius':
                self.params[name]= value
            
    def _set_details(self):
        """
            Concatenate details of the two models to create
            this model details 
        """
        for name ,detail in self.model1.details.iteritems():
            self.details[name]= detail
            
        for name , detail in self.model2.details.iteritems():
            if not name in self.details.keys()and name != 'radius':
                self.details[name]= detail
                
    def setParam(self, name, value):
        """ 
            Set the value of a model parameter
        
            @param name: name of the parameter
            @param value: value of the parameter
        """

        self._setParamHelper( name, value)

        if name in self.model1.getParamList():
            self.model1.setParam( name, value)
            
        if self.model2.name != 'NoStructure':
            if len(self.diapara[self.para[0]])>1 and \
                    (name == self.diapara[self.para[0]][0] or \
                     name == self.diapara[self.para[0]][1]):
                self._set_params()
            elif self.modelD !=None:
                if name == self.diapara[self.para[0]]:
                    self.modelD.params[self.para[0]]= value
                    self.model2.setParam('radius', self.modelD.run())
                elif name == self.diapara[self.para[1]]:
                    self.modelD.params[self.para[1]]= value
                    self.model2.setParam('radius', self.modelD.run())
            elif name in self.model2.getParamList():
                self.model2.setParam( name, value)

        #print "val2=",name,self.model2.params['radius']
            
        self._setParamHelper( name, value)
        
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
                if item.lower()==name.lower():
                    self.params[item] = value
                    return
            
        raise ValueError, "Model does not contain parameter %s" % name
    
        
   
             
   
    def _set_fixed_params(self):
        """
             fill the self.fixed list with the two models fixed list
        """
        for item in self.model1.fixed:
            self.fixed.append(item)
            
        for item in self.model2.fixed:
            if not item in self.fixed:
                self.fixed.append(item)
        self.fixed.sort()
        

    def _set_diaparams(self):
        """
            Assign diamfunction parameters from model1.
        """
        #For virial coefficients for only two P(Q) models,"CylinderModel","EllipsoidModel". SphereModel works w/o it.
        modelDiam = None
        
        #List of models by type that can be multiplied of  P(Q)*S(Q) 
        #Parameters of model1 that need apply to the modelDiam corresponding to the models above
        list_sph_model_param = {'SphereModel':[['radius']],\
                                'CoreShellModel':[['radius','thickness']],\
                                'VesicleModel':[['radius','thickness']], \
                                 'BinaryHSModel':[['l_radius']], \
                                'MultiShellModel':[['core_radius','s_thickness']]}
        list_cyl_model_param = {'CylinderModel':[['radius'],['length']],\
                                'CoreShellCylinderModel':[['radius','thickness'],['length']],\
                                'HollowCylinderModel':[['radius'],['length']],\
                                'FlexibleCylinderModel':[['radius'],['length']]}
        list_ell_model_param = {'EllipsoidModel':[['radius_a'],['radius_b']],\
                                'CoreShellEllipsoidModel':[['polar_shell'],['equat_shell']]}   
        
        #This is where the list of the input parameters for ModelDiam will be.
        self.diapara = {}
        for key in list_sph_model_param:
            print "list_sph_models.param[]",len(list_sph_model_param['SphereModel'])
        #Find the input parameters for ModelDiam depending on model1.        
        para = {}
        self.para = {}
        
        #Determine the type of the model1
        if self.model1.__class__.__name__ in list_cyl_model_param.keys():
            Model1DPlugin("DiamCylFunc")
            basename = 'CylinderModel'
            modelDiam = DiamCylFunc()
            #loop for the # of parameters of DiamCylFunc()
            for idx in (0,len(list_cyl_model_param[basename])-1):
                #Parameter names of DiamCYlFunc
                para[idx] = list_cyl_model_param[basename][idx][0]
                #Find the  equivalent parameters of model1 function .
                self.diapara[para[idx]] = list_cyl_model_param[self.model1.__class__.__name__][idx]
                self.para[idx] = para[idx]
            
        elif self.model1.__class__.__name__  in list_ell_model_param.keys():
            Model1DPlugin("DiamEllipFunc")
            basename = 'EllipsoidModel'
            modelDiam = DiamEllipFunc()
            for idx in (0,len(list_ell_model_param[basename])-1):
                para[idx ] = list_ell_model_param[basename][idx ][0]
                self.diapara[para[idx]] = list_ell_model_param[self.model1.__class__.__name__][idx]
                self.para[idx] = para[idx]
                                
        elif self.model1.__class__.__name__  in list_sph_model_param.keys() :
            basename = 'SphereModel'
            for idx in (0,len(list_sph_model_param[basename])-1):
                para[idx] = list_sph_model_param[basename][idx][0]
                self.diapara[para[idx]] = list_sph_model_param[self.model1.__class__.__name__][idx]
                self.para[idx] = para[idx]
            
        #print "self.diapara1",para[0],self.diapara[para[0]]
        
        self.modelD = modelDiam
                        
    def run(self, x = 0.0):
        """ Evaluate the model
            @param x: input q-value (float or [float, float] as [r, theta])
            @return: (DAB value)
        """
        return self.model1.run(x)*self.model2.run(x)
   
    def runXY(self, x = 0.0):
        """ Evaluate the model
            @param x: input q-value (float or [float, float] as [qx, qy])
            @return: DAB value
        """
        print "model1.effecitve_radius",self.model1.calculate_ER() 
        return self.model1.runXY(x)* self.model2.runXY(x)
    
    def set_dispersion(self, parameter, dispersion):
        """
            Set the dispersion object for a model parameter
            @param parameter: name of the parameter [string]
            @dispersion: dispersion object of type DispersionModel
        """
        value= None
        try:
            if parameter in self.model1.dispersion.keys():
                value= self.model1.set_dispersion(parameter, dispersion)
            #There is no dispersion for the structure factors(S(Q)) for now. 
            #ToDo: need to decide whether or not the dispersion for S(Q) has to be considered for P*S.  
            elif parameter in self.model2.dispersion.keys()and name !='radius':
                value= self.model2.set_dispersion(parameter, dispersion)
            self._set_dispersion()
            return value
        except:
            raise 


    