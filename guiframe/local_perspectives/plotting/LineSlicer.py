#TODO: the line slicer should listen to all 2DREFRESH events, get the data and slice it
#      before pushing a new 1D data update.


#
#TODO: NEED MAJOR REFACTOR
#

# Debug printout
import math
import wx
from copy import deepcopy

from sans.guicomm.events import NewPlotEvent, StatusEvent,SlicerParameterEvent,EVT_SLICER_PARS
from BaseInteractor import _BaseInteractor



class LineInteractor(_BaseInteractor):
    """
        Select a slice through a 2D plot
    """
    #TODO: get rid of data that is not related to the image
    # For instance, get rid of access to qmax
    
    def __init__(self,base,axes,color='black', zorder=3):
        _BaseInteractor.__init__(self, base, axes, color=color)
        self.markers = []
        self.axes = axes
        self._mouse_x = 0
        self._mouse_y = self.base.data2D.xmax/2
        self._save_x  = 0
        self._save_y  = self.base.data2D.xmax/2
        self.scale = 10.0
        
        self.npts = 150
        ## Number of bins on the line
        self.nbins = 50
        ## Width of the line
        self.tolerance = None
        
        try:
            self.marker = self.axes.plot([0],[self.base.qmax/2], linestyle='',
                                          marker='s', markersize=10,
                                          color=self.color, alpha=0.6,
                                          label="pick", 
                                          zorder=zorder, # Prefer this to other lines
                                          visible=True)[0]
        except:
            self.marker = self.axes.plot([0],[self.base.qmax/2], linestyle='',
                                          marker='s', markersize=10,
                                          color=self.color, alpha=0.6,
                                          pickradius=5, label="pick", 
                                          visible=True)[0]
            
            message  = "\nTHIS PROTOTYPE NEEDS THE LATEST VERSION OF MATPLOTLIB\n"
            message += "Get the SVN version that is at least as recent as June 1, 2007"
                          
        self.line = self.axes.plot([0,0],[0.0,self.base.qmax/2*self.scale],
                                      linestyle='-', marker='',
                                      color=self.color,
                                      visible=True)[0]
        
            
        self.connect_markers([self.marker])
        self.update()
        self._post_data()
        
        # Bind to slice parameter events
        self.base.parent.Bind(EVT_SLICER_PARS, self._onEVT_SLICER_PARS)
        
    def _onEVT_SLICER_PARS(self, event):
        event.Skip()
        wx.PostEvent(self.base.parent, StatusEvent(status="LineSlicer._onEVT_SLICER_PARS"))
        if event.type == self.__class__.__name__:
            self.set_params(event.params)
            self.base.update()
        
    def update_and_post(self):
        self.update()
        self._post_data()

    def save_data(self, path, image, x, y):
        output = open(path, 'w')
        
        data_x, data_y = self.get_data(image, x, y)
        
        output.write("<q>  <average>\n")
        for i in range(len(data_x)):
            output.write("%g  %g\n" % (data_x[i], data_y[i]))
        output.close()


    def get_event(self, image=None, x=None, y=None):
        evt = SliceEvent(self._mouse_x, self._mouse_y)
        evt.type = SliceInteractor
        if not image==None and not x==None and not y==None:
            data_x, data_y = self.get_data(image, x, y)
            evt.data_x = data_x
            evt.data_y = data_y
        evt.min_xlim = 0
        evt.max_xlim = self.base.qmax
        evt.params = self.get_params()
        evt.ylabel = r'$\rm{Intensity}\ (cm^{-1})$'
        evt.xlabel = r'$\rm{q}\ (A^{-1})$'

        return evt

    def set_layer(self, n):
        self.layernum = n
        self.update()
        
    def clear(self):
        self.clear_markers()
        try:
            self.marker.remove()
            self.line.remove()
        except:
            # Old version of matplotlib
            for item in range(len(self.axes.lines)):
                del self.axes.lines[0]
        
        # Unbind panel
        #self.base.connect.disconnect()
        self.base.parent.Unbind(EVT_SLICER_PARS)

        
    def update(self):
        """
        Draw the new roughness on the graph.
        """
        self.marker.set(xdata=[self._mouse_x],ydata=[self._mouse_y])
        self.line.set(xdata=[0,self._mouse_x*self.scale], ydata=[0,self._mouse_y*self.scale])

    def get_data(self, image=None, x=None, y=None):
        """
            Return the slice data
        """
        #TODO: Computer variance 
        
        # If we have no data, just return
        if image == None:
            return
        
        # Now the slice
        nbins = self.nbins
        data_x = nbins*[0]
        data_y = nbins*[0]
        counts = nbins*[0]
        
        length = len(image)
        qmax = x[length-1]
        
        #TODO: only good for square detector!
        #data_step = (x[length-1]-x[length-2])/2.0
        data_step = (x[length-1]-x[length-2])
        if self.tolerance==None:
            self.tolerance = data_step
        else:
            data_step = self.tolerance
        
        #TODO: calculate the slice from the actual matrix 
        # this must be done for real data
        print "STEP", data_step
        for i_x in range(length):
            for i_y in range(length):
                    
                # Check whether that cell touches the line
                # Careful with the sign of the slope
                xval = x[i_x]
                yval = y[i_y]
                
                if (self._mouse_x==0 and math.fabs(xval)<data_step) \
                    or (self._mouse_x>0 and \
                        math.fabs(yval-xval*self._mouse_y/self._mouse_x)<data_step) \
                    or (self._mouse_x<0 and \
                        math.fabs(yval+xval*self._mouse_y/self._mouse_x)<data_step) \
                    or (self._mouse_y>0 and \
                        math.fabs(xval-yval*self._mouse_x/self._mouse_y)<data_step) \
                    or (self._mouse_y<0 and \
                        math.fabs(xval+yval*self._mouse_x/self._mouse_y)<data_step):
                    
                    q = math.sqrt(x[i_x]*x[i_x] + y[i_y]*y[i_y])
                       
                    i_bin = int(math.floor(q/(qmax/nbins)))
                    
                    # Check for out-of-range q bins (possible in the corners)
                    if i_bin<nbins:
                        #data_y[i_bin] += math.exp(image[i_x][i_y])
                        data_y[i_bin] += image[i_y][i_x]
                        counts[i_bin] += 1
                    
        data_pos_x = []
        data_pos_y = []
        for i in range(nbins):
            data_x[i] = (i+0.5)*qmax/nbins
            if counts[i]>0:
                data_y[i] = data_y[i]/counts[i]
                data_pos_x.append(data_x[i])
                data_pos_y.append(data_y[i])
        
        return data_x, data_y


    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self._save_x = self._mouse_x
        self._save_y = self._mouse_y
        self.base.freeze_axes()

    def _post_data(self):
        # Compute data
        data = self.base.get_corrected_data()
        # If we have no data, just return
        if data == None:
            return

        data_x, data_y = self.get_data(data, self.base.x, self.base.y)
        
        name = "Line"
        if hasattr(self.base, "name"):
            name += " %s" % self.base.name
        print "data_x", data_x
        """    
        wx.PostEvent(self.base.parent, AddPlotEvent(name=name,
                                               x = data_x,
                                               y = data_y,
                                               yscale = 'log',
                                               variable = 'Q',
                                               ylabel = "\\rm{Intensity} ",
                                               yunits = "cm^{-1}",
                                               xlabel = '\\rm{q} ',
                                               xunits = 'A^{-1}',
                                               parent = self.base.__class__.__name__))
        """
    def moveend(self, ev):
        self.base.thaw_axes()
        
        # Post paramters
        event = SlicerParameterEvent()
        event.type = self.__class__.__name__
        event.params = self.get_params()
        wx.PostEvent(self.base.parent, event)

        self._post_data()
            
    def restore(self):
        """
        Restore the roughness for this layer.
        """
        self._mouse_x = self._save_x
        self._mouse_y = self._save_y

    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        self._mouse_x = x
        self._mouse_y = y
        
    def set_cursor(self, x, y):
        self.move(x, y, None)
        self.update()
        self._post_data()
        
    def get_params(self):
        params = {}
        params["x"] = self._mouse_x
        params["y"] = self._mouse_y
        params["nbins"] = self.nbins
        params["line_width"] = self.tolerance
        return params
    
    def set_params(self, params):

        x = params["x"] 
        y = params["y"] 
        if "nbins" in params:
            self.nbins = int(params["nbins"])
        if "line_width" in params:
            self.tolerance = params["line_width"]
        self.set_cursor(x, y)
        