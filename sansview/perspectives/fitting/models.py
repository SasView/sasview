import wx
import os
import os.path

(ModelEvent, EVT_MODEL) = wx.lib.newevent.NewEvent()
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
                    pass
                finally:
                    if not file==None:
                        file.close()
    except:
        pass
    return plugins


class ModelManager:
    
    ## Dictionary of models
    model_list = {}
    model_list_box = {}
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
        from sans.models.CylinderModel import CylinderModel
        self.model_list[str(wx.NewId())] = CylinderModel 
      
        from sans.models.SphereModel import SphereModel
        self.model_list[str(wx.NewId())] = SphereModel
   
        from sans.guitools.LineModel import LineModel
        self.model_list[str(wx.NewId())]  = LineModel
      
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

        for id_str,value in self.model_list.iteritems():
            item = self.model_list[id_str]
            
            name = item.__name__
            if hasattr(item, "name"):
                name = item.name
                
            self.model_list_box[name] =value
            
            modelmenu.Append(int(id_str), name, name)
            wx.EVT_MENU(event_owner, int(id_str), self._on_model)       
    
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
           
            model = self.model_list[str(evt.GetId())]()
            evt = ModelEvent(model=model)
            wx.PostEvent(self.event_owner, evt)
        
    def get_model_list(self):    
        """ @ return dictionary of models for fitpanel use """
        return self.model_list_box
    
    
    
 