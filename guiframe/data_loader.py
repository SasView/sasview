import os, sys
import wx
from danse.common.plottools.plottables import Data1D, Theory1D, Data2D
from DataLoader.loader import Loader
class MetaData1D(Data1D):
    def __init__(self, output):
        self.datainfo = output
        Data1D.__init__(self,x=output.x, y=output.y, dy=output.dy)
        
class MetaTheory1D(Theory1D):
    def __init__(self, output):
        self.datainfo = output
        Theory1D.__init__(self, x=output.x, y=output.y)
        

class MetaData2D(Data2D):
    def __init__(self, output):
        self.datainfo = output
        Data2D.__init__(self,image= output.data,err_image=output.err_data,
                       xmin=output.xmin,xmax=output.xmax,ymin=output.ymin,ymax=output.ymax)
class MetaTheory2D(Data2D):
    def __init__(self, output):
        self.datainfo = output
        Data2D.__init__(self,image= output.data,err_image=output.err_data,
                       xmin=output.xmin,xmax=output.xmax,ymin=output.ymin,ymax=output.ymax)
        
        
    
def choose_data_file(parent, location=None):
    path = None
    if location==None:
        location = os.getcwd()
    
    l = Loader()
    cards = l.get_wildcards()
    wlist = '|'.join(cards)
    
    dlg = wx.FileDialog(parent, "Choose a file", location, "", wlist, wx.OPEN)
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
    from sans.guicomm.events import NewPlotEvent, StatusEvent
   
    from DataLoader.loader import  Loader
    import numpy
    #Instantiate a loader 
    L=Loader()
    
    #Recieves data 
    try:
        output=L.load(path)
    except:
        wx.PostEvent(parent, StatusEvent(status="Problem loading file: %s" % sys.exc_value))
        return
    if hasattr(output,'data'):
        new_plot = MetaData2D(output)
        new_plot.x_bins=output.x_bins
        new_plot.y_bins=output.y_bins
    else:
        if output.dy==None:
            new_plot = MetaTheory1D(output)
        else:
            new_plot = MetaData1D(output)
        
    filename = os.path.basename(path)
        
    new_plot.name = name
    new_plot.interactive = True
    # If the data file does not tell us what the axes are, just assume...
    new_plot.xaxis("\\rm{Q}",'A^{-1}')
    new_plot.yaxis("\\rm{Intensity} ","cm^{-1}")
    new_plot.group_id = filename
       
    wx.PostEvent(parent, NewPlotEvent(plot=new_plot, title=filename))
