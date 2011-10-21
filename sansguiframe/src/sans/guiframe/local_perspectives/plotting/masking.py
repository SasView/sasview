
################################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation. 
#
#If you use DANSE applications to do scientific research that leads to 
#publication, we ask that you acknowledge the use of the software with the 
#following sentence:
#
#This work benefited from DANSE software developed under NSF award DMR-0520547. 
#
#copyright 2008, University of Tennessee
################################################################################


##Todo: cleaning up, improving the maskplotpanel initialization, and testing.
import wx
import sys
import pylab
import math
import copy
import numpy
from danse.common.plottools.PlotPanel import PlotPanel
from danse.common.plottools.plottables import Graph
from binder import BindArtist
from sans.guiframe.dataFitting import Data2D
from boxMask import BoxMask
from sectorMask import SectorMask
from sans.guiframe.events import SlicerEvent
from sans.guiframe.events import StatusEvent
(InternalEvent, EVT_INTERNAL) = wx.lib.newevent.NewEvent()

DEFAULT_CMAP = pylab.cm.jet
_BOX_WIDTH = 76
_SCALE = 1e-6
_STATICBOX_WIDTH = 380
PANEL_SIZE = 420
#SLD panel size 
if sys.platform.count("win32") > 0:
    FONT_VARIANT = 0
else:
    FONT_VARIANT = 1
    

