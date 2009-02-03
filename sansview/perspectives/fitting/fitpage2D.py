import sys
import wx
import wx.lib
import numpy,math
import copy

from sans.guicomm.events import StatusEvent   
(ModelEventbox, EVT_MODEL_BOX) = wx.lib.newevent.NewEvent()
_BOX_WIDTH = 80

from modelpage import format_number
from old_fitpage1D import FitPage1D
    
class FitPage2D(FitPage1D):
    """
        FitPanel class contains fields allowing to display results when
        fitting  a model and one data
        @note: For Fit to be performed the user should check at least one parameter
        on fit Panel window.
  
    """
    ## Internal name for the AUI manager
    window_name = "Fit page"
    ## Title to appear on top of the window
    window_caption = "Fit Page"
    
    
    def __init__(self, parent,data, *args, **kwargs):
        wx.ScrolledWindow.__init__(self, parent, *args, **kwargs)
        """ 
            Initialization of the Panel
        """
        self.manager = None
        self.parent  = parent
        self.event_owner=None
        #panel interface
        self.vbox  = wx.BoxSizer(wx.VERTICAL)
        self.sizer6 = wx.GridBagSizer(5,5)
        self.sizer5 = wx.GridBagSizer(5,5)
        self.sizer4 = wx.GridBagSizer(5,5)
        self.sizer3 = wx.GridBagSizer(5,5)
        self.sizer2 = wx.GridBagSizer(5,5)
        self.sizer1 = wx.GridBagSizer(5,5)
        
        #self.DataSource      = wx.TextCtrl(self, -1,size=(_BOX_WIDTH,20))
        #self.DataSource.SetToolTipString("name of data to fit")
        #self.DataSource.SetValue(str(data.name))
        #self.DataSource.Disable()
        self.DataSource  =wx.StaticText(self, -1,str(data.name))
        self.modelbox = wx.ComboBox(self, -1)
        id = wx.NewId()
        self.btFit =wx.Button(self,id,'Fit')
        self.btFit.Bind(wx.EVT_BUTTON, self.onFit,id=id)
        self.btFit.SetToolTipString("Perform fit.")
        self.static_line_1 = wx.StaticLine(self, -1)
        
        self.vbox.Add(self.sizer3)
        self.vbox.Add(self.sizer2)
        self.vbox.Add(self.static_line_1, 0, wx.EXPAND, 0)
        self.vbox.Add(self.sizer5)
        self.vbox.Add(self.sizer6)
        self.vbox.Add(self.sizer4)
        self.vbox.Add(self.sizer1)
        ## Q range
        self.qmin= 0.001
        self.qmax= 0.1
        
        id = wx.NewId()
        self.btClose =wx.Button(self,id,'Close')
        self.btClose.Bind(wx.EVT_BUTTON, self.onClose,id=id)
        self.btClose.SetToolTipString("Close page.")
        ix = 0
        iy = 1
        self.sizer3.Add(wx.StaticText(self, -1, 'Data Source'),(iy,ix),\
                 (1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1
        self.sizer3.Add(self.DataSource,(iy,ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 1
        self.sizer3.Add((20,20),(iy,ix),(1,1),wx.RIGHT|wx.EXPAND|wx.ADJUST_MINSIZE,0)
        ix = 0
        iy += 1
        self.sizer3.Add(wx.StaticText(self,-1,'Model'),(iy,ix),(1,1)\
                  , wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1
        self.sizer3.Add(self.modelbox,(iy,ix),(1,1),  wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        
        ix = 0
        iy = 1
        #set maximum range for x in linear scale
        self.text4_3 = wx.StaticText(self, -1, 'Maximum Data\n Range (Linear)', style=wx.ALIGN_LEFT)
        self.sizer4.Add(self.text4_3,(iy,ix),(1,1),\
                   wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1
        self.text4_1 = wx.StaticText(self, -1, 'Min')
        self.sizer4.Add(self.text4_1,(iy, ix),(1,1),\
                            wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        #self.text4_1.Hide()
        ix += 2
        self.text4_2 = wx.StaticText(self, -1, 'Max')
        self.sizer4.Add(self.text4_2,(iy, ix),(1,1),\
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        #self.text4_2.Hide()
       
        #self.text4_3.Hide()
        ix = 0
        iy += 1
        self.text4_4 = wx.StaticText(self, -1, 'x range')
        self.sizer4.Add(self.text4_4,(iy, ix),(1,1),\
                            wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1
        self.xmin    = wx.TextCtrl(self, -1,size=(_BOX_WIDTH,20))
        self.xmin.SetValue(format_number(data.xmin))
        self.xmin.SetToolTipString("Minimun value of x in linear scale.")
        self.sizer4.Add(self.xmin,(iy, ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        self.xmin.Bind(wx.EVT_KILL_FOCUS, self._onTextEnter)
        self.xmin.Bind(wx.EVT_TEXT_ENTER, self._onTextEnter)
        
        ix += 2
        self.xmax    = wx.TextCtrl(self, -1,size=(_BOX_WIDTH,20))
        self.xmax.SetValue(format_number(data.xmax))
        self.xmax.SetToolTipString("Maximum value of x in linear scale.")
        self.sizer4.Add(self.xmax,(iy,ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        self.xmax.Bind(wx.EVT_KILL_FOCUS, self._onTextEnter)
        self.xmax.Bind(wx.EVT_TEXT_ENTER, self._onTextEnter)
        
        iy +=1
        ix = 0
        self.text4_5 = wx.StaticText(self, -1, 'y range')
        self.sizer4.Add(self.text4_5,(iy, ix),(1,1),\
                            wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1
        self.ymin    = wx.TextCtrl(self, -1,size=(_BOX_WIDTH,20))
        self.ymin.SetValue(format_number(data.ymin))
        self.ymin.SetToolTipString("Minimun value of y in linear scale.")
        self.sizer4.Add(self.ymin,(iy, ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        self.ymin.Bind(wx.EVT_KILL_FOCUS, self._onTextEnter)
        self.ymin.Bind(wx.EVT_TEXT_ENTER, self._onTextEnter)
       
        ix += 2
        self.ymax    = wx.TextCtrl(self, -1,size=(_BOX_WIDTH,20))
        self.ymax.SetValue(format_number(data.ymax))
        self.ymax.SetToolTipString("Maximum value of y in linear scale.")
        self.sizer4.Add(self.ymax,(iy,ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        self.ymax.Bind(wx.EVT_KILL_FOCUS, self._onTextEnter)
        self.ymax.Bind(wx.EVT_TEXT_ENTER, self._onTextEnter)
        
        #Set chisqr  result into TextCtrl
        ix = 0
        iy = 1
        self.text1_1 = wx.StaticText(self, -1, 'Chi2/dof', style=wx.ALIGN_LEFT)
        self.sizer1.Add(self.text1_1,(iy,ix),(1,1),\
                   wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1
        self.tcChi    = wx.TextCtrl(self, -1,size=(_BOX_WIDTH,20))
        self.tcChi.SetToolTipString("Chi^2 over degrees of freedom.")
        self.sizer1.Add(self.tcChi,(iy,ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix +=2
        self.sizer1.Add(self.btFit,(iy,ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix+= 1
        self.sizer1.Add( self.btClose,(iy,ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix= 1
        iy+=1
        self.sizer1.Add((20,20),(iy,ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        # contains link between  model ,all its parameters, and panel organization
        self.parameters=[]
        self.fixed_param=[]
        #contains link between a model and selected parameters to fit 
        self.param_toFit=[]
        # model on which the fit would be performed
        self.model=None
        # preview selected model name
       
        
        #dictionary of model name and model class
        self.model_list_box={}
       
        self.data = data
        self.vbox.Layout()
        self.vbox.Fit(self) 
        self.SetSizer(self.vbox)
        self.SetScrollbars(20,20,55,40)
        self.Centre()
        
   
        
    def compute_chisqr(self):
        """ @param fn: function that return model value
            @return residuals
        """
        flag=self.checkFitRange()
        res=[]
        if flag== True:
            try:
                xmin = float(self.xmin.GetValue())
                xmax = float(self.xmax.GetValue())
                ymin = float(self.ymin.GetValue())
                ymax = float(self.ymax.GetValue())
                for i in range(len(self.data.x_bins)):
                    if self.data.x_bins[i]>= xmin and self.data.x_bins[i]<= xmax:
                        for j in range(len(self.data.y_bins)):
                            if self.data.y_bins[j]>= ymin and self.data.y_bins[j]<= ymax:
                                res.append( (self.data.data[j][i]- self.model.runXY(\
                                 [self.data.x_bins[i],self.data.y_bins[j]]))\
                                    /self.data.err_data[j][i] )
                sum=0
               
                for item in res:
                    if numpy.isfinite(item):
                        sum +=item
                #print "chisqr : sum 2D", xmin, xmax, ymin, ymax,sum
                #print res
                self.tcChi.SetValue(format_number(math.fabs(sum)))
            except:
                wx.PostEvent(self.parent.GrandParent, StatusEvent(status=\
                            "Chisqr cannot be compute: %s"% sys.exc_value))
        
 
