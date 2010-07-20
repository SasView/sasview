
import os, sys,numpy
import wx
import re

from dataFitting import Data1D
from dataFitting import Data2D
from DataLoader.loader import Loader
from load_thread import DataReader

from sans.guicomm.events import StatusEvent
from sans.guicomm.events import  NewStoreDataEvent
from sans.guicomm.events import NewPlotEvent


def enable_add_data(existing_panel, new_plot):
    """
    Enable append data on a plot panel
    """
    is_theory = len(existing_panel.plots)<= 1 and \
        existing_panel.plots.values()[0].__class__.__name__=="Theory1D"
        
    is_data2d = hasattr(new_plot, 'data')
    is_data1d = existing_panel.__class__.__name__ == "ModelPanel1D"\
        and existing_panel.group_id is not None
   
    return is_data1d and not is_data2d and not is_theory

def parse_name(name, expression):
    """
    remove "_" in front of a name
    """
    if re.match(expression, name) is not None:
        word = re.split(expression, name, 1)
        for item in word:           
            if item.lstrip().rstrip() != '':
                return item
    else:
        return name
    
def choose_data_file(parent, location=None):
    """
    return a list of file path to read
    """
    path = None
    if location == None:
        location = os.getcwd()
    
    l = Loader()
    cards = l.get_wildcards()
    wlist = '|'.join(cards)
    
    dlg = wx.FileDialog(parent, "Choose a file", location, "", wlist,
                        style=wx.OPEN|wx.MULTIPLE|wx.CHANGE_DIR)
    if dlg.ShowModal() == wx.ID_OK:
        path = dlg.GetPaths()
        if path:
            mypath = os.path.basename(path[0])
    dlg.Destroy()
   
    return path

def choose_data_folder(parent, location=None):
    """
    return a list of folder to read
    """
    path = None
    if location == None:
        location = os.getcwd()
    
    l = Loader()
    cards = l.get_wildcards()
    wlist = '|'.join(cards)
    
    dlg = wx.DirDialog(parent, "Choose a directory", location,
                        style=wx.DD_DEFAULT_STYLE)
    if dlg.ShowModal() == wx.ID_OK:
        path = dlg.GetPath()
        mypath = os.path.basename(path)
    dlg.Destroy()
    
    return [path]

def open_dialog_append_data(panel_name, data_name):
    """
    Pop up an error message.
    
    :param panel_name: the name of the current panel
    :param data_name: the name of the current data
    
    """
    message = " Do you want to append %s data\n in "%(str(data_name))
    message += " %s panel?\n\n"%(str(panel_name))
    dial = wx.MessageDialog(None, message, 'Question',
                       wx.YES_NO|wx.NO_DEFAULT|wx.ICON_QUESTION)
    if dial.ShowModal() == wx.ID_YES:
        return True
    else:
        return False


def load_error(error=None):
    """
    Pop up an error message.
    
    :param error: details error message to be displayed
    """
    message = "You had to try this, didn't you?\n\n"
    message += "The data file you selected could not be loaded.\n"
    message += "Make sure the content of your file is properly formatted.\n\n"
    
    if error is not None:
        message += "When contacting the DANSE team, mention the following:\n%s" % str(error)
    
    dial = wx.MessageDialog(None, message, 'Error Loading File', wx.OK | wx.ICON_EXCLAMATION)
    dial.ShowModal()    

def on_load_error(parent):
    """
    """
    wx.PostEvent(parent, StatusEvent(status="Load cancel..", info="warning",
                                                type="stop"))
    


def read_data(parent, path):
    """
    Create a list of data to read
    """
    list = []
    if path is not None and len(path) > 0:
        for p in path:
            if os.path.isdir(p):
               list = [os.path.join(os.path.abspath(p), file) for file in os.listdir(p) ]
              
            if os.path.isfile(p):
               list.append(p)
               
    return plot_data(parent, numpy.array(list))
    