class MaskPanel(wx.Dialog):
    """
    Provides the Mask Editor GUI.
    """
    ## Internal nickname for the window, used by the AUI manager
    window_name = "Mask Editor"
    ## Name to appear on the window title bar
    window_caption = "Mask Editor"
    ## Flag to tell the AUI manager to put this panel in the center pane
    CENTER_PANE = True
    def __init__(self, parent=None, base=None, 
                 data=None, id=-1, *args, **kwds):
        kwds["style"] = wx.DEFAULT_DIALOG_STYLE
        kwds["size"] = wx.Size(_STATICBOX_WIDTH * 2, PANEL_SIZE) 
        wx.Dialog.__init__(self, parent, id=id,  *args, **kwds)
        
        if data != None:
            #Font size 
            kwds = []
            self.SetWindowVariant(variant=FONT_VARIANT)
            self.SetTitle("Mask Editor for " + data.name)
            self.parent = base
            self.data = data
            self.str = self.data.__str__()
            ## mask for 2D
            self.mask = data.mask
            self.default_mask = copy.deepcopy(data.mask)
            ## masked data from GUI
            self.slicer_mask = None
            self.slicer = None
            self.slicer_z = 5
            self.data.interactive = True
            ## when 2 data have the same id override the 1 st plotted
            self.name = self.data.name
            # Panel for 2D plot
            self.plotpanel = Maskplotpanel(self, -1,
                                           style=wx.TRANSPARENT_WINDOW)
            self.cmap = DEFAULT_CMAP
            ## Create Artist and bind it
            self.subplot = self.plotpanel.subplot
            self.connect = BindArtist(self.subplot.figure)
            self._setup_layout()
            self.newplot = Data2D(image=self.data.data)
            self.newplot.setValues(self.data)
            self.plotpanel.add_image(self.newplot) 
            self._update_mask(self.mask)
            self.Centre()
            self.Layout()
            # bind evt_close to _draw in fitpage
            self.Bind(wx.EVT_CLOSE, self.OnClose)
            
    def ShowMessage(self, msg=''):
        """
        Show error message when mask covers whole data area
        """
        mssg = 'Erase, redraw or clear the mask. \n\r'
        mssg += 'The data range can not be completely masked... \n\r'
        mssg += msg
        wx.MessageBox(mssg, 'Error', wx.OK | wx.ICON_ERROR)
    
    def _setup_layout(self):
        """
        Set up the layout
        """
        note = "Note: This masking applies\n     only to %s." % self.data.name
        note_txt = wx.StaticText(self, -1, note) 
        note_txt.SetForegroundColour(wx.RED)
        shape = "Select a Shape for Masking:"
        #  panel
        sizer = wx.GridBagSizer(10, 10)
        #---------inputs----------------
        shape_txt = wx.StaticText(self, -1, shape)  
        sizer.Add(shape_txt, (1, 1), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=5)
        self.innersector_rb = wx.RadioButton(self, -1, "Double Wings")
        self.Bind(wx.EVT_RADIOBUTTON, self.onInnerSectorMask,
                  id=self.innersector_rb.GetId())
        sizer.Add(self.innersector_rb, (2, 1), 
                  flag=wx.RIGHT|wx.BOTTOM, border=5)
        self.innercircle_rb = wx.RadioButton(self, -1, "Circular Disk")
        self.Bind(wx.EVT_RADIOBUTTON, self.onInnerRingMask,
                  id=self.innercircle_rb.GetId())
        sizer.Add(self.innercircle_rb, (3, 1),
                   flag=wx.RIGHT|wx.BOTTOM, border=5)
        
        self.innerbox_rb = wx.RadioButton(self, -1, "Rectangular Disk")
        self.Bind(wx.EVT_RADIOBUTTON, self.onInnerBoxMask,
                  id=self.innerbox_rb.GetId())
        sizer.Add(self.innerbox_rb, (4, 1), flag=wx.RIGHT|wx.BOTTOM, border=5)

        self.outersector_rb = wx.RadioButton(self, -1, "Double Wing Window")
        self.Bind(wx.EVT_RADIOBUTTON, self.onOuterSectorMask, 
                  id=self.outersector_rb.GetId())
        sizer.Add(self.outersector_rb, (5, 1),
                  flag=wx.RIGHT|wx.BOTTOM, border=5)
        
        #outersector_y_txt = wx.StaticText(self, -1, 'Outer Sector')
        self.outercircle_rb = wx.RadioButton(self, -1, "Circular Window")
        self.Bind(wx.EVT_RADIOBUTTON, self.onOuterRingMask,
                  id=self.outercircle_rb.GetId())
        sizer.Add(self.outercircle_rb, (6, 1), 
                  flag=wx.RIGHT|wx.BOTTOM, border=5)
        #outerbox_txt = wx.StaticText(self, -1, 'Outer Box')
        self.outerbox_rb = wx.RadioButton(self, -1, "Rectangular Window")
        self.Bind(wx.EVT_RADIOBUTTON, self.onOuterBoxMask, 
                  id=self.outerbox_rb.GetId())
        sizer.Add(self.outerbox_rb, (7, 1), flag=wx.RIGHT|wx.BOTTOM, border=5)
        sizer.Add(note_txt, (8, 1), flag=wx.RIGHT|wx.BOTTOM, border=5)
        self.innercircle_rb.SetValue(False)
        self.outercircle_rb.SetValue(False)        
        self.innerbox_rb.SetValue(False)
        self.outerbox_rb.SetValue(False)
        self.innersector_rb.SetValue(False)
        self.outersector_rb.SetValue(False)
        sizer.Add(self.plotpanel, (0, 2), (13, 13), 
                  wx.EXPAND|wx.LEFT|wx.RIGHT, 15)

        #-----Buttons------------1
        id_button = wx.NewId()
        button_add = wx.Button(self, id_button, "Add")
        button_add.SetToolTipString("Add the mask drawn.")
        button_add.Bind(wx.EVT_BUTTON, self.onAddMask, id=button_add.GetId()) 
        sizer.Add(button_add, (13, 7))
        id_button = wx.NewId()
        button_erase = wx.Button(self, id_button, "Erase")
        button_erase.SetToolTipString("Erase the mask drawn.")
        button_erase.Bind(wx.EVT_BUTTON, self.onEraseMask,
                          id=button_erase.GetId()) 
        sizer.Add(button_erase, (13, 8))
        id_button = wx.NewId()
        button_reset = wx.Button(self, id_button, "Reset")
        button_reset.SetToolTipString("Reset the mask.")
        button_reset.Bind(wx.EVT_BUTTON, self.onResetMask,
                          id=button_reset.GetId()) 
        sizer.Add(button_reset, (13, 9), flag=wx.RIGHT|wx.BOTTOM, border=15)
        id_button = wx.NewId()
        button_reset = wx.Button(self, id_button, "Clear")
        button_reset.SetToolTipString("Clear all mask.")
        button_reset.Bind(wx.EVT_BUTTON, self.onClearMask,
                          id=button_reset.GetId()) 
        sizer.Add(button_reset, (13, 10), flag=wx.RIGHT|wx.BOTTOM, border=15)
        sizer.AddGrowableCol(3)
        sizer.AddGrowableRow(2)
        self.SetSizerAndFit(sizer)
        self.Centre()
        self.Show(True)

    def onInnerBoxMask(self, event=None):
        """
        Call Draw Box Slicer and get mask inside of the box
        """
        #get ready for next evt
        event.Skip()        
        #from boxMask import BoxMask
        if event != None:
            self.onClearSlicer(event)         
        self.slicer_z += 1
        self.slicer =  BoxMask(self, self.subplot,
                               zorder=self.slicer_z, side=True)
        self.subplot.set_ylim(self.data.ymin, self.data.ymax)
        self.subplot.set_xlim(self.data.xmin, self.data.xmax)
        self.update()
        self.slicer_mask = self.slicer.update()
        
    def onOuterBoxMask(self, event=None):
        """
        Call Draw Box Slicer and get mask outside of the box
        """
        event.Skip()        
        #from boxMask import BoxMask
        if event != None:
            self.onClearSlicer(event)      
        self.slicer_z += 1
        self.slicer =  BoxMask(self, self.subplot,
                               zorder=self.slicer_z, side=False)
        self.subplot.set_ylim(self.data.ymin, self.data.ymax)
        self.subplot.set_xlim(self.data.xmin, self.data.xmax)
        self.update()
        self.slicer_mask = self.slicer.update()

    def onInnerSectorMask(self, event=None):
        """
        Call Draw Sector Slicer and get mask inside of the sector
        """
        event.Skip()
        from sectorMask import SectorMask
        if event != None:
            self.onClearSlicer(event)
        self.slicer_z += 1
        self.slicer =  SectorMask(self, self.subplot,
                                  zorder=self.slicer_z, side=True)
        self.subplot.set_ylim(self.data.ymin, self.data.ymax)
        self.subplot.set_xlim(self.data.xmin, self.data.xmax)   
        self.update()
        self.slicer_mask = self.slicer.update() 

    def onOuterSectorMask(self,event=None):
        """
        Call Draw Sector Slicer and get mask outside of the sector
        """
        event.Skip()
        from sectorMask import SectorMask
        if event != None:
            self.onClearSlicer(event)
        self.slicer_z += 1
        self.slicer =  SectorMask(self, self.subplot,
                                  zorder=self.slicer_z, side=False)
        self.subplot.set_ylim(self.data.ymin, self.data.ymax)
        self.subplot.set_xlim(self.data.xmin, self.data.xmax)    
        self.update()     
        self.slicer_mask = self.slicer.update()   

    def onInnerRingMask(self, event=None):
        """
        Perform inner circular cut on Phi and draw circular slicer
        """
        event.Skip()
        from AnnulusSlicer import CircularMask
        if event != None:
            self.onClearSlicer(event)
        self.slicer_z += 1
        self.slicer = CircularMask(self, self.subplot,
                                   zorder=self.slicer_z, side=True)
        self.subplot.set_ylim(self.data.ymin, self.data.ymax)
        self.subplot.set_xlim(self.data.xmin, self.data.xmax)   
        self.update()
        self.slicer_mask = self.slicer.update() 

    def onOuterRingMask(self, event=None):
        """
        Perform outer circular cut on Phi and draw circular slicer
        """
        event.Skip()
        from AnnulusSlicer import CircularMask
        if event != None:
            self.onClearSlicer(event)
        self.slicer_z += 1
        self.slicer = CircularMask(self,self.subplot,
                                   zorder=self.slicer_z, side=False)   
        self.subplot.set_ylim(self.data.ymin, self.data.ymax)
        self.subplot.set_xlim(self.data.xmin, self.data.xmax)
        self.update()
        self.slicer_mask = self.slicer.update()     
        
    def onAddMask(self, event):
        """
        Add new mask to old mask 
        """
        if not self.slicer == None:
            data = Data2D()
            data = self.data
            self.slicer_mask = self.slicer.update()
            data.mask = self.data.mask & self.slicer_mask
            self._check_display_mask(data.mask, event)
            
    def _check_display_mask(self, mask, event):
        """
        check if the mask valid and update the plot
        
        :param mask: mask data
        """
        ## Redraw the current image
        self._update_mask(mask)

    def onEraseMask(self, event):
        """
        Erase new mask from old mask
        """
        if not self.slicer==None:
            self.slicer_mask = self.slicer.update()
            mask = self.data.mask
            mask[self.slicer_mask==False] = True
            self._check_display_mask(mask, event)
            
    def onResetMask(self, event):
        """
        Reset mask to the original mask 
        """        
        self.slicer_z += 1
        self.slicer =  BoxMask(self, self.subplot, 
                               zorder=self.slicer_z, side=True)
        self.subplot.set_ylim(self.data.ymin, self.data.ymax)
        self.subplot.set_xlim(self.data.xmin, self.data.xmax)   
        mask = copy.deepcopy(self.default_mask)
        self.data.mask = mask
        # update mask plot
        self._check_display_mask(mask, event)
        
    def onClearMask(self, event):
        """
        Clear mask
        """            
        self.slicer_z += 1
        self.slicer =  BoxMask(self, self.subplot,
                               zorder=self.slicer_z, side=True)
        self.subplot.set_ylim(self.data.ymin, self.data.ymax)
        self.subplot.set_xlim(self.data.xmin, self.data.xmax)   
        #mask = copy.deepcopy(self.default_mask)
        mask = numpy.ones(len(self.data.mask), dtype=bool)
        self.data.mask = mask
        # update mask plot
        self._check_display_mask(mask, event)
        
    def onClearSlicer(self, event):
        """
        Clear the slicer on the plot
        """
        if not self.slicer == None:
            self.slicer.clear()
            self.subplot.figure.canvas.draw()
            self.slicer = None

    def _setSlicer(self):
        """
        Clear the previous slicer and create a new one.Post an internal
        event.
        
        :param slicer: slicer class to create
        """
        ## Clear current slicer
        if not self.slicer == None:  
            self.slicer.clear()            
        ## Create a new slicer    
        self.slicer_z += 1
        self.slicer = slicer(self, self.subplot, zorder=self.slicer_z)
        self.subplot.set_ylim(self.data2D.ymin, self.data2D.ymax)
        self.subplot.set_xlim(self.data2D.xmin, self.data2D.xmax)
        ## Draw slicer
        self.update()
        self.slicer.update()
        msg = "Plotter2D._setSlicer  %s"%self.slicer.__class__.__name__
        wx.PostEvent(self.parent, StatusEvent(status=msg))
        # Post slicer event
        event = self._getEmptySlicerEvent()
        event.type = self.slicer.__class__.__name__
        event.obj_class = self.slicer.__class__
        event.params = self.slicer.get_params()
        wx.PostEvent(self, event)
   
    def update(self, draw=True):
        """
        Respond to changes in the model by recalculating the 
        profiles and resetting the widgets.
        """
        self.plotpanel.draw()
        
    def _set_mask(self, mask):
        """
        Set mask
        """
        self.data.mask = mask
        
    def set_plot_unfocus(self):
        """
        Not implemented
        """
        pass
    
    def _update_mask(self,mask):
        """
        Respond to changes in masking
        """ 
        # the case of liitle numbers of True points
        if (len(mask[mask]) < 10 and self.data != None):
            self.ShowMessage()
            mask = copy.deepcopy(self.mask)
            self.data.mask = mask
        else:
            self.mask = mask
        # make temperary data to plot
        temp_mask = numpy.zeros(len(mask))
        temp_data = copy.deepcopy(self.data)
        # temp_data default is None
        # This method is to distinguish between masked point and data point = 0.
        temp_mask = temp_mask/temp_mask
        temp_mask[mask] = temp_data.data[mask]
        # set temp_data value for self.mask==True, else still None 
        #temp_mask[mask] = temp_data[mask]
        temp_data.data[mask==False] = temp_mask[mask==False]
        self.plotpanel.clear()
        if self.slicer != None:
            self.slicer.clear()
            self.slicer = None
        # Post slicer None event
        event = self._getEmptySlicerEvent()
        wx.PostEvent(self, event)
       
        ##use this method
        #set zmax and zmin to plot: Fix it w/ data.
        if self.plotpanel.scale == 'log':
            zmax = math.log(max(self.data.data[self.data.data>0]))
            zmin = math.log(min(self.data.data[self.data.data>0]))
        else:
            zmax = max(self.data.data[self.data.data>0])
            zmin = min(self.data.data[self.data.data>0])
        #plot    
        plot = self.plotpanel.image(data=temp_mask,
                       qx_data=self.data.qx_data,
                       qy_data=self.data.qy_data,
                       xmin=self.data.xmin,
                       xmax=self.data.xmax,
                       ymin=self.data.ymin,
                       ymax=self.data.ymax,
                       zmin=zmin,
                       zmax=zmax,
                       cmap=self.cmap,
                       color=0, symbol=0, label=self.data.name)
        # axis labels
        self.plotpanel.axes[0].set_xlabel('$\\rm{Q}_{x}(A^{-1})$')
        self.plotpanel.axes[0].set_ylabel('$\\rm{Q}_{y}(A^{-1})$')
        self.plotpanel.render()
        self.plotpanel.subplot.figure.canvas.draw_idle()
        
    def _getEmptySlicerEvent(self):
        """
        create an empty slicervent 
        """
        self.innerbox_rb.SetValue(False)
        self.outerbox_rb.SetValue(False)
        self.innersector_rb.SetValue(False)
        self.outersector_rb.SetValue(False)
        self.innercircle_rb.SetValue(False)
        self.outercircle_rb.SetValue(False)
        return SlicerEvent(type=None,
                           params=None,
                           obj_class=None) 
             
    def _draw_model(self, event):
        """
         on_close, update the model2d plot
        """
        pass
        
    def freeze_axes(self):
        """
        freeze axes
        """
        self.plotpanel.axes_frozen = True
        
    def thaw_axes(self):
        """
        thaw axes
        """
        self.plotpanel.axes_frozen = False       
         
    def onMouseMotion(self, event):
        """
        onMotion event
        """
        pass
    
    def onWheel(self, event):
        """
        on wheel event
        """
        pass  
    
    def OnClose(self, event):
        """
        """
        try:
            self.parent._draw_masked_model(event)
        except:
            # when called by data panel
            event.Skip()
            pass
        
