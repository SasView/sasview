
import wx
import sys
from copy import deepcopy
from sas.dataloader.loader import Loader
from sas.guiframe.utils import check_float

_BOX_WIDTH = 60
if sys.platform.count("win32")>0:
    _STATICBOX_WIDTH = 450
    PANEL_WIDTH = 500
    PANEL_HEIGHT = 290
    FONT_VARIANT = 0
else:
    _STATICBOX_WIDTH = 480
    PANEL_WIDTH = 530
    PANEL_HEIGHT = 320
    FONT_VARIANT = 1
    
class ApertureDialog(wx.Dialog):
    def __init__(self, parent=None, manager=None, aperture=None, *args, **kwds):
        """
        Dialog allows to enter values for aperture
        """
        kwds['size'] = (PANEL_WIDTH, PANEL_HEIGHT)
        kwds['title'] = "Aperture Editor"
        wx.Dialog.__init__(self, parent=parent, *args, **kwds)
        self.parent = parent
        self.manager = manager
        self._aperture = aperture
        self._reset_aperture = deepcopy(aperture)
        self._notes = ""
        #self_description = "Edit aperture"
        
        #Attributes for panel
        self.aperture_name_tcl = None
        self.main_sizer = None
        self.box_aperture = None
        self.boxsizer_aperture = None
        self.name_sizer = None
        self.name_sizer = None
        self.size_name_tcl  = None
        self.type_sizer = None
        self.distance_sizer = None
        self.size_name_sizer = None
        self.aperture_size_unit_tcl = None
        self.aperture_size_sizer = None
        self.button_sizer = None
        self.aperture_name_tcl = None
        self.type_tcl = None
        self.distance_tcl = None
        self.distance_unit_tcl = None
        self.x_aperture_size_tcl = None
        self.y_aperture_size_tcl = None
        self.z_aperture_size_tcl = None
        self.bt_apply = None
        self.bt_cancel = None
        self.bt_close = None
        
        self._do_layout()
        self.set_values()
      
    def _define_structure(self):
        """
        define initial sizer 
        """
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.box_aperture = wx.StaticBox(self, -1, str("Aperture"))
        self.boxsizer_aperture = wx.StaticBoxSizer(self.box_aperture, 
                                                   wx.VERTICAL)
       
        self.name_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.type_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.distance_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.size_name_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.aperture_size_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.button_sizer = wx.BoxSizer(wx.HORIZONTAL)
 
    def _layout_name(self):
        """
        Do the layout for aperture name related widgets
        """
        #Aperture name [string]
        aperture_name_txt = wx.StaticText(self, -1, 'Aperture Name : ')  
        self.aperture_name_tcl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH*5, 20),
                                              style=0) 
        self.name_sizer.AddMany([(aperture_name_txt, 0, wx.LEFT|wx.RIGHT, 10),
                                       (self.aperture_name_tcl, 0, wx.EXPAND)])
    def _layout_type(self):
        """
        Do the  layout for aperture type  related widgets
        """
        #Aperture type [string]
        type_txt = wx.StaticText(self, -1, 'Type: ')  
        self.type_tcl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH, 20), style=0)
        self.type_sizer.AddMany([(type_txt, 0, wx.LEFT|wx.RIGHT, 10),
                                     (self.type_tcl, 0, wx.LEFT, 20)])
        
    def _layout_distance(self):
        """
        Do the  layout for aperture distance related widgets
        """
        #Aperture distance [float]
        distance_txt = wx.StaticText(self, -1, 'Distance:') 
        self.distance_tcl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH, 20), 
                                        style=0)   
        distance_unit_txt = wx.StaticText(self, -1, 'Unit: ') 
        self.distance_unit_tcl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH, 20),
                                             style=0)  
        self.distance_sizer.AddMany([(distance_txt, 0, wx.LEFT|wx.RIGHT, 10),
                                     (self.distance_tcl, 0, wx.LEFT, 10),
                                (distance_unit_txt, 0,  wx.LEFT|wx.RIGHT, 10),
                                     (self.distance_unit_tcl, 0, wx.EXPAND)])  
    def _layout_size_name(self):
        """
        Do the  layout for size name related widgets
        """
        # Size name [string]
        size_name_txt = wx.StaticText(self, -1, 'Size Name : ')  
        self.size_name_tcl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH*5, 20),
                                          style=0) 
        self.size_name_sizer.AddMany([(size_name_txt, 0, wx.LEFT|wx.RIGHT, 10),
                                       (self.size_name_tcl, 0, wx.EXPAND)])
        
    def _layout_size(self):
        """
        Do the  layout for aperture size related widgets
        """
        #Aperture size [Vector]
        aperture_size_txt = wx.StaticText(self, -1, 'Size:') 
        x_aperture_size_txt = wx.StaticText(self, -1, 'x = ')  
        self.x_aperture_size_tcl = wx.TextCtrl(self, -1, 
                                               size=(_BOX_WIDTH,20), style=0) 
        y_aperture_size_txt = wx.StaticText(self, -1, 'y = ')  
        self.y_aperture_size_tcl = wx.TextCtrl(self, -1,
                                                size=(_BOX_WIDTH,20), style=0) 
        z_aperture_size_txt = wx.StaticText(self, -1, 'z = ')  
        self.z_aperture_size_tcl = wx.TextCtrl(self, -1,
                                                size=(_BOX_WIDTH,20), style=0)  
        aperture_size_unit_txt = wx.StaticText(self, -1, 'Unit: ') 
        self.aperture_size_unit_tcl = wx.TextCtrl(self, -1, 
                                                size=(_BOX_WIDTH,20), style=0)  
        self.aperture_size_sizer.AddMany([(aperture_size_txt,
                                         0, wx.LEFT|wx.RIGHT, 10),
                                     (x_aperture_size_txt, 0, wx.LEFT, 17),
                                (self.x_aperture_size_tcl, 0, wx.RIGHT, 10),
                                     (y_aperture_size_txt, 0, wx.EXPAND),
                                (self.y_aperture_size_tcl, 0, wx.RIGHT, 10),
                                     (z_aperture_size_txt, 0, wx.EXPAND),
                                (self.z_aperture_size_tcl, 0, wx.RIGHT, 10),
                                     (aperture_size_unit_txt, 0, wx.EXPAND),
                            (self.aperture_size_unit_tcl, 0, wx.RIGHT, 10)])
        
    def _layout_button(self):  
        """
        Do the layout for the button widgets
        """ 
        self.bt_apply = wx.Button(self, -1,'Apply')
        self.bt_apply.Bind(wx.EVT_BUTTON, self.on_click_apply)
        self.bt_apply.SetToolTipString("Apply current changes to aperture.")
        self.bt_cancel = wx.Button(self, -1,'Cancel')
        self.bt_cancel.SetToolTipString("Cancel current changes.")
        self.bt_cancel.Bind(wx.EVT_BUTTON, self.on_click_cancel)
        self.bt_close = wx.Button(self, wx.ID_CANCEL,'Close')
        self.bt_close.SetToolTipString("Close window.")
        self.button_sizer.AddMany([(self.bt_apply, 0, wx.LEFT, 200),
                                   (self.bt_cancel, 0, wx.LEFT, 10),
                                   (self.bt_close, 0, wx.LEFT, 10)])
        
    def _do_layout(self ):#, data=None):
        """
        Draw the current panel
        """
        self._define_structure()
        self._layout_name()
        self._layout_type()
        self._layout_distance()
        self._layout_size_name()
        self._layout_size()
        self._layout_button()
        self.boxsizer_aperture.AddMany([(self.name_sizer, 0,
                                          wx.EXPAND|wx.TOP|wx.BOTTOM, 5),
                                   (self.type_sizer, 0,
                                     wx.EXPAND|wx.TOP|wx.BOTTOM, 5),
                                   (self.distance_sizer, 0,
                                     wx.EXPAND|wx.TOP|wx.BOTTOM, 5),
                                   (self.size_name_sizer, 0,
                                    wx.EXPAND|wx.TOP|wx.BOTTOM, 5),
                                   (self.aperture_size_sizer, 0,
                                    wx.EXPAND|wx.TOP|wx.BOTTOM, 5)])
        self.main_sizer.AddMany([(self.boxsizer_aperture, 0, wx.ALL, 10),
                                  (self.button_sizer, 0,
                                    wx.EXPAND|wx.TOP|wx.BOTTOM, 5)])
        self.SetSizer(self.main_sizer)
        self.SetAutoLayout(True)
    
    def set_manager(self, manager):
        """    
        Set manager of this window
        """
        self.manager = manager
        
    def reset_aperture(self):
        """
        put the default value of the detector back to the current aperture
        """
        self._aperture.name = self._reset_aperture.name
        self._aperture.type = self._reset_aperture.type
        self._aperture.size_name = self._reset_aperture.size_name
        self._aperture.size.x = self._reset_aperture.size.x
        self._aperture.size.y = self._reset_aperture.size.y
        self._aperture.size.z = self._reset_aperture.size.z
        self._aperture.size_unit = self._reset_aperture.size_unit
        self._aperture.distance = self._reset_aperture.distance
        self._aperture.distance_unit = self._reset_aperture.distance_unit
        
    def set_values(self):
        """
        take the aperture values of the current data and display them
        through the panel
        """
        aperture = self._aperture
        #Name
        self.aperture_name_tcl.SetValue(str(aperture.name))
        #Type
        self.type_tcl.SetValue(str(aperture.type))
        #distance
        self.distance_tcl.SetValue(str(aperture.distance))
        #distance unit
        self.distance_unit_tcl.SetValue(str(aperture.distance_unit))
        #Size name 
        self.size_name_tcl.SetValue(str(aperture.size_name))
        #Aperture size as a vector
        x, y, z = aperture.size.x, aperture.size.y, aperture.size.z
        self.x_aperture_size_tcl.SetValue(str(x))  
        self.y_aperture_size_tcl.SetValue(str(y)) 
        self.z_aperture_size_tcl.SetValue(str(z))  
        self.aperture_size_unit_tcl.SetValue(str(aperture.size_unit))
    
    def get_aperture(self):
        """
        return the current aperture
        """
        return self._aperture
    
    def get_notes(self):
        """
        return notes
        """
        return self._notes
    
    def on_change_name(self):
        """
        Change name
        """
        #Change the name of the aperture
        name = self.aperture_name_tcl.GetValue().lstrip().rstrip()
        if name == "":
            name = str(None)
        if self._aperture.name != name:
            self._notes += "Change sample 's "
            self._notes += "name from %s to %s \n"% (self._aperture.name, name)
            self._aperture.name = name
            
    def on_change_type(self):
        """
        Change aperture type
        """
        #Change type 
        type = self.type_tcl.GetValue().lstrip().rstrip()
        self._aperture.type = type
        self._notes += " Change type from"
        self._notes += " %s to %s \n"% (self._aperture.type, type)
        
    def on_change_distance(self):
        """
        Change distance of the aperture
        """
        #Change distance
        distance = self.distance_tcl.GetValue().lstrip().rstrip()
        if distance == "" or distance == str(None):
            distance = None
            self._aperture.distance = distance
        else:
            if check_float(self.distance_tcl):
                if self._aperture.distance != float(distance):
                    self._notes += "Change distance from "
                    self._notes += "%s to %s \n"% (self._aperture.distance, 
                                                  distance)
                    self._aperture.distance  = float(distance)
            else:
                self._notes += "Error: Expected a float for distance  "
                self._notes += "won't changes distance from "
                self._notes += "%s to %s"% (self._aperture.distance, distance)
        #change the distance unit
        unit = self.distance_unit_tcl.GetValue().lstrip().rstrip()
        if self._aperture.distance_unit != unit:
            self._notes += " Change distance 's unit from "
            self._notes += "%s to %s"% (self._aperture.distance_unit, unit)
        
    def on_change_size_name(self):
        """
        Change the size's name
        """
        #Change size name
        size_name = self.size_name_tcl.GetValue().lstrip().rstrip()
        self._aperture.size_name = size_name
        self._notes += " Change size name from"
        self._notes += " %s to %s \n"% (self._aperture.size_name, size_name)
   
    def on_change_size(self):
        """
        Change aperture size
        """
        #Change x coordinate
        x_aperture_size = self.x_aperture_size_tcl.GetValue().lstrip().rstrip()
        if x_aperture_size == "" or x_aperture_size == str(None):
            x_aperture_size = None
        else:
            if check_float(self.x_aperture_size_tcl):
                if self._aperture.size.x != float(x_aperture_size) :
                    self._notes += "Change x of aperture size from "
                    self._notes += "%s to %s \n"% (self._aperture.size.x,
                                                   x_aperture_size)
                    self._aperture.aperture_size.x  = float(x_aperture_size)
            else:
                self._notes += "Error: Expected a"
                self._notes += " float for the aperture size 's x "
                self._notes += "won't changes x aperture size from "
                self._notes += "%s to %s"% (self._aperture.size.x, 
                                           x_aperture_size)
        #Change y coordinate
        y_aperture_size = self.y_aperture_size_tcl.GetValue().lstrip().rstrip()
        if y_aperture_size == "" or y_aperture_size == str(None):
            y_aperture_size = None
            self._aperture.size.y = y_aperture_size
        else:
            if check_float(self.y_aperture_size_tcl):
                if self._aperture.size.y != float(y_aperture_size):
                    self._notes += "Change y of aperture size from "
                    self._notes += "%s to %s \n"% (self._aperture.size.y,
                                                   y_aperture_size)
                    self._aperture.size.y  = float(y_aperture_size)
            else:
                self._notes += "Error: Expected a float for the"
                self._notes += " aperture size's y "
                self._notes += "won't changes y aperture size from "
                self._notes += "%s to %s"% (self._aperture.size.y,
                                            y_aperture_size)
        #Change z coordinate
        z_aperture_size = self.z_aperture_size_tcl.GetValue().lstrip().rstrip()
        if z_aperture_size == "" or z_aperture_size == str(None):
            z_aperture_size = None
            self._aperture.size.z = z_aperture_size
        else:
            if check_float(self.z_aperture_size_tcl):
                if self._aperture.size.z != float(z_aperture_size):
                    self._notes += "Change z of aperture size from "
                    self._notes += "%s to %s \n"% (self._aperture.size.z,
                                                   z_aperture_size)
                    self._aperture.size.z  = float(z_aperture_size)
            else:
                self._notes += "Error: Expected a float for the offset 's x "
                self._notes += "won't changes z aperture size from "
                self._notes += "%s to %s"% (self._aperture.size.z,
                                            z_aperture_size)
        #change the aperture center unit
        unit = self.aperture_size_unit_tcl.GetValue().lstrip().rstrip()
        if self._aperture.size_unit != unit:
            self._notes += " Change aperture size's unit from "
            self._notes += "%s to %s"% (self._aperture.size_unit, unit)
            self._aperture.size_unit = unit
                 
    def on_click_apply(self, event):
        """
        Apply user values to the aperture
        """
        self.on_change_name()
        self.on_change_type()
        self.on_change_distance()
        self.on_change_size_name()
        self.on_change_size()
        self.set_values()
        if self.manager is not None:
            self.manager.set_aperture(self._aperture)
        if event is not None:
            event.Skip()
            
    def on_click_cancel(self, event):
        """
        reset the current aperture to its initial values
        """
        self.reset_aperture()
        self.set_values()
        if self.manager is not None:
             self.manager.set_aperture(self._aperture)
        if event is not None:
            event.Skip()
 
if __name__ == "__main__":
   
    app  = wx.App()
    # Instantiate a loader 
    loader = Loader()
    # Load data 
    from sas.dataloader.data_info import Aperture
    ap = Aperture()
    dlg = ApertureDialog(aperture=ap)
    dlg.ShowModal()
    app.MainLoop()
 