def load_helper(parent , output, path):
    """
    """
    filename = os.path.basename(path)
    #print output.process
    if not  output.__class__.__name__ == "list":
        ## Creating a Data2D with output
        if hasattr(output,'data'):
            msg = "Loading 2D data: %s "%output.filename
            wx.PostEvent(parent, StatusEvent(status=msg, info="info", type="stop"))
            new_plot = Data2D(image=None, err_image=None)
      
        else:
            msg = "Loading 1D data: %s "%output.filename
            wx.PostEvent(parent, StatusEvent(status=msg, info="info", type="stop"))
            new_plot = Data1D(x=[], y=[], dx=None, dy=None)
            
        new_plot.copy_from_datainfo(output) 
        output.clone_without_data(clone=new_plot)      
      
        ## data 's name
        if output.filename is None or output.filename == "":
            output.filename = str(filename)
        ## name of the data allow to differentiate data when plotted
        name = parse_name(name=output.filename, expression="_")
        if not name in parent.indice_load_data.keys():
            parent.indice_load_data[name] = 0
        else:
            ## create a copy of the loaded data
            parent.indice_load_data[name] += 1
            name = name +"[%i]"%parent.indice_load_data[name]
       
        new_plot.name = name
        ## allow to highlight data when plotted
        new_plot.interactive = True
        ## when 2 data have the same id override the 1 st plotted
        new_plot.id = name
        ##group_id specify on which panel to plot this data
        new_plot.group_id = name
        new_plot.is_data = True
        ##post data to plot
        title = output.filename
        if hasattr(new_plot,"title"):
            title = str(new_plot.title.lstrip().rstrip())
            if title == "":
                title = str(name)
        else:
            title = str(name)
        if hasattr(parent, "panel_on_focus") and not(parent.panel_on_focus is None):
                existing_panel  = parent.panel_on_focus
                panel_name = existing_panel.window_caption
                data_name = new_plot.name
                if enable_add_data(existing_panel, new_plot):
                    if open_dialog_append_data(panel_name, data_name):
                        #add this plot the an existing panel
                        new_plot.group_id = existing_panel.group_id
        return [(new_plot, path)]
        #wx.PostEvent(parent, NewStoreDataEvent(data=new_plot))
        
    ## the output of the loader is a list , some xml files contain more than one data
    else:
        i=1
        temp=[]
        for item in output:
            msg = "Loading 1D data: %s "%str(item.run[0])
            wx.PostEvent(parent, StatusEvent(status=msg, info="info", type="stop"))
            try:
                dx = item.dx
                dxl = item.dxl
                dxw = item.dxw
            except:
                dx = None
                dxl = None
                dxw = None

            new_plot = Data1D(x=item.x,y=item.y,dx=dx,dy=item.dy)
            new_plot.copy_from_datainfo(item)
            item.clone_without_data(clone=new_plot)
            new_plot.dxl = dxl
            new_plot.dxw = dxw
           
            name = parse_name(name=str(item.run[0]), expression="_")
            if not name in parent.indice_load_data.keys():
                parent.indice_load_data[name] = 0
            else:
                ## create a copy of the loaded data
                
                #TODO: this is a very annoying feature. We should make this
                # an option. Excel doesn't do this. Why should we?
                # What is the requirement for this feature, and are the
                # counter arguments stronger? Is this feature developed
                # to please at least 80% of the users or a special few?
                parent.indice_load_data[name] += 1
                name = name + "(copy %i)"%parent.indice_load_data[name]
                
            new_plot.name = name
            new_plot.interactive = True
            new_plot.group_id = name
            new_plot.id = name
            new_plot.is_data = True
        
            if hasattr(item,"title"):
                title = item.title.lstrip().rstrip()
                if title == "":
                    title = str(name)
            else:
                title = name
            if hasattr(parent, "panel_on_focus") and not(parent.panel_on_focus is None):
                existing_panel  = parent.panel_on_focus
                panel_name = existing_panel.window_caption
                data_name = new_plot.name
                if enable_add_data(existing_panel, new_plot):
                    if open_dialog_append_data(panel_name, data_name):
                        #add this plot the an existing panel
                        new_plot.group_id = existing_panel.group_id
            temp.append((new_plot, path))
            #wx.PostEvent(parent, NewStoreDataEvent(data=new_plot))
            i+=1
        return temp
    
    
def plot_data(parent, path):
    """
    Use the DataLoader loader to created data to plot.
    
    :param path: the path of the data to load
    
    """
    from sans.guicomm.events import NewPlotEvent, StatusEvent
    from DataLoader.loader import  Loader
   
    # Instantiate a loader 
    L = Loader()
    
    # Load data 
    msg = ""
    list_of_data = []
    for p in path:
        try:
            list_of_data.append((L.load(p), p))
        except:
            p_msg = "Loading... " + str(sys.exc_value)
            wx.PostEvent(parent, StatusEvent(status=p_msg, info="warning"))
            msg += (str(sys.exc_value)+"\n")
    if msg.lstrip().rstrip() != "":
        load_error(msg)
        
    #output = map(L.load, path)
   
    # Notify user if the loader completed the load but no data came out
    if len(list_of_data) == 0 or numpy.array(list_of_data).all() is None:
        load_error("The data file appears to be empty.")
        msg = "Loading complete: %s"%output.filename
        wx.PostEvent(parent, StatusEvent(status=msg, info="warning", type="stop"))
        return
    result =[]
    for output , path in list_of_data:
        result += load_helper(parent=parent, output=output, path=path)
    msg = "Loading complete: %s"%output.filename
    wx.PostEvent(parent, StatusEvent(status=msg, info="info", type="stop"))
    return result
    
    
