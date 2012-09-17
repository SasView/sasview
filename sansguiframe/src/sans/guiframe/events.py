import wx.lib.newevent
#send  data to data manager
(NewStoreDataEvent, EVT_NEW_STORE_DATA) = wx.lib.newevent.NewEvent()
# send data to other perspectives
(NewLoadedDataEvent, EVT_NEW_LOADED_DATA) = wx.lib.newevent.NewEvent()
# plot data
(NewPlotEvent, EVT_NEW_PLOT) = wx.lib.newevent.NewEvent()
# print the messages on statusbar
(StatusEvent,  EVT_STATUS)   = wx.lib.newevent.NewEvent()
#create a panel slicer 
(SlicerPanelEvent, EVT_SLICER_PANEL)   = wx.lib.newevent.NewEvent()
#print update paramaters for panel slicer 
(SlicerParamUpdateEvent, EVT_SLICER_PARS_UPDATE)   = wx.lib.newevent.NewEvent()
#update the slicer from the panel 
(SlicerParameterEvent, EVT_SLICER_PARS)   = wx.lib.newevent.NewEvent()
#slicer event
(SlicerEvent, EVT_SLICER)   = wx.lib.newevent.NewEvent()
## event that that destroy panel name in the datapanel combobox
(DeletePlotPanelEvent, EVT_DELETE_PLOTPANEL)   = wx.lib.newevent.NewEvent()
##event that allow to add more that to the same plot
(AddManyDataEvent, EVT_ADD_MANY_DATA)   = wx.lib.newevent.NewEvent()
##event for the panel on focus
(PanelOnFocusEvent, EVT_PANEL_ON_FOCUS)   = wx.lib.newevent.NewEvent()
#book mark event
(AppendBookmarkEvent, EVT_APPEND_BOOKMARK) = wx.lib.newevent.NewEvent()
#event to ask dataloader plugin to load data if dataloader plugin exist
(NewLoadDataEvent, EVT_NEW_LOAD_DATA) = wx.lib.newevent.NewEvent()
#event to toggle from single model to  batch
(NewBatchEvent, EVT_NEW_BATCH) = wx.lib.newevent.NewEvent()
##color event
(NewColorEvent, EVT_NEW_COLOR) = wx.lib.newevent.NewEvent()
##change category event
(ChangeCategoryEvent, EVT_CATEGORY) = wx.lib.newevent.NewEvent()
