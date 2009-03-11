#TODO: add comments to document this module
#TODO: clean-up the exception handling.
#TODO: clean-up existing comments/documentation. 
#      For example, the _getModelList method advertises 
#      an 'id' parameter that is not part of the method's signature.
#      It also advertises an ID as return value but it always returns zero.
#TODO: clean-up the FractalAbsModel and PowerLawAbsModel menu items. Those
#      model definitions do not belong here. They belong with the rest of the
#      models.

import wx
import imp
import os,sys,math
import os.path

(ModelEvent, EVT_MODEL) = wx.lib.newevent.NewEvent()

# Time is needed by the log method
import time

# Explicitly import from the pluginmodel module so that py2exe
# places it in the distribution. The Model1DPlugin class is used
# as the base class of plug-in models.
from sans.models.pluginmodel import Model1DPlugin
    
def log(message):
    out = open("plugins.log", 'a')
    out.write("%10g:  %s\n" % (time.clock(), message))
    out.close()

def findModels():
    log("looking for models in: %s/plugins" % os.getcwd())
    if os.path.isdir('plugins'):
        return _findModels('plugins')
    return []
    
def _findModels(dir):
    # List of plugin objects
    plugins = []
    # Go through files in plug-in directory
    try:
        list = os.listdir(dir)
        for item in list:
            toks = os.path.splitext(os.path.basename(item))
            if toks[1]=='.py' and not toks[0]=='__init__':
                name = toks[0]
            
                path = [os.path.abspath(dir)]
                file = None
                try:
                    (file, path, info) = imp.find_module(name, path)
                    module = imp.load_module( name, file, item, info )
                    if hasattr(module, "Model"):
                        try:
                            plugins.append(module.Model)
                        except:
                            log("Error accessing Model in %s\n  %s" % (name, sys.exc_value))
                except:
                    log("Error accessing Model in %s\n  %s" % (name, sys.exc_value))
                finally:
              
                    if not file==None:
                        file.close()
    except:
        # Don't deal with bad plug-in imports. Just skip.
        pass
    return plugins


