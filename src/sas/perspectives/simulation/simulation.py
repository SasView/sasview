"""
This software was developed by the University of Tennessee as part of the
Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
project funded by the US National Science Foundation. 

See the license text in license.txt

copyright 2009, University of Tennessee
"""
import wx
import os
import numpy
import time
import logging

# Application imports
import SimCanvas
import ShapeParameters
import ShapeAdapter
from sas.guiframe.dataFitting import Data1D
# Real-space simulation import
import sas.realspace.VolumeCanvas as VolumeCanvas

from sas.data_util.calcthread import CalcThread
from sas.guicomm.events import NewPlotEvent, StatusEvent    

class Calc1D(CalcThread):
    """
        Thread object to simulate I(q)
    """
    
    def __init__(self, x, model,
                 completefn = None,
                 updatefn   = None,
                 yieldtime  = 0.01,
                 worktime   = 0.01
                 ):
        CalcThread.__init__(self,completefn,
                 updatefn,
                 yieldtime,
                 worktime)
        self.x = x
        self.model = model
        self.starttime = 0
        
    def compute(self):
        x = self.x
        output = numpy.zeros(len(x))
        error = numpy.zeros(len(x))
        
        self.starttime = time.time()
        
        for i_x in range(len(self.x)):
            # Check whether we need to bail out
            self.isquit()
            self.update(output=output, error=error)
            
            value, err = self.model.getIqError(float(self.x[i_x]))
            output[i_x] = value
            error[i_x] = err
            
        elapsed = time.time()-self.starttime
        self.complete(output=output, error=error, elapsed=elapsed)

## Default minimum q-value for simulation output    
DEFAULT_Q_MIN = 0.01
## Default maximum q-value for simulation output
DEFAULT_Q_MAX = 0.4
## Default number of q point for simulation output
DEFAULT_Q_NPTS = 10
## Default number of real-space points per Angstrom cube
DEFAULT_PT_DENSITY = 0.1
   
