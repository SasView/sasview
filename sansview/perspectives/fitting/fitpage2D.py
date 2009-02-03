import sys
import wx
import wx.lib
import numpy,math
import copy

from sans.guicomm.events import StatusEvent   
(ModelEventbox, EVT_MODEL_BOX) = wx.lib.newevent.NewEvent()
_BOX_WIDTH = 80

from modelpage import format_number
from fitpage1D import FitPage1D
    
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
        FitPage1D.__init__(self, parent, *args, **kwargs)
        """ 
            Initialization of the Panel
        """
       
        
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
        
 