class Maskplotpanel(PlotPanel):
    """
    """
    def __init__(self, parent, id=-1, color=None, dpi=None, **kwargs):
        """
        """
        PlotPanel.__init__(self, parent, id=id, color=color, dpi=dpi, **kwargs)
        
        # Keep track of the parent Frame
        self.parent = parent
        # Internal list of plottable names (because graph 
        # doesn't have a dictionary of handles for the plottables)
        self.plots = {}
        self.graph = Graph()
        
    def add_toolbar(self):
        """ 
        Add toolbar
        """
        # Not implemented
        pass
    def on_set_focus(self, event):
        """
        send to the parenet the current panel on focus
        """
        #change the panel background
        #self.SetColor((170, 202, 255))
        self.draw()   
         
    def add_image(self, plot):
        """
        Add Image
        """
        self.plots[plot.name] = plot
        #init graph
        self.gaph = Graph()
        #add plot
        self.graph.add(plot)
        #add axes
        self.graph.xaxis('\\rm{Q}_{x} ', 'A^{-1}')
        self.graph.yaxis('\\rm{Q}_{y} ', 'A^{-1}')
        #draw
        self.graph.render(self)
        self.subplot.figure.canvas.draw_idle()
        
    def onMouseMotion(self, event):
        """
        Disable dragging 2D image
        """
        pass
   
    def onContextMenu(self, event):
        """
        Default context menu for a plot panel
        """
        # Slicer plot popup menu
        slicerpop = wx.Menu()
        
        id_cm = wx.NewId()
        slicerpop.Append(id_cm, '&Toggle Linear/Log scale')
        wx.EVT_MENU(self, id_cm, self._onToggleScale)
               
        pos = event.GetPosition()
        pos = self.ScreenToClient(pos)
        self.PopupMenu(slicerpop, pos)

class ViewerFrame(wx.Frame):
    """
    Add comment
    """
    def __init__(self, parent, id, title):
        """
        comment
        :param parent: parent panel/container
        """
        # Initialize the Frame object
        wx.Frame.__init__(self, parent, id, title,
                          wx.DefaultPosition, wx.Size(950, 850))
        # Panel for 1D plot
        self.plotpanel = Maskplotpanel(self, -1, style=wx.RAISED_BORDER)

class ViewApp(wx.App):
    def OnInit(self):
        frame = ViewerFrame(None, -1, 'testView')    
        frame.Show(True)
        #self.SetTopWindow(frame)
        
        return True
               
if __name__ == "__main__": 
    app = ViewApp(0)
    app.MainLoop()     
