

import copy

class PageState(object):
    """
        Contains info to reconstruct a page
    """
    def __init__(self, parent,model=None, data=None):
        
        """ 
            Initialization of the Panel
        """
        #TODO: remove this once the inheritence is cleaned up
        ## Data member to store the dispersion object created
        self._disp_obj_dict = {}
        ## reset True change the state of exsiting button
        self.reset = False
        #Data used for fitting 
        self.data = data
        #engine type
        self.engine_type = None
        # flag to allow data2D plot
        self.enable2D = False
        # model on which the fit would be performed
        self.model = model
        #if not hasattr(self.model, "_persistency_dict"):
        #    self.model._persistency_dict = {}
        #self.model._persistency_dict = copy.deepcopy(model._persistency_dict)
        #fit page manager 
        self.manager = None
        #Store the parent of this panel parent
        # For this application fitpanel is the parent
        self.parent  = parent
        # Event_owner is the owner of model event
        self.event_owner = None
        ##page name
        self.page_name = ""
        # Contains link between  model ,all its parameters, and panel organization
        self.parameters =[]
        # Contains list of parameters that cannot be fitted and reference to 
        #panel objects 
        self.fixed_param =[]
        # Contains list of parameters with dispersity and reference to 
        #panel objects 
        self.fittable_param =[]
        ## orientation parameters
        self.orientation_params=[]
        ## orientation parmaters for gaussian dispersity
        self.orientation_params_disp=[]
        ## smearer info
        self.smearer=None
        #list of dispersion paramaters
        self.disp_list =[]
        if self.model !=None:
            self.disp_list = self.model.getDispParamList()
        self._disp_obj_dict={}
        self.disp_cb_dict={}
        self.values=[]
        self.weights=[]
                    
        #contains link between a model and selected parameters to fit 
        self.param_toFit =[]
        ##dictionary of model type and model class
        self.model_list_box = None
        ## save the state of the context menu
        self.saved_states={}
        ## save selection of combobox
        self.formfactorcombobox = None
        self.structurecombobox  = None
        ## radio box to select type of model
        self.shape_rbutton = False
        self.shape_indep_rbutton = False
        self.struct_rbutton = False
        self.plugin_rbutton = False
        ## the indice of the current selection
        self.disp_box = 0
        ## Qrange
        ## Q range
        self.qmin= 0.001
        self.qmax= 0.1
        self.npts = None
        self.name=""
        ## enable smearering state
        self.enable_smearer = False
        self.disable_smearer = True
        ## disperity selection
        self.enable_disp= False
        self.disable_disp= True
        ## plot 2D data
        self.enable2D= False
        ## state of selected all check button
        self.cb1 = False
        ## store value of chisqr
        self.tcChi= None
    
    def clone(self):
        model=None
        if self.model !=None:
            model = self.model.clone()
        
        obj          = PageState( self.parent,model= model )
        obj.data = copy.deepcopy(self.data)
        obj.model_list_box = copy.deepcopy(self.model_list_box)
        obj.engine_type = copy.deepcopy(self.engine_type)
        
        obj.formfactorcombobox= self.formfactorcombobox
        obj.structurecombobox  =self.structurecombobox  
        
        obj.shape_rbutton = self.shape_rbutton 
        obj.shape_indep_rbutton = self.shape_indep_rbutton
        obj.struct_rbutton = self.struct_rbutton
        obj.plugin_rbutton = self.plugin_rbutton
        
        obj.manager = self.manager
        obj.event_owner = self.event_owner
        obj.disp_list = copy.deepcopy(self.disp_list)
        
        obj.enable2D = copy.deepcopy(self.enable2D)
        obj.parameters = copy.deepcopy(self.parameters)
        obj.fixed_param = copy.deepcopy(self.fixed_param)
        obj.fittable_param = copy.deepcopy(self.fittable_param)
        obj.orientation_params =  copy.deepcopy(self.orientation_params)
        obj.orientation_params_disp =  copy.deepcopy(self.orientation_params_disp)
        obj.enable_disp = copy.deepcopy(self.enable_disp)
        obj.disable_disp = copy.deepcopy(self.disable_disp)
        obj.tcChi = self.tcChi
  
        if len(self._disp_obj_dict)>0:
            for k , v in self._disp_obj_dict.iteritems():
                obj._disp_obj_dict[k]= v
        if len(self.disp_cb_dict)>0:
            for k , v in self.disp_cb_dict.iteritems():
                obj.disp_cb_dict[k]= v
                
        obj.values = copy.deepcopy(self.values)
        obj.weights = copy.deepcopy(self.weights)
        obj.enable_smearer = copy.deepcopy(self.enable_smearer)
        obj.disable_smearer = copy.deepcopy(self.disable_smearer)
       
        obj.disp_box = copy.deepcopy(self.disp_box)
        obj.qmin = copy.deepcopy(self.qmin)
        obj.qmax = copy.deepcopy(self.qmax)
        obj.npts = copy.deepcopy(self.npts )
        obj.cb1 = copy.deepcopy(self.cb1)
        obj.smearer = copy.deepcopy(self.smearer)
        
        for name, state in self.saved_states.iteritems():
            copy_name = copy.deepcopy(name)
            copy_state = state.clone()
            obj.saved_states[copy_name]= copy_state
        return obj

      
    def old__repr__(self):
        """ output string for printing"""
        rep = "\n\nState name: %s\n"%self.name
        rep +="data : %s\n"% str(self.data)
        rep += "Plotting Range: min: %s, max: %s, steps: %s\n"%(str(self.qmin),
                                                str(self.qmax),str(self.npts))
        rep +="model  : %s\n\n"% str(self.model)
        rep +="number parameters(self.parameters): %s\n"%len(self.parameters)
        for item in self.parameters:
            rep += "parameter name: %s \n"%str(item[1])
            rep += "value: %s\n"%str(item[2])
            rep += "selected: %s\n"%str(item[0])
            rep += "error displayed : %s \n"%str(item[4][0])
            rep += "error value:%s \n"%str(item[4][1])
            rep += "minimum displayed : %s \n"%str(item[5][0])
            rep += "minimum value : %s \n"%str(item[5][1])
            rep += "maximum displayed : %s \n"%str(item[6][0])
            rep += "maximum value : %s \n"%str(item[6][1])
            rep += "parameter unit: %s\n\n"%str(item[7])
        rep +="number orientation parameters"
        rep +="(self.orientation_params): %s\n"%len(self.orientation_params)
        for item in self.orientation_params:
            rep += "parameter name: %s \n"%str(item[1])
            rep += "value: %s\n"%str(item[2])
            rep += "selected: %s\n"%str(item[0])
            rep += "error displayed : %s \n"%str(item[4][0])
            rep += "error value:%s \n"%str(item[4][1])
            rep += "minimum displayed : %s \n"%str(item[5][0])
            rep += "minimum value : %s \n"%str(item[5][1])
            rep += "maximum displayed : %s \n"%str(item[6][0])
            rep += "maximum value : %s \n"%str(item[6][1])
            rep += "parameter unit: %s\n\n"%str(item[7])
        rep +="number dispersity parameters"
        rep +="(self.orientation_params_disp): %s\n"%len(self.orientation_params_disp)
        for item in self.orientation_params_disp:
            rep += "parameter name: %s \n"%str(item[1])
            rep += "value: %s\n"%str(item[2])
            rep += "selected: %s\n"%str(item[0])
            rep += "error displayed : %s \n"%str(item[4][0])
            rep += "error value:%s \n"%str(item[4][1])
            rep += "minimum displayed : %s \n"%str(item[5][0])
            rep += "minimum value : %s \n"%str(item[5][1])
            rep += "maximum displayed : %s \n"%str(item[6][0])
            rep += "maximum value : %s \n"%str(item[6][1])
            rep += "parameter unit: %s\n\n"%str(item[7])
        
        return rep

        
       
       