class Plugin:
    """
        Real-space simulation plug-in for guiframe
    """
    ## Minimum q-value for simulation output    
    q_min = DEFAULT_Q_MIN
    ## Maximum q-value for simulation output
    q_max = DEFAULT_Q_MAX
    ## Number of q point for simulation output
    q_npts = DEFAULT_Q_NPTS    
    
    def __init__(self):
        ## Plug-in name
        self.sub_menu = "Simulation"
        ## Reference to the parent window
        self.parent = None
        ## List of panels for the simulation perspective (names)
        self.perspective = []
        # Default save location
        self._default_save_location = os.getcwd()
        # Log startup
        logging.info("Simulation plug-in started")
        
    def get_panels(self, parent):
        """
            Create and return a list of panel objects
        """
        self.parent = parent
        
        # 3D viewer
        self.plotPanel  = SimCanvas.SimPanel(self.parent, -1, style=wx.RAISED_BORDER)

        # Central simulation panel
        self.paramPanel = ShapeParameters.ShapeParameterPanel(self.parent, 
                                                              q_min = self.q_min,
                                                              q_max = self.q_max,
                                                              q_npts = self.q_npts,
                                                              pt_density = DEFAULT_PT_DENSITY,
                                                              style=wx.RAISED_BORDER)
        
        # Simulation
        self.volCanvas = VolumeCanvas.VolumeCanvas()
        self.volCanvas.setParam('lores_density', DEFAULT_PT_DENSITY)
        self.adapter = ShapeAdapter.ShapeVisitor()
        self._data_1D = None
        self.calc_thread_1D = None
        self.speedCheck = False
        self.speed = 3.0e-7
        
        # Q-values for plotting simulated I(Q)
        step = (self.q_max-self.q_min)/(self.q_npts-1)
        self.x = numpy.arange(self.q_min, self.q_max+step*0.01, step)        
        
        # Set the list of panels that are part of the simulation perspective
        self.perspective = []
        self.perspective.append(self.plotPanel.window_name)
        self.perspective.append(self.paramPanel.window_name)
        
        # Bind state events
        self.parent.Bind(ShapeParameters.EVT_ADD_SHAPE, self._onAddShape)
        self.parent.Bind(ShapeParameters.EVT_DEL_SHAPE, self._onDelShape)
        self.parent.Bind(ShapeParameters.EVT_Q_RANGE, self._on_q_range_changed)
        self.parent.Bind(ShapeParameters.EVT_PT_DENSITY, self._on_pt_density_changed)

        return [self.plotPanel, self.paramPanel]

    def _onAddShape(self, evt):
        """
            Process a user event to add a newly created 
            or modified shape to the canvas
        """
        evt.Skip()
        
        # Give the new shape to the canvas
        if evt.new:
            shape = evt.shape.accept(self.adapter)
            id = self.volCanvas.addObject(shape)
            self.plotPanel.canvas.addShape(evt.shape, id)
        else:
            self.adapter.update(self.volCanvas, evt.shape)
        
        # Compute the simulated I(Q)
        self._simulate_Iq()
        
        # Refresh the 3D viewer
        self._refresh_3D_viewer()
        
    def _onDelShape(self, evt):
        """
            Remove a shape from the simulation
        """
        # Notify the simulation canvas
        self.volCanvas.delete(evt.id)
        # Notify the UI canvas
        self.plotPanel.canvas.delShape(evt.id)
        
        # Compute the simulated I(Q)
        self._simulate_Iq()
        
        # Refresh the 3D viewer
        self._refresh_3D_viewer()   
        
    def _on_q_range_changed(self, evt):
        """
            Modify the Q range of the simulation output
        """
        if evt.q_min is not None:
            self.q_min = evt.q_min
        if evt.q_max is not None:
            self.q_max = evt.q_max
        if evt.npts is not None:
            self.q_npts = evt.npts
        
        # Q-values for plotting simulated I(Q)
        step = (self.q_max-self.q_min)/(self.q_npts-1)
        self.x = numpy.arange(self.q_min, self.q_max+step*0.01, step)    
         
        # Compute the simulated I(Q)
        self._simulate_Iq()
        
    def _on_pt_density_changed(self, evt):
        """
            Modify the Q range of the simulation output
        """
        if evt.npts is not None:
            self.volCanvas.setParam('lores_density', evt.npts)
         
        # Compute the simulated I(Q)
        self._simulate_Iq()
        
    def _simulate_Iq(self):
        """
            Simulate I(q) using the current VolumeCanvas object. 
        """
        # Check that the VolumeCanvas object exists
        if not isinstance(self.volCanvas, VolumeCanvas.VolumeCanvas):
            return
        
        # If a computation thread is running, stop it
        if self.calc_thread_1D != None and self.calc_thread_1D.isrunning():
            self.calc_thread_1D.stop()
            ## stop just raises the flag -- the thread is supposed to 
            ## then kill itself. In August 2014 it was shown that this is
            ## incorrectly handled by fitting.py and a fix implemented. 
            ## It is not clear that it is improperly used here so no fix
            ## is being added here.
            ##
            ##    -PDB January 25, 2015                  
            
        # Create a computation thread
        self.calc_thread_1D = Calc1D(self.x, self.volCanvas, 
                            completefn=self._simulation_completed_1D,
                            updatefn=None)
        self.calc_thread_1D.queue()
        self.calc_thread_1D.ready(2.5)
    
        # Evaluate maximum number of points on the canvas and the 
        # maximum computation time
        
        # TODO: the getMaxVolume should be a call to the VolumeCanvas object.
        # Since the VolumeCanvas doesn't currently have that functionality, and
        # since the simulation panel holds the list of graphical representations
        # for the shapes, we will take the information from there until VolumeCanvas 
        # is updated.
        npts = self.plotPanel.canvas.getMaxVolume() * self.volCanvas.params['lores_density'] 
        
        est = self.speed * npts * npts
        self.parent.SetStatusText("Calculation started: this might take a moment... [up to %d secs, %g points]" % (int(est), int(npts)))

  
    def _simulation_completed_1D(self, output, elapsed, error=None):
        """
            Called by the computation thread when the simulation is complete.
            This method processes the simulation output, plots it, and updates
            the simulation time estimate.
            
            @param output: simulated distribution I(q)
            @param elapsed: simulation time, in seconds
            @param error: standard deviation on the I(q) points
        """
        # Create the plotting event to pop up the I(Q) plot.
        new_plot = Data1D(x=self.x, y=output, dy=error)
        new_plot.name = "I(Q) Simulation"
        new_plot.group_id = "simulation_output"
        new_plot.xaxis("\\rm{Q}", 'A^{-1}')
        new_plot.yaxis("\\rm{Intensity} ","cm^{-1}")
        wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot, title="Simulation I(Q)"))
        
        # Create the plotting event to pop up the P(r) plot.
        r, pr = self.volCanvas.getPrData()
        new_plot = Data1D(x=r, y=pr, dy=[0]*len(r))
        new_plot.name = "P(r) Simulation"
        new_plot.group_id = "simulated_pr"
        new_plot.xaxis("\\rm{r}", 'A')
        new_plot.yaxis("\\rm{P(r)} ","cm^{-3}") 
        
        wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot, title="Simulated P(r)"))        
        
        
        # Notify the user of the simlation time and update the basic
        # simulation estimate that will allow us to estimate simulation time
        # next time we are asked to simulate.
        msg = "Calculation completed in %g secs! [%g points]" % (elapsed, self.volCanvas.npts)
        wx.PostEvent(self.parent, StatusEvent(status=msg))
        if self.volCanvas.npts>0:
            self.speed = elapsed/self.volCanvas.npts**2
         
    
    def get_perspective(self):
        """
            Get the list of panel names for this perspective
        """
        return self.perspective
    
    def populate_menu(self, id, owner):
        """
            Create a menu for the plug-in
        """
        return []  
    
    def _change_point_density(self, point_density):
        """
            Placeholder for changing the simulation point density
            TODO: refactor this away by writing a single update method for the simulation parameters
        """
        self.volCanvas.setParam('lores_density', point_density)
    
    def help(self, evt):
        """
            Provide help for the simulation
        """
        pass
    
    def on_perspective(self, event):
        """
            Call back function for the perspective menu item.
            We notify the parent window that the perspective
            has changed.
        """
        self.parent.set_perspective(self.perspective)
    
    def post_init(self):
        """
            Post initialization call back to close the loose ends
            [Somehow openGL needs this call]
        """
        self.parent.set_perspective(self.perspective) 
        self.parent._mgr.Update()

    def _refresh_3D_viewer(self):
        """
            Refresh the 3D viewer window
            #TODO: don't access data member directly
        """
        self.plotPanel.canvas.Refresh(False)
        # Give focus back to 3D canvas so that the 
        # zooming works
        #self.plotPanel.canvas.SetFocus()
        #self.plotPanel.SetFocus()
