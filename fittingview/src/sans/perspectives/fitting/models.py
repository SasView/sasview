
import wx
import wx.lib.newevent
import imp
import os
import sys
import math
import os.path
# Time is needed by the log method
import time
import logging
import py_compile
from sans.guiframe.events import StatusEvent  
# Explicitly import from the pluginmodel module so that py2exe
# places it in the distribution. The Model1DPlugin class is used
# as the base class of plug-in models.
from sans.models.pluginmodel import Model1DPlugin
   
PLUGIN_DIR = 'plugins' 

def log(message):
    """
    """
    out = open("plugins.log", 'a')
    out.write("%10g:  %s\n" % (time.clock(), message))
    out.close()


def _check_plugin(model, name):
    """
    Do some checking before model adding plugins in the list
    
    :param model: class model to add into the plugin list
    :param name:name of the module plugin
    
    :return model: model if valid model or None if not valid
    
    """
    #Check is the plugin is of type Model1DPlugin
    if not issubclass(model, Model1DPlugin):
        msg = "Plugin %s must be of type Model1DPlugin \n"%str(name)
        log(msg)
        return None
    if model.__name__!="Model":
        msg= "Plugin %s class name must be Model \n"%str(name)
        log(msg)
        return None
    try:
        new_instance= model()
    except:
        msg="Plugin %s error in __init__ \n\t: %s %s\n"%(str(name),
                                    str(sys.exc_type),sys.exc_value)
        log(msg)
        return None
   
    new_instance= model() 
    if hasattr(new_instance,"function"):
        try:
           value=new_instance.function()
        except:
           msg="Plugin %s: error writing function \n\t :%s %s\n "%(str(name),
                                    str(sys.exc_type),sys.exc_value)
           log(msg)
           return None
    else:
       msg="Plugin  %s needs a method called function \n"%str(name)
       log(msg)
       return None
    return model
  
def find_plugins_dir():
    """
    Find path of the plugins dir
    """
    dir = os.path.abspath(PLUGIN_DIR)
    if not os.path.isdir(dir):
        dir = os.path.join(os.getcwd(), PLUGIN_DIR)
    if not os.path.isdir(dir):
        dir = os.path.join(os.path.dirname(__file__), PLUGIN_DIR)
    if not os.path.isdir(dir):
        dir = os.path.join(os.path.dirname(os.path.sys.path[0]), PLUGIN_DIR)
    return dir

class ReportProblem:
    def __nonzero__(self):
        type, value, traceback = sys.exc_info()
        if type is not None and issubclass(type, py_compile.PyCompileError):
            print "Problem with", repr(value)
            raise type, value, traceback
        return 1
    
report_problem = ReportProblem()

def compile_file(dir):
    """
    Compile a py file
    """
    try:
        import compileall
        compileall.compile_dir(dir=dir, ddir=dir, force=1, quiet=report_problem)
    except:
        type, value, traceback = sys.exc_info()
        return value
    return None

def _findModels(dir):
    """
    """
    # List of plugin objects
    plugins = {}
    # Go through files in plug-in directory
    #always recompile the folder plugin
    import compileall
    dir = find_plugins_dir()
    if not os.path.isdir(dir):
        msg = "SansView couldn't locate Model plugin folder."
        msg += """ "%s" does not exist""" % dir
        logging.warning(msg)
        return plugins
    else:
        log("looking for models in: %s" % str(dir))
        compile_file(dir)
        logging.info("pluging model dir: %s\n" % str(dir))
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
                            if _check_plugin(module.Model, name)!=None:
                                plugins[name] = module.Model
                        except:
                            msg="Error accessing Model"
                            msg+="in %s\n  %s %s\n" % (name,
                                    str(sys.exc_type), sys.exc_value)
                            log(msg)
                except:
                    msg="Error accessing Model"
                    msg +=" in %s\n  %s %s \n" %(name,
                                    str(sys.exc_type), sys.exc_value)
                    log(msg)
                finally:
              
                    if not file==None:
                        file.close()
    except:
        # Don't deal with bad plug-in imports. Just skip.
        msg = "Could not import model plugin: %s\n" % sys.exc_value
        log(msg)
        pass
    return plugins

class ModelList(object):
    """
    Contains dictionary of model and their type
    """
    def __init__(self):
        """
        """
        self.mydict = {}
        
    def set_list(self, name, mylist):
        """
        :param name: the type of the list
        :param mylist: the list to add
        
        """
        if name not in self.mydict.keys():
            self.mydict[name] = mylist
            
            
    def get_list(self):
        """
        return all the list stored in a dictionary object
        """
        return self.mydict
        
