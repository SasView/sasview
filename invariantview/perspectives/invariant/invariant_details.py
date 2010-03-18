
import wx
import sys
import colorsys
import numpy
from sans.guiframe.utils import format_number, check_float
# Dimensions related to chart
RECTANGLE_WIDTH  = 400.0  
RECTANGLE_HEIGHT = 20
RECTANGLE_SCALE  = 0.0001
DEFAULT_QSTAR = 1.0
#Invariant panel size 
_BOX_WIDTH = 76
_BOX_PERCENT_WIDTH = 100  
  
if sys.platform.count("win32")>0:
    _STATICBOX_WIDTH = 450
    PANEL_WIDTH = 500
    PANEL_HEIGHT = 700
    FONT_VARIANT = 0
else:
    _STATICBOX_WIDTH = 480
    PANEL_WIDTH = 530
    PANEL_HEIGHT = 700
    FONT_VARIANT = 1
    
    
class InvariantDetailsPanel(wx.ScrolledWindow):
    """
        This panel describes proportion of invariants 
    """
    def __init__(self, parent, qstar_container=None):
        wx.ScrolledWindow.__init__(self, parent, 
                                    style=wx.FULL_REPAINT_ON_RESIZE)
       
        #Font size 
        self.SetWindowVariant(variant=FONT_VARIANT)
        self.parent = parent
        #self.qstar_container
        self.qstar_container = qstar_container
        self.compute_scale()
        #warning message
        self.warning_msg = ""
        #Define scale of each bar
        low_inv_scale = self.qstar_container.qstar_low_scale
        self.low_scale = self.check_scale(scale=low_inv_scale, scale_name="Low")
        inv_scale = self.qstar_container.qstar_scale
        self.inv_scale = self.check_scale(scale=inv_scale, scale_name="Inv")
        high_inv_scale = self.qstar_container.qstar_high_scale
        self.high_scale = self.check_scale(scale=high_inv_scale, scale_name="High")
        #Default color the extrapolation bar is grey
        self.extrapolation_color_low = wx.Colour(169,  169, 168, 128)
        self.extrapolation_color_high = wx.Colour(169,  169, 168, 128)
        #change color of high and low bar when necessary
        self.set_color_bar()
        #draw the panel itself
        self._do_layout()
        self.set_values()
 
    def _define_structure(self):
        """
            Define main sizers needed for this panel
        """
        #Box sizers must be defined first before defining buttons/textctrls (MAC).
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        #Sizer related to chart
        chart_box = wx.StaticBox(self, -1, "Invariant Chart")
        self.chart_sizer = wx.StaticBoxSizer(chart_box, wx.VERTICAL)
        self.chart_sizer.SetMinSize((PANEL_WIDTH,-1))
        #Sizer related to invariant values
        self.invariant_sizer =  wx.GridBagSizer(4, 4)
        #Sizer related to warning message
        warning_box = wx.StaticBox(self, -1, "Warning")
        self.warning_sizer = wx.StaticBoxSizer(warning_box, wx.VERTICAL)
        self.warning_sizer.SetMinSize((PANEL_WIDTH,-1))
        #Sizer related to button
        self.button_sizer = wx.BoxSizer(wx.HORIZONTAL)
      
    def _layout_shart(self):
        """
            Draw widgets related to chart
        """
        self.panel_chart = wx.Panel(self)
        self.panel_chart.Bind(wx.EVT_PAINT, self.on_paint)
        self.chart_sizer.Add(self.panel_chart, 1, wx.EXPAND|wx.ALL, 0)
        
    def _layout_invariant(self):
        """
            Draw widgets related to invariant
        """
        uncertainty = "+/-" 
        unit_invariant = '[1/cm][1/A]'
     
        invariant_txt = wx.StaticText(self, -1, 'Invariant')
        self.invariant_tcl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        self.invariant_tcl.SetEditable(False)
        self.invariant_tcl.SetToolTipString("Invariant in the data set's Q range.")
        self.invariant_err_tcl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        self.invariant_err_tcl.SetEditable(False)
        self.invariant_err_tcl.SetToolTipString("Uncertainty on the invariant.")
        invariant_units_txt = wx.StaticText(self, -1, unit_invariant)
       
        invariant_low_txt = wx.StaticText(self, -1, 'Invariant in low-Q region')
        self.invariant_low_tcl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        self.invariant_low_tcl.SetEditable(False)
        self.invariant_low_tcl.SetToolTipString("Invariant computed with the extrapolated low-Q data.")
        self.invariant_low_err_tcl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        self.invariant_low_err_tcl.SetEditable(False)
        self.invariant_low_err_tcl.SetToolTipString("Uncertainty on the invariant.")
        invariant_low_units_txt = wx.StaticText(self, -1,  unit_invariant)
        
        invariant_high_txt = wx.StaticText(self, -1, 'Invariant in high-Q region')
        self.invariant_high_tcl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        self.invariant_high_tcl.SetEditable(False)
        self.invariant_high_tcl.SetToolTipString("Invariant computed with the extrapolated high-Q data")
        self.invariant_high_err_tcl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,-1))
        self.invariant_high_err_tcl.SetEditable(False)
        self.invariant_high_err_tcl.SetToolTipString("Uncertainty on the invariant.")
        invariant_high_units_txt = wx.StaticText(self, -1,  unit_invariant)
   
        #Invariant low
        iy = 1
        ix = 0 
        self.invariant_sizer.Add(invariant_low_txt, (iy, ix), (1,1),
                             wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1
        self.invariant_sizer.Add(self.invariant_low_tcl, (iy, ix), (1,1),
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        ix += 1
        self.invariant_sizer.Add( wx.StaticText(self, -1, uncertainty),
                         (iy, ix),(1,1),wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        ix += 1
        self.invariant_sizer.Add(self.invariant_low_err_tcl, (iy, ix), (1,1),
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 1
        self.invariant_sizer.Add(invariant_low_units_txt
                         ,(iy, ix),(1,1),wx.EXPAND|wx.ADJUST_MINSIZE, 0)  
        #Invariant 
        iy += 1
        ix = 0 
        self.invariant_sizer.Add(invariant_txt, (iy, ix), (1,1),
                             wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1
        self.invariant_sizer.Add(self.invariant_tcl, (iy, ix), (1,1),
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        ix += 1
        self.invariant_sizer.Add(wx.StaticText(self, -1, uncertainty),
                         (iy, ix),(1,1),wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        ix += 1
        self.invariant_sizer.Add(self.invariant_err_tcl, (iy, ix), (1,1),
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        ix +=1
        self.invariant_sizer.Add(invariant_units_txt
                         ,(iy, ix),(1,1),wx.EXPAND|wx.ADJUST_MINSIZE, 0)  
        #Invariant high
        iy += 1
        ix = 0 
        self.invariant_sizer.Add(invariant_high_txt, (iy, ix), (1,1),
                             wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1
        self.invariant_sizer.Add(self.invariant_high_tcl, (iy, ix), (1,1),
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        ix += 1
        self.invariant_sizer.Add(wx.StaticText(self, -1, uncertainty),
                         (iy, ix),(1,1),wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        ix += 1
        self.invariant_sizer.Add(self.invariant_high_err_tcl, (iy, ix), (1,1),
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        ix += 1
        self.invariant_sizer.Add(invariant_high_units_txt
                         ,(iy, ix),(1,1),wx.EXPAND|wx.ADJUST_MINSIZE, 0)  
       
    def _layout_warning(self):
        """
            Draw widgets related to warning
        """
        #Warning [string]
        self.warning_msg_txt = wx.StaticText(self, -1,self.warning_msg)  
        self.warning_msg_txt.SetForegroundColour('red') 
        self.warning_sizer.AddMany([(self.warning_msg_txt, 0, wx.EXPAND)])
        
    def _layout_button(self):
        """
            Draw widgets related to button
        """
        #Close button
        id = wx.NewId()
        button_ok = wx.Button(self, id, "Ok")
        button_ok.SetToolTipString("Give Details on Computation")
        self.Bind(wx.EVT_BUTTON, self.on_close, id=id)
        self.button_sizer.AddMany([((20,20), 0 , wx.LEFT, 400),
                                   (button_ok, 0 , wx.RIGHT, 10)])
    def _do_layout(self):
        """
            Draw window content
        """
        self._define_structure()
        self._layout_shart()
        self._layout_invariant()
        self._layout_warning()
        self._layout_button()
        self.main_sizer.AddMany([(self.chart_sizer, 1, wx.ALL, 10),
                                 (self.invariant_sizer, 0, wx.ALL, 10),
                                  (self.warning_sizer, 0, wx.ALL, 10),
                                  (self.button_sizer, 0, wx.ALL, 10)])
        self.SetSizer(self.main_sizer)
        self.SetScrollbars(20,20,25,65)
        self.SetAutoLayout(True)
        
    def set_values(self):
        """
            Set value of txtcrtl
        """
        self.invariant_tcl.SetValue(format_number(self.qstar_container.qstar))
        self.invariant_err_tcl.SetValue(format_number(self.qstar_container.qstar_err)) 
        self.invariant_low_tcl.SetValue(format_number(self.qstar_container.qstar_low))
        self.invariant_low_err_tcl.SetValue(format_number(self.qstar_container.qstar_low_err)) 
        self.invariant_high_tcl.SetValue(format_number(self.qstar_container.qstar_high))
        self.invariant_high_err_tcl.SetValue(format_number(self.qstar_container.qstar_high_err)) 
    
    def compute_scale(self):
        """
            Compute scale
        """
        qstar_total = self.qstar_container.qstar_total
        if qstar_total is None:
            qstar_total = DEFAULT_QSTAR
        #compute the percentage of invariant
        inv = self.qstar_container.qstar
        if inv is None:
            inv = 0.0 
        inv_scale = inv/qstar_total
        self.qstar_container.qstar_scale = inv_scale
        #compute the percentage of low q invariant
        inv_low = self.qstar_container.qstar_low
        if inv_low is None:
            inv_low = 0.0 
        inv_scale = inv_low/qstar_total
        self.qstar_container.qstar_low_scale = inv_scale
        #compute the percentage of high q invariant
        inv_high = self.qstar_container.qstar_high
        if inv_high is None:
            inv_high = 0.0 
        inv_scale = inv_high/qstar_total
        self.qstar_container.qstar_high_scale = inv_scale
       
    def check_scale(self, scale, scale_name='scale'):
        """
            Check scale receive in this panel. i
        """
        try: 
            if scale is None:
                scale = 0.0
            scale = float(scale)
            if  scale == 0.0:
                scale = RECTANGLE_SCALE
        except:
            scale = RECTANGLE_SCALE
            self.warning_msg += "Receive an invalid scale for %s\n"
            self.warning_msg += "check this value : %s\n"%(str(scale_name),str(scale))
        return scale
    
    def set_color_bar(self):
        """
            Change the color for low and high bar when necessary
        """
        #warning to the user when the extrapolated invariant is greater than %5
        if self.low_scale >= 0.05:
            self.extrapolation_color_low = wx.Colour(255,  0, 0, 128)
            self.warning_msg += "The value of invariant extrapolated at \n"
            self.warning_msg += "low q range is %s percent \n"%(str(self.low_scale*100))
        if self.high_scale >= 0.05:
            self.extrapolation_color_high = wx.Colour(255,  0, 0, 128)
            self.warning_msg += "The value of invariant extrapolated at \n"
            self.warning_msg += "high q range is %s percent \n"%(str(self.high_scale*100))
    
    def on_close(self, event):
        """
            Close the current window
        """
        self.Close()
        self.parent.Close()
        
    def on_paint(self, event):
        """
            Draw the chart
        """
        dc = wx.PaintDC(self.panel_chart)
        try:
            gc = wx.GraphicsContext.Create(dc)
        except NotImplementedError:
            dc.DrawText("This build of wxPython does not support the wx.GraphicsContext "
                        "family of classes.", 25, 25)
            return
        #Start the drawing
        font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        font.SetWeight(wx.BOLD)
        gc.SetFont(font)
        # Draw a rectangle
        path = gc.CreatePath()
        path.AddRectangle(-RECTANGLE_WIDTH/2,-RECTANGLE_HEIGHT/2,
                          RECTANGLE_WIDTH/2,RECTANGLE_HEIGHT/2)
        x_origine = 50
        y_origine = 15
        #Draw low rectangle
        gc.PushState()        
        label = "Low"
        PathFunc = gc.DrawPath
        w, h = gc.GetTextExtent(label)
        gc.DrawText(label, x_origine, y_origine)
        #Translate the rectangle
        x_center = x_origine + RECTANGLE_WIDTH * self.low_scale/2 + w +10
        y_center = y_origine + h
        gc.Translate(x_center, y_center)    
        gc.SetPen(wx.Pen("black", 1))
        gc.SetBrush(wx.Brush(self.extrapolation_color_low))
        # Increase width by self.low_scale
        gc.Scale(self.low_scale, 1.0) 
        PathFunc(path)
        gc.PopState()  
        #Draw rectangle for invariant   
        gc.PushState()    # save it again
        y_origine += 20         
        gc.DrawText("Inv", x_origine, y_origine)
        # offset to the lower part of the window
        x_center = x_origine + RECTANGLE_WIDTH * self.inv_scale/2 + w + 10
        y_center = y_origine + h
        gc.Translate(x_center, y_center)
        # 128 == half transparent
        gc.SetBrush(wx.Brush(wx.Colour(67,  208,  128, 128))) 
        # Increase width by self.inv_scale
        gc.Scale(self.inv_scale, 1.0)    
        gc.DrawPath(path)
        gc.PopState()
        # restore saved state
        #Draw rectangle for high invariant
        gc.PushState() 
        y_origine += 20 
        gc.DrawText("High", x_origine, y_origine) 
        #define the position of the new rectangle
        x_center = x_origine + RECTANGLE_WIDTH * self.high_scale/2 + w + 10
        y_center = y_origine + h
        gc.Translate(x_center, y_center)
        gc.SetBrush(wx.Brush(self.extrapolation_color_high)) 
        # increase scale by self.high_scale
        gc.Scale(self.high_scale, 1.0)  
        gc.DrawPath(path)
        gc.PopState()
        
class InvariantDetailsWindow(wx.Frame):
    def __init__(self, parent, qstar_container=None, *args, **kwds):
        kwds["size"]= (PANEL_WIDTH +100, 450)
        wx.Frame.__init__(self, parent, *args, **kwds)
        self.container = qstar_container
        if self.container is None:
            from invariant_panel import InvariantContainer
            self.container = InvariantContainer()
            self.container.qstar_total = 1
            self.container.qstar = 0.75
            self.container.qstar_low = 0.60
            self.container.qstar_high = 0.0049
        self.panel = InvariantDetailsPanel(parent=self, 
                                           qstar_container=self.container)
      
        self.Show()
   
if __name__ =="__main__":
    app  = wx.App()
    window = InvariantDetailsWindow(parent=None, title="Source Editor")
    app.MainLoop()
