#TODO: the line slicer should listen to all 2DREFRESH events, get the data and slice it
#      before pushing a new 1D data update.

#
#TODO: NEED MAJOR REFACTOR
#


# Debug printout
from config import printEVT
from BaseInteractor import _BaseInteractor
from copy import deepcopy
import math

from Plotter1D import AddPlotEvent
import SlicerParameters
import wx

class AnnulusInteractor(_BaseInteractor):
    """
         Select an annulus through a 2D plot
    """
    def __init__(self,base,axes,color='black', zorder=3, x_min=0.025, x_max=0.025, y_min=0.025, y_max=0.025):
        
        _BaseInteractor.__init__(self, base, axes, color=color)
        self.markers = []
        self.axes = axes
        self.qmax = self.base.qmax
        self.connect = self.base.connect
        self.xmin=xmin
        self.ymin=ymin
        self.xmax=xmax
        self.ymax=ymax
        ## Number of points on the plot
        self.nbins = 20
        
        #self.theta3= 2*self.theta2 -self.theta1
        # Inner circle
        self.left_line = VerticalLine(self, self.base.subplot,color='blue', zorder=zorder, 
                                        ymin=-1*self.ymin, ymax=self.ymax,
                                        xmin=-1*self.xmin,xmax=-1*self.xmax)
        self.left_line.qmax = self.base.qmax
        
        self.right_line= VerticalLine(self, self.base.subplot,color='black', zorder=zorder,
                                     ymin=-1*self.ymin, ymax=self.ymax,
                                     xmin=self.xmin,xmax=self.xmax)
        self.right_line.qmax = self.base.qmax
        
        self.top_line= HorizontalLine(self, self.base.subplot,color='green', zorder=zorder,
                                    ymin=self.ymax, ymax=self.ymax,
                                    xmin=-1*self.xmax,xmax=self.xmax)
        self.top_line.qmax = self.base.qmax
        
        self.bottom_line= HorizontalLine(self, self.base.subplot,color='red', zorder=zorder,
                                    ymin=-1*self.ymin, ymax=-1*self.ymin,
                                    xmin=-1*self.xmin,xmax=self.xmin)
        self.bottom_line.qmax = self.base.qmax
        #self.outer_circle.set_cursor(self.base.qmax/1.8, 0)
        
                      
        #self.update()
        self._post_data()
        
        # Bind to slice parameter events
        self.base.parent.Bind(SlicerParameters.EVT_SLICER_PARS, self._onEVT_SLICER_PARS)


    def _onEVT_SLICER_PARS(self, event):
        printEVT("AnnulusSlicer._onEVT_SLICER_PARS")
        event.Skip()
        if event.type == self.__class__.__name__:
            #self.set_params(event.params)
            self.base.update()

    def update_and_post(self):
        self.update()
        self._post_data()

    def save_data(self, path, image, x, y):
        output = open(path, 'w')
        
        data_x, data_y = self.get_data(image, x, y)
        
        output.write("<phi>  <average>\n")
        for i in range(len(data_x)):
            output.write("%g  %g\n" % (data_x[i], data_y[i]))
        output.close()

    def set_layer(self, n):
        self.layernum = n
        self.update()
        
    def clear(self):
        self.clear_markers()
        self.outer_circle.clear()
        self.inner_circle.clear()
        #self.base.connect.disconnect()
        self.base.parent.Unbind(SlicerParameters.EVT_SLICER_PARS)
        
    def update(self):
        """
        Respond to changes in the model by recalculating the profiles and
        resetting the widgets.
        """
        if self.left_line.has_move:
            print "left has moved"
            self.left_line.update()
            self.right_line.update()
            #self.right_line.update(xmin= self.left_line.x ,xmax=-1*self.left_line.x)
            self.top_line.update( xmin= self.left_line.x ,xmax= self.right_line.x)
            self.bottom_line.update(xmin= self.left_line.x ,xmax= self.right_line.x)
        if self.right_line.has_move:
            print "right has moved"
            self.right_line.update()
            self.left_line.update()
            #self.left_line.update(xmin= self.right_line.x ,xmax=-1*self.right_line.x)
            self.top_line.update( xmin= self.left_line.x ,xmax= self.right_line.x)
            self.bottom_line.update(xmin= self.left_line.x ,xmax= self.right_line.x)
            
            
        if self.bottom_line.has_move:
            print "bottom has moved"
            self.bottom_line.update()
            self.top_line.update()
            #self.top_line.update(ymin= -1*self.bottom_line.y ,ymax=-1*self.bottom_line.y)
            self.left_line.update( ymin= self.bottom_line.y ,ymax= self.top_line.y)
            self.right_line.update(ymin= self.bottom_line.y ,ymax= self.top_line.y)
            
        if self.top_line.has_move:
            print "top has moved"
            self.top_line.update()
            #self.bottom_line.update()
            self.bottom_line.update(ymin= -1*self.top_line.y ,ymax=-1*self.top_line.y)
            self.left_line.update(ymin= self.bottom_line.y ,ymax= self.top_line.y)
            self.right_line.update(ymin= self.bottom_line.y ,ymax= self.top_line.y)
            
    def get_data(self, image, x, y):
        """ 
            Return a 1D vector corresponding to the slice
            @param image: data matrix
            @param x: x matrix
            @param y: y matrix
        """
        # If we have no data, just return
        if image == None:
            return        
        
        nbins = self.nbins
        
        data_x = nbins*[0]
        data_y = nbins*[0]
        counts = nbins*[0]
        length = len(image)
        print "length x , y , image", len(x), len(y), length
        
        for i_x in range(length):
            for i_y in range(length):
                        
                q = math.sqrt(x[i_x]*x[i_x] + y[i_y]*y[i_y])
                if (q>self.inner_circle._inner_mouse_x \
                    and q<self.outer_circle._inner_mouse_x) \
                    or (q<self.inner_circle._inner_mouse_x \
                    and q>self.outer_circle._inner_mouse_x):
                            
                    i_bin = int(math.ceil(nbins*(math.atan2(y[i_y], x[i_x])+math.pi)/(2.0*math.pi)) - 1)
                    
                    
                    #data_y[i_bin] += math.exp(image[i_x][i_y])
                    data_y[i_bin] += image[i_y][i_x]
                    counts[i_bin] += 1.0
                    
        for i in range(nbins):
            data_x[i] = (1.0*i+0.5)*2.0*math.pi/nbins
            if counts[i]>0:
                data_y[i] = data_y[i]/counts[i]
        
        return data_x, data_y

    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self.base.freeze_axes()
        self.inner_circle.save(ev)
        self.outer_circle.save(ev)

    def _post_data(self):
        # Compute data
        data = self.base.get_corrected_data()
        # If we have no data, just return
        if data == None:
            return

        data_x, data_y = self.get_data(data, self.base.x, self.base.y)
        
        name = "Ring"
        if hasattr(self.base, "name"):
            name += " %s" % self.base.name
        
        wx.PostEvent(self.base.parent, AddPlotEvent(name=name,
                                               x = data_x,
                                               y = data_y,
                                               qmin = self.inner_circle._inner_mouse_x,
                                               qmax = self.outer_circle._inner_mouse_x,
                                               yscale = 'log',
                                               variable = 'ANGLE',
                                               ylabel = "\\rm{Intensity} ",
                                               yunits = "cm^{-1}",
                                               xlabel = "\\rm{\phi}",
                                               xunits = "rad",
                                               parent = self.base.__class__.__name__))
                                               
        
    def moveend(self, ev):
        self.base.thaw_axes()
        
        # Post paramters
        event = SlicerParameters.SlicerParameterEvent()
        event.type = self.__class__.__name__
        #event.params = self.get_params()
        wx.PostEvent(self.base.parent, event)

        self._post_data()
            
    def restore(self):
        """
        Restore the roughness for this layer.
        """
        self.inner_circle.restore()
        self.outer_circle.restore()

    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        pass
        
    def set_cursor(self, x, y):
        pass
        
    def get_params(self):
        params = {}
        #params["main_phi"] = self.right_line.get_radius()
        #params["left_phi"] = self.left_line.get_radius()
        
        params["nbins"] = self.nbins
        return params
    
    def set_params(self, params):
        
        main = params["main_phi"] 
        left = params["left_phi"] 
       
        self.nbins = int(params["nbins"])
        #self.main_line.set_cursor(inner, self.inner_circle._inner_mouse_y)
        #self.outer_circle.set_cursor(outer, self.outer_circle._inner_mouse_y)
        self._post_data()
        
    def freeze_axes(self):
        self.base.freeze_axes()
        
    def thaw_axes(self):
        self.base.thaw_axes()

    def draw(self):
        self.base.draw()

