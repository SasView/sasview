
import wx
from wx import ToolBar as Tbar

UNDO_ID = wx.NewId()
REDO_ID = wx.NewId()
BOOKMARK_ID = wx.NewId()
SAVE_ID = wx.NewId()
ZOOM_IN_ID = wx.NewId()
ZOOM_OUT_ID = wx.NewId()
ZOOM_ID = wx.NewId()
DRAG_ID = wx.NewId()
RESET_ID = wx.NewId()
PREVIEW_ID = wx.NewId()
PRINT_ID = wx.NewId()
CURRENT_APPLICATION = wx.NewId()

class ToolBar(Tbar):
    def __init__(self, parent,  *args, **kwds):
        Tbar.__init__(self, parent,  *args, **kwds)
        self.parent = parent
        self.do_layout()
        self.on_bind_button()
        
    def do_layout(self):
        """
        """
        tbar_size = (-1,-1)
        save_bmp =  wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE, wx.ART_TOOLBAR,
                                             size=tbar_size)
        self.AddLabelTool(SAVE_ID, 'Save', save_bmp, shortHelp='Save')
       
        bookmark_bmp =  wx.ArtProvider.GetBitmap(wx.ART_ADD_BOOKMARK, wx.ART_TOOLBAR,
                                                 size=tbar_size)
        self.AddLabelTool(BOOKMARK_ID, 'Bookmark', bookmark_bmp,shortHelp='Bookmark')
        
        zoom_in_bmp = wx.ArtProvider.GetBitmap(wx.ART_GO_UP, wx.ART_TOOLBAR,
                                                size=tbar_size)
        self.AddLabelTool(ZOOM_IN_ID, 'Zoom in', zoom_in_bmp,shortHelp='Zoom in')
        
        zoom_out_bmp = wx.ArtProvider.GetBitmap(wx.ART_GO_DOWN, wx.ART_TOOLBAR,
                                                 size=tbar_size)
        self.AddLabelTool(ZOOM_OUT_ID,'Zoom out',zoom_out_bmp,shortHelp='Zoom out')
        
        zoom_bmp =  wx.ArtProvider.GetBitmap(wx.ART_GO_FORWARD, wx.ART_TOOLBAR,
                                             size=tbar_size)
        self.AddLabelTool(ZOOM_ID, 'Zoom', zoom_bmp,shortHelp='Zoom')
        
        drag_bmp =  wx.ArtProvider.GetBitmap(wx.ART_REMOVABLE, wx.ART_TOOLBAR,
                                             size=tbar_size)
        self.AddLabelTool(DRAG_ID, 'Drag', drag_bmp,shortHelp='Drag')
        
        preview_bmp =  wx.ArtProvider.GetBitmap(wx.ART_REPORT_VIEW, wx.ART_TOOLBAR,
                                                size=tbar_size)
        self.AddLabelTool(PREVIEW_ID, 'Preview', preview_bmp,shortHelp='Report')
        
        print_bmp =  wx.ArtProvider.GetBitmap(wx.ART_PRINT, wx.ART_TOOLBAR,
                                              size=tbar_size)
        self.AddLabelTool(PRINT_ID, 'Print', print_bmp,shortHelp='Print')
        
        undo_bmp =  wx.ArtProvider.GetBitmap(wx.ART_UNDO, wx.ART_TOOLBAR,
                                             size=tbar_size)
        self.AddLabelTool(UNDO_ID, 'Undo', undo_bmp,shortHelp='Undo')
        
      
        redo_bmp =  wx.ArtProvider.GetBitmap(wx.ART_REDO, wx.ART_TOOLBAR,
                                             size=tbar_size)
        self.AddLabelTool(REDO_ID, 'Redo', redo_bmp,shortHelp='Redo')
        self.button = wx.Button(self, -1, 'Welcome')
        self.button.SetForegroundColour('black')
        self.button.SetBackgroundColour('#1874CD')
        #self.button.Disable()
        self.AddControl(self.button)
    
        self.SetToolBitmapSize(tbar_size)
        self.Realize()
        
    def on_bind_button(self):
        """
        """
        if self.parent is not None:
            self.parent.Bind(wx.EVT_TOOL, self.parent.on_redo_panel,id=REDO_ID)
            self.parent.Bind(wx.EVT_TOOL, self.parent.on_undo_panel,id=UNDO_ID)
            self.parent.Bind(wx.EVT_TOOL, self.parent.on_bookmark_panel,id=BOOKMARK_ID)
            self.parent.Bind(wx.EVT_TOOL, self.parent.on_save_panel,id=SAVE_ID)
            self.parent.Bind(wx.EVT_TOOL, self.parent.on_zoom_in_panel,id=ZOOM_IN_ID)
            self.parent.Bind(wx.EVT_TOOL, self.parent.on_zoom_out_panel,id=ZOOM_OUT_ID)
            self.parent.Bind(wx.EVT_TOOL, self.parent.on_zoom_panel,id=ZOOM_ID)
            self.parent.Bind(wx.EVT_TOOL, self.parent.on_drag_panel,id=DRAG_ID)
            self.parent.Bind(wx.EVT_TOOL, self.parent.on_reset_panel,id=RESET_ID)
            self.parent.Bind(wx.EVT_TOOL, self.parent.on_preview_panel,id=PREVIEW_ID)
            self.parent.Bind(wx.EVT_TOOL, self.parent.on_print_panel,id=PRINT_ID)
            
            
    def set_active_perspective(self, name='Welcome'):
        """
        """
        print "set button"
        self.button.SetLabel(str(name))
        
    def update_button(self, panel=None):
        """
        """
        if panel is None:
            #self.Disable()
            self.EnableTool(PRINT_ID, False)
            self.EnableTool(UNDO_ID,False)
            self.EnableTool(REDO_ID, False)
            self.EnableTool(ZOOM_ID, False)
            self.EnableTool(ZOOM_IN_ID, False)
            self.EnableTool(ZOOM_OUT_ID, False)
            self.EnableTool(BOOKMARK_ID, False)
            self.EnableTool(PREVIEW_ID, False)
            self.EnableTool(SAVE_ID, False)
            self.EnableTool(DRAG_ID, False)
            self.EnableTool(RESET_ID, False)
        else:
            self.Enable()
            self.EnableTool(PRINT_ID, panel.is_print_enabled())
            self.EnableTool(UNDO_ID, panel.is_undo_enabled())
            self.EnableTool(REDO_ID, panel.is_redo_enabled())
            self.EnableTool(ZOOM_ID, panel.is_zoom_enabled())
            self.EnableTool(ZOOM_IN_ID, panel.is_zoom_in_enabled())
            self.EnableTool(ZOOM_OUT_ID, panel.is_zoom_out_enabled())
            self.EnableTool(BOOKMARK_ID, panel.is_bookmark_enabled())
            self.EnableTool(PREVIEW_ID, panel.is_preview_enabled())
            self.EnableTool(SAVE_ID, panel.is_save_enabled())
            self.EnableTool(DRAG_ID, panel.is_drag_enabled())
            self.EnableTool(RESET_ID, panel.is_reset_enabled())

  

              
