"""
    Object to manage the state of the application
"""

import wx
import wx.lib.newevent

import ModelParameters
import AveragerParameters
import Averager2D
import history
import modelData
from model_thread import Calc2D
from copy import deepcopy
from fitting import ChiUpdateEvent 

(Refresh2DEvent, EVT_2DREFRESH) = wx.lib.newevent.NewEvent()

# Debug printout
from config import printEVT
import config
from state import State
import Plotter1D
import Plotter2D

(StateEvent, EVT_STATE)   = wx.lib.newevent.NewEvent()

class DetectorMemento:
    def __init__(self, qmax=0.1, npts=10, beam=None, zmin=None, zmax=None, sym4=False):
        self.qmax = qmax
        self.npts = npts
        self.zmin = zmin
        self.zmax = zmax
        self.beam = beam
        self.sym4 = sym4
        
    def toString(self, memento):
        """
            Return a string that describes the difference
            between the given memento and the current one
            @param memento: memento to compare to
            @return: string
        """
        if memento == None:
            return "/Qmax = %g/Det npts = %g" % (self.qmax, self.npts)
        else:
            descr = ''
            if not memento.qmax == self.qmax:
                descr += "/Qmax = %g" % self.qmax
            if not memento.npts == self.npts:
                descr += "/Det npts = %g" % self.npts
            if not self.zmin==None and not memento.zmin == self.zmin:
                descr += "/Zmin = %g" % self.zmin
            if self.zmax and not memento.zmax == self.zmax:
                descr += "/Zmax = %g" % self.zmax
            if not memento.beam == self.beam:
                descr += "/beamstop = %g" % self.beam
            return descr

