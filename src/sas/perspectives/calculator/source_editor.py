"""
"""
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
    
class SourceDialog(wx.Dialog):
    def __init__(self, parent=None, manager=None, source=None, *args, **kwds):
        kwds['title'] = "Source Editor"
        kwds['size'] = (PANEL_WIDTH, PANEL_HEIGHT)
        wx.Dialog.__init__(self, parent=parent, *args, **kwds)
        
        self.parent = parent
        self.manager = manager
        self._source = source
        self._reset_source = deepcopy(source)
        self._notes = ""
        self._description = "Edit source"
        self._do_layout()
        self.set_values()
   
    def _define_structure(self):
        """
            define initial sizer 
        """
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.box_source = wx.StaticBox(self, -1, str("source"))
        self.boxsizer_source = wx.StaticBoxSizer(self.box_source,
                                                    wx.VERTICAL)
        self.name_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.radiation_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.beam_shape_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.wavelength_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.wavelength_min_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.wavelength_max_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.wavelength_spread_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.beam_size_name_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.beam_size_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.button_sizer = wx.BoxSizer(wx.HORIZONTAL)
       
    def _layout_name(self):
        """
            Do the layout for sample name related widgets
        """
        # Sample name [string]
        sample_name_txt = wx.StaticText(self, -1, 'Sample Name : ')  
        self.sample_name_tcl = wx.TextCtrl(self, -1,
                                            size=(_BOX_WIDTH*5, 20), style=0) 
        self.name_sizer.AddMany([(sample_name_txt, 0, wx.LEFT|wx.RIGHT, 10),
                                       (self.sample_name_tcl, 0, wx.EXPAND)])
    def _layout_radiation(self):
        """
            Do the  layout for  radiation related widgets
        """
        #Radiation type [string]
        radiation_txt = wx.StaticText(self, -1, 'Radiation: ')  
        self.radiation_tcl = wx.TextCtrl(self, -1, 
                                         size=(_BOX_WIDTH, 20), style=0)
        self.radiation_sizer.AddMany([(radiation_txt, 0, wx.LEFT|wx.RIGHT, 10),
                                     (self.radiation_tcl, 0, wx.LEFT, 20)])
        
    def _layout_beam_shape(self):
        """
            Do the  layout for beam shape related widgets
        """
        #Beam shape [string]
        beam_shape_txt = wx.StaticText(self, -1, 'Beam shape:') 
        self.beam_shape_tcl = wx.TextCtrl(self, -1,
                                           size=(_BOX_WIDTH, 20), style=0)  
        self.beam_shape_sizer.AddMany([(beam_shape_txt, 0,
                                         wx.LEFT|wx.RIGHT, 10),
                                     (self.beam_shape_tcl, 0, wx.LEFT, 10)])
        
    def _layout_wavelength(self):
        """
            Do the  layout for wavelength related widgets
        """
        #Wavelength [float] [Angstrom]
        wavelength_txt = wx.StaticText(self, -1, 'wavelength:') 
        self.wavelength_tcl = wx.TextCtrl(self, -1,
                                           size=(_BOX_WIDTH, 20), style=0)   
        wavelength_unit_txt = wx.StaticText(self, -1, 'Unit: ') 
        self.wavelength_unit_tcl = wx.TextCtrl(self, -1,
                                                size=(_BOX_WIDTH, 20),style=0)  
        self.wavelength_sizer.AddMany([(wavelength_txt,
                                         0, wx.LEFT|wx.RIGHT, 10),
                                     (self.wavelength_tcl, 0, wx.LEFT, 12),
                            (wavelength_unit_txt, 0, wx.LEFT|wx.RIGHT, 10),
                                     (self.wavelength_unit_tcl, 0, wx.EXPAND)]) 
        
    def _layout_wavelength_min(self):
        """
            Do the  layout for wavelength min related widgets
        """
        #Minimum wavelength [float] [Angstrom]
        wavelength_min_txt = wx.StaticText(self, -1, 'Wavelength min:') 
        self.wavelength_min_tcl = wx.TextCtrl(self, -1,
                                               size=(_BOX_WIDTH, 20), style=0)   
        wavelength_min_unit_txt = wx.StaticText(self, -1, 'Unit: ') 
        self.wavelength_min_unit_tcl = wx.TextCtrl(self, -1,
                                             size=(_BOX_WIDTH, 20), style=0)  
        self.wavelength_min_sizer.AddMany([(wavelength_min_txt, 
                                            0, wx.LEFT|wx.RIGHT, 10),
                                     (self.wavelength_min_tcl, 0, wx.LEFT, 10),
                            (wavelength_min_unit_txt, 0, wx.LEFT|wx.RIGHT, 10),
                            (self.wavelength_min_unit_tcl, 0, wx.EXPAND)])  
    
    def _layout_wavelength_max(self):
        """
            Do the  layout for wavelength max related widgets
        """
        #Maximum wavelength [float] [Angstrom]
        wavelength_max_txt = wx.StaticText(self, -1, 'Wavelength max:') 
        self.wavelength_max_tcl = wx.TextCtrl(self, -1,
                                             size=(_BOX_WIDTH, 20), style=0)   
        wavelength_max_unit_txt = wx.StaticText(self, -1, 'Unit: ') 
        self.wavelength_max_unit_tcl = wx.TextCtrl(self, -1,
                                             size=(_BOX_WIDTH, 20), style=0)  
        self.wavelength_max_sizer.AddMany([(wavelength_max_txt, 0,
                                             wx.LEFT|wx.RIGHT, 10),
                                     (self.wavelength_max_tcl, 0, wx.LEFT, 7),
                            (wavelength_max_unit_txt, 0, wx.LEFT|wx.RIGHT, 10),
                            (self.wavelength_max_unit_tcl, 0, wx.EXPAND)]) 
    
    def _layout_wavelength_spread(self):
        """
            Do the  layout for wavelength spread related widgets
        """
        ## Wavelength spread [float] [Angstrom]
        wavelength_spread = None
        wavelength_spread_unit = 'percent'
        wavelength_spread_txt = wx.StaticText(self, -1, 'Wavelength spread:') 
        self.wavelength_spread_tcl = wx.TextCtrl(self, -1,
                                             size=(_BOX_WIDTH, 20), style=0)   
        wavelength_spread_unit_txt = wx.StaticText(self, -1, 'Unit: ') 
        self.wavelength_spread_unit_tcl = wx.TextCtrl(self, -1,
                                             size=(_BOX_WIDTH, 20), style=0)  
        self.wavelength_spread_sizer.AddMany([(wavelength_spread_txt,
                                                0, wx.LEFT, 10),
                                (self.wavelength_spread_tcl, 0, wx.LEFT, 5),
                        (wavelength_spread_unit_txt, 0, wx.LEFT|wx.RIGHT, 10),
                        (self.wavelength_spread_unit_tcl, 0, wx.EXPAND)]) 
    def _layout_beam_size_name(self):
        """
            Do the layout for beam size name related widgets
        """
        # Beam size name [string]
        beam_size_name_txt = wx.StaticText(self, -1, 'Beam size name : ')  
        self.beam_size_name_tcl = wx.TextCtrl(self, -1,
                                               size=(_BOX_WIDTH*5, 20), style=0) 
        self.beam_size_name_sizer.AddMany([(beam_size_name_txt,
                                             0, wx.LEFT|wx.RIGHT, 10),
                                       (self.beam_size_name_tcl, 0, wx.EXPAND)])
        
    def _layout_beam_size(self):
        """
            Do the  layout for beam size related widgets
        """
        ## Beam size [Vector] [mm]
        beam_size = None
        beam_size_unit = 'mm'
       
        beam_size_txt = wx.StaticText(self, -1, 'Beam size:') 
        x_beam_size_txt = wx.StaticText(self, -1, 'x = ')  
        self.x_beam_size_tcl = wx.TextCtrl(self, -1,
                                            size=(_BOX_WIDTH, 20), style=0) 
        y_beam_size_txt = wx.StaticText(self, -1, 'y = ')  
        self.y_beam_size_tcl = wx.TextCtrl(self, -1,
                                            size=(_BOX_WIDTH, 20), style=0) 
        z_beam_size_txt = wx.StaticText(self, -1, 'z = ')  
        self.z_beam_size_tcl = wx.TextCtrl(self, -1, 
                                           size=(_BOX_WIDTH, 20), style=0)  
        beam_size_unit_txt = wx.StaticText(self, -1, 'Unit: ') 
        self.beam_size_unit_tcl = wx.TextCtrl(self, -1, 
                                              size=(_BOX_WIDTH, 20), style=0)  
        self.beam_size_sizer.AddMany([(beam_size_txt, 0, wx.LEFT|wx.RIGHT, 10),
                                     (x_beam_size_txt, 0, wx.LEFT, 17),
                                     (self.x_beam_size_tcl, 0, wx.RIGHT, 10),
                                     (y_beam_size_txt, 0, wx.EXPAND),
                                     (self.y_beam_size_tcl, 0, wx.RIGHT, 10),
                                     (z_beam_size_txt, 0, wx.EXPAND),
                                     (self.z_beam_size_tcl, 0, wx.RIGHT, 10),
                                     (beam_size_unit_txt, 0, wx.EXPAND),
                                    (self.beam_size_unit_tcl, 0, wx.RIGHT, 10)])
        
    def _layout_button(self):  
        """
            Do the layout for the button widgets
        """ 
        self.bt_apply = wx.Button(self, -1,'Apply')
        self.bt_apply.Bind(wx.EVT_BUTTON, self.on_click_apply)
        self.bt_apply.SetToolTipString("Apply current changes to the source.")
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
        self._layout_radiation()
        self._layout_beam_shape()
        self._layout_wavelength()
        self._layout_wavelength_min()
        self._layout_wavelength_max()
        self._layout_wavelength_spread()
        self._layout_beam_size_name()
        self._layout_beam_size()
        self._layout_button()
     
        self.boxsizer_source.AddMany([(self.name_sizer, 0,
                                          wx.EXPAND|wx.TOP|wx.BOTTOM, 5),
                                   (self.radiation_sizer, 0,
                                     wx.EXPAND|wx.TOP|wx.BOTTOM, 5),
                                   (self.beam_shape_sizer, 0,
                                     wx.EXPAND|wx.TOP|wx.BOTTOM, 5),
                                   (self.wavelength_sizer, 0,
                                    wx.EXPAND|wx.TOP|wx.BOTTOM, 5),
                                   (self.wavelength_min_sizer, 0,
                                    wx.EXPAND|wx.TOP|wx.BOTTOM, 5),
                                   (self.wavelength_max_sizer, 0,
                                    wx.EXPAND|wx.TOP|wx.BOTTOM, 5),
                                    (self.wavelength_spread_sizer, 0,
                                    wx.EXPAND|wx.TOP|wx.BOTTOM, 5),
                                   (self.beam_size_name_sizer, 0,
                                     wx.EXPAND|wx.TOP|wx.BOTTOM, 5),
                                    (self.beam_size_sizer, 0,
                                     wx.EXPAND|wx.TOP|wx.BOTTOM, 5)])
        self.main_sizer.AddMany([(self.boxsizer_source, 0, wx.ALL, 10),
                                  (self.button_sizer, 0,
                                    wx.EXPAND|wx.TOP|wx.BOTTOM, 5)])
        
        self.SetSizer(self.main_sizer)
        self.SetAutoLayout(True)
    
    def set_manager(self, manager):
        """    
            Set manager of this window
        """
        self.manager = manager
        
    def reset_source(self):
        """
            put back initial values of the source
        """
        self._source.name = self._reset_source.name
        self._source.radiation = self._reset_source.radiation
        self._source.beam_size_name = self._reset_source.beam_size_name
       
        self._source.beam_size.x =  self._reset_source.beam_size.x
        self._source.beam_size.y =  self._reset_source.beam_size.y
        self._source.beam_size.z =  self._reset_source.beam_size.z
        self._source.beam_size_unit = self._reset_source.beam_size_unit
        
        self._source.beam_shape = self._reset_source.beam_shape
        self._source.wavelength = self._reset_source.wavelength
        self._source.wavelength_unit = self._reset_source.wavelength_unit
        ## Minimum wavelength [float] [Angstrom]
        self._source.wavelength_min = self._reset_source.wavelength_min
        self._source.wavelength_min_unit = self._reset_source.wavelength_min_unit
        
        self._source.wavelength_max = self._reset_source.wavelength_max
        self._source.wavelength_max_unit = self._reset_source.wavelength_max_unit
        
        self._source.wavelength_spread = self._reset_source.wavelength_spread
        self._source.wavelength_spread_unit = self._reset_source.wavelength_spread_unit
       
    def set_values(self):
        """
            take the source values of the current data and display them
            through the panel
        """
        source = self._source
        #Name
        self.sample_name_tcl.SetValue(str(source.name))
        #Radiation
        self.radiation_tcl.SetValue(str(source.radiation))
        #Beam shape 
        self.beam_shape_tcl.SetValue(str(source.beam_shape))
        #Wavelength
        self.wavelength_tcl.SetValue(str(source.wavelength))
        self.wavelength_unit_tcl.SetValue(str(source.wavelength_unit))
        #Wavelength min
        self.wavelength_min_tcl.SetValue(str(source.wavelength_min))
        self.wavelength_min_unit_tcl.SetValue(str(source.wavelength_min_unit))
        #Wavelength max
        self.wavelength_max_tcl.SetValue(str(source.wavelength_max))
        self.wavelength_max_unit_tcl.SetValue(str(source.wavelength_max_unit))
        #Wavelength spread
        self.wavelength_spread_tcl.SetValue(str(source.wavelength_spread))
        self.wavelength_spread_unit_tcl.SetValue(str(source.wavelength_spread_unit))
        #Beam size 
        self.beam_size_name_tcl.SetValue(str(source.beam_size_name))
        x, y, z = source.beam_size.x, source.beam_size.y , source.beam_size.z
        self.x_beam_size_tcl.SetValue(str(x))  
        self.y_beam_size_tcl.SetValue(str(y)) 
        self.z_beam_size_tcl.SetValue(str(z))  
        self.beam_size_unit_tcl.SetValue(str(source.beam_size_unit))
    
    def get_source(self):
        """
            return the current source
        """
        return self._source
    
    def get_notes(self):
        """
            return notes
        """
        return self._notes
    
    def on_change_name(self):
        """
            Change name
        """
        #Change the name of the source
        name = self.sample_name_tcl.GetValue().lstrip().rstrip()
        if name == "" or name == str(None):
            name = None
        if self._source.name != name:
            self._notes += "Change sample 's "
            self._notes += "name from %s to %s \n"%(self._source.name, name)
            self._source.name = name
            
    def on_change_radiation(self):
        """
            Change radiation of the sample 
        """
        #Change radiation
        radiation = self.radiation_tcl.GetValue().lstrip().rstrip()
        self._source.radiation = radiation
        self._notes += " Change radiation from"
        self._notes += " %s to %s \n"%(self._source.radiation, radiation)
        
    def on_change_beam_shape(self):
        """
            Change beams shape
        """
       #Change beam shape 
        beam_shape = self.beam_shape_tcl.GetValue().lstrip().rstrip()
        self._source.beam_shape = beam_shape
        self._notes += " Change beam shape from"
        self._notes += " %s to %s \n"%(self._source.beam_shape, beam_shape)
        
    def on_change_wavelength(self):
        """
            Change the wavelength
        """
        #Change wavelength  
        wavelength = self.wavelength_tcl.GetValue().lstrip().rstrip()
        self._source.wavelength = wavelength
        self._notes += " Change wavelength from"
        self._notes += " %s to %s \n"%(self._source.wavelength, wavelength)
        #change the wavelength  unit
        unit = self.wavelength_unit_tcl.GetValue().lstrip().rstrip()
        if self._source.wavelength_unit != unit:
            self._notes += " Change wavelength's unit from "
            self._notes += "%s to %s"%(self._source.wavelength_unit, unit)
            
    def on_change_wavelength_min(self):
        """
            Change the wavelength minimum
        """
        #Change wavelength min
        wavelength_min = self.wavelength_min_tcl.GetValue().lstrip().rstrip()
        self._source.wavelength_min = wavelength_min
        self._notes += " Change wavelength  min from"
        self._notes += " %s to %s \n" % (self._source.wavelength_min,
                                          wavelength_min)
        #change the wavelength min unit
        unit = self.wavelength_min_unit_tcl.GetValue().lstrip().rstrip()
        if self._source.wavelength_min_unit != unit:
            self._notes += " Change wavelength min's unit from "
            self._notes += "%s to %s" % (self._source.wavelength_min_unit, unit)
            
    def on_change_wavelength_max(self):
        """
            Change the wavelength maximum
        """
        #Change wavelength max
        wavelength_max = self.wavelength_max_tcl.GetValue().lstrip().rstrip()
        self._source.wavelength_max = wavelength_max
        self._notes += " Change wavelength  max from"
        self._notes += " %s to %s \n" % (self._source.wavelength_max,
                                        wavelength_max)
        #change the wavelength max unit
        unit = self.wavelength_max_unit_tcl.GetValue().lstrip().rstrip()
        if self._source.wavelength_max_unit != unit:
            self._notes += " Change wavelength max's unit from "
            self._notes += "%s to %s"%(self._source.wavelength_max_unit, unit)
            
    def on_change_wavelength_spread(self):
        """
            Change the wavelength spread
        """
        #Change wavelength spread
        wavelength_spread = self.wavelength_spread_tcl.GetValue().lstrip().rstrip()
        self._notes += " Change wavelength  spread from"
        self._notes += " %s to %s \n" % (self._source.wavelength_spread, 
                                         wavelength_spread)
        self._source.wavelength_spread = wavelength_spread
        #change the wavelength spread unit
        unit = self.wavelength_spread_unit_tcl.GetValue().lstrip().rstrip()
        if self._source.wavelength_spread_unit != unit:
            self._notes += " Change wavelength spread's unit from "
            self._notes += "%s to %s" % (self._source.wavelength_spread_unit, 
                                         unit)
            self._source.wavelength_spread_unit = unit
    
    def on_change_beam_size_name(self):
        """
            Change beam size name
        """
        #Change beam size name
        name = self.beam_size_name_tcl.GetValue().lstrip().rstrip()
        if name == "" or name == str(None):
            name = None
        if self._source.beam_size_name != name:
            self._notes += "Change beam size  's "
            self._notes += "name from %s to %s \n" % (self._source.beam_size_name,
                                                       name)
            self._source.name = name
            
    def on_change_beam_size(self):
        """
            Change beam size
        """
        #Change x coordinate
        x_beam_size = self.x_beam_size_tcl.GetValue().lstrip().rstrip()
        if x_beam_size == "" or x_beam_size == str(None):
            x_beam_size = None
        else:
            if check_float(self.x_beam_size_tcl):
                if self._source.beam_size.x != float(x_beam_size) :
                    self._notes += "Change x of beam size from "
                    self._notes += "%s to %s \n" % (self._source.beam_size.x,
                                                     x_beam_size)
                    self._source.beam_size.x  = float(x_beam_size)
            else:
                self._notes += "Error: Expected a float for the beam size 's x "
                self._notes += "won't changes x beam size from "
                self._notes += "%s to %s" % (self._source.beam_size.x,
                                            x_beam_size)
        #Change y coordinate
        y_beam_size = self.y_beam_size_tcl.GetValue().lstrip().rstrip()
        if y_beam_size == "" or y_beam_size == str(None):
            y_beam_size = None
            self._source.beam_size.y = y_beam_size
        else:
            if check_float(self.y_beam_size_tcl):
                if self._source.beam_size.y != float(y_beam_size):
                    self._notes += "Change y of beam size from "
                    self._notes += "%s to %s \n" % (self._source.beam_size.y,
                                                     y_beam_size)
                    self._source.beam_size.y  = float(y_beam_size)
            else:
                self._notes += "Error: Expected a float for the beam size's y "
                self._notes += "won't changes y beam size from "
                self._notes += "%s to %s" % (self._source.beam_size.y,
                                              y_beam_size)
        #Change z coordinate
        z_beam_size = self.z_beam_size_tcl.GetValue().lstrip().rstrip()
        if z_beam_size == "" or z_beam_size == str(None):
            z_beam_size = None
            self._source.beam_size.z = z_beam_size
        else:
            if check_float(self.z_beam_size_tcl):
                if self._source.beam_size.z != float(z_beam_size):
                    self._notes += "Change z of beam size from "
                    self._notes += "%s to %s \n" % (self._source.beam_size.z,
                                                     z_beam_size)
                    self._source.beam_size.z  = float(z_beam_size)
            else:
                self._notes += "Error: Expected a float for the beam size 's z "
                self._notes += "won't changes z beam size from "
                self._notes += "%s to %s" % (self._source.beam_size.z,
                                              z_beam_size)
        #change the beam center unit
        unit = self.beam_size_unit_tcl.GetValue().lstrip().rstrip()
        if self._source.beam_size_unit != unit:
            self._notes += " Change beam size's unit from "
            self._notes += "%s to %s"%(self._source.beam_size_unit, unit)
            self._source.beam_size_unit = unit
                 
    def on_click_apply(self, event):
        """
        Apply user values to the source
        """
        self.on_change_name()
        self.on_change_radiation()
        self.on_change_beam_shape()
        self.on_change_wavelength()
        self.on_change_wavelength_min()
        self.on_change_wavelength_max()
        self.on_change_wavelength_spread()
        self.on_change_beam_size_name()
        self.on_change_beam_size()
        if self.manager is not None:
            self.manager.set_source(self._source, self._notes)
        if event is not None:
            event.Skip()
        
    def on_click_cancel(self, event):
        """
        reset the current source
        """
        self.reset_source()
        self.set_values()
        if self.manager is not None:
            self.manager.set_source(self._source)
        if event is not None:
            event.Skip()
    
if __name__ =="__main__":
    app  = wx.App()
    from sas.dataloader.data_info import Source
    source = Source()
    dlg = SourceDialog(source=source)
    dlg.ShowModal()
    app.MainLoop()
 