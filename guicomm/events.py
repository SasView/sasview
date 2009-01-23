import wx.lib
# plot data
(NewPlotEvent, EVT_NEW_PLOT) = wx.lib.newevent.NewEvent()
# print the messages on statusbar
(StatusEvent,  EVT_STATUS)   = wx.lib.newevent.NewEvent()
#event to get id for model view 2D panel
(Model2DPanelEvent, EVT_MODEL2D_PANEL)   = wx.lib.newevent.NewEvent()
#create a panel slicer 
(SlicerPanelEvent, EVT_SLICER_PANEL)   = wx.lib.newevent.NewEvent()
#print update paramaters for panel slicer 
(SlicerParamUpdateEvent, EVT_SLICER_PARS_UPDATE)   = wx.lib.newevent.NewEvent()