class StateManager:
    
    def __init__(self, target=None, model=None, slicer=None):
        self.target = target
        self.state  = State(target, model, slicer)
        
        # Listen to parameter changes to fire history events

        self.target.Bind(ModelParameters.EVT_MODEL_PARS, self._onEVT_MODEL_PARS)
        self.target.Bind(AveragerParameters.EVT_AVG_PARS, self._onEVT_AVG_PARS)
        self.target.Bind(EVT_STATE, self._onEVT_STATE)
        self.target.Bind(Plotter2D.EVT_DETECTOR, self._onEVT_DETECTOR)
        self.target.Bind(Plotter1D.EVT_PLOT1D_PARS, self._onEVT_PLOT1D_PARS)
                
    def setModel(self, target, model, tag=''):
        """
            Set the model and send a history event
        """
        # Prepare the restore event
        self._saveCurrent(tag)
        
        # Now change the model
        self.state.setModel(model)
        evt = ModelParameters.ModelEvent(model=model, data=self.state, new=True)
        wx.PostEvent(target, evt)
        # Posting averager state
        wx.PostEvent(target, AveragerParameters.AveragerStateEvent(memento=AveragerParameters.AveragerParameterMemento()))
        
    def _saveCurrent(self, tag=''):
        """
            Send a history event to capture the current state
        """
        #TODO: need a way to find the difference between old and new model
        if not self.state.model == None:
            stored_event = StateEvent(state = self.state.clone())
            
            # Send the history event
            evt = history.HistoryEvent(name = self.state.model.name+'%s/%s' % (self.state.description, tag),
                                       item = stored_event)
            wx.PostEvent(self.target, evt)
        
        
    def setSlicer(self, slicer):
        """
            Set the slicer
        """
        printEVT("StateManager.setSlicer: Slicer not implmeted")
        self.state.slicer = slicer
        
    def _onEVT_STATE(self, event):
        """
            Restor a stored state
            @param event: state event
        """
        self.state.stop()
        self.state = event.state.clone()
        
        # Posting detector parameter panel state event
        if not self.state.detector_memento == None:
            det_event = Plotter2D.createDetectorParsEvent(qmax=self.state.detector_memento.qmax,
                                                          npts=self.state.detector_memento.npts,
                                                          beam=self.state.detector_memento.beam,
                                                          zmin=self.state.detector_memento.zmin,
                                                          zmax=self.state.detector_memento.zmax,
                                                          sym4=self.state.detector_memento.sym4,
                                                          info_only=True)
        else:
            det_event = Plotter2D.createDetectorParsEvent(qmax=None,
                                                          npts=None,
                                                          info_only=True)
        printEVT("StateManager: posting detector memento")
        wx.PostEvent(self.target, det_event)
        
        # Posting 1D plot parameters
        if not self.state.pars1D_memento == None:
            pars1D_event = Plotter1D.createPlot1DParsEvent(qmax=self.state.pars1D_memento.qmax,
                                                           npts=self.state.pars1D_memento.npts,
                                                           qmin=self.state.pars1D_memento.qmin,
                                                           info_only=True)
        else:
            pars1D_event = Plotter1D.createPlot1DParsEvent(qmin=None,
                                                           qmax=None,
                                                           npts=None,
                                                           info_only=True)
        printEVT("StateManager: posting 1D plot pars memento")
        wx.PostEvent(self.target, pars1D_event)
        
        
        # Posting averager state
        wx.PostEvent(self.target, AveragerParameters.AveragerStateEvent(memento=event.state.averager_memento))
        
        # Posting model event
        evt = ModelParameters.ModelEvent(model=self.state.model, data=self.state, new=True)
        wx.PostEvent(self.target, evt)
        
        # Posting parameter panel state event
        evt2 = ModelParameters.ModelParameterStateEvent(memento=event.state.model_par_memento)
        wx.PostEvent(self.target, evt2)
        
        printEVT("State.onEVT_STATE: history item restored: %s" % self.state.model.name)
        
    def _onEVT_DETECTOR(self, event):
        config.printEVT("StateManager._onEVT_DETECTOR")
        if event.info_only:
            config.printEVT("   skip EVT_DETECTOR")
            return
        
        event.Skip()
        self._saveCurrent()
        
        # Clear current data to invoke recalculation
        #self.state.clear_data()
        self.state.setDetectorMemento(DetectorMemento(event.qmax, event.npts,
                                                      zmin = event.zmin, zmax = event.zmax,
                                                      beam = event.beam, sym4 = event.sym4))
        
        # Send an update event to the plotters
        evt = ModelParameters.ModelEvent(model=self.state.model, data=self.state, new=False)
        wx.PostEvent(self.target, evt)

    def _onEVT_PLOT1D_PARS(self, event):
        config.printEVT("StateManager._onEVT_PLOT1D_PARS")
        if event.info_only:
            config.printEVT("   skip EVT_PLOT1D_PARS")
            return
        
        event.Skip()
        self._saveCurrent()
        
        # Update the state
        self.state.setPars1DMemento(Plotter1D.Plot1DMemento(event.qmin, 
                                                              event.qmax, 
                                                              event.npts))
        
        # Send an update event to the plotters
        evt = ModelParameters.ModelEvent(model=self.state.model, data=self.state, new=False)
        wx.PostEvent(self.target, evt)

        
    def _onEVT_MODEL_PARS(self, event):
        """
            Modify the parameters of the model and
            fire a history event
            
            @param event: parameter change event
        """
        printEVT("State.onEVT_MODEL_PARS")

        # Save the state before changing it
        stored_event = StateEvent(state = self.state.clone())

        # Post message to status bar
        wx.PostEvent(self.target, config.StatusBarEvent(message=event.status))
        
        # Dispersion?
        disp_tag = ''
        if event.disp_changed and len(event.disp)>0:
            if not self.state.model.__class__.__name__ == "Averager2D":
                config.printEVT("StateMng: setting up averager")
                new_model = Averager2D.Averager2D()
                flag = new_model.set_model(self.state.model.clone())
                self.state.setModel(new_model)
            else:
                disp_list = deepcopy(self.state.model.get_dispersity())
                for item in disp_list:
                    disp_tag += '/Disp[%s]=%g [%g pts]' % (item[0], item[1], item[2])
                
            self.state.model.set_dispersity(event.disp)
            
        if not event.average and \
            self.state.model.__class__.__name__ == "Averager2D":
            disp_list = deepcopy(self.state.model.get_dispersity())
            if self.state.model.set_dispersity([]):
                for item in disp_list:
                    disp_tag += '/Disp[%s]=%g [%g pts]' % (item[0], item[1], item[2])
        
        # Push parameters to model
        name = self.state.setParams(event.params)
        self.state.setModelParMemento(event.memento)

        #print str(self.state.model)

        # Send an update event to the plotters
        evt = ModelParameters.ModelEvent(model=self.state.model, data=self.state, new=False)
        wx.PostEvent(self.target, evt)

        if len(event.params)>0 or len(event.disp)>0 or event.disp_changed:      
            # Send the history event
            evt = history.HistoryEvent(name = name+disp_tag,
                                       item = stored_event)
            wx.PostEvent(self.target, evt)
            
            # Post chi^2 recalculation event for fit panel
            wx.PostEvent(self.target, ChiUpdateEvent())
            
    def _onEVT_AVG_PARS(self, event):
        printEVT("State._onEVT_AVG_PARS")

        # Save the state before changing it
        stored_event = StateEvent(state = self.state.clone())
        
        # Inspect the change to give a proper title to the 
        # history item
        info = "Phi = OFF/THETA=ON (filename)"
        
        # Set averager memento to retreive the same state from history panel
        self.state.setAveragerMemento(event.memento)
        
        # Flags for history event
        phi_flag   = "OFF"
        theta_flag = "OFF"
                    
        #theta_file = os.path.basename(self.theta_file_path)
        
        # Post message to status bar if needed
        if not event.status == None:
             wx.PostEvent(self.target, config.StatusBarEvent(message=event.status))
            
        # Check if we already have an Averager2D model
        # When we reach this points, either we need an Averager2D 
        # or we already have one.
        if not self.state.model.__class__.__name__ == "Averager2D":
            model = Averager2D.Averager2D()
            flag = model.set_model(self.state.model.clone())
            if flag:
                self.state.setModel(model)                        
            else:
                message = "Current model doesn't have theta or phi: skipping"
                wx.PostEvent(self.target, config.StatusBarEvent(message=message))
                return
        else:
            if self.state.model.phi_on:
                phi_flag = "ON"
            if self.state.model.theta_on:
                theta_flag = "ON"
            
        # Set phi info
        if event.phi_on:
            if not self.state.model.setPhiFile(event.phi_file):
                message = "Current model doesn't have phi: skipping"
                wx.PostEvent(self.target, config.StatusBarEvent(message=message))
        else:
            self.state.model.setPhiFile(None)
        
        # Set theta info
        if event.theta_on:
            if not self.state.model.setThetaFile(event.theta_file):
                message = "Current model doesn't have phi: skipping"
                wx.PostEvent(self.target, config.StatusBarEvent(message=message))                
        else:
            self.state.model.setThetaFile(None)
        
        # Send the history event
        hist_evt = history.HistoryEvent(name = "%s/Phi %s/Theta %s" % \
                                        (self.state.model.name, phi_flag, theta_flag),
                                   item = stored_event)
        wx.PostEvent(self.target, hist_evt)
        
        # Send an update event to the plotters
        evt = ModelParameters.ModelEvent(model=self.state.model, data=self.state, new=False)
        wx.PostEvent(self.target, evt)

            
            