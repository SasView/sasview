import os, sys,numpy
import wx
from dataFitting import Data1D, Theory1D
from danse.common.plottools.plottables import Data2D
from DataLoader.loader import Loader

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
    if path and os.path.isfile(path):
    
        file_x = numpy.zeros(0)
        file_y = numpy.zeros(0)
        file_dy = numpy.zeros(0)
        file_dx = numpy.zeros(0)
        
        input_f = open(path,'r')
        buff = input_f.read()
        lines = buff.split('\n')
        
        has_dy = False
        has_dx = False
        
        for line in lines:
            try:
                toks = line.split()
                x = float(toks[0])
                y = float(toks[1])
                if len(toks)==3:
                    has_dy = True
                    errdy = float(toks[2])
                else:
                    errdy = 0.0
                if len(toks)==4:
                    has_dx = True
                    errdx = float(toks[3])
                else:
                    errdx = 0.0
                file_x  = numpy.append(file_x, x)
                file_y  = numpy.append(file_y, y)
                file_dy = numpy.append(file_dy, dyerr)
                file_dx = numpy.append(file_dx, dxerr)
            except:
                print "READ ERROR", line
    
        if has_dy==False:
            file_dy = None
        if has_dx==False:
            file_dx = None
            
        return file_x, file_y, file_dy, file_dx
    return None, None, None

def plot_data(parent, path):
    """
        Use the DataLoader loader to created data to plot.
        @param path: the path of the data to load
    """
    from sans.guicomm.events import NewPlotEvent, StatusEvent
    from DataLoader.loader import  Loader
   
    #Instantiate a loader 
    L = Loader()
    
    #Recieves data 
    try:
        output=L.load(path)
        
    except:
        wx.PostEvent(parent, StatusEvent(status="Problem loading file: %s" % sys.exc_value))
        return
    filename = os.path.basename(path)
    
    if not  output.__class__.__name__=="list":
        ## smearing info
        try:
            dxl = output.dxl
            dxw = output.dxw
        except:
            dxl = None
            dxw = None
        ## data 's name
        if output.filename==None:
            output.filename=str(filename)
            
        ## Creating a Data2D with output
        if hasattr(output,'data'):
            temp = output.err_data
            temp[temp==0]=1
            msg= "Loading 2D error bars of value 1 were added to"
            wx.PostEvent(parent, StatusEvent(status=" %s %s"% (msg,output.filename)))
            new_plot = Data2D(image=output.data,err_image=temp,
                              xmin=output.xmin,xmax=output.xmax,
                              ymin=output.ymin,ymax=output.ymax)
            new_plot.x_bins=output.x_bins
            new_plot.y_bins=output.y_bins
            
        ## Creating a pic image2D with output    
        elif hasattr(output,'image'):
            msg= "Transformed an image to plot from"
            wx.PostEvent(parent, StatusEvent(status=" %s %s"% (msg,output.filename)))
            new_plot = Data2D(image=output.image,
                              xmin=output.xmin,xmax=output.xmax,
                              ymin=output.ymin,ymax=output.ymax, pictype = 'image')
            new_plot.x_bins=output.x_bins
            new_plot.y_bins=output.y_bins
            
        ##Creating Data1D with output
        else:
            ##dy values checked
            if output.dy ==None :
                new_plot = Theory1D(output.x,output.y, dxl, dxw)
                
            elif len(output.dy[output.dy==0])==len(output.dy):
                output.dy[output.dy==0]=1 
                msg="Loading 1D error bars of value 1 were added to "
                wx.PostEvent(parent, StatusEvent(status= "%s %s"%(msg, output.filename)))
                new_plot = Theory1D(output.x,output.y,output.dy, dxl, dxw)
            else:
                msg="Loading 1D data: "
                wx.PostEvent(parent, StatusEvent(status= "%s %s"%(msg, output.filename)))
                new_plot = Data1D(x=output.x, y=output.y, dx=output.dx,
                                  dy=output.dy, dxl=dxl, dxw=dxw)
                
        ## source will request in dataLoader .manipulation module
        new_plot.source=output.source
        ## name of the data allow to differentiate data when plotted
        name= output.filename
        
            
        #print "data_name_list",data_name_list
        new_plot.name = name
        ## allow to highlight data when plotted
        new_plot.interactive = True
        ## when 2 data have the same id override the 1 st plotted
        new_plot.id = name
        ## info is a reference to output of dataloader that can be used
        ## to save  data 1D as cansas xml file
        new_plot.info= output
        ## detector used by dataLoader.manipulation module
        new_plot.detector =output.detector
        ## If the data file does not tell us what the axes are, just assume...
        new_plot.xaxis(output._xaxis,output._xunit)
        new_plot.yaxis(output._yaxis,output._yunit)
        ##group_id specify on which panel to plot this data
        new_plot.group_id = name
        ##post data to plot
        wx.PostEvent(parent, NewPlotEvent(plot=new_plot, title=str(name)))
        
    ## the output of the loader is a list , some xml files contain more than one data
    else:
        i=1
        for item in output:
            try:
                dx=item.dx
                dxl=item.dxl
                dxw=item.dxw
            except:
                dx=None
                dxl=None
                dxw=None
                
            if item.dy ==None:
                new_plot = Theory1D(item.x,item.y,dxl,dxw)
            else:
                new_plot = Data1D(x=item.x,y=item.y,dx=dx,dy=item.dy,dxl=dxl,dxw=dxw)
           
            new_plot.source=item.source
            
            name= str(item.run[0])
            
            new_plot.name = name
            new_plot.interactive = True
            new_plot.detector =item.detector
            # If the data file does not tell us what the axes are, just assume...
            new_plot.xaxis(item._xaxis,item._xunit)
            new_plot.yaxis(item._yaxis,item._yunit)
            new_plot.group_id = name
            new_plot.id = name
            new_plot.info= item
            
            if hasattr(item,"title"):
                title= item.title
            else:
                title= name
            wx.PostEvent(parent, NewPlotEvent(plot=new_plot, title=str(title)))
            i+=1
           
            