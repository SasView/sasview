
import wx
import sys
from copy import deepcopy
from sas.guiframe.utils import check_float

_BOX_WIDTH = 60
if sys.platform.count("win32") > 0:
    _STATICBOX_WIDTH = 450
    PANEL_WIDTH = 500
    PANEL_HEIGHT = 430
    FONT_VARIANT = 0
else:
    _STATICBOX_WIDTH = 480
    PANEL_WIDTH = 550
    PANEL_HEIGHT = 430
    FONT_VARIANT = 1
    
class SampleDialog(wx.Dialog):
    def __init__(self, parent=None, manager=None, sample=None,
                 size=(PANEL_WIDTH, PANEL_HEIGHT),title='Sample Editor'):
       
        wx.Dialog.__init__(self, parent=parent, size=size, title=title)
        self.parent = parent
        self.manager = manager 
        self._sample = sample
        self._reset_sample = deepcopy(sample)
        self._notes = ""
        self._description = "Edit Sample"
        self._do_layout()
        self.set_values()
    
    def _define_structure(self):
        """
            define initial sizer 
        """
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.box_sample = wx.StaticBox(self, -1,str("Sample"))
        self.boxsizer_sample = wx.StaticBoxSizer(self.box_sample,
                                                    wx.VERTICAL)
        self.name_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.id_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.thickness_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.transmission_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.temperature_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.position_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.orientation_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.details_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.button_sizer = wx.BoxSizer(wx.HORIZONTAL)
       
    def _layout_name(self):
        """
            Do the layout for sample name related widgets
        """
        ## Short name for sample [string]
        sample_name_txt = wx.StaticText(self, -1, 'Sample Name : ')  
        self.sample_name_tcl = wx.TextCtrl(self, -1,
                                            size=(_BOX_WIDTH*5, 20), style=0) 
        self.name_sizer.AddMany([(sample_name_txt, 0, wx.LEFT|wx.RIGHT, 10),
                                       (self.sample_name_tcl, 0, wx.EXPAND)])
    def _layout_id(self):
        """
            Do the layout for id related widgets
        """
        ## ID [String]
        id_txt = wx.StaticText(self, -1, 'ID: ')  
        self.id_tcl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH, 20), style=0)
        self.id_sizer.AddMany([(id_txt, 0, wx.LEFT|wx.RIGHT, 10),
                                     (self.id_tcl, 0, wx.LEFT, 55)])
        
    def _layout_thickness(self):
        """
            Do the  layout for thickness related widgets
        """
        ## Thickness [float] [mm]
        thickness_txt = wx.StaticText(self, -1, 'Thickness:') 
        self.thickness_tcl = wx.TextCtrl(self, -1,
                                          size=(_BOX_WIDTH, 20),style=0)  
        thickness_unit_txt = wx.StaticText(self, -1, 'Unit: ') 
        self.thickness_unit_tcl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH, 20),
                                              style=0)  
        self.thickness_sizer.AddMany([(thickness_txt, 0, wx.LEFT|wx.RIGHT, 10),
                                     (self.thickness_tcl, 0, wx.LEFT, 25),
                            (thickness_unit_txt, 0, wx.LEFT|wx.RIGHT, 10),
                                     (self.thickness_unit_tcl, 0, wx.EXPAND)]) 
    def _layout_transmission(self):
        """
            Do the  layout for transmission related widgets
        """
        ## Transmission [float] [fraction]
        transmission = None
        transmission_txt = wx.StaticText(self, -1, 'Transmission:') 
        self.transmission_tcl = wx.TextCtrl(self, -1,
                                             size=(_BOX_WIDTH, 20),style=0)   
        self.transmission_sizer.AddMany([(transmission_txt,
                                         0, wx.LEFT|wx.RIGHT, 10),
                                     (self.transmission_tcl, 0, wx.LEFT, 12)]) 
        
    def _layout_temperature(self):
        """
            Do the  layout for temperature related widgets
        """
        ## Temperature [float] [C]
        temperature_txt = wx.StaticText(self, -1, 'Temperature:') 
        self.temperature_tcl = wx.TextCtrl(self, -1, 
                                           size=(_BOX_WIDTH, 20), style=0)   
        temperature_unit_txt = wx.StaticText(self, -1, 'Unit: ') 
        self.temperature_unit_tcl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH, 20),
                                                            style=0)  
        self.temperature_sizer.AddMany([(temperature_txt, 0,
                                          wx.LEFT|wx.RIGHT, 10),
                                     (self.temperature_tcl, 0, wx.LEFT, 10),
                                (temperature_unit_txt, 0, wx.LEFT|wx.RIGHT, 10),
                                     (self.temperature_unit_tcl, 0, wx.EXPAND)])  
    
    def _layout_position(self):
        """
            Do the  layout for position related widgets
        """
        ## Position [Vector] [mm]
        position_txt = wx.StaticText(self, -1, 'Position:') 
        x_position_txt = wx.StaticText(self, -1, 'x = ')  
        self.x_position_tcl = wx.TextCtrl(self, -1,
                                           size=(_BOX_WIDTH,20), style=0) 
        y_position_txt = wx.StaticText(self, -1, 'y = ')  
        self.y_position_tcl = wx.TextCtrl(self, -1,
                                           size=(_BOX_WIDTH,20), style=0) 
        z_position_txt = wx.StaticText(self, -1, 'z = ')  
        self.z_position_tcl = wx.TextCtrl(self, -1,
                                           size=(_BOX_WIDTH,20), style=0)  
        position_unit_txt = wx.StaticText(self, -1, 'Unit: ') 
        self.position_unit_tcl = wx.TextCtrl(self, -1, 
                                             size=(_BOX_WIDTH,20), style=0)  
        self.position_sizer.AddMany([(position_txt, 0, wx.LEFT|wx.RIGHT, 10),
                                     (x_position_txt, 0, wx.LEFT, 14),
                                     (self.x_position_tcl, 0, wx.RIGHT, 10),
                                     (y_position_txt, 0, wx.EXPAND),
                                     (self.y_position_tcl, 0, wx.RIGHT, 10),
                                     (z_position_txt, 0, wx.EXPAND),
                                     (self.z_position_tcl, 0, wx.RIGHT, 10),
                                     (position_unit_txt, 0, wx.EXPAND),
                                     (self.position_unit_tcl, 0, wx.RIGHT, 10)])
    def _layout_orientation(self):
        """
            Do the  layout for orientation related widgets
        """
        ## Orientation [Vector] [degrees]
        orientation_txt = wx.StaticText(self, -1, 'Orientation:') 
        x_orientation_txt = wx.StaticText(self, -1, 'x = ')  
        self.x_orientation_tcl = wx.TextCtrl(self, -1,
                                              size=(_BOX_WIDTH,20), style=0) 
        y_orientation_txt = wx.StaticText(self, -1, 'y = ')  
        self.y_orientation_tcl = wx.TextCtrl(self, -1,
                                              size=(_BOX_WIDTH,20), style=0) 
        z_orientation_txt = wx.StaticText(self, -1, 'z = ')  
        self.z_orientation_tcl = wx.TextCtrl(self, -1,
                                              size=(_BOX_WIDTH,20), style=0)  
        orientation_unit_txt = wx.StaticText(self, -1, 'Unit: ') 
        self.orientation_unit_tcl = wx.TextCtrl(self, -1,
                                                 size=(_BOX_WIDTH,20), style=0)  
        self.orientation_sizer.AddMany([(orientation_txt, 0,
                                          wx.LEFT|wx.RIGHT, 10),
                                     (x_orientation_txt, 0, wx.LEFT, 0),
                                     (self.x_orientation_tcl, 0, wx.RIGHT, 10),
                                     (y_orientation_txt, 0, wx.EXPAND),
                                     (self.y_orientation_tcl, 0, wx.RIGHT, 10),
                                     (z_orientation_txt, 0, wx.EXPAND),
                                     (self.z_orientation_tcl, 0, wx.RIGHT, 10),
                                     (orientation_unit_txt, 0, wx.EXPAND),
                            (self.orientation_unit_tcl, 0, wx.RIGHT, 10)])
        
    def _layout_details(self):
        """
            Do the layout for beam size name related widgets
        """
        ## Details
        details = None
        details_txt = wx.StaticText(self, -1, 'Details: ')  
        self.details_tcl = wx.TextCtrl(self, -1,size=(_BOX_WIDTH*5,_BOX_WIDTH),
                                       style=wx.TE_MULTILINE | wx.HSCROLL)
        self.details_sizer.AddMany([(details_txt, 0, wx.LEFT|wx.RIGHT, 10),
                                       (self.details_tcl, 0, wx.EXPAND)])
    
    def _layout_button(self):  
        """
            Do the layout for the button widgets
        """ 
        self.bt_apply = wx.Button(self, -1,'Apply')
        self.bt_apply.Bind(wx.EVT_BUTTON, self.on_click_apply)
        self.bt_apply.SetToolTipString("Apply current changes to the sample.")
        self.bt_cancel = wx.Button(self, -1,'Cancel')
        self.bt_cancel.SetToolTipString("Cancel current changes.")
        self.bt_cancel.Bind(wx.EVT_BUTTON, self.on_click_cancel)
        self.bt_close = wx.Button(self, wx.ID_CANCEL,'Close')
        self.bt_close.SetToolTipString("Close window.")
        self.button_sizer.AddMany([(self.bt_apply, 0, wx.LEFT, 200),
                                   (self.bt_cancel, 0, wx.LEFT, 10),
                                   (self.bt_close, 0, wx.LEFT, 10)])
        
    def _do_layout(self, data=None):
        """
             Draw the current panel
        """
        self._define_structure()
        self._layout_name()
        self._layout_id()
        self._layout_thickness()
        self._layout_transmission()
        self._layout_temperature()
        self._layout_position()
        self._layout_orientation()
        self._layout_details()
        self._layout_button()
        self.boxsizer_sample.AddMany([(self.name_sizer, 0,
                                          wx.EXPAND|wx.TOP|wx.BOTTOM, 5),
                                   (self.id_sizer, 0,
                                     wx.EXPAND|wx.TOP|wx.BOTTOM, 5),
                                   (self.thickness_sizer, 0,
                                     wx.EXPAND|wx.TOP|wx.BOTTOM, 5),
                                   (self.transmission_sizer, 0,
                                    wx.EXPAND|wx.TOP|wx.BOTTOM, 5),
                                   (self.temperature_sizer, 0,
                                    wx.EXPAND|wx.TOP|wx.BOTTOM, 5),
                                   (self.position_sizer, 0,
                                    wx.EXPAND|wx.TOP|wx.BOTTOM, 5),
                                    (self.orientation_sizer, 0,
                                    wx.EXPAND|wx.TOP|wx.BOTTOM, 5),
                                   (self.details_sizer, 0,
                                     wx.EXPAND|wx.TOP|wx.BOTTOM, 5)])
        self.main_sizer.AddMany([(self.boxsizer_sample, 0, wx.ALL, 10),
                                  (self.button_sizer, 0,
                                    wx.EXPAND|wx.TOP|wx.BOTTOM, 5)])
        
        self.SetSizer(self.main_sizer)
        self.SetAutoLayout(True)
    
    def reset_sample(self):
        """
            Put initial values of the sample back to the current sample
        """
        self._sample.name = self._reset_sample.name
        self._sample.ID = self._reset_sample.ID
        self._sample.thickness = self._reset_sample.thickness
        self._sample.thickness_unit = self._reset_sample.thickness_unit
        self._sample.transmission = self._reset_sample.transmission
        self._sample.temperature = self._reset_sample.temperature
        self._sample.temperature_unit = self._reset_sample.temperature_unit
       
        self._sample.position.x = self._reset_sample.position.x
        self._sample.position.y = self._reset_sample.position.y
        self._sample.position.z = self._reset_sample.position.x
        self._sample.position_unit = self._reset_sample.position_unit
        
        self._sample.orientation.x = self._reset_sample.orientation.x
        self._sample.orientation.y = self._reset_sample.orientation.y
        self._sample.orientation.z = self._reset_sample.orientation.x
        self._sample.orientation_unit = self._reset_sample.orientation_unit
       
        self._sample.details = self._reset_sample.details
        
    def set_manager(self, manager):
        """    
            Set manager of this window
        """
        self.manager = manager
    
    def set_values(self):
        """
            take the sample values of the current data and display them
            through the panel
        """
        sample = self._sample
        #Name
        self.sample_name_tcl.SetValue(str(sample.name))
        #id 
        self.id_tcl.SetValue(str(sample.ID))
        #thickness
        self.thickness_tcl.SetValue(str(sample.thickness))
        self.thickness_unit_tcl.SetValue(str(sample.thickness_unit))
        #transmission
        self.transmission_tcl.SetValue(str(sample.transmission))
        #temperature
        self.temperature_tcl.SetValue(str(sample.temperature))
        self.temperature_unit_tcl.SetValue(str(sample.temperature_unit))
        #position
        x, y, z = sample.position.x, sample.position.y , sample.position.z
        self.x_position_tcl.SetValue(str(x))  
        self.y_position_tcl.SetValue(str(y)) 
        self.z_position_tcl.SetValue(str(z))  
        self.position_unit_tcl.SetValue(str(sample.position_unit))
        #orientation
        x, y = sample.orientation.x, sample.orientation.y 
        z = sample.orientation.z
        self.x_orientation_tcl.SetValue(str(x))  
        self.y_orientation_tcl.SetValue(str(y)) 
        self.z_orientation_tcl.SetValue(str(z))  
        self.orientation_unit_tcl.SetValue(str(sample.orientation_unit))
        
        self.set_details(sample)
        
    def set_details(self, sample):
        """
            print details on the current sample
        """
        #detail
        msg = ''
        if sample.details is not None or sample.details:
            for item in sample.details:
                msg += "      %s\n" % item
        self.details_tcl.SetValue(str(msg))
        
    def get_sample(self):
        """
            return the current sample
        """
        return self._sample
    
    def get_notes(self):
        """
            return notes
        """
        return self._notes
    
    def on_change_name(self):
        """
            Change name
        """
        #Change the name of the sample
        name = self.sample_name_tcl.GetValue().lstrip().rstrip()
        if name == "" or name == str(None):
            name = None
        if self._sample.name != name:
            self._notes += "Change sample 's "
            self._notes += "name from %s to %s \n"%(self._sample.name, name)
            self._sample.name = name
            
    def on_change_id(self):
        """
            Change id of the sample 
        """
        #Change id
        id = self.id_tcl.GetValue().lstrip().rstrip()
        self._sample.ID = id
        self._notes += " Change ID from"
        self._notes += " %s to %s \n"%(self._sample.ID, id)
        
    def on_change_thickness(self):
        """
            Change thickness
        """
       #Change thickness
        thickness = self.thickness_tcl.GetValue().lstrip().rstrip()
        self._sample.thickness = thickness
        self._notes += " Change thickness from"
        self._notes += " %s to %s \n"%(self._sample.thickness, thickness)
        
    def on_change_transmission(self):
        """
            Change transmission
        """
        #Change transmission
        transmission = self.transmission_tcl.GetValue().lstrip().rstrip()
        if self._sample.transmission != transmission:
            self._notes += " Change transmission from"
            self._notes += " %s to %s \n" % (self._sample.transmission,
                                              transmission)
            self._sample.transmission = transmission
            
    def on_change_temperature(self):
        """
            Change temperature
        """
        #Change temperature
        temperature = self.temperature_tcl.GetValue().lstrip().rstrip()
        self._sample.temperature = temperature
        self._notes += " Change temperature from"
        self._notes += " %s to %s \n"%(self._sample.temperature, temperature)
        #change temperature unit
        unit = self.temperature_unit_tcl.GetValue().lstrip().rstrip()
        if self._sample.temperature_unit != unit:
            self._notes += " Change temperature's unit from "
            self._notes += "%s to %s"%(self._sample.temperature_unit, unit)
            self._sample.temperature_unit = unit
            
    def on_change_position(self):
        """
            Change position
        """
        #Change x coordinate
        x_position = self.x_position_tcl.GetValue().lstrip().rstrip()
        if x_position == "" or x_position == str(None):
            x_position = None
        else:
            if check_float(self.x_position_tcl):
                if self._sample.position.x != float(x_position) :
                    self._notes += "Change x of position from "
                    self._notes += "%s to %s \n" % (self._sample.position.x,
                                                     x_position)
                    self._sample.position.x  = float(x_position)
            else:
                self._notes += "Error: Expected a float for the position 's x "
                self._notes += "won't changes x position from "
                self._notes += "%s to %s"%(self._sample.position.x, x_position)
        #Change y coordinate
        y_position = self.y_position_tcl.GetValue().lstrip().rstrip()
        if y_position == "" or y_position == str(None):
            y_position = None
            self._sample.position.y = y_position
        else:
            if check_float(self.y_position_tcl):
                if self._sample.position.y != float(y_position):
                    self._notes += "Change y of position from "
                    self._notes += "%s to %s \n" % (self._sample.position.y, 
                                                    y_position)
                    self._sample.position.y  = float(y_position)
            else:
                self._notes += "Error: Expected a float for the beam size's y "
                self._notes += "won't changes y position from "
                self._notes += "%s to %s"%(self._sample.position.y, y_position)
        #Change z coordinate
        z_position = self.z_position_tcl.GetValue().lstrip().rstrip()
        if z_position == "" or z_position == str(None):
            z_position = None
            self._sample.position.z = z_position
        else:
            if check_float(self.z_position_tcl):
                if self._sample.position.z != float(z_position):
                    self._notes += "Change z of position from "
                    self._notes += "%s to %s \n" % (self._sample.position.z,
                                                    z_position)
                    self._sample.position.z  = float(z_position)
            else:
                self._notes += "Error: Expected a float for position's x "
                self._notes += "won't changes z position from "
                self._notes += "%s to %s"%(self._sample.position.z, z_position)
        #change the beam center unit
        unit = self.position_unit_tcl.GetValue().lstrip().rstrip()
        if self._sample.position_unit != unit:
            self._notes += " Change position's unit from "
            self._notes += "%s to %s"%(self._sample.position_unit, unit)
            
    def on_change_orientation(self):
        """
            Change orientation
        """
        #Change x coordinate
        x_orientation = self.x_orientation_tcl.GetValue().lstrip().rstrip()
        if x_orientation == "" or x_orientation == str(None):
            x_orientation = None
        else:
            if check_float(self.x_orientation_tcl):
                if self._sample.orientation.x != float(x_orientation) :
                    self._notes += "Change x of orientation from "
                    self._notes += "%s to %s \n"%(self._sample.orientation.x,
                                                   x_orientation)
                    self._sample.orientation.x  = float(x_orientation)
            else:
                self._notes += "Error: Expected a float for orientation 's x "
                self._notes += "won't changes x orientation from "
                self._notes += "%s to %s" % (self._sample.orientation.x,
                                              x_orientation)
        #Change y coordinate
        y_orientation = self.y_orientation_tcl.GetValue().lstrip().rstrip()
        if y_orientation == "" or y_orientation == str(None):
            y_orientation = None
            self._sample.orientation.y = y_orientation
        else:
            if check_float(self.y_orientation_tcl):
                if self._sample.orientation.y != float(y_orientation):
                    self._notes += "Change y of orientation from "
                    self._notes += "%s to %s \n" % (self._sample.orientation.y,
                                                     y_orientation)
                    self._sample.orientation.y  = float(y_orientation)
            else:
                self._notes += "Error: Expected a float for orientation's y "
                self._notes += "won't changes y orientation from "
                self._notes += "%s to %s" % (self._sample.orientation.y,
                                            y_orientation)
        #Change z coordinate
        z_orientation = self.z_orientation_tcl.GetValue().lstrip().rstrip()
        if z_orientation == "" or z_orientation == str(None):
            z_orientation = None
            self._sample.orientation.z = z_orientation
        else:
            if check_float(self.z_orientation_tcl):
                if self._sample.orientation.z != float(z_orientation):
                    self._notes += "Change z of orientation from "
                    self._notes += "%s to %s \n" % (self._sample.orientation.z,
                                                     z_orientation)
                    self._sample.orientation.z = float(z_orientation)
            else:
                self._notes += "Error: Expected a float for orientation 's x "
                self._notes += "won't changes z orientation from "
                self._notes += "%s to %s" % (self._sample.orientation.z,
                                              z_orientation)
        #change the beam center unit
        unit = self.orientation_unit_tcl.GetValue().lstrip().rstrip()
        if self._sample.orientation_unit != unit:
            self._notes += " Change orientation's unit from "
            self._notes += "%s to %s"%(self._sample.orientation_unit, unit)
            
    def on_change_details(self):
        """
            Change details
        """
        #Change details
        details = self.details_tcl.GetValue().lstrip().rstrip()
        msg = ""
        if self._sample.details is not None or self._sample.details:
            for item in self._sample.details:
                if item != details:
                    msg += "      %s\n" % item
                    self._notes += " Change details from"
                    self._notes += " %s to %s \n"%(msg, details)
                    self._sample.details.append(details)
  
    def on_click_apply(self, event):
        """
            Apply user values to the sample
        """
        self.on_change_name()
        self.on_change_id()
        self.on_change_thickness()
        self.on_change_transmission()
        self.on_change_temperature()
        self.on_change_position()
        self.on_change_orientation()
        self.on_change_details()
        self.set_details(self._sample)
        if self.manager is not None:
            self.manager.set_sample(self._sample)
        if event is not None:
            event.Skip()
            
    def on_click_cancel(self, event):
        """
            leave the sample as it is and close
        """
        self.reset_sample()
        self.set_values()
        if self.manager is not None:
             self.manager.set_sample(self._sample, self._notes)
        if event is not None:
            event.Skip()

if __name__ == "__main__":
    app = wx.App()
    from sas.dataloader.data_info import Sample
    sample = Sample()
    dlg = SampleDialog(sample=sample)
    dlg.ShowModal()
    app.MainLoop()
 