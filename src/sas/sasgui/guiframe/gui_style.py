
"""
Provide the style for guiframe
"""
from __future__ import print_function

import wx
import os
from sas.sasgui.guiframe import get_data_path


class GUIFRAME:
    MANAGER_ON = 1
    FLOATING_PANEL = 2
    FIXED_PANEL = 4
    PLOTTING_ON = 8
    DATALOADER_ON = 16
    TOOLBAR_ON = 32
    CALCULATOR_ON = 256
    SINGLE_APPLICATION = 64
    WELCOME_PANEL_ON = 128
    DEFAULT_STYLE = SINGLE_APPLICATION|DATALOADER_ON|PLOTTING_ON|FIXED_PANEL
    MULTIPLE_APPLICATIONS = DEFAULT_STYLE
    
class GUIFRAME_ID:
    UNDO_ID = wx.NewId()
    REDO_ID = wx.NewId()
    COPY_ID = wx.NewId()
    PASTE_ID = wx.NewId()
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
    COPYEX_ID = wx.NewId()
    COPYLAT_ID = wx.NewId()
    COPYAS_ID = wx.NewId()


class GUIFRAME_ICON:
    PATH = get_data_path(media='images')
    FRAME_ICON_PATH = os.path.join(PATH, 'ball.ico')
    SAVE_ICON_PATH = os.path.join(PATH, 'save.png')
    UNDO_ICON_PATH = os.path.join(PATH, 'undo.png')
    REDO_ICON_PATH = os.path.join(PATH, 'redo.png')
    COPY_ICON_PATH = os.path.join(PATH, 'copy.png')
    PASTE_ICON_PATH = os.path.join(PATH, 'paste.png')
    BOOKMARK_ICON_PATH = os.path.join(PATH, 'bookmark.png')
    ZOOM_IN_ID_PATH = os.path.join(PATH, 'zoom_in.png')
    ZOOM_OUT_ID_PATH = os.path.join(PATH, 'zoom_out.png')
    ZOOM_ID_PATH = os.path.join(PATH, 'search_pan.png')
    DRAG_ID_PATH = os.path.join(PATH, 'drag_hand.png')
    RESET_ID_PATH = os.path.join(PATH, 'reset.png')
    REPORT_ID_PATH = os.path.join(PATH, 'report.png')
    PREVIEW_ID_PATH = os.path.join(PATH, 'preview.png')
    PRINT_ID_PATH = os.path.join(PATH, 'printer.png')
    HIDE_ID_PATH = os.path.join(PATH, 'hide.png')
    
    # Note: wx 4 requires that the app be defined before
    # the images are loaded, so they can't be processed
    # at module load time.  Instead, need to load icons
    # when the app is created.
    @classmethod
    def load_icons(cls):
        cls.SAVE_ICON = wx.Image(cls.SAVE_ICON_PATH)
        cls.UNDO_ICON = wx.Image(cls.UNDO_ICON_PATH)
        cls.REDO_ICON = wx.Image(cls.REDO_ICON_PATH)
        cls.COPY_ICON = wx.Image(cls.COPY_ICON_PATH)
        cls.PASTE_ICON = wx.Image(cls.PASTE_ICON_PATH)
        cls.BOOKMARK_ICON = wx.Image(cls.BOOKMARK_ICON_PATH)
        cls.ZOOM_IN_ICON = wx.Image(cls.ZOOM_IN_ID_PATH)
        cls.ZOOM_OUT_ICON = wx.Image(cls.ZOOM_OUT_ID_PATH)
        cls.ZOOM_ICON = wx.Image(cls.ZOOM_ID_PATH)
        cls.DRAG_ICON = wx.Image(cls.DRAG_ID_PATH)
        cls.RESET_ICON = wx.Image(cls.RESET_ID_PATH)
        cls.REPORT_ICON = wx.Image(cls.REPORT_ID_PATH)
        cls.PREVIEW_ICON = wx.Image(cls.PREVIEW_ID_PATH)
        cls.PRINT_ICON = wx.Image(cls.PRINT_ID_PATH)
        cls.HIDE_ICON = wx.Image(cls.HIDE_ID_PATH)

if __name__ == "__main__":
  
    print(GUIFRAME.DEFAULT_STYLE)
    print(GUIFRAME.FLOATING_PANEL)
    print(GUIFRAME.SINGLE_APPLICATION)
    style = GUIFRAME.MULTIPLE_APPLICATIONS
    style &= GUIFRAME.PLOTTING_ON
    print(style == GUIFRAME.PLOTTING_ON)
    style1 = GUIFRAME.MULTIPLE_APPLICATIONS
    style1 &= (~GUIFRAME.MANAGER_ON)
    print(style1 == GUIFRAME.DEFAULT_STYLE)
    print(style1)
