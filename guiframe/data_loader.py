import os
import wx

def choose_data_file(parent, location=None):
    path = None
    if location==None:
        location = os.getcwd()
       
    dlg = wx.FileDialog(parent, "Choose a file", location, "","*", wx.OPEN)
    if dlg.ShowModal() == wx.ID_OK:
        path = dlg.GetPath()
        mypath = os.path.basename(path)
    dlg.Destroy()
    
    return path


def load_ascii_1D(path):
    """
        Load a 1D ascii file, with errors
    """
    import numpy
    if path and os.path.isfile(path):
    
        file_x = numpy.zeros(0)
        file_y = numpy.zeros(0)
        file_dy = numpy.zeros(0)
        
        input_f = open(path,'r')
        buff = input_f.read()
        lines = buff.split('\n')
        
        has_dy = False
        
        for line in lines:
            try:
                toks = line.split()
                x = float(toks[0])
                y = float(toks[1])
                if len(toks)==3:
                    has_dy = True
                    err = float(toks[2])
                else:
                    err = 0.0
                file_x  = numpy.append(file_x, x)
                file_y  = numpy.append(file_y, y)
                file_dy = numpy.append(file_dy, err)
            except:
                print "READ ERROR", line
    
        if has_dy==False:
            file_dy = None
            
        return file_x, file_y, file_dy
    return None, None, None

def plot_data(parent, path, name="Loaded Data"):
    from sans.guicomm.events import NewPlotEvent
    from sans.guitools.plottables import Data1D, Theory1D
    from DataLoader.loader import  Loader
    #Instantiate a loader 
    L=Loader()
    
    #Recieves data 
    output=L.load(path)
    
    import numpy
    
    if output.dy==None:
        new_plot = Theory1D(output.x, output.y)
    else:
        new_plot = Data1D(output.x, output.y, dy=output.dy)
    new_plot.name = name
    new_plot.interactive = True
    
    # If the data file does not tell us what the axes are, just assume...
    new_plot.xaxis("\\rm{Q}", 'A^{-1}')
    new_plot.yaxis("\\rm{Intensity} ","cm^{-1}")
        
    wx.PostEvent(parent, NewPlotEvent(plot=new_plot, title="Loaded data"))
