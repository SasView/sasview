

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
        # flag to allow data2D plot
        self.enable2D = False
        # model on which the fit would be performed
        self.model = model
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
        #list of dispersion paramaters
        self.disp_list =[]
        #contains link between a model and selected parameters to fit 
        self.param_toFit =[]
        ##dictionary of model type and model class
        self.model_list_box = None
        ## save the state of the context menu
        self.saved_states={}
        ## save  current value of combobox
        self.formfactorcombobox = ""
        self.structurecombobox  = ""
        ## the indice of the current selection
        self.disp_box = 0
        ## Qrange
        ## Q range
        self.qmin= 0.001
        self.qmax= 0.1
        self.npts = None
        ## enable smearering state
        self.enable_smearer = False
        ## disperity selection
        self.enable_disp= False
        ## state of selected all check button
        self.cb1 = False
       
   
    def save_data(self, data):
        """
            Save data
        """
        self.data = copy.deepcopy(data)

        
    def clone(self):
        model=None
        if self.model !=None:
            model = self.model.clone()
        
        obj          = PageState( self.parent,model= model )
        obj.data = copy.deepcopy(self.data)
        obj.model_list_box = copy.deepcopy(self.model_list_box)
        obj.manager = self.manager
        obj.event_owner = self.event_owner
        obj.parameters = copy.deepcopy(self.parameters)
        obj.fixed_param = copy.deepcopy(self.fixed_param)
        obj.fittable_param = copy.deepcopy(self.fittable_param)
        obj.orientation_params =  copy.deepcopy(self.orientation_params)
        obj.enable_disp = copy.deepcopy(self.enable_disp)
        obj.enable_smearer = copy.deepcopy(self.enable_smearer)
        obj.disp_box = copy.deepcopy(self.disp_box)
        obj.qmin = copy.deepcopy(self.qmin)
        obj.qmax = copy.deepcopy(self.qmax)
        obj.npts = copy.deepcopy(self.npts )
        obj.cb1 = copy.deepcopy(self.cb1)
        for name, state in self.saved_states.iteritems():
            copy_name = copy.deepcopy(name)
            copy_state = state.clone()
            obj.saved_states[copy_name]= copy_state
        return obj

class PageMemento(object):
    """
        Store the state of a fitpage or model page of fitpanel
    """
    def __init__(self, state):
        """ Initialization"""
        self.state = state
       
    def setState(self,state):
        """
            set current state
            @param state: new state
        """
        self.state = state
        
    def getState(self):
        """
            @return state
        """
        return self.state
       
       
       
       