class HorizontalLine(_BaseInteractor):
    """
         Select an annulus through a 2D plot
    """
    def __init__(self,base,axes,color='black', zorder=5, ymin=0.0, ymax=0.5,xmin=0.0,xmax=0.5):
        
        _BaseInteractor.__init__(self, base, axes, color=color)
        self.markers = []
        self.axes = axes
        
        self.y=ymin
        self.save_y=ymin
        
        self.xmin=xmin
        self.save_xmin=xmin
        self.xmax=xmax
        self.save_xmax=xmax
        
        self.line = self.axes.plot([self.xmin,self.xmax],[self.y,self.y],
                                      linestyle='-', marker='',
                                      color=self.color,
                                      visible=True)[0]
      
        self.npts = 20
        self.has_move=False
        self.connect_markers([self.line])
        self.update()

    def set_layer(self, n):
        self.layernum = n
        self.update()
        
    def clear(self):
        self.clear_markers()
        try:
            
            self.line.remove()
        except:
            # Old version of matplotlib
            for item in range(len(self.axes.lines)):
                del self.axes.lines[0]
        
        
        
    def get_radius(self):
        
        return 0
        
    def update(self,xmin=None, xmax=None,ymin=None, ymax=None):
        """
        Draw the new roughness on the graph.
        """
        #print "update main line", self.has_move
        if xmin !=None:
            self.xmin=xmin
        if xmax !=None:
            self.xmax=xmax
        if ymin !=None:
            self.y=ymin
        if ymax !=None:
            self.y = ymax
        self.line.set(xdata=[self.xmin,self.xmax], ydata=[self.y,self.y])
     
        
        
    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self.save_xmin= self.xmin
        self.save_xmax= self.xmax
       
        self.save_y= self.y
        self.base.freeze_axes()

    def moveend(self, ev):
        
        self.has_move=False
        self.base.moveend(ev)
            
    def restore(self):
        """
        Restore the roughness for this layer.
        """
        self.ymin = self.save_ymin
        self.ymax = self.save_ymax

    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        self.y=y
       
        
        self.has_move=True
        self.base.base.update()
        
    def set_cursor(self, x, y):
        self.move(x, y, None)
        self.update()
        
        
    def get_params(self):
        params = {}
        params["radius"] = self.xmin
        params["theta"] = self.xmax
        return params
    
    def set_params(self, params):

        x = params["radius"] 
        self.set_cursor(x, self._inner_mouse_y)
        



