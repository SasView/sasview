
import wx
from wx import ToolBar as Tbar
from sans.guiframe.gui_style import GUIFRAME_ID


class GUIToolBar(Tbar):
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
        self.AddLabelTool(GUIFRAME_ID.SAVE_ID, 'Save', save_bmp, shortHelp='Save')
        self.AddSeparator()
       
        bookmark_bmp =  wx.ArtProvider.GetBitmap(wx.ART_ADD_BOOKMARK, wx.ART_TOOLBAR,
                                                 size=tbar_size)
        self.AddLabelTool(GUIFRAME_ID.BOOKMARK_ID, 'Bookmark', bookmark_bmp,shortHelp='Bookmark')
        self.AddSeparator()
        zoom_in_bmp = wx.ArtProvider.GetBitmap(wx.ART_GO_UP, wx.ART_TOOLBAR,
                                                size=tbar_size)
        self.AddLabelTool(GUIFRAME_ID.ZOOM_IN_ID, 'Zoom in', zoom_in_bmp,shortHelp='Zoom in')
        self.AddSeparator()
        zoom_out_bmp = wx.ArtProvider.GetBitmap(wx.ART_GO_DOWN, wx.ART_TOOLBAR,
                                                 size=tbar_size)
        self.AddLabelTool(GUIFRAME_ID.ZOOM_OUT_ID,'Zoom out',zoom_out_bmp,shortHelp='Zoom out')
        self.AddSeparator()
        zoom_bmp =  wx.ArtProvider.GetBitmap(wx.ART_GO_FORWARD, wx.ART_TOOLBAR,
                                             size=tbar_size)
        self.AddLabelTool(GUIFRAME_ID.ZOOM_ID, 'Zoom', zoom_bmp,shortHelp='Zoom')
        self.AddSeparator()
        drag_bmp =  wx.ArtProvider.GetBitmap(wx.ART_REMOVABLE, wx.ART_TOOLBAR,
                                             size=tbar_size)
        self.AddLabelTool(GUIFRAME_ID.DRAG_ID, 'Drag', drag_bmp,shortHelp='Drag')
        self.AddSeparator()
        preview_bmp =  wx.ArtProvider.GetBitmap(wx.ART_REPORT_VIEW, wx.ART_TOOLBAR,
                                                size=tbar_size)
        self.AddLabelTool(GUIFRAME_ID.PREVIEW_ID, 'Preview', preview_bmp,shortHelp='Report')
        self.AddSeparator()
        print_bmp =  wx.ArtProvider.GetBitmap(wx.ART_PRINT, wx.ART_TOOLBAR,
                                              size=tbar_size)
        self.AddLabelTool(GUIFRAME_ID.PRINT_ID, 'Print', print_bmp,shortHelp='Print')
        self.AddSeparator()
        undo_bmp =  wx.ArtProvider.GetBitmap(wx.ART_UNDO, wx.ART_TOOLBAR,
                                             size=tbar_size)
        self.AddLabelTool(GUIFRAME_ID.UNDO_ID, 'Undo', undo_bmp,shortHelp='Undo')
        self.AddSeparator()
        redo_bmp =  wx.ArtProvider.GetBitmap(wx.ART_REDO, wx.ART_TOOLBAR,
                                             size=tbar_size)
        self.AddLabelTool(GUIFRAME_ID.REDO_ID, 'Redo', redo_bmp,shortHelp='Redo')
        self.AddSeparator()
        #add button for the current application
        self.button_application = wx.StaticText(self, -1, 'Welcome')
        self.button_application.SetForegroundColour('black')
        self.button_application.SetBackgroundColour('#1874CD')
        self.AddControl(self.button_application)
        self.AddSeparator()
         #add button for the panel on focus
        self.button_panel = wx.StaticText(self, -1, 'No Panel')
        self.button_panel.SetForegroundColour('black')
        self.button_panel.SetBackgroundColour('#90EE90')
        self.AddControl(self.button_panel)
    
        self.SetToolBitmapSize(tbar_size)
        self.Realize()
        
    def on_bind_button(self):
        """
        """
        if self.parent is not None:
            self.parent.Bind(wx.EVT_TOOL, self.parent.on_redo_panel,
                             id=GUIFRAME_ID.REDO_ID)
            self.parent.Bind(wx.EVT_TOOL, self.parent.on_undo_panel,
                             id=GUIFRAME_ID.UNDO_ID)
            self.parent.Bind(wx.EVT_TOOL, self.parent.on_bookmark_panel,
                             id=GUIFRAME_ID.BOOKMARK_ID)
            self.parent.Bind(wx.EVT_TOOL, self.parent.on_save_panel,
                             id=GUIFRAME_ID.SAVE_ID)
            self.parent.Bind(wx.EVT_TOOL, self.parent.on_zoom_in_panel,
                             id=GUIFRAME_ID.ZOOM_IN_ID)
            self.parent.Bind(wx.EVT_TOOL, self.parent.on_zoom_out_panel,
                             id=GUIFRAME_ID.ZOOM_OUT_ID)
            self.parent.Bind(wx.EVT_TOOL, self.parent.on_zoom_panel,
                             id=GUIFRAME_ID.ZOOM_ID)
            self.parent.Bind(wx.EVT_TOOL, self.parent.on_drag_panel,
                             id=GUIFRAME_ID.DRAG_ID)
            self.parent.Bind(wx.EVT_TOOL, self.parent.on_reset_panel,
                             id=GUIFRAME_ID.RESET_ID)
            self.parent.Bind(wx.EVT_TOOL, self.parent.on_preview_panel,
                             id=GUIFRAME_ID.PREVIEW_ID)
            self.parent.Bind(wx.EVT_TOOL, self.parent.on_print_panel,
                             id=GUIFRAME_ID.PRINT_ID)
            
    def update_button(self, application_name='', panel_name=''):
        """
        """
        self.button_application.SetLabel(str(application_name))
        self.button_panel.SetLabel(str(panel_name))
        print "update_button", application_name, panel_name
    def update_toolbar(self, panel=None):
        """
        """
        if panel is None:
            #self.Disable()
            self.EnableTool(GUIFRAME_ID.PRINT_ID, False)
            self.EnableTool(GUIFRAME_ID.UNDO_ID,False)
            self.EnableTool(GUIFRAME_ID.REDO_ID, False)
            self.EnableTool(GUIFRAME_ID.ZOOM_ID, False)
            self.EnableTool(GUIFRAME_ID.ZOOM_IN_ID, False)
            self.EnableTool(GUIFRAME_ID.ZOOM_OUT_ID, False)
            self.EnableTool(GUIFRAME_ID.BOOKMARK_ID, False)
            self.EnableTool(GUIFRAME_ID.PREVIEW_ID, False)
            self.EnableTool(GUIFRAME_ID.SAVE_ID, False)
            self.EnableTool(GUIFRAME_ID.DRAG_ID, False)
            self.EnableTool(GUIFRAME_ID.RESET_ID, False)
        else:
            self.Enable()
            self.EnableTool(GUIFRAME_ID.PRINT_ID, panel.get_print_flag())
            self.EnableTool(GUIFRAME_ID.UNDO_ID, panel.get_undo_flag())
            self.EnableTool(GUIFRAME_ID.REDO_ID, panel.get_redo_flag())
            self.EnableTool(GUIFRAME_ID.ZOOM_ID, panel.get_zoom_flag())
            self.EnableTool(GUIFRAME_ID.ZOOM_IN_ID, panel.get_zoom_in_flag())
            self.EnableTool(GUIFRAME_ID.ZOOM_OUT_ID, panel.get_zoom_out_flag())
            self.EnableTool(GUIFRAME_ID.BOOKMARK_ID, panel.get_bookmark_flag())
            self.EnableTool(GUIFRAME_ID.PREVIEW_ID, panel.get_preview_flag())
            self.EnableTool(GUIFRAME_ID.SAVE_ID, panel.get_save_flag())
            self.EnableTool(GUIFRAME_ID.DRAG_ID, panel.get_drag_flag())
            self.EnableTool(GUIFRAME_ID.RESET_ID, panel.get_reset_flag())

  

              
