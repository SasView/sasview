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

class SectorInteractor(_BaseInteractor):
    """
         Select an annulus through a 2D plot
    """
    def __init__(self,base,axes,color='black', zorder=3):
        
        _BaseInteractor.__init__(self, base, axes, color=color)
        self.markers = []
        self.axes = axes
        self.qmax = self.base.qmax
        self.connect = self.base.connect
        
        ## Number of points on the plot
        self.nbins = 20
        self.theta1= math.pi/4
        self.theta2= math.pi/3
        self.phi=math.pi/12
        #self.theta3= 2*self.theta2 -self.theta1
        # Inner circle
        self.main_line = LineInteractor(self, self.base.subplot,color='blue', zorder=zorder, r=self.qmax,
                                           theta= self.theta2)
        self.main_line.qmax = self.base.qmax
        #self.left_line = SectionInteractor(self, self.base.subplot, zorder=zorder+1, r=self.qmax,
        #                                   theta1= self.theta1, theta2= self.theta2)
        #self.left_line.qmax = self.base.qmax
        self.right_line= SideInteractor(self, self.base.subplot,color='black', zorder=zorder,
                                     r=self.qmax,
                                           phi= -1*self.phi,
                                           theta2=self.theta2)
        self.right_line.qmax = self.base.qmax
        self.left_line= SideInteractor(self, self.base.subplot,color='green', zorder=zorder,
                                     r=self.qmax,
                                           phi= self.phi,
                                           theta2=self.theta2)
        self.left_line.qmax = self.base.qmax
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
        # Update locations        
        
        #if self.main_line.has_move:
        #self.main_line.update()   
        #self.right_line.update()    
        #self.left_line.update()     
        if self.main_line.has_move:
            self.main_line.update()
            self.right_line.update( delta = self.main_line.get_radius(),mline= self.main_line)
            self.left_line.update( delta = self.main_line.get_radius() ,mline= self.main_line)
            print "Main line has moved ---> phi right",math.degrees(self.main_line.theta-self.right_line.theta)
            print "Main line has moved ---> phi left",math.degrees(self.main_line.theta-self.left_line.theta)
        if self.left_line.has_move:
            print "left line has moved --->"
            self.main_line.update()
            self.left_line.update(phi=None,delta=None, mline=self.main_line,side=True)
            #self.right_line.update(-1*delta,linem=self.main_line,linel=self.left_line)
            self.right_line.update(phi=-1*self.left_line.phi,delta=None, mline=self.main_line,side=True)
        if self.right_line.has_move:
            print "right line has moved --->"
           
            self.main_line.update()
            self.right_line.update(phi=None,delta=None, mline=self.main_line,side=True)
            #self.right_line.update(-1*delta,linem=self.main_line,linel=self.left_line)
            self.left_line.update(phi=-1*self.right_line.phi,delta=None, mline=self.main_line,side=True)
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
        params["main_phi"] = self.main_line.get_radius()
        params["left_phi"] = self.left_line.get_radius()
        
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

        
class SideInteractor(_BaseInteractor):
    """
         Select an annulus through a 2D plot
    """
    def __init__(self,base,axes,color='black', zorder=5, r=1.0,phi=math.pi/4, theta2= math.pi/3):
        
        _BaseInteractor.__init__(self, base, axes, color=color)
        self.markers = []
        self.axes = axes
        
        self.save_theta = theta2 + phi
        
        self.theta=  theta2 + phi
        
        self.theta2 = theta2
        
        self.radius = r
        
        self.phi = phi
        self.scale = 10.0
        print "init for line side theta2, phi, theta",math.degrees(theta2),math.degrees(phi),math.degrees(self.theta) 
        #raise "Version error", message
          
        # Inner circle
        x1= self.radius*math.cos(self.theta)
        y1= self.radius*math.sin(self.theta)
        x2= -1*self.radius*math.cos(self.theta)
        y2= -1*self.radius*math.sin(self.theta)
       
        self.line = self.axes.plot([x1,x2],[y1,y2],
                                      linestyle='-', marker='',
                                      color=self.color,
                                      visible=True)[0]
       
        self.npts = 20
        self.has_move=False
        self.connect_markers([self.line])
        #self.update()

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
        
        return self.theta - self.save_theta
        
    def update(self,phi=None,delta=None, mline=None,side=False):
        """
        Draw the new roughness on the graph.
        """
        #print "update left or right ", self.has_move
        
        if phi !=None:
            self.phi = phi
        if delta==None:
            delta = 0
        if side== True:
            self.theta=  mline.theta + self.phi
        if mline!=None:
            self.theta2 = mline.theta
        print "U:for line side theta2, phi, theta",math.degrees(self.theta2),math.degrees(self.phi),math.degrees(self.theta) 
        x1= self.radius*math.cos(self.theta + delta)
        y1= self.radius*math.sin(self.theta + delta)
        x2= -1*self.radius*math.cos(self.theta + delta)
        y2= -1*self.radius*math.sin(self.theta + delta)
       
        
        self.line.set(xdata=[x1,x2], ydata=[y1,y2])  
        
       
        
        
    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self.save_theta= self.theta
        self.base.freeze_axes()

    def moveend(self, ev):
        
        self.has_move=False
        self.base.moveend(ev)
            
    def restore(self):
        """
        Restore the roughness for this layer.
        """
        self.theta = self.save_theta

    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        
        self.theta= math.atan2(y,x)
        self.phi= self.theta2 - self.theta
        
        print "move left or right phi ---theta--thetaM", self.phi, self.theta, self.theta2
        self.has_move=True
        self.base.base.update()
        
    def set_cursor(self, x, y):
        self.move(x, y, None)
        self.update()
        
        
    def get_params(self):
        params = {}
        params["radius"] = self.radius
        params["theta"] = self.theta
        return params
    
    def set_params(self, params):

        x = params["radius"] 
        self.set_cursor(x, self._inner_mouse_y)
        


        
        
