
"""
Provide the style for guiframe
"""
import wx

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
    MULTIPLE_APPLICATIONS = DEFAULT_STYLE|MANAGER_ON|WELCOME_PANEL_ON
    
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
    
 
  