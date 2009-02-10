"""
    Object to manage the state of the application
"""

#TODO: use both CPUs and break the calculations in two threads
#TODO: stop threads before starting a new one

import wx
import wx.lib.newevent

#import ModelParameters
#import history
import modelData
from model_thread import Calc2D, Calc1D, Calc2D_4fold, Calc2D_all
from copy import deepcopy

#TODO: State should report back to StateManager instead
#    of firing these events itself
(Refresh2DEvent, EVT_2DREFRESH) = wx.lib.newevent.NewEvent()
(Refresh1DEvent, EVT_1DREFRESH) = wx.lib.newevent.NewEvent()

# Debug printout
#from config import printEVT



class State:
    
    def __init__(self, target=None,data=None, model=None, slicer=None, panel=None):
        self.target = target
        self.model  = model
        self.data   = data
        self.type_panel= None
        self.disp_list = []
        self.manager = None
        self.parent  = parent
        self.event_owner = None
        self.modelbox = wx.ComboBox(self, -1)
         # preview selected model name
        self.prevmodel_name=name
        #print "model view prev_model",name
        self.modelbox.SetValue(self.prevmodel_name)
        #enable model 2D draw
        self.enable2D= False
         ## Q range
        self.qmin_x= 0.001
        self.qmax_x= 0.1
        self.num_points= 100
        self.parameters=[]
        self.fixed_param=[]
        self.fittable_param=[]
        #contains link between a model and selected parameters to fit 
        self.param_toFit=[]
        
        #dictionary of model name and model class
        self.model_list_box={}
        #Draw initial panel
        self.enable_disp= None
        self.disable_disp=None    
            
        if panel !=None:
            self.panel= panel
            
        
        
        self.slicer = slicer
        self.model_par_memento = None
        self.detector_memento = None
        self.averager_memento = None
        self.pars1D_memento   = None
        
        # Keep the latest data 
        self._data_2D = None
        self._data_1D = None
        # The following should disappear
        self.qmax = None
        self.x_1D = None
        
        # Threads
        self.active = True
        self.calc_thread_2D = None
        self.calc_thread_1D = None
        
        # Info for history
        self.description = ''
    def clone_panel(self):
        obj          = State(self.target, self.model.clone(),self.panel)
        obj.data = deepcopy(self.data)
        
        
        
        
    def clone(self):
        obj          = State(self.target, self.model.clone(), self.slicer)
        obj._data_1D = deepcopy(self._data_1D)
        obj._data_2D = deepcopy(self._data_2D)
        obj.qmax     = deepcopy(self.qmax)
        obj.x_1D     = deepcopy(self.x_1D)
        obj.model_par_memento = deepcopy(self.model_par_memento)
        obj.detector_memento = deepcopy(self.detector_memento)
        obj.averager_memento = deepcopy(self.averager_memento)
        obj.description = self.description
        return obj
        
    def clear_data(self):
        self._data_1D = None
        self._data_2D = None
        
    def stop(self):
        self.active = False
        if self.calc_thread_1D != None and self.calc_thread_1D.isrunning():
            self.calc_thread_1D.stop()
        if self.calc_thread_2D != None and self.calc_thread_2D.isrunning():
            self.calc_thread_2D.stop()
        
    def setModelParMemento(self, memento):
        self.model_par_memento = memento
        
    def setDetectorMemento(self, memento):
        self.clear_data()
        # Change description
        self.description = '%s' % memento.toString(self.detector_memento)
        self.detector_memento = memento
        
    def setPars1DMemento(self, memento):
        self.clear_data()
        # Change description
        self.description = '%s' % memento.toString(self.pars1D_memento)
        self.pars1D_memento = memento
        
    def setAveragerMemento(self, memento):
        self.clear_data()
        self.averager_memento = memento
        
    def setModel(self, model):
        """
            Set the model and send a history event
        """
        # Clean the data to invoke recalc
        self._data_1D = None
        self._data_2D = None
        
        # Set the model 
        self.model = model
        
        self.description = ''
        
        return str(self.model.name)
        
    def setParams(self, params):
        """
            Update parameters and return a name
            that represents the change (key)
        """
        # Clean the data to invoke recalc
        self._data_1D = None
        self._data_2D = None

        # Compose string to summarize change        
        name = self.model.name
        
        # Identify and perform changes
        for item in params:
            name += "/%s=%-5.5g" % (item, self.model.getParam(item))
            self.model.setParam(item, params[item])
        
        return name

    def setSlicer(self, slicer):
        self.slicer = slicer
        
    def get_data_1d(self, x):
        """
            Calculate the data 
            @param min: minimum q-value
            @param max: maximum q-value
        """
        
        printEVT("State.get_data_1d")
        if not self.model:
            return
        
        if self._data_1D == None:
            self.x_1D = deepcopy(x)
            if self.calc_thread_1D != None and self.calc_thread_1D.isrunning():
                self.calc_thread_1D.stop()
                
            self.calc_thread_1D = Calc1D(x, self.model.clone(), 
                                completefn=self.complete1D,
                                updatefn=self.update1D)
            self.calc_thread_1D.queue()
            self.calc_thread_1D.ready(2.5)
        else:
            printEVT("Dispatch 1D non-recalc data") 
            wx.PostEvent(self.target, Refresh1DEvent(name=self.model.name, x = self.x_1D,
                                                     output=deepcopy(self._data_1D)))
         
    
    def get_data_2d(self, max, x, y):
        """ 
            Calculate 2D data
            @param max: maximum q-value
        """
        if not self.model:
            return
        
        if self._data_2D == None:
            self.qmax = max
            if self.calc_thread_2D != None and self.calc_thread_2D.isrunning():
                self.calc_thread_2D.stop()
                
            if self.detector_memento == None or self.detector_memento.sym4 == False:    
                self.calc_thread_2D = Calc2D(x, y, self.model.clone(), 
                                    completefn=self.complete2D,
                                    updatefn=self.update2D,
                                    yieldtime=0.0)
            else:
                self.calc_thread_2D = Calc2D_4fold(x, y, self.model.clone(), 
                                    completefn=self.complete2D,
                                    updatefn=self.update2D,
                                    yieldtime=0.0)
                
            self.calc_thread_2D.queue()
            self.calc_thread_2D.ready(2.5)
        else:
            print
            #printEVT("Dispatch 2D non-recalc data") 
            #wx.PostEvent(self.target, Refresh2DEvent(output=deepcopy(self._data_2D),
            #                                        qmax=self.qmax))
            
             
    def update2D(self, output):
        printEVT("State.updated2D")
        if self.active:
            #self._data_2D = output
            self._data_2D = deepcopy(output)
            wx.PostEvent(self.target, Refresh2DEvent(output=deepcopy(self._data_2D),
                                                qmax=self.qmax))
    
    def complete2D(self, output, elapsed):
        printEVT("%s: Calc 2D complete in %g sec" % (self.model.name, elapsed)) 
        if self.active:
            self._data_2D = deepcopy(output)
            wx.PostEvent(self.target, Refresh2DEvent(output=deepcopy(self._data_2D),
                                                qmax=self.qmax))
        else:
            printEVT("Active = False!")

    def update1D(self, output):
        pass
    
    def complete1D(self, output, elapsed):
        printEVT("Calc 1D complete in %g sec" % elapsed) 
        self._data_1D = deepcopy(output)
        wx.PostEvent(self.target, Refresh1DEvent(name=self.model.name, x = self.x_1D,
                                                 output=deepcopy(self._data_1D)))

    