class LineInteractor(_BaseInteractor):
    """
         Select an annulus through a 2D plot
    """
    def __init__(self,base,axes,color='black', zorder=5, r=1.0,theta=math.pi/4):
        
        _BaseInteractor.__init__(self, base, axes, color=color)
        self.markers = []
        self.axes = axes
        
        self.save_theta = theta 
        self.theta= theta
        
        self.radius = r
      
        self.scale = 10.0
      
        #raise "Version error", message
            
        # Inner circle

           
        x1= self.radius*math.cos(self.theta)
        y1= self.radius*math.sin(self.theta)
        x2= -1*self.radius*math.cos(self.theta)
        y2= -1*self.radius*math.sin(self.theta)
       
        self.line = self.axes.plot([x1,x2],[y1,y2],
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
        
        return self.theta - self.save_theta
        
    def update(self):
        """
        Draw the new roughness on the graph.
        """
        #print "update main line", self.has_move
        
        x1= self.radius*math.cos(self.theta)
        y1= self.radius*math.sin(self.theta)
        x2= -1*self.radius*math.cos(self.theta)
        y2= -1*self.radius*math.sin(self.theta)
      
        self.line.set(xdata=[x1,x2], ydata=[y1,y2])  
     
        
        
    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self.save_theta= self.theta
        self.base.freeze_axes()

    def moveend(self, ev):
        
        self.has_move=False
        self.base.moveend(ev)
            
    def restore(self):
        """
        Restore the roughness for this layer.
        """
        self.theta = self.save_theta

    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        
        self.theta= math.atan2(y,x)
        print "main_line previous theta --- next theta ",math.degrees(self.save_theta),math.degrees(self.theta)
        
        self.has_move=True
        self.base.base.update()
        
    def set_cursor(self, x, y):
        self.move(x, y, None)
        self.update()
        
        
    def get_params(self):
        params = {}
        params["radius"] = self.radius
        params["theta"] = self.theta
        return params
    
    def set_params(self, params):

        x = params["radius"] 
        self.set_cursor(x, self._inner_mouse_y)
        


        