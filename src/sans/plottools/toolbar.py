"""
    This module overwrites matplotlib toolbar
"""
import wx
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg

class NavigationToolBar(NavigationToolbar2WxAgg):
    """
    Overwrite matplotlib toolbar
    """
    def __init__(self, canvas, parent=None):
        NavigationToolbar2WxAgg.__init__(self, canvas)
        #the panel using this toolbar
        self.parent = parent
        #save canvas
        self.canvas = canvas
        #remove some icones
        self.delete_option()
        #add more icone
        self.add_option()
       
    def delete_option(self):
        """
        remove default toolbar item
        """
        #delte reset button
        self.DeleteToolByPos(0)
        #delete unwanted button that configures subplot parameters
        self.DeleteToolByPos(5)
        
    def add_option(self):
        """
        add item to the toolbar
        """
        #add print button
        id_context = wx.NewId()
        context_tip = 'Graph Menu: \n'
        context_tip += '    For more menu options, \n'
        context_tip += '    right-click the data symbols.'
        context = wx.ArtProvider.GetBitmap(wx.ART_LIST_VIEW, wx.ART_TOOLBAR)
        self.InsertSimpleTool(0, id_context, context,
                                   context_tip, context_tip)
        wx.EVT_TOOL(self, id_context, self.on_menu)
        self.InsertSeparator(1)
        
        id_print = wx.NewId()
        print_bmp = wx.ArtProvider.GetBitmap(wx.ART_PRINT, wx.ART_TOOLBAR)
        self.AddSimpleTool(id_print, print_bmp,
                           'Print', 'Activate printing')
        wx.EVT_TOOL(self, id_print, self.on_print)
        #add reset button
        id_reset = wx.NewId()
        reset_bmp = wx.ArtProvider.GetBitmap(wx.ART_GO_HOME, wx.ART_TOOLBAR)
        self.AddSimpleTool(id_reset, reset_bmp,
                           'Reset Graph Range', 'Reset graph range')
        wx.EVT_TOOL(self, id_reset, self.on_reset)
        
    def on_menu(self, event):
        """
        activate reset
        """
        try:
            self.parent.onToolContextMenu(event=event)
        except:
            pass
        
    def on_reset(self, event):
        """
        activate reset
        """
        try:
            self.parent.onResetGraph(event=event)
        except:
            pass
        
    def on_print(self, event):
        """
        activate print
        """
        try:
            self.canvas.Printer_Print(event=event)
        except:
            pass
        