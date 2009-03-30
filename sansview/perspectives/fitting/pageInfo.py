

import wx
import copy

class PageInfo(object):
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

        #Data used for fitting 
        self.data = data
        # flag to allow data2D plot
        self.enable2D=False
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
        self.page_name=""
        # Contains link between  model ,all its parameters, and panel organization
        self.parameters=[]
        # Contains list of parameters that cannot be fitted and reference to 
        #panel objects 
        self.fixed_param=[]
        # Contains list of parameters with dispersity and reference to 
        #panel objects 
        self.fittable_param=[]
        #list of dispersion paramaters
        self.disp_list=[]
        #contains link between a model and selected parameters to fit 
        self.param_toFit=[]
        #dictionary of model type and model class
        self.model_list_box =None
        ## list of check box   
        self.list_of_radiobox={} 
        ## save  current value of combobox
        self.formfactorcombobox = ""
        self.structurecombobox  = ""
        ## Qrange
        self.qmin=None
        self.qmax=None
        self.npts=None
       
        
                  
    def save_radiobox_state(self, object ):
        """
            save  radiobox state 
            @param object: radiobox
            self.list_of_check= ["label", id, state]
           
        """
        label = object.GetLabel()
        id = object.GetId()
        state = object.GetValue()
        self.list_of_radiobox[label]=[label, id, state]    
    
    def clone(self):
        model=None
        if self.model !=None:
            model = self.model.clone()
        
        obj          = PageInfo( self.parent,model= model )
        obj.data = copy.deepcopy(self.data)
        
        return obj

       