class ModelManagerBase:
    """
    """
    ## external dict for models
    model_combobox = ModelList()
    ## Dictionary of form models
    form_factor_dict = {}
    ## dictionary of other
    struct_factor_dict = {}
    ##list of form factors
    shape_list = []
    ## independent shape model list
    shape_indep_list = []
    ##list of structure factors 
    struct_list = []
    ##list of model allowing multiplication
    multiplication_factor = []
    ##list of multifunctional shapes
    multi_func_list = []
    ## list of added models
    plugins = []
    ## Event owner (guiframe)
    event_owner = None
    last_time_dir_modified = 0
    def __init__(self):
        """
        """
       
        self.stored_plugins = {}
        self._getModelList()
        
        
    def findModels(self):
        """
        find  plugin model in directory of plugin .recompile all file
        in the directory if file were modified
        """
        temp = {}
        if self.is_changed():
            return  _findModels(dir)
        logging.info("pluging model : %s\n" % str(temp))
        return temp
        
    def _getModelList(self):
        """
        List of models we want to make available by default
        for this application
    
        :return: the next free event ID following the new menu events
        
        """
        from sans.models.SphereModel import SphereModel
        self.shape_list.append(SphereModel)
        self.multiplication_factor.append(SphereModel)
        
        from sans.models.BinaryHSModel import BinaryHSModel
        self.shape_list.append(BinaryHSModel)
                        
        from sans.models.FuzzySphereModel import FuzzySphereModel
        self.shape_list.append(FuzzySphereModel)
        self.multiplication_factor.append(FuzzySphereModel)
           
        from sans.models.CoreShellModel import CoreShellModel
        self.shape_list.append(CoreShellModel)
        self.multiplication_factor.append(CoreShellModel)
        
        from sans.models.CoreMultiShellModel import CoreMultiShellModel
        self.shape_list.append(CoreMultiShellModel)
        self.multiplication_factor.append(CoreMultiShellModel)
        self.multi_func_list.append(CoreMultiShellModel)

        from sans.models.VesicleModel import VesicleModel
        self.shape_list.append(VesicleModel)
        self.multiplication_factor.append(VesicleModel)
        
        from sans.models.MultiShellModel import MultiShellModel
        self.shape_list.append(MultiShellModel)
        self.multiplication_factor.append(MultiShellModel)
        
        from sans.models.OnionExpShellModel import OnionExpShellModel
        self.shape_list.append(OnionExpShellModel)
        self.multiplication_factor.append(OnionExpShellModel)
        self.multi_func_list.append(OnionExpShellModel)
                         
        from sans.models.SphericalSLDModel import SphericalSLDModel
        self.shape_list.append(SphericalSLDModel)
        self.multiplication_factor.append(SphericalSLDModel)
        self.multi_func_list.append(SphericalSLDModel)
        
        from sans.models.PearlNecklaceModel import PearlNecklaceModel
        self.shape_list.append(PearlNecklaceModel)
        #self.multiplication_factor.append(PearlNecklaceModel)
        
        from sans.models.CylinderModel import CylinderModel
        self.shape_list.append(CylinderModel)
        self.multiplication_factor.append(CylinderModel)
        
        from sans.models.CoreShellCylinderModel import CoreShellCylinderModel
        self.shape_list.append(CoreShellCylinderModel)
        self.multiplication_factor.append(CoreShellCylinderModel)
        
        from sans.models.HollowCylinderModel import HollowCylinderModel
        self.shape_list.append(HollowCylinderModel)
        self.multiplication_factor.append(HollowCylinderModel)
              
        from sans.models.FlexibleCylinderModel import FlexibleCylinderModel
        self.shape_list.append(FlexibleCylinderModel)

        from sans.models.FlexCylEllipXModel import FlexCylEllipXModel
        self.shape_list.append(FlexCylEllipXModel)
        
        from sans.models.StackedDisksModel import StackedDisksModel
        self.shape_list.append(StackedDisksModel)
        self.multiplication_factor.append(StackedDisksModel)
        
        from sans.models.ParallelepipedModel import ParallelepipedModel
        self.shape_list.append(ParallelepipedModel)
        self.multiplication_factor.append(ParallelepipedModel)
        
        from sans.models.CSParallelepipedModel import CSParallelepipedModel
        self.shape_list.append(CSParallelepipedModel)
        self.multiplication_factor.append(CSParallelepipedModel)
        
        from sans.models.EllipticalCylinderModel import EllipticalCylinderModel
        self.shape_list.append(EllipticalCylinderModel)
        self.multiplication_factor.append(EllipticalCylinderModel)
        
        from sans.models.BarBellModel import BarBellModel
        self.shape_list.append(BarBellModel)
        # not implemeted yet!
        #self.multiplication_factor.append(BarBellModel)
        
        from sans.models.CappedCylinderModel import CappedCylinderModel
        self.shape_list.append(CappedCylinderModel)
        # not implemeted yet!
        #self.multiplication_factor.append(CappedCylinderModel)
        
        from sans.models.EllipsoidModel import EllipsoidModel
        self.shape_list.append(EllipsoidModel)
        self.multiplication_factor.append(EllipsoidModel)
      
        from sans.models.CoreShellEllipsoidModel import CoreShellEllipsoidModel
        self.shape_list.append(CoreShellEllipsoidModel)
        self.multiplication_factor.append(CoreShellEllipsoidModel)
         
        from sans.models.TriaxialEllipsoidModel import TriaxialEllipsoidModel
        self.shape_list.append(TriaxialEllipsoidModel)
        self.multiplication_factor.append(TriaxialEllipsoidModel)
        
        from sans.models.LamellarModel import LamellarModel
        self.shape_list.append(LamellarModel)
        
        from sans.models.LamellarFFHGModel import LamellarFFHGModel
        self.shape_list.append(LamellarFFHGModel)
        
        from sans.models.LamellarPSModel import LamellarPSModel
        self.shape_list.append(LamellarPSModel)
     
        from sans.models.LamellarPSHGModel import LamellarPSHGModel
        self.shape_list.append(LamellarPSHGModel)
        
        from sans.models.LamellarPCrystalModel import LamellarPCrystalModel
        self.shape_list.append(LamellarPCrystalModel)
        
        from sans.models.SCCrystalModel import SCCrystalModel
        self.shape_list.append(SCCrystalModel)
        
        from sans.models.FCCrystalModel import FCCrystalModel
        self.shape_list.append(FCCrystalModel)
        
        from sans.models.BCCrystalModel import BCCrystalModel
        self.shape_list.append(BCCrystalModel)
      
        ## Structure factor 
        from sans.models.SquareWellStructure import SquareWellStructure
        self.struct_list.append(SquareWellStructure)
        
        from sans.models.HardsphereStructure import HardsphereStructure
        self.struct_list.append(HardsphereStructure)
         
        from sans.models.StickyHSStructure import StickyHSStructure
        self.struct_list.append(StickyHSStructure)
        
        from sans.models.HayterMSAStructure import HayterMSAStructure
        self.struct_list.append(HayterMSAStructure)
        
        ##shape-independent models
        from sans.models.PowerLawAbsModel import PowerLawAbsModel
        self.shape_indep_list.append( PowerLawAbsModel )
        
        from sans.models.BEPolyelectrolyte import BEPolyelectrolyte
        self.shape_indep_list.append(BEPolyelectrolyte )
        self.form_factor_dict[str(wx.NewId())] =  [SphereModel]
        
        from sans.models.BroadPeakModel import BroadPeakModel
        self.shape_indep_list.append(BroadPeakModel)
        
        from sans.models.CorrLengthModel import CorrLengthModel
        self.shape_indep_list.append(CorrLengthModel)
        
        from sans.models.DABModel import DABModel
        self.shape_indep_list.append(DABModel )
        
        from sans.models.DebyeModel import DebyeModel
        self.shape_indep_list.append(DebyeModel )
        
        #FractalModel (a c-model)is now being used instead of FractalAbsModel.
        from sans.models.FractalModel import FractalModel
        self.shape_indep_list.append(FractalModel )
        
        from sans.models.FractalCoreShellModel import FractalCoreShellModel
        self.shape_indep_list.append(FractalCoreShellModel )
        
        from sans.models.GaussLorentzGelModel import GaussLorentzGelModel
        self.shape_indep_list.append(GaussLorentzGelModel) 
                
        from sans.models.GuinierModel import GuinierModel
        self.shape_indep_list.append(GuinierModel )
        
        from sans.models.GuinierPorodModel import GuinierPorodModel
        self.shape_indep_list.append(GuinierPorodModel )

        from sans.models.LorentzModel import LorentzModel
        self.shape_indep_list.append( LorentzModel) 
        
        from sans.models.PeakGaussModel import PeakGaussModel
        self.shape_indep_list.append(PeakGaussModel)
        
        from sans.models.PeakLorentzModel import PeakLorentzModel
        self.shape_indep_list.append(PeakLorentzModel)
        
        from sans.models.Poly_GaussCoil import Poly_GaussCoil
        self.shape_indep_list.append(Poly_GaussCoil)
        
        from sans.models.PolymerExclVolume import PolymerExclVolume
        self.shape_indep_list.append(PolymerExclVolume)
        
        from sans.models.PorodModel import PorodModel
        self.shape_indep_list.append(PorodModel )      
        
        from sans.models.RPA10Model import RPA10Model
        self.shape_indep_list.append(RPA10Model)
        self.multi_func_list.append(RPA10Model)
        
        from sans.models.TeubnerStreyModel import TeubnerStreyModel
        self.shape_indep_list.append(TeubnerStreyModel )
        
        from sans.models.TwoLorentzianModel import TwoLorentzianModel
        self.shape_indep_list.append(TwoLorentzianModel )
        
        from sans.models.TwoPowerLawModel import TwoPowerLawModel
        self.shape_indep_list.append(TwoPowerLawModel )
        
        from sans.models.UnifiedPowerRgModel import UnifiedPowerRgModel
        self.shape_indep_list.append(UnifiedPowerRgModel )
        self.multi_func_list.append(UnifiedPowerRgModel)
        
        from sans.models.LineModel import LineModel
        self.shape_indep_list.append(LineModel)
        
        from sans.models.ReflectivityModel import ReflectivityModel
        self.multi_func_list.append(ReflectivityModel)
        
        from sans.models.ReflectivityIIModel import ReflectivityIIModel
        self.multi_func_list.append(ReflectivityIIModel)
    
        #Looking for plugins
        self.stored_plugins = self.findModels()
        self.plugins = self.stored_plugins.values()
        self.plugins.append(ReflectivityModel)
        self.plugins.append(ReflectivityIIModel)
        self._get_multifunc_models()
       
        return 0

    def is_changed(self):
        """
        check the last time the plugin dir has changed and return true
         is the directory was modified else return false
        """
        is_modified = False
        if os.path.isdir(PLUGIN_DIR):
            # getmtime doesn't seem to work well: use getatime
            temp =  os.path.getatime(PLUGIN_DIR)
            if  self.last_time_dir_modified != temp:
                is_modified = True
                self.last_time_dir_modified = temp
        
        return is_modified
    
    def update(self):
        """
        return a dictionary of model if 
        new models were added else return empty dictionary
        """
        new_plugins = self.findModels()
        if len(new_plugins) > 0:
            for name, plug in  new_plugins.iteritems():
                if name not in self.stored_plugins.keys():
                    self.stored_plugins[name] = plug
                    self.plugins.append(plug)
            self.model_combobox.set_list("Customized Models", self.plugins)
            return self.model_combobox.get_list()
        else:
            return {}
    
             
    def populate_menu(self, modelmenu, event_owner):
        """
        Populate a menu with our models
        
        :param id: first menu event ID to use when binding the menu events
        :param modelmenu: wx.Menu object to populate
        :param event_owner: wx object to bind the menu events to
        
        :return: the next free event ID following the new menu events
        
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
        multip_models = wx.Menu()
        ## create menu with shape
        self._fill_simple_menu(menuinfo=["Shapes",shape_submenu," simple shape"],
                         list1=self.shape_list)
        
        self._fill_simple_menu(menuinfo=["Shape-Independent",shape_indep_submenu,
                                    "List of shape-independent models"],
                         list1=self.shape_indep_list )
        
        self._fill_simple_menu(menuinfo=["Structure Factors",structure_factor,
                                          "List of Structure factors models" ],
                                list1=self.struct_list)
        
        self._fill_plugin_menu(menuinfo=["Customized Models", added_models,
                                            "List of additional models"],
                                 list1=self.plugins)
        
        self._fill_menu(menuinfo=["P(Q)*S(Q)",multip_models,
                                  "mulplication of 2 models"],
                                   list1=self.multiplication_factor ,
                                   list2= self.struct_list)
        return 0
    
    def _fill_plugin_menu(self, menuinfo, list1):
        """
        fill the plugin menu with costumized models
        """
        if len(list1)==0:
            id = wx.NewId() 
            msg= "No model available check plugins.log for errors to fix problem"
            menuinfo[1].Append(int(id),"Empty",msg)
        self._fill_simple_menu( menuinfo,list1)
        
    def _fill_simple_menu(self, menuinfo, list1):
        """
        Fill the menu with list item
        
        :param modelmenu: the menu to fill
        :param menuinfo: submenu item for the first column of this modelmenu
                         with info.Should be a list :
                         [name(string) , menu(wx.menu), help(string)]
        :param list1: contains item (form factor )to fill modelmenu second column
        
        """
        if len(list1)>0:
            self.model_combobox.set_list(menuinfo[0],list1)
            
            for item in list1:
                try:
                    id = wx.NewId() 
                    struct_factor=item()
                    struct_name = struct_factor.__class__.__name__
                    if hasattr(struct_factor, "name"):
                        struct_name = struct_factor.name
                        
                    menuinfo[1].Append(int(id),struct_name,struct_name)
                    if not  item in self.struct_factor_dict.itervalues():
                        self.struct_factor_dict[str(id)]= item
                    wx.EVT_MENU(self.event_owner, int(id), self._on_model)
                except:
                    msg= "Error Occured: %s"%sys.exc_value
                    wx.PostEvent(self.event_owner, StatusEvent(status=msg))
                
        id = wx.NewId()         
        self.modelmenu.AppendMenu(id, menuinfo[0],menuinfo[1],menuinfo[2])
        
    def _fill_menu(self, menuinfo, list1, list2):
        """
        Fill the menu with list item
        
        :param menuinfo: submenu item for the first column of this modelmenu
                         with info.Should be a list :
                         [name(string) , menu(wx.menu), help(string)]
        :param list1: contains item (form factor )to fill modelmenu second column
        :param list2: contains item (Structure factor )to fill modelmenu 
                third column
                
        """
        if len(list1)>0:
            self.model_combobox.set_list(menuinfo[0],list1)
            
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
                        
                form_id= wx.NewId()    
                menuinfo[1].AppendMenu(int(form_id), form_name,newmenu,menuinfo[2])
        id=wx.NewId()
        self.modelmenu.AppendMenu(id,menuinfo[0],menuinfo[1], menuinfo[2])
        
    def _on_model(self, evt):
        """
        React to a model menu event
        
        :param event: wx menu event
        
        """
        if int(evt.GetId()) in self.form_factor_dict.keys():
            from sans.models.MultiplicationModel import MultiplicationModel
            model1, model2 = self.form_factor_dict[int(evt.GetId())]
            model = MultiplicationModel(model1, model2)    
        else:
            model= self.struct_factor_dict[str(evt.GetId())]()
        evt = ModelEvent(model=model)
        wx.PostEvent(self.event_owner, evt)
        
    def _get_multifunc_models(self):
        """
        Get the multifunctional models
        """
        for item in self.plugins:
            try:
                # check the multiplicity if any
                if item.multiplicity_info[0] > 1:
                    self.multi_func_list.append(item)
            except:
                # pass to other items
                pass
                    
    def get_model_list(self):    
        """
        return dictionary of models for fitpanel use 
        
        """
        self.model_combobox.set_list("Shapes", self.shape_list)
        self.model_combobox.set_list("Shape-Independent", self.shape_indep_list)
        self.model_combobox.set_list("Structure Factors", self.struct_list)
        self.model_combobox.set_list("Customized Models", self.plugins)
        self.model_combobox.set_list("P(Q)*S(Q)", self.multiplication_factor)
        self.model_combobox.set_list("multiplication", self.multiplication_factor)
        self.model_combobox.set_list("Multi-Functions", self.multi_func_list)
        return self.model_combobox.get_list()
    
  
        
class ModelManager(object):
    """
    implement model 
    """
    __modelmanager = ModelManagerBase()
    
    def findModels(self):
        return self.__modelmanager.findModels()
    
    def _getModelList(self):
        return self.__modelmanager._getModelList()
    
    def is_changed(self):
        return self.__modelmanager.is_changed()
    
    def update(self):
        return self.__modelmanager.update()
    
    def populate_menu(self, modelmenu, event_owner):
        return self.__modelmanager.populate_menu(modelmenu, event_owner)
    
    def _on_model(self, evt):
        return self.__modelmanager._on_model(evt)
    
    def _get_multifunc_models(self):
        return self.__modelmanager._get_multifunc_models()
    
    def get_model_list(self): 
        return self.__modelmanager.get_model_list()
    
    
  