def old_plot_data(parent, path):
    """
    Use the DataLoader loader to created data to plot.
    
    :param path: the path of the data to load
    
    """
    from sans.guicomm.events import NewPlotEvent, StatusEvent
    from DataLoader.loader import  Loader
   
    # Instantiate a loader 
    L = Loader()
    
    # Load data 
    try:
        output = L.load(path)
    except:
        raise
        #load_error(sys.exc_value)
        return
    
    # Notify user if the loader completed the load but no data came out
    if output == None:
        load_error("The data file appears to be empty.")
        return
  
     
    filename = os.path.basename(path)
    
    if not  output.__class__.__name__ == "list":
        ## Creating a Data2D with output
        if hasattr(output,'data'):
            msg = "Loading 2D data: %s"%output.filename
            wx.PostEvent(parent, StatusEvent(status=msg, info="info", type="stop"))
            new_plot = Data2D(image=None, err_image=None)
      
        else:
            msg = "Loading 1D data: %s"%output.filename
            wx.PostEvent(parent, StatusEvent(status=msg, info="info", type="stop"))
            new_plot = Data1D(x=[], y=[], dx=None, dy=None)
            
        new_plot.copy_from_datainfo(output) 
        output.clone_without_data(clone=new_plot)      
      
        ## data 's name
        if output.filename is None or output.filename == "":
            output.filename = str(filename)
        ## name of the data allow to differentiate data when plotted
        name = parse_name(name=output.filename, expression="_")
        if not name in parent.indice_load_data.keys():
            parent.indice_load_data[name] = 0
        else:
            ## create a copy of the loaded data
            parent.indice_load_data[name] += 1
            name = name +"[%i]"%parent.indice_load_data[name]
       
        new_plot.name = name
        ## allow to highlight data when plotted
        new_plot.interactive = True
        ## when 2 data have the same id override the 1 st plotted
        new_plot.id = name
        ##group_id specify on which panel to plot this data
        new_plot.group_id = name
        new_plot.is_data = True
        ##post data to plot
        title = output.filename
        if hasattr(new_plot,"title"):
            title = str(new_plot.title.lstrip().rstrip())
            if title == "":
                title = str(name)
        else:
            title = str(name)
        if hasattr(parent, "panel_on_focus") and not(parent.panel_on_focus is None):
                existing_panel  = parent.panel_on_focus
                panel_name = existing_panel.window_caption
                data_name = new_plot.name
                if enable_add_data(existing_panel, new_plot):
                    if open_dialog_append_data(panel_name, data_name):
                        #add this plot the an existing panel
                        new_plot.group_id = existing_panel.group_id
        wx.PostEvent(parent, NewPlotEvent(plot=new_plot, title=title))
        
    ## the output of the loader is a list , some xml files contain more than one data
    else:
        i=1
        for item in output:
            msg = "Loading 1D data: %s"%str(item.run[0])
            wx.PostEvent(parent, StatusEvent(status=msg, info="info", type="stop"))
            try:
                dx = item.dx
                dxl = item.dxl
                dxw = item.dxw
            except:
                dx = None
                dxl = None
                dxw = None

            new_plot = Data1D(x=item.x,y=item.y,dx=dx,dy=item.dy)
            new_plot.copy_from_datainfo(item)
            item.clone_without_data(clone=new_plot)
            new_plot.dxl = dxl
            new_plot.dxw = dxw
           
            name = parse_name(name=str(item.run[0]), expression="_")
            if not name in parent.indice_load_data.keys():
                parent.indice_load_data[name] = 0
            else:
                ## create a copy of the loaded data
                
                #TODO: this is a very annoying feature. We should make this
                # an option. Excel doesn't do this. Why should we?
                # What is the requirement for this feature, and are the
                # counter arguments stronger? Is this feature developed
                # to please at least 80% of the users or a special few?
                parent.indice_load_data[name] += 1
                name = name + "(copy %i)"%parent.indice_load_data[name]
                
            new_plot.name = name
            new_plot.interactive = True
            new_plot.group_id = name
            new_plot.id = name
            new_plot.is_data = True
        
            if hasattr(item,"title"):
                title = item.title.lstrip().rstrip()
                if title == "":
                    title = str(name)
            else:
                title = name
            if hasattr(parent, "panel_on_focus") and not(parent.panel_on_focus is None):
                existing_panel  = parent.panel_on_focus
                panel_name = existing_panel.window_caption
                data_name = new_plot.name
                if enable_add_data(existing_panel, new_plot):
                    if open_dialog_append_data(panel_name, data_name):
                        #add this plot the an existing panel
                        new_plot.group_id = existing_panel.group_id
            wx.PostEvent(parent, NewPlotEvent(plot=new_plot, title=str(title)))
            i+=1
  