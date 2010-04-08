
import wx
import sys
import numpy
import math
import logging

import models
import model_panel
from model_panel import ModelPanel
from sans.guicomm.events import NewPlotEvent, StatusEvent 
from sans.guiframe.dataFitting import Data2D
from sans.guiframe.dataFitting import Theory1D

DEFAULT_BEAM = 0.005
DEFAULT_QMIN = 0.001
DEFAULT_QMAX = 0.13
DEFAULT_NPTS = 50

class PlotInfo:
    """
        store some plotting field
    """
    _xunit = 'A^{-1}'
    _xaxis= "\\rm{Q}"
    _yunit = "cm^{-1}"
    _yaxis= "\\rm{Intensity} "
    id = "Model"
    group_id = "Model"
    title= None
    info= None
    
class Plugin:
    """
        This class defines the interface for a Plugin class
        for calculator perspective
    """
    
    def __init__(self, standalone=True):
        """
            Abstract class for gui_manager Plugins.
        """
        ## Plug-in name. It will appear on the application menu.
        self.sub_menu = "Theory"        
        
        ## Reference to the parent window. Filled by get_panels() below.
        self.parent = None
        
        ## List of panels that you would like to open in AUI windows
        #  for your plug-in. This defines your plug-in "perspective"
        self.perspective = []
        # Log startup
        logging.info("Theory plug-in started")   
        
        #Provide list of models existing in the application
        self.menu_mng = models.ModelManager()
        # reference to the current running thread
        self.calc_2D= None
        self.calc_1D= None
        
    def populate_menu(self, id, owner):
        """
            Create and return the list of application menu
            items for the plug-in. 
            
            @param id: deprecated. Un-used.
            @param parent: parent window
            @return: plug-in menu
        """
        return []
      
    def get_panels(self, parent):
        """
            Create and return the list of wx.Panels for your plug-in.
            Define the plug-in perspective.
            
            Panels should inherit from DefaultPanel defined below,
            or should present the same interface. They must define
            "window_caption" and "window_name".
            
            @param parent: parent window
            @return: list of panels
        """
        ## Save a reference to the parent
        self.parent = parent
        # Define a panel
        self.model_panel= ModelPanel(self.parent, page_info =None,
                model_list_box= self.menu_mng.get_model_list().get_list())
        self.model_panel.set_manager(self)
       
        # If needed, add its name to the perspective list
        self.perspective.append(self.model_panel.window_name)
        self.parent.Bind(model_panel.EVT_MODEL_BOX,self._on_model_panel)
        # Return the list of panels
        return [self.model_panel]
    
    def get_context_menu(self, graph=None):
        """
            This method is optional.
        
            When the context menu of a plot is rendered, the 
            get_context_menu method will be called to give you a 
            chance to add a menu item to the context menu.
            
            A ref to a Graph object is passed so that you can
            investigate the plot content and decide whether you
            need to add items to the context menu.  
            
            This method returns a list of menu items.
            Each item is itself a list defining the text to 
            appear in the menu, a tool-tip help text, and a
            call-back method.
            
            @param graph: the Graph object to which we attach the context menu
            @return: a list of menu items with call-back function
        """
        return []    
    
    def get_perspective(self):
        """
            Get the list of panel names for this perspective
        """
        return self.perspective
    
    def on_perspective(self, event):
        """
            Call back function for the perspective menu item.
            We notify the parent window that the perspective
            has changed.
            @param event: menu event
        """
        self.parent.set_perspective(self.perspective)
    
    def post_init(self):
        """
            Post initialization call back to close the loose ends
        """
        pass
            
    def draw_model(self, model, data= None,smearer= None,
                   enable1D= True, enable2D= False,
                   qmin= DEFAULT_QMIN, qmax= DEFAULT_QMAX, qstep= DEFAULT_NPTS):
        """
             Draw model.
             @param model: the model to draw
             @param name: the name of the model to draw
             @param data: the data on which the model is based to be drawn
             @param description: model's description
             @param enable1D: if true enable drawing model 1D
             @param enable2D: if true enable drawing model 2D
             @param qmin:  Range's minimum value to draw model
             @param qmax:  Range's maximum value to draw model
             @param qstep: number of step to divide the x and y-axis
             
        """
        ## draw model 1D with no loaded data
        self._draw_model1D( model= model, data= data,enable1D=enable1D, smearer= smearer,
                           qmin= qmin, qmax= qmax, qstep= qstep )
        ## draw model 2D with no initial data
        self._draw_model2D(model=model,
                           data = data,
                           enable2D= enable2D,
                           qmin=qmin,
                           qmax=qmax,
                           qstep=qstep)
        
    def _on_model_panel(self, evt):
        """
            react to model selection on any combo box or model menu.plot the model  
            @param evt: wx.combobox event
        """
        model = evt.model
        qmin = evt.qmin
        qmax = evt.qmax
        qstep = evt.qstep
        if model ==None:
            return
        # save model name
        self.draw_model(model=model, qmin=qmin, qmax=qmax, qstep=qstep)
        
    def _draw_model2D(self,model,data=None, enable2D=False,
                      qmin=DEFAULT_QMIN, qmax=DEFAULT_QMAX, qstep=DEFAULT_NPTS):
        """
            draw model in 2D
            @param model: instance of the model to draw
            @param enable2D: when True allows to draw model 2D
            @param qmin: the minimum value to  draw model 2D
            @param qmax: the maximum value to draw model 2D
            @param qstep: the number of division of Qx and Qy of the model to draw
            
        """
        x=  numpy.linspace(start= -1*qmax,
                               stop= qmax,
                               num= qstep,
                               endpoint=True )  
        y = numpy.linspace(start= -1*qmax,
                               stop= qmax,
                               num= qstep,
                               endpoint=True )
         
        ## use data info instead
        if data !=None:
            ## check if data2D to plot
            if hasattr(data, "x_bins"):
                enable2D = True
                x= data.x_bins
                y= data.y_bins

        if not enable2D:
            return
        try:
            from model_thread import Calc2D
            ## If a thread is already started, stop it
            if self.calc_2D != None and self.calc_2D.isrunning():
                self.calc_2D.stop()
            self.calc_2D = Calc2D(  x= x,
                                    y= y,
                                    model= model, 
                                    data = data,
                                    qmin= qmin,
                                    qmax= qmax,
                                    qstep= qstep,
                                    completefn= self._complete2D,
                                    updatefn= self._update2D )
            self.calc_2D.queue()
            
        except:
            raise
            #msg= " Error occurred when drawing %s Model 2D: "%model.name
            #msg+= " %s"%sys.exc_value
            #wx.PostEvent( self.parent, StatusEvent(status= msg ))
            #return  
   
    def _draw_model1D(self, model, data=None, smearer= None,
                qmin=DEFAULT_QMIN, qmax=DEFAULT_QMAX, qstep= DEFAULT_NPTS,
                enable1D= True):
        """
            Draw model 1D from loaded data1D
            @param data: loaded data
            @param model: the model to plot
        """
        x=  numpy.linspace(start= qmin,
                           stop= qmax,
                           num= qstep,
                           endpoint=True
                           )
        if data!=None:
            ## check for data2D
            if hasattr(data,"x_bins"):
                return
            x = data.x
            if qmin == DEFAULT_QMIN :
                qmin = min(data.x)
            if qmax == DEFAULT_QMAX:
                qmax = max(data.x) 
           
        
        if not enable1D:
            return
    
        try:
            from model_thread import Calc1D
            ## If a thread is already started, stop it
            if self.calc_1D!= None and self.calc_1D.isrunning():
                self.calc_1D.stop()
            self.calc_1D= Calc1D( x= x,
                                  data = data,
                                  model= model, 
                                  qmin = qmin,
                                  qmax = qmax,
                                  smearer = smearer,
                                  completefn = self._complete1D,
                                  updatefn = self._update1D  )
            self.calc_1D.queue()
            
        except:
            msg = " Error occurred when drawing %s Model 1D: "%model.name
            msg += " %s"%sys.exc_value
            wx.PostEvent(self.parent, StatusEvent(status=msg))
            
    def _update1D(self,x, output):
        """
            Update the output of plotting model 1D
        """
        wx.PostEvent(self.parent, StatusEvent(status="Plot \
        #updating ... ",type="update"))
        self.ready_fit()
        #self.calc_thread.ready(0.01)
    
    
    def _fill_default_model2D(self, theory, qmax,qstep, qmin=None):
        """
            fill Data2D with default value 
            @param theory: Data2D to fill
        """
        from DataLoader.data_info import Detector, Source
        
        detector = Detector()
        theory.detector.append(detector)         
        theory.source= Source()
        
        ## Default values    
        theory.detector[0].distance= 8000   # mm        
        theory.source.wavelength= 6         # A      
        theory.detector[0].pixel_size.x= 5  # mm
        theory.detector[0].pixel_size.y= 5  # mm
        
        theory.detector[0].beam_center.x= qmax
        theory.detector[0].beam_center.y= qmax
        
        
        ## create x_bins and y_bins of the model 2D
        pixel_width_x = theory.detector[0].pixel_size.x
        pixel_width_y = theory.detector[0].pixel_size.y
        center_x      = theory.detector[0].beam_center.x/pixel_width_x
        center_y      = theory.detector[0].beam_center.y/pixel_width_y

        # theory default: assume the beam center is located at the center of sqr detector
        xmax = qmax
        xmin = -qmax
        ymax = qmax
        ymin = -qmax
        
        x=  numpy.linspace(start= -1*qmax,
                               stop= qmax,
                               num= qstep,
                               endpoint=True )  
        y = numpy.linspace(start= -1*qmax,
                               stop= qmax,
                               num= qstep,
                               endpoint=True )
         
        ## use data info instead
        new_x = numpy.tile(x, (len(y),1))
        new_y = numpy.tile(y, (len(x),1))
        new_y = new_y.swapaxes(0,1)
        
        # all data reuire now in 1d array
        qx_data = new_x.flatten()
        qy_data = new_y.flatten()
        
        q_data = numpy.sqrt(qx_data*qx_data+qy_data*qy_data)
        # set all True (standing for unmasked) as default
        mask    = numpy.ones(len(qx_data), dtype = bool)
        
        # calculate the range of qx and qy: this way, it is a little more independent
        x_size = xmax- xmin
        y_size = ymax -ymin
        
        # store x and y bin centers in q space
        x_bins  = x
        y_bins  = y 
        # bin size: x- & y-directions
        xstep = x_size/len(x_bins-1)
        ystep = y_size/len(y_bins-1)
        
        #theory.data = numpy.zeros(len(mask))
        theory.err_data = numpy.zeros(len(mask))
        theory.qx_data = qx_data 
        theory.qy_data = qy_data  
        theory.q_data = q_data 
        theory.mask = mask            
        theory.x_bins = x_bins  
        theory.y_bins = y_bins   
        
        # max and min taking account of the bin sizes
        theory.xmin= xmin 
        theory.xmax= xmax 
        theory.ymin= ymin
        theory.ymax= ymax 
        theory.group_id ="Model"
        theory.id ="Model"
        
        
    def _get_plotting_info(self, data=None):
        """
            get plotting info from data if data !=None
            else use some default
        """
        my_info = PlotInfo()
        if data !=None:
            if hasattr(data,"info"):
                x_name, x_units = data.get_xaxis() 
                y_name, y_units = data.get_yaxis() 
                
                my_info._xunit = x_units
                my_info._xaxis = x_name
                my_info._yunit = y_units
                my_info._yaxis = y_name
                
            my_info.title= data.name
            if hasattr(data, "info"):
                my_info.info= data.info
            if hasattr(data, "group_id"):
                my_info.group_id= data.group_id
        
        return my_info
                
                
    def _complete1D(self, x,y, elapsed,model,data=None):
        """
            Complete plotting 1D data
        """ 
       
        try:
            new_plot = Theory1D(x=x, y=y)
            my_info = self._get_plotting_info( data)
            new_plot.name = model.name
            new_plot.id = my_info.id
            new_plot.group_id = my_info.group_id
            
            new_plot.xaxis( my_info._xaxis,  my_info._xunit)
            new_plot.yaxis( my_info._yaxis, my_info._yunit)
            if data!=None:
                if new_plot.id == data.id:
                    new_plot.id += "Model"
                new_plot.is_data =False 
           
            # Pass the reset flag to let the plotting event handler
            # know that we are replacing the whole plot
           
            title = "Analytical model 1D "
            if data ==None:
                wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot,
                             title= str(title), reset=True ))
            else:
                wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot,
                             title= str(title)))
            msg = "Plot 1D  complete !"
            wx.PostEvent( self.parent, StatusEvent( status= msg , type="stop" ))
        except:
            msg= " Error occurred when drawing %s Model 1D: "%new_plot.name
            msg+= " %s"%sys.exc_value
            wx.PostEvent( self.parent, StatusEvent(status= msg, type="stop"  ))
            return  
                  
    
        
    def _update2D(self, output,time=None):
        """
            Update the output of plotting model
        """
        wx.PostEvent(self.parent, StatusEvent(status="Plot \
        #updating ... ",type="update"))
        self.ready_fit()
        #self.calc_thread.ready(0.01)
        
        
    def _complete2D(self, image,data, model,  elapsed,qmin, qmax,qstep=DEFAULT_NPTS):
        """
            Complete get the result of modelthread and create model 2D
            that can be plot.
        """
        err_image = numpy.zeros(numpy.shape(image))
       
        theory= Data2D(image= image , err_image= err_image)
        theory.name= model.name

        if data ==None:
            self._fill_default_model2D(theory= theory, qmax=qmax,qstep=qstep, qmin= qmin)
        
        else:
            theory.id= data.id+"Model"
            theory.group_id= data.name+"Model"
            theory.x_bins= data.x_bins
            theory.y_bins= data.y_bins
            theory.detector= data.detector
            theory.source= data.source
            theory.is_data =False 
            theory.qx_data = data.qx_data
            theory.qy_data = data.qy_data
            theory.q_data = data.q_data
            theory.err_data = data.err_data
            theory.mask = data.mask
            ## plot boundaries
            theory.ymin= data.ymin
            theory.ymax= data.ymax
            theory.xmin= data.xmin
            theory.xmax= data.xmax
       
        ## plot
        wx.PostEvent(self.parent, NewPlotEvent(plot=theory,
                         title="Analytical model 2D ", reset=True ))
        msg = "Plot 2D complete !"
        wx.PostEvent( self.parent, StatusEvent( status= msg , type="stop" ))
         
            