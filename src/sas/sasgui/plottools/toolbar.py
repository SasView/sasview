"""
    This module overwrites matplotlib toolbar
"""
import wx
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg
from matplotlib.backends.backend_wx import _load_bitmap
import logging

# Event binding code changed after version 2.5
if wx.VERSION_STRING >= '2.5':
    def bind(actor, event, action, **kw):
        actor.Bind(event, action, **kw)
else:
    def bind(actor, event, action, id=None):
        if id is not None:
            event(actor, id, action)
        else:
            event(actor, action)

class NavigationToolBar(NavigationToolbar2WxAgg):
    _NTB2_HOME = wx.NewId()
    _NTB2_BACK = wx.NewId()
    _NTB2_FORWARD = wx.NewId()
    _NTB2_PAN = wx.NewId()
    _NTB2_ZOOM = wx.NewId()
    _NTB2_SAVE = wx.NewId()
    _NTB2_PRINT = wx.NewId()
    _NTB2_RESET = wx.NewId()
    _NTB2_COPY = wx.NewId()
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

        # for mpl 1.2+ compatibility
        self.wx_ids = {}
        self.wx_ids['Back'] = self._NTB2_BACK
        self.wx_ids['Forward'] = self._NTB2_FORWARD
        self.wx_ids['Pan'] = self._NTB2_PAN
        self.wx_ids['Zoom'] = self._NTB2_ZOOM

        self.SetToolBitmapSize(wx.Size(24, 24))

        context_tip = 'Graph Menu: \n'
        context_tip += '    For more menu options, \n'
        context_tip += '    right-click the data symbols.'
        context = wx.ArtProvider.GetBitmap(wx.ART_LIST_VIEW, wx.ART_TOOLBAR)
        self.AddSimpleTool(self._NTB2_HOME, context, context_tip, context_tip)

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
        self.AddSimpleTool(self._NTB2_SAVE, _load_bitmap('filesave.png'),
                           'Save', 'Save plot contents to file')

        print_bmp = wx.ArtProvider.GetBitmap(wx.ART_PRINT, wx.ART_TOOLBAR)
        self.AddSimpleTool(self._NTB2_PRINT, print_bmp, 'Print', 'Print plot')

        reset_bmp = wx.ArtProvider.GetBitmap(wx.ART_GO_HOME, wx.ART_TOOLBAR)
        self.AddSimpleTool(self._NTB2_RESET, reset_bmp, 'Reset', 'Reset graph range')

        bind(self, wx.EVT_TOOL, self.context_menu, id=self._NTB2_HOME)
        bind(self, wx.EVT_TOOL, self.forward, id=self._NTB2_FORWARD)
        bind(self, wx.EVT_TOOL, self.back, id=self._NTB2_BACK)
        bind(self, wx.EVT_TOOL, self.zoom, id=self._NTB2_ZOOM)
        bind(self, wx.EVT_TOOL, self.pan, id=self._NTB2_PAN)
        bind(self, wx.EVT_TOOL, self.save_figure, id=self._NTB2_SAVE)
        bind(self, wx.EVT_TOOL, self.print_figure, id=self._NTB2_PRINT)
        bind(self, wx.EVT_TOOL, self.home, id=self._NTB2_RESET)

        self.Realize()

    def on_menu(self, event):
        try:
            self._parent.onToolContextMenu(event=event)
        except:
            logging.error("Plot toolbar could not show menu")

    def context_menu(self, event):
        """
        Default context menu for a plot panel

        """
        # Slicer plot popup menu
        popup = wx.Menu()
        popup.Append(self._NTB2_SAVE, '&Save image', 'Save image as PNG')
        wx.EVT_MENU(self, self._NTB2_SAVE, self.save_figure)

        popup.Append(self._NTB2_PRINT, '&Print image', 'Print image ')
        wx.EVT_MENU(self, self._NTB2_PRINT, self.print_figure)

        popup.Append(self._NTB2_COPY, '&Copy to Clipboard', 'Copy image to the clipboard')
        wx.EVT_MENU(self, self._NTB2_COPY, self.copy_figure)

        # Show the popup menu relative to the location of the toolbar
        self.PopupMenu(popup, (0,0))


    def print_figure(self, event):
        try:
            _printer = wx.Printer()
            _printer.Print(self.canvas, PlotPrintout(self.canvas), True)
        except:
            import traceback
            logging.error(traceback.format_exc())

    def copy_figure(self, event):
        copy_image_to_clipboard(self.canvas)

class PlotPrintout(wx.Printout):
    """
    Create the wx.Printout object for matplotlib figure from the PlotPanel.
    Provides the required OnPrintPage and HasPage overrides.  Other methods
    may be added/overriden in the future.
    :TODO: this needs LOTS of TLC .. but fixes immediate problem
    """
    def __init__(self, canvas):
        """
        Initialize wx.Printout and get passed figure object
        """
        wx.Printout.__init__(self)
        self.canvas = canvas

    def OnPrintPage(self, page):
        """
        Most rudimentry OnPrintPage overide.  instatiates a dc object, gets
        its size, gets the size of the figure object, scales it to the dc
        canvas size keeping the aspect ratio intact, then prints as bitmap
        """
        _dc = self.GetDC()
        (_dcX, _dcY) = _dc.GetSizeTuple()
        (_bmpX,_bmpY) = self.canvas.GetSize()
        _scale = min(_dcX/_bmpX, _dcY/_bmpY)
        _dc.SetUserScale(_scale, _scale)
        _dc.DrawBitmap(self.canvas.bitmap, 0, 0, False,)
        return True

    def GetPageInfo(self):
        """
        just sets the page to 1 - no flexibility for now
        """
        return (1, 1, 1, 1)


def copy_image_to_clipboard(canvas):
    bmp = wx.BitmapDataObject()
    bmp.SetBitmap(canvas.bitmap)

    wx.TheClipboard.Open()
    wx.TheClipboard.SetData(bmp)
    wx.TheClipboard.Close()


