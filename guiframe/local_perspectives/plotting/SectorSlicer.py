#TODO: the line slicer should listen to all 2DREFRESH events, get the data and slice it
#      before pushing a new 1D data update.

#
#TODO: NEED MAJOR REFACTOR
#


# Debug printout
from sans.guicomm.events import StatusEvent 
from sans.guicomm.events import NewPlotEvent
from BaseInteractor import _BaseInteractor
from copy import deepcopy
import math


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
        self.qmax = math.sqrt(2)*self.base.qmax
        self.connect = self.base.connect
        
        ## Number of points on the plot
        self.nbins = 20
        self.theta1= math.pi/4
        self.theta2= math.pi/3
        self.phi=math.pi/12
        #self.theta3= 2*self.theta2 -self.theta1
        # Inner circle
        self.main_line = LineInteractor(self, self.base.subplot,color='green', zorder=zorder, r=self.qmax,
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
        self.left_line= SideInteractor(self, self.base.subplot,color='blue', zorder=zorder,
                                     r=self.qmax,
                                           phi= self.phi,
                                           theta2=self.theta2)
        self.left_line.qmax = self.base.qmax
        #self.outer_circle.set_cursor(self.base.qmax/1.8, 0)
        
                      
        self.update()
        self._post_data()
        
        # Bind to slice parameter events
        self.base.parent.Bind(SlicerParameters.EVT_SLICER_PARS, self._onEVT_SLICER_PARS)


    def _onEVT_SLICER_PARS(self, event):
        wx.PostEvent(self.base.parent, StatusEvent(status="SectorSlicer._onEVT_SLICER_PARS"))
        event.Skip()
        if event.type == self.__class__.__name__:
            self.set_params(event.params)
            self.base.update()

    def update_and_post(self):
        self.update()
        #self._post_data()

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
        self.main_line.clear()
        self.left_line.clear()
        self.right_line.clear()
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
            print "Main line has moved ---> phi right",math.degrees(self.main_line.get_radius()+self.right_line.theta)
            print "Main line has moved ---> phi left",math.degrees(self.left_line.theta+self.main_line.get_radius())
        if self.left_line.has_move:
            print "left line has moved --->"
            self.main_line.update()
            self.left_line.update(phi=None,delta=None, mline=self.main_line,side=True, left=True)
            #self.right_line.update(-1*delta,linem=self.main_line,linel=self.left_line)
            self.right_line.update(phi=-1*self.left_line.phi,delta=None, mline=self.main_line,side=True, left=True)
        if self.right_line.has_move:
            print "right line has moved --->"
           
            self.main_line.update()
            self.right_line.update(phi=None,delta=None, mline=self.main_line,side=True, right=True)
            #self.right_line.update(-1*delta,linem=self.main_line,linel=self.left_line)
            self.left_line.update(phi=-1*self.right_line.phi,delta=None, mline=self.main_line,side=True, left=True)
   
    
    

    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self.base.freeze_axes()
        self.inner_circle.save(ev)
        self.outer_circle.save(ev)

    def _post_data(self, nbins=None):
        # Compute data
        data = self.base.data2D
        # If we have no data, just return
        if data == None:
            return

        name = "Sector "
        from DataLoader.manipulations import SectorQ
        radius = self.qmax #radius=math.sqrt(math.pow(self.qmax,2)+math.pow(self.qmax,2))
        phimin = self.right_line.theta+math.pi
        phimax = self.left_line.theta+math.pi

        sect = SectorQ(r_min=0.0, r_max= radius , phi_min=phimin, phi_max=phimax)
        #sect = SectorQ(r_min=-1*radius , r_max= radius , phi_min=phimin, phi_max=phimax)
        if nbins!=None:
            sect.nbins = nbins
        
        sector = sect(self.base.data2D)
        
        from sans.guiframe.dataFitting import Data1D
        if hasattr(sector,"dxl"):
            dxl= sector.dxl
        else:
            dxl= None
        if hasattr(sector,"dxw"):
            dxw= sector.dxw
        else:
            dxw= None
       
        new_plot = Data1D(x=sector.x,y=sector.y,dy=sector.dy,dxl=dxl,dxw=dxw)
        new_plot.name = "SectorQ" +"("+ self.base.data2D.name+")"
        
       

        new_plot.source=self.base.data2D.source
        #new_plot.info=self.base.data2D.info
        new_plot.interactive = True
        #print "loader output.detector",output.source
        new_plot.detector =self.base.data2D.detector
        # If the data file does not tell us what the axes are, just assume...
        new_plot.xaxis("\\rm{Q}", 'A^{-1}')
        new_plot.yaxis("\\rm{Intensity} ","cm^{-1}")
        new_plot.group_id = "SectorQ"+self.base.data2D.name
        wx.PostEvent(self.base.parent, NewPlotEvent(plot=new_plot,
                                                 title="SectorQ" ))
        
         
        
    def moveend(self, ev):
        self.base.thaw_axes()
        
        # Post paramters
        event = SlicerParameters.SlicerParameterEvent()
        event.type = self.__class__.__name__
        event.params = self.get_params()
        wx.PostEvent(self.base.parent, event)
        self._post_data()
            
    def restore(self):
        """
        Restore the roughness for this layer.
        """
        self.main_line.restore()
        self.left_line.restore()
        self.right_line.restore()

    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        pass
        
    def set_cursor(self, x, y):
        pass
        
    def get_params(self):
        params = {}
        params["main_phi"] = self.main_line.theta
        if math.fabs(self.left_line.phi) != math.fabs(self.right_line.phi):
            raise ValueError,"Phi left and phi right are different %f, %f"%(self.left_line.phi, self.right_line.phi)
        params["left_phi"] = math.fabs(self.left_line.phi)
        params["nbins"] = self.nbins
        return params
    
    def set_params(self, params):
        
        main = params["main_phi"] 
        phi = params["left_phi"] 
        self.nbins = int(params["nbins"])
        self.main_line.theta= main
        
        self.main_line.update()
        self.right_line.update(phi=-1*phi,delta=None, mline=self.main_line,side=True)
        self.left_line.update(phi=phi,delta=None, mline=self.main_line,side=True)
       
        self._post_data(nbins=self.nbins)
        
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
        #print "init for line side theta2, phi, theta",math.degrees(theta2),math.degrees(phi),math.degrees(self.theta) 
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
        
    def update(self,phi=None,delta=None, mline=None,side=False, left= False, right=False):
        """
        Draw the new roughness on the graph.
        """
        #print "update left or right ", self.has_move
        
        if phi !=None:
            self.phi = phi
        if delta==None:
            delta = 0
        if side:
            self.theta=  mline.theta + self.phi
            
            
        if mline!=None:
            self.theta2 = mline.theta
            #self.phi= math.fabs(self.theta2 - (self.theta+delta))
        #print "U:for line side theta2, phi, theta",math.degrees(self.theta2),math.degrees(self.phi),math.degrees(self.theta) 
        #if self.theta2 >= self.theta and self.theta>=0:
        #    print "between 0-pi",math.degrees(self.theta) 
        
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
        
        self.phi= math.fabs(self.theta2 - self.theta)
        
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
        
    def update(self, theta=None):
        """
        Draw the new roughness on the graph.
        """
        print "update main line", self.theta
        if theta !=None:
            self.theta= theta
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
        


        