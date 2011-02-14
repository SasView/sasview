
import wx
import os
from wx import ToolBar as Tbar


from sans.guiframe.gui_style import GUIFRAME_ID
from sans.guiframe.gui_style import GUIFRAME_ICON


def clear_image(image):
    w, h = image.GetSize()
    factor = 155
    compress = lambda x: int(x * factor/255.) + factor
    for y in range(h):
        for x in range(w):
            grey = compress(image.GetGreen(x, y))
            image.SetRGB(x, y, grey, grey, grey)
    if image.HasAlpha():
        image.ConvertAlphaToMask()
    return image

class GUIToolBar(Tbar):
    """
    Implement toolbar for guiframe
    """
    def __init__(self, parent,  *args, **kwds):
        Tbar.__init__(self, parent,  *args, **kwds)
        self.parent = parent
        self.do_layout()
        self.on_bind_button()
       
    def do_layout(self):
        """
        """
        tbar_size = (22, 22)
        button_type =  wx.ITEM_NORMAL
        save_im = GUIFRAME_ICON.SAVE_ICON
        save_im.Rescale(tbar_size[0], tbar_size[1], wx.IMAGE_QUALITY_HIGH)
        save_bmp = save_im.ConvertToBitmap()
        #disable_save_bmp = clear_image(save_im).ConvertToBitmap()
        disable_save_bmp = wx.NullBitmap
        self.AddLabelTool(GUIFRAME_ID.SAVE_ID, 'Save', save_bmp, 
                          disable_save_bmp,button_type, shortHelp='Save')
        self.AddSeparator()
        bookmark_im = GUIFRAME_ICON.BOOKMARK_ICON
        bookmark_im.Rescale(tbar_size[0], tbar_size[1], wx.IMAGE_QUALITY_HIGH)
        bookmark_bmp = bookmark_im.ConvertToBitmap()
        #disable_bookmark_bmp = clear_image(bookmark_im).ConvertToBitmap()
        disable_bookmark_bmp = wx.NullBitmap
        self.AddLabelTool(GUIFRAME_ID.BOOKMARK_ID, 'Bookmark', bookmark_bmp,
                   disable_bookmark_bmp, button_type,'Bookmark')
        self.AddSeparator()
        zoom_in_im = GUIFRAME_ICON.ZOOM_IN_ICON
        zoom_in_im.Rescale(tbar_size[0], tbar_size[1], wx.IMAGE_QUALITY_HIGH)
        zoom_in_bmp = zoom_in_im.ConvertToBitmap()
        #disable_zoom_in_bmp = clear_image(zoom_in_im).ConvertToBitmap()
        disable_zoom_in_bmp = wx.NullBitmap
        self.AddLabelTool(GUIFRAME_ID.ZOOM_IN_ID, 'Zoom In', zoom_in_bmp,
                   disable_zoom_in_bmp, button_type,'Zoom In')
        self.AddSeparator()
        zoom_out_im = GUIFRAME_ICON.ZOOM_OUT_ICON
        zoom_out_im.Rescale(tbar_size[0], tbar_size[1], wx.IMAGE_QUALITY_HIGH)
        zoom_out_bmp = zoom_out_im.ConvertToBitmap()
        #disable_zoom_out_bmp = clear_image(zoom_out_im).ConvertToBitmap()
        disable_zoom_out_bmp = wx.NullBitmap
        self.AddLabelTool(GUIFRAME_ID.ZOOM_OUT_ID, 'Zoom Out', zoom_out_bmp,
                   disable_zoom_out_bmp, button_type,'Zoom Out')
        self.AddSeparator()
        zoom_im = GUIFRAME_ICON.ZOOM_ICON
        zoom_im.Rescale(tbar_size[0], tbar_size[1], wx.IMAGE_QUALITY_HIGH)
        zoom_bmp = zoom_im.ConvertToBitmap()
        #disable_zoom_bmp = clear_image(zoom_im).ConvertToBitmap()
        disable_zoom_bmp = wx.NullBitmap
        self.AddLabelTool(GUIFRAME_ID.ZOOM_ID, 'Zoom', zoom_bmp,
                   disable_zoom_bmp, button_type,'Zoom In')
        self.AddSeparator()
        reset_im = GUIFRAME_ICON.RESET_ICON
        reset_im.Rescale(tbar_size[0], tbar_size[1], wx.IMAGE_QUALITY_HIGH)
        reset_bmp = reset_im.ConvertToBitmap()
        #disable_reset_bmp = clear_image(reset_im).ConvertToBitmap()
        disable_reset_bmp = wx.NullBitmap
        self.AddLabelTool(GUIFRAME_ID.RESET_ID, 'Reset', reset_bmp,
                   disable_reset_bmp, button_type,'Reset In')
        self.AddSeparator()
        drag_im = GUIFRAME_ICON.DRAG_ICON
        drag_im.Rescale(tbar_size[0], tbar_size[1], wx.IMAGE_QUALITY_HIGH)
        drag_bmp = drag_im.ConvertToBitmap()
        #disable_drag_bmp = clear_image(drag_im).ConvertToBitmap()
        disable_drag_bmp = wx.NullBitmap
        self.AddLabelTool(GUIFRAME_ID.DRAG_ID, 'Drag', drag_bmp,
                   disable_drag_bmp, button_type,'Drag')
        self.AddSeparator()
        report_im = GUIFRAME_ICON.REPORT_ICON
        report_im.Rescale(tbar_size[0], tbar_size[1], wx.IMAGE_QUALITY_HIGH)
        report_bmp = report_im.ConvertToBitmap()
        #disable_report_bmp = clear_image(report_im).ConvertToBitmap()
        disable_report_bmp = wx.NullBitmap
        self.AddLabelTool(GUIFRAME_ID.PREVIEW_ID, 'Report', report_bmp,
                   disable_report_bmp, button_type,'Report')
        self.AddSeparator()
        print_im = GUIFRAME_ICON.PRINT_ICON
        print_im.Rescale(tbar_size[0], tbar_size[1], wx.IMAGE_QUALITY_HIGH)
        print_bmp = print_im.ConvertToBitmap()
        #disable_print_bmp = clear_image(print_im).ConvertToBitmap()
        disable_print_bmp = wx.NullBitmap
        self.AddLabelTool(GUIFRAME_ID.PRINT_ID, 'Print', print_bmp,
                          disable_print_bmp, button_type, 'Print')
        self.AddSeparator()
        undo_im = GUIFRAME_ICON.UNDO_ICON
        undo_im.Rescale(tbar_size[0], tbar_size[1], wx.IMAGE_QUALITY_HIGH)
        undo_bmp = undo_im.ConvertToBitmap()
        #disable_undo_bmp = clear_image(undo_im).ConvertToBitmap()
        disable_undo_bmp = wx.NullBitmap
        self.AddLabelTool(GUIFRAME_ID.UNDO_ID, 'Undo', undo_bmp,
                          disable_undo_bmp, button_type,'Undo')
        self.AddSeparator()
        redo_im = GUIFRAME_ICON.REDO_ICON
        redo_im.Rescale(tbar_size[0], tbar_size[1], wx.IMAGE_QUALITY_HIGH)
        redo_bmp = redo_im.ConvertToBitmap()
        #disable_redo_bmp = clear_image(redo_im).ConvertToBitmap()
        disable_redo_bmp = wx.NullBitmap
        self.AddLabelTool(GUIFRAME_ID.REDO_ID, 'Redo', redo_bmp,
                          disable_redo_bmp, button_type,'Redo')
        self.AddSeparator()
        #add button for the current application
        self.button_application = wx.StaticText(self, -1, 'Welcome')
        self.button_application.SetForegroundColour('black')
        self.button_application.SetBackgroundColour('#1874CD')
        hint = 'Active Application'
        self.button_application.SetToolTipString(hint)
        self.AddControl(self.button_application)
        self.AddSeparator()
         #add button for the panel on focus
        self.button_panel = wx.StaticText(self, -1, 'No Panel')
        self.button_panel.SetForegroundColour('black')
        self.button_panel.SetBackgroundColour('#90EE90')
        hint = 'Panel on Focus'
        self.button_panel.SetToolTipString(hint)
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
        
    def update_toolbar(self, panel=None):
        """
        """
        if panel is None:
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
        self.Realize()
        
    def enable_undo(self, panel):
        self.EnableTool(GUIFRAME_ID.PRINT_ID, panel.get_print_flag())
        self.Realize()
        
    def enable_redo(self, panel):
        self.EnableTool(GUIFRAME_ID.REDO_ID, panel.get_redo_flag())
        self.Realize()
        
    def enable_print(self, panel):
        self.EnableTool(GUIFRAME_ID.PRINT_ID, panel.get_print_flag())
        self.Realize()
    
    def enable_zoom(self, panel):
        self.EnableTool(GUIFRAME_ID.ZOOM_ID, panel.get_zoom_flag())
        self.Realize()
        
    def enable_zoom_in(self, panel):
        self.EnableTool(GUIFRAME_ID.ZOOM_IN_ID, panel.get_zoom_in_flag())
        self.Realize()
        
    def enable_zoom_out(self, panel):
        self.EnableTool(GUIFRAME_ID.ZOOM_OUT_ID, panel.get_zoom_out_flag())
        self.Realize()
        
    def enable_bookmark(self, panel):
        self.EnableTool(GUIFRAME_ID.BOOKMARK_ID, panel.get_bookmark_flag())
        self.Realize()
        
    def enable_save(self, panel):
        self.EnableTool(GUIFRAME_ID.SAVE_ID, panel.get_save_flag())
        self.Realize()
        
    def enable_reset(self, panel):
        self.EnableTool(GUIFRAME_ID.RESET_ID, panel.get_reset_flag())
        self.Realize()
    
    def enable_preview(self, panel):
        self.EnableTool(GUIFRAME_ID.PREVIEW_ID, panel.get_preview_flag())
        self.Realize()

              