class ModelManager:
    ## external dict for models
    form_factor_dict_for_combox = {}
    ## Dictionary of form models
    form_factor_dict = {}
    ## dictionary of other
    struct_factor_dict = {}
    ##list of form factors
    shape_list =[]
    ## independent shape model list
    shape_indep_list = []
    ##list of structure factors 
    struct_list= []
    ## list of added models
    plugins=[]
    ## Event owner (guiframe)
    event_owner = None
    
    def _getModelList(self):
        """
            List of models we want to make available by default
            for this application
            
            @param id: first event ID to register the menu events with
            @return: the next free event ID following the new menu events
        """
        ## form factor
        from sans.models.SphereModel import SphereModel
        self.shape_list.append(SphereModel)
        
        from sans.models.CylinderModel import CylinderModel
        self.shape_list.append(CylinderModel)
      
        from sans.models.CoreShellModel import CoreShellModel
        self.shape_list.append(CoreShellModel)
        
        from sans.models.CoreShellCylinderModel import CoreShellCylinderModel
        self.shape_list.append(CoreShellCylinderModel)
        
        from sans.models.EllipticalCylinderModel import EllipticalCylinderModel
        self.shape_list.append(EllipticalCylinderModel)
        
        from sans.models.EllipsoidModel import EllipsoidModel
        self.shape_list.append(EllipsoidModel)
         
        from sans.models.LineModel import LineModel
        self.shape_list.append(LineModel)
        
        ## Structure factor 
        from sans.models.NoStructure import NoStructure
        self.struct_list.append(NoStructure)
        
        from sans.models.SquareWellStructure import SquareWellStructure
        self.struct_list.append(SquareWellStructure)
        
        from sans.models.HardsphereStructure import HardsphereStructure
        self.struct_list.append(HardsphereStructure)
         
        from sans.models.StickyHSStructure import StickyHSStructure
        self.struct_list.append(StickyHSStructure)
        
        from sans.models.HayterMSAStructure import HayterMSAStructure
        self.struct_list.append(HayterMSAStructure)
        
        
        ##shape-independent models
        from sans.models.BEPolyelectrolyte import BEPolyelectrolyte
        self.shape_indep_list.append(BEPolyelectrolyte )
        self.form_factor_dict[str(wx.NewId())] =  [SphereModel]
        from sans.models.DABModel import DABModel
        self.shape_indep_list.append(DABModel )
        
        from sans.models.GuinierModel import GuinierModel
        self.shape_indep_list.append(GuinierModel )
        
        from sans.models.DebyeModel import DebyeModel
        self.shape_indep_list.append(DebyeModel )
        
        from sans.models.PorodModel import PorodModel
        self.shape_indep_list.append(PorodModel )
        
        from sans.models.FractalModel import FractalModel
        class FractalAbsModel(FractalModel):
            def _Fractal(self, x):
                return FractalModel._Fractal(self, math.fabs(x))
        self.shape_indep_list.append(FractalAbsModel)
        
        from sans.models.LorentzModel import LorentzModel
        self.shape_indep_list.append( LorentzModel) 
            
        from sans.models.PowerLawModel import PowerLawModel
        class PowerLawAbsModel(PowerLawModel):
            def _PowerLaw(self, x):
                try:
                    return PowerLawModel._PowerLaw(self, math.fabs(x))
                except:
                    print sys.exc_value  
        self.shape_indep_list.append( PowerLawAbsModel )
        from sans.models.TeubnerStreyModel import TeubnerStreyModel
        self.shape_indep_list.append(TeubnerStreyModel )
    
        #Looking for plugins
        self.plugins = findModels()
       
        return 0

    
    def populate_menu(self, modelmenu, event_owner):
        """
            Populate a menu with our models
            
            @param id: first menu event ID to use when binding the menu events
            @param modelmenu: wx.Menu object to populate
            @param event_owner: wx object to bind the menu events to
            @return: the next free event ID following the new menu events
        """
        ## Fill model lists
        self._getModelList()
        ## store reference to model menu of guiframe
        self.modelmenu = modelmenu
        ## guiframe reference
        self.event_owner = event_owner
        
        
        shape_submenu = wx.Menu()
        shape_indep_submenu = wx.Menu()
        structure_factor = wx.Menu()
        added_models = wx.Menu()
        ## create menu with shape
        self._fill_menu( menuinfo = ["shapes...",shape_submenu," simple shape"],
                         list1 = self.shape_list,
                         list2 = self.struct_list )
        self._fill_menu( menuinfo = ["Shape-independent...",shape_indep_submenu,
                                    "List of shape-independent models"],
                         list1 = self.shape_indep_list,
                         list2 = self.struct_list )
        
        self._fill_simple_menu( menuinfo= ["Structure Factors...",structure_factor,
                                          "List of Structure factors models" ],
                                list1= self.struct_list )
        
        self._fill_simple_menu( menuinfo = ["Added models...", added_models,
                                            "List of additional models"],
                                 list1= self.plugins)
        return 0
    
    def _fill_simple_menu(self,menuinfo, list1):
        """
            Fill the menu with list item
            @param modelmenu: the menu to fill
            @param menuinfo: submenu item for the first column of this modelmenu
                             with info.Should be a list :
                             [name(string) , menu(wx.menu), help(string)]
            @param list1: contains item (form factor )to fill modelmenu second column
        """
        if len(list1)>0:
            for item in list1:
                id = wx.NewId() 
                if not item in self.form_factor_dict_for_combox.itervalues():
                    self.form_factor_dict_for_combox[int(id)] =item
                struct_factor=item()
                struct_name = struct_factor.__class__.__name__
                if hasattr(struct_factor, "name"):
                    struct_name = struct_factor.name
                    
                menuinfo[1].Append(int(id),struct_name,struct_name)
                if not  item in self.struct_factor_dict.itervalues():
                    self.struct_factor_dict[str(id)]= item
                wx.EVT_MENU(self.event_owner, int(id), self._on_model)
                
        id = wx.NewId()         
        self.modelmenu.AppendMenu(id, menuinfo[0],menuinfo[1],menuinfo[2])
        
        
        
    def _fill_menu(self,menuinfo, list1,list2  ):
        """
            Fill the menu with list item
            @param menuinfo: submenu item for the first column of this modelmenu
                             with info.Should be a list :
                             [name(string) , menu(wx.menu), help(string)]
            @param list1: contains item (form factor )to fill modelmenu second column
            @param list2: contains item (Structure factor )to fill modelmenu third column
        """
        for item in list1:   
            
            form_factor= item()
            form_name = form_factor.__class__.__name__
            if hasattr(form_factor, "name"):
                form_name = form_factor.name
            ### store form factor to return to other users   
            newmenu= wx.Menu()
            if len(list2)>0:
                for model  in list2:
                    id = wx.NewId()
                    struct_factor = model()
                    name = struct_factor.__class__.__name__
                    if hasattr(struct_factor, "name"):
                        name = struct_factor.name
                    newmenu.Append(id,name, name)
                    wx.EVT_MENU(self.event_owner, int(id), self._on_model)
                    ## save form_fact and struct_fact
                    self.form_factor_dict[int(id)] = [form_factor,struct_factor]
                    
                    if not item in self.form_factor_dict_for_combox.itervalues():
                        self.form_factor_dict_for_combox[int(id)] =item
            
            form_id= wx.NewId()    
            menuinfo[1].AppendMenu(int(form_id), form_name,newmenu,menuinfo[2])
        id=wx.NewId()
        self.modelmenu.AppendMenu(id,menuinfo[0],menuinfo[1], menuinfo[2])
        
        
        
        
    def _on_model(self, evt):
        """
            React to a model menu event
            @param event: wx menu event
        """
        if int(evt.GetId()) in self.form_factor_dict.keys():
            from sans.models.MultiplicationModel import MultiplicationModel
            model1, model2 = self.form_factor_dict[int(evt.GetId())]
            model = MultiplicationModel(model1, model2)
               
        else:
            model= self.struct_factor_dict[str(evt.GetId())]()
            
        evt = ModelEvent( model= model )
        wx.PostEvent(self.event_owner, evt)
        
    def get_model_list(self):    
        """ @ return dictionary of models for fitpanel use """
        return self.form_factor_dict_for_combox
    
    
    def get_form_struct(self):
        """ retunr list of form structures"""
        return self.struct_list
        
    
    
 