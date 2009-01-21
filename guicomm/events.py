import wx.lib
(NewPlotEvent, EVT_NEW_PLOT) = wx.lib.newevent.NewEvent()
(StatusEvent,  EVT_STATUS)   = wx.lib.newevent.NewEvent()
#(SlicerParameterEvent, EVT_SLICER_PARS)   = wx.lib.newevent.NewEvent()
(SlicerPanelEvent, EVT_SLICER_PANEL)   = wx.lib.newevent.NewEvent()
(SlicerParamUpdateEvent, EVT_SLICER_PARS_UPDATE)   = wx.lib.newevent.NewEvent()