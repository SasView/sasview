import os
import wx

def choose_data_file(parent):
    path = None
    dlg = wx.FileDialog(parent, "Choose a file", os.getcwd(), "", "*.txt", wx.OPEN)
    if dlg.ShowModal() == wx.ID_OK:
        path = dlg.GetPath()
        mypath = os.path.basename(path)
    dlg.Destroy()
    
    return path