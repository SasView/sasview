import os
import wx

def choose_data_file(parent, location=None):
    path = None
    if location==None:
        location = os.getcwd()
    dlg = wx.FileDialog(parent, "Choose a file", location, "", "*.txt", wx.OPEN)
    if dlg.ShowModal() == wx.ID_OK:
        path = dlg.GetPath()
        mypath = os.path.basename(path)
    dlg.Destroy()
    
    return path


def load_ascii_1D(path):
    """
        Load a 1D ascii file, with errors
    """
        
    if path and os.path.isfile(path):
    
        file_x = []
        file_y = []
        file_dy = []
        
        input_f = open(path,'r')
        buff = input_f.read()
        lines = buff.split('\n')
        for line in lines:
            try:
                toks = line.split()
                x = float(toks[0])
                y = float(toks[1])
                if len(toks)==3:
                    err = float(toks[2])
                else:
                    err = 0.0
                file_x.append(x)
                file_y.append(y)
                file_dy.append(err)
            except:
                print "READ ERROR", line
    
        return file_x, file_y, file_dy
    return None, None, None