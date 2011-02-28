
"""
Provide the style for guiframe
"""
import wx
import os
from sans.guiframe import get_data_path


class GUIFRAME:
    MANAGER_ON = 1
    FLOATING_PANEL = 2
    FIXED_PANEL = 4
    PLOTTING_ON = 8
    DATALOADER_ON = 16
    TOOL_ON = 32
    SINGLE_APPLICATION = 64
    WELCOME_PANEL_ON = 128
    DEFAULT_STYLE = SINGLE_APPLICATION|DATALOADER_ON|PLOTTING_ON|FIXED_PANEL
    MULTIPLE_APPLICATIONS = DEFAULT_STYLE|WELCOME_PANEL_ON
    
class GUIFRAME_ID:
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
    CURVE_SYMBOL_NUM = 13
    
class GUIFRAME_ICON:
    PATH = get_data_path(media='images')
    SAVE_ICON_PATH = os.path.join(PATH, 'save.png')
    UNDO_ICON_PATH = os.path.join(PATH, 'undo.png')
    REDO_ICON_PATH = os.path.join(PATH, 'redo.png')
    BOOKMARK_ICON_PATH = os.path.join(PATH, 'bookmark.png')
    ZOOM_IN_ID_PATH = os.path.join(PATH, 'zoom_in.png')
    ZOOM_OUT_ID_PATH = os.path.join(PATH, 'zoom_out.png')
    ZOOM_ID_PATH = os.path.join(PATH, 'search_pan.png')
    DRAG_ID_PATH = os.path.join(PATH, 'drag_hand.png')
    RESET_ID_PATH = os.path.join(PATH, 'reset.png')
    PREVIEW_ID_PATH = os.path.join(PATH, 'report.png')
    PRINT_ID_PATH = os.path.join(PATH, 'printer.png')
    
    SAVE_ICON = wx.Image(os.path.join(PATH, 'save.png'))
    UNDO_ICON = wx.Image(os.path.join(PATH, 'undo.png'))
    REDO_ICON = wx.Image(os.path.join(PATH, 'redo.png'))
    BOOKMARK_ICON = wx.Image(os.path.join(PATH, 'bookmark.png'))
    ZOOM_IN_ICON = wx.Image(os.path.join(PATH, 'zoom_in.png'))
    ZOOM_OUT_ICON = wx.Image(os.path.join(PATH, 'zoom_out.png'))
    ZOOM_ICON = wx.Image(os.path.join(PATH, 'search_pan.png'))
    DRAG_ICON = wx.Image(os.path.join(PATH, 'drag_hand.png'))
    RESET_ICON = wx.Image(os.path.join(PATH, 'reset.png'))
    REPORT_ICON = wx.Image(os.path.join(PATH, 'report.png'))
    PREVIEW_ICON = wx.Image(os.path.join(PATH, 'preview.png'))
    PRINT_ICON = wx.Image(os.path.join(PATH, 'printer.png'))

if __name__ == "__main__":
  
    print GUIFRAME.DEFAULT_STYLE
    print GUIFRAME.FLOATING_PANEL
    print GUIFRAME.SINGLE_APPLICATION
    style = GUIFRAME.MULTIPLE_APPLICATIONS
    style &= GUIFRAME.PLOTTING_ON
    print style == GUIFRAME.PLOTTING_ON
    style1 = GUIFRAME.MULTIPLE_APPLICATIONS
    style1 &= (~GUIFRAME.MANAGER_ON)
    print style1 == GUIFRAME.DEFAULT_STYLE
    print style1
    
 
  