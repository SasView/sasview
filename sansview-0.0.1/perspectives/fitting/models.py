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
    
    ## Dictionary of models
    model_list = {}
    indep_model_list = {}
    model_list_box = {}
    custom_models={}
    plugins=[]
    indep_model=[]
    ## Event owner
    event_owner = None
    
    def _getModelList(self):
        """
            List of models we want to make available by default
            for this application
            
            @param id: first event ID to register the menu events with
            @return: the next free event ID following the new menu events
        """
        self.model_list = {}
        self.model_list_box = {}
       
        
        from sans.models.SphereModel import SphereModel
        self.model_list[str(wx.NewId())] =  SphereModel
        
        from sans.models.CylinderModel import CylinderModel
        self.model_list[str(wx.NewId())] =CylinderModel
      
        from sans.models.CoreShellModel import CoreShellModel
        self.model_list[str(wx.NewId())] = CoreShellModel 
        
        from sans.models.CoreShellCylinderModel import CoreShellCylinderModel
        self.model_list[str(wx.NewId())] =CoreShellCylinderModel
        
        from sans.models.EllipticalCylinderModel import EllipticalCylinderModel
        self.model_list[str(wx.NewId())] =EllipticalCylinderModel
        
        from sans.models.EllipsoidModel import EllipsoidModel
        self.model_list[str(wx.NewId())] = EllipsoidModel 
        
        from sans.models.SquareWellStructure import SquareWellStructure
        self.model_list[str(wx.NewId())] =  SquareWellStructure
        
        from sans.models.HardsphereStructure import HardsphereStructure
        self.model_list[str(wx.NewId())] =  HardsphereStructure
        
        from sans.models.StickyHSStructure import StickyHSStructure
        self.model_list[str(wx.NewId())] =  StickyHSStructure
        
        from sans.models.HayterMSAStructure import HayterMSAStructure
        self.model_list[str(wx.NewId())] =  HayterMSAStructure
        
        from sans.models.LineModel import LineModel
        self.model_list[str(wx.NewId())]  = LineModel
        
        
        model_info="shape-independent models"
        
        from sans.models.BEPolyelectrolyte import BEPolyelectrolyte
        self.indep_model.append(BEPolyelectrolyte )
        
        from sans.models.DABModel import DABModel
        self.indep_model.append(DABModel )
        
        from sans.models.GuinierModel import GuinierModel
        self.indep_model.append(GuinierModel )
        
        from sans.models.DebyeModel import DebyeModel
        self.indep_model.append(DebyeModel )
        
        from sans.models.FractalModel import FractalModel
        class FractalAbsModel(FractalModel):
            def _Fractal(self, x):
                return FractalModel._Fractal(self, math.fabs(x))
        self.indep_model.append(FractalAbsModel)
        
        from sans.models.LorentzModel import LorentzModel
        self.indep_model.append( LorentzModel) 
            
        from sans.models.PowerLawModel import PowerLawModel
        class PowerLawAbsModel(PowerLawModel):
            def _PowerLaw(self, x):
                try:
                    return PowerLawModel._PowerLaw(self, math.fabs(x))
                except:
                    print sys.exc_value  
        self.indep_model.append( PowerLawAbsModel )
        from sans.models.TeubnerStreyModel import TeubnerStreyModel
        self.indep_model.append(TeubnerStreyModel )
    
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
        self._getModelList()
        self.event_owner = event_owner
        shape_submenu= wx.Menu() 
        indep_submenu = wx.Menu()
        added_models = wx.Menu()
        for id_str,value in self.model_list.iteritems():
            item = self.model_list[id_str]()
            name = item.__class__.__name__
            if hasattr(item, "name"):
                name = item.name
            self.model_list_box[name] =value
            shape_submenu.Append(int(id_str), name, name)
            wx.EVT_MENU(event_owner, int(id_str), self._on_model)
        modelmenu.AppendMenu(wx.NewId(), "Shapes...", shape_submenu, "List of shape-based models")
        id = wx.NewId()
        if len(self.indep_model_list) == 0:
            for items in self.indep_model:
                #if item not in self.indep_model_list.values():
                    #self.indep_model_list[str(id)] = item
                self.model_list[str(id)]=items
                item=items()
                name = item.__class__.__name__
                if hasattr(item, "name"):
                    name = item.name
                indep_submenu.Append(id,name, name)
                self.model_list_box[name] =items
                wx.EVT_MENU(event_owner, int(id), self._on_model)
                id = wx.NewId()         
        modelmenu.AppendMenu(wx.NewId(), "Shape-independent...", indep_submenu, "List of shape-independent models")
        id = wx.NewId()
        if len(self.custom_models) == 0:
            for items in self.plugins:
                #if item not in self.custom_models.values():
                    #self.custom_models[str(id)] = item
                self.model_list[str(id)]=items
                name = items.__name__
                if hasattr(items, "name"):
                    name = items.name
                added_models.Append(id, name, name)
                self.model_list_box[name] =items
                wx.EVT_MENU(event_owner, int(id), self._on_model)
                id = wx.NewId()
        modelmenu.AppendMenu(wx.NewId(),"Added models...", added_models, "List of additional models")
        return 0
    
    def _on_model(self, evt):
        """
            React to a model menu event
            @param event: wx menu event
        """
        if str(evt.GetId()) in self.model_list.keys():
            # Notify the application manager that a new model has been set
            #self.app_manager.set_model(self.model_list[str(evt.GetId())]())
            
            #TODO: post a model event to update all panels that need
            #evt = ModelEvent(model=self.model_list[str(evt.GetId())]())
           
            model = self.model_list[str(evt.GetId())]
            evt = ModelEvent(model= model )
            wx.PostEvent(self.event_owner, evt)
        
    def get_model_list(self):    
        """ @ return dictionary of models for fitpanel use """
        return self.model_list_box
    
    
    
 