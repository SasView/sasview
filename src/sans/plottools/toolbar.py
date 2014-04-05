"""
    This module overwrites matplotlib toolbar
"""
import wx
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg
from matplotlib.backends.backend_wx import _load_bitmap
import logging

# Event binding code changed after version 2.5
if wx.VERSION_STRING >= '2.5':
    def bind(actor,event,action,**kw):
        actor.Bind(event,action,**kw)
else:
    def bind(actor,event,action,id=None):
        if id is not None:
            event(actor, id, action)
        else:
            event(actor,action)

class NavigationToolBar(NavigationToolbar2WxAgg):
    """
    Overwrite matplotlib toolbar
    """
    def __init__(self, canvas, parent=None):
        NavigationToolbar2WxAgg.__init__(self, canvas)

    # CRUFT: mpl 1.1 uses save rather than save_figure
    try: save_figure = NavigationToolbar2WxAgg.save
    except AttributeError: pass
    def _init_toolbar(self):
        self._parent = self.canvas.GetParent()
        _NTB2_HOME         = wx.NewId()
        self._NTB2_BACK    = wx.NewId()
        self._NTB2_FORWARD = wx.NewId()
        self._NTB2_PAN     = wx.NewId()
        self._NTB2_ZOOM    = wx.NewId()
        _NTB2_SAVE         = wx.NewId()
        _NTB2_PRINT        = wx.NewId()
        _NTB2_RESET        = wx.NewId()

        # for mpl 1.2+ compatibility
        self.wx_ids = {}
        self.wx_ids['Back'] = self._NTB2_BACK
        self.wx_ids['Forward'] = self._NTB2_FORWARD
        self.wx_ids['Pan'] = self._NTB2_PAN
        self.wx_ids['Zoom'] = self._NTB2_ZOOM

        self.SetToolBitmapSize(wx.Size(24,24))

        context_tip = 'Graph Menu: \n'
        context_tip += '    For more menu options, \n'
        context_tip += '    right-click the data symbols.'
        context = wx.ArtProvider.GetBitmap(wx.ART_LIST_VIEW, wx.ART_TOOLBAR)
        self.AddSimpleTool(_NTB2_HOME, context, context_tip, context_tip)

        self.InsertSeparator(1)
        
        self.AddSimpleTool(self._NTB2_BACK, _load_bitmap('back.png'),
                           'Back', 'Back navigation view')
        self.AddSimpleTool(self._NTB2_FORWARD, _load_bitmap('forward.png'),
                           'Forward', 'Forward navigation view')
        # todo: get new bitmap
        self.AddCheckTool(self._NTB2_PAN, _load_bitmap('move.png'),
                           shortHelp='Pan',
                           longHelp='Pan with left, zoom with right')
        self.AddCheckTool(self._NTB2_ZOOM, _load_bitmap('zoom_to_rect.png'),
                           shortHelp='Zoom', longHelp='Zoom to rectangle')

        self.AddSeparator()
        self.AddSimpleTool(_NTB2_SAVE, _load_bitmap('filesave.png'),
                           'Save', 'Save plot contents to file')
        
        print_bmp = wx.ArtProvider.GetBitmap(wx.ART_PRINT, wx.ART_TOOLBAR)
        self.AddSimpleTool(_NTB2_PRINT, print_bmp, 'Print', 'Print plot')
        
        reset_bmp = wx.ArtProvider.GetBitmap(wx.ART_GO_HOME, wx.ART_TOOLBAR)
        self.AddSimpleTool(_NTB2_RESET, reset_bmp, 'Reset', 'Reset graph range')

        bind(self, wx.EVT_TOOL, self.on_menu, id=_NTB2_HOME)
        bind(self, wx.EVT_TOOL, self.forward, id=self._NTB2_FORWARD)
        bind(self, wx.EVT_TOOL, self.back, id=self._NTB2_BACK)
        bind(self, wx.EVT_TOOL, self.zoom, id=self._NTB2_ZOOM)
        bind(self, wx.EVT_TOOL, self.pan, id=self._NTB2_PAN)
        bind(self, wx.EVT_TOOL, self.save_figure, id=_NTB2_SAVE)
        bind(self, wx.EVT_TOOL, self.on_print, id=_NTB2_PRINT)
        bind(self, wx.EVT_TOOL, self.on_reset, id=_NTB2_RESET)

        self.Realize()

    def on_menu(self, event):
        """
            Plot menu
        """
        try:
            self._parent.onToolContextMenu(event=event)
        except:
            logging.error("Plot toolbar could not show menu")

    def on_reset(self, event):
        """
            Reset plot
        """
        try:
            self._parent.onResetGraph(event=event)
        except:
            logging.error("Plot toolbar could not reset plot")

    def on_print(self, event):
        """
            Print
        """
        try:
            self.canvas.Printer_Preview(event=event)
        except:
            logging.error("Plot toolbar could not print")
        