class VerticalLine(_BaseInteractor):
    """
         Select an annulus through a 2D plot
    """
    def __init__(self,base,axes,color='black', zorder=5, ymin=0.0, ymax=0.5,xmin=0.0,xmax=0.5):
        
        _BaseInteractor.__init__(self, base, axes, color=color)
        self.markers = []
        self.axes = axes
        
        self.x=xmin
        self.save_x=xmin
        
        self.ymin=ymin
        self.save_ymin=ymin
        self.ymax=ymax
        self.save_ymax=ymax
        
        self.line = self.axes.plot([self.x,self.x],[self.ymin,self.ymax],
                                      linestyle='-', marker='',
                                      color=self.color,
                                      visible=True)[0]
      
        self.npts = 20
        self.has_move=False
        self.connect_markers([self.line])
        self.update()

    def set_layer(self, n):
        self.layernum = n
        self.update()
        
    def clear(self):
        self.clear_markers()
        try:
            
            self.line.remove()
        except:
            # Old version of matplotlib
            for item in range(len(self.axes.lines)):
                del self.axes.lines[0]
        
        
        
    def get_radius(self):
        
        return 0
        
    def update(self,xmin=None, xmax=None,ymin=None, ymax=None):
        """
        Draw the new roughness on the graph.
        """
        
        if xmin !=None:
            self.x=xmin
        if xmin !=None:
            self.x=xmax
        if ymin !=None:
            self.ymin=ymin
        if ymax !=None:
            self.ymax=ymax
        print "update vertical line", self.has_move,[self.x,self.x], [self.ymin,self.ymax]
        self.line.set(xdata=[self.x,self.x], ydata=[self.ymin,self.ymax])
     
        
        
    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self.save_x= self.x
      
        self.save_ymin= self.ymin
        self.save_ymax= self.ymax
        self.base.freeze_axes()

    def moveend(self, ev):
        
        self.has_move=False
        self.base.moveend(ev)
            
    def restore(self):
        """
        Restore the roughness for this layer.
        """
        self.x = self.save_x
        
        self.ymin=self.save_ymin
        self.ymax=self.save_ymax
    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        self.x=x
        
        
        
        self.has_move=True
        self.base.base.update()
        
    def set_cursor(self, x, y):
        self.move(x, y, None)
        self.update()
        
        
    def get_params(self):
        params = {}
        params["radius"] = self.xmin
        params["theta"] = self.xmax
        params["radius"] = self.xmin
        params["theta"] = self.xmax
        return params
    
    def set_params(self, params):

        x = params["radius"] 
        self.set_cursor(x, self._inner_mouse_y)
        


        