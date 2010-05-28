"""
This software was developed by the University of Tennessee as part of the
Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
project funded by the US National Science Foundation. 

See the license text in license.txt

copyright 2009, University of Tennessee
"""
import  re
import sys
import wx
import logging
import numpy
import math
import string
import time
import thread
from copy import deepcopy

import models
import fitpage

from DataLoader.loader import Loader

from sans.guiframe.dataFitting import Data2D
from sans.guiframe.dataFitting import Data1D
from sans.guiframe.dataFitting import Theory1D

from sans.guicomm.events import NewPlotEvent, StatusEvent  
from sans.guicomm.events import EVT_SLICER_PANEL,ERR_DATA,EVT_REMOVE_DATA
from sans.guicomm.events import EVT_SLICER_PARS_UPDATE

from sans.fit.AbstractFitEngine import Model
from sans.fit.AbstractFitEngine import FitAbort
from console import ConsoleUpdate

from fitproblem import FitProblem
from fitpanel import FitPanel
from fit_thread import FitThread
from pagestate import Reader

DEFAULT_BEAM = 0.005
DEFAULT_QMIN = 0.001
DEFAULT_QMAX = 0.13
DEFAULT_NPTS = 50

(PageInfoEvent, EVT_PAGE_INFO)   = wx.lib.newevent.NewEvent()

from fitpage import Chi2UpdateEvent
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
        Fitting plugin is used to perform fit 
    """
    def __init__(self):
        ## Plug-in name
        self.sub_menu = "Fitting"
        
        ## Reference to the parent window
        self.parent = None
        #Provide list of models existing in the application
        self.menu_mng = models.ModelManager()
        ## List of panels for the simulation perspective (names)
        self.perspective = []
        #list of panel to send to guiframe
        self.mypanels = []
        # reference to the current running thread
        self.calc_2D = None
        self.calc_1D = None
        self.calc_fit = None
        
        # Start with a good default
        self.elapsed = 0.022
        # the type of optimizer selected, park or scipy
        self.fitter  = None
        #let fit ready
        self.fitproblem_count = None
        #Flag to let the plug-in know that it is running stand alone
        self.standalone = True
        ## dictionary of page closed and id 
        self.closed_page_dict = {}
        ## Fit engine
        self._fit_engine = 'scipy'
        #List of selected data
        self.selected_data_list = []
        ## list of slicer panel created to display slicer parameters and results
        self.slicer_panels = []
        # model 2D view
        self.model2D_id = None
        #keep reference of the simultaneous fit page
        self.sim_page = None
        #dictionary containing data name and error on dy of that data 
        self.err_dy = {}
        self.theory_data = None  
        #Create a reader for fit page's state
        self.state_reader = None 
        # Log startup
        logging.info("Fitting plug-in started") 
        
    def populate_menu(self, id, owner):
        """
            Create a menu for the Fitting plug-in
            @param id: id to create a menu
            @param owner: owner of menu
            @ return : list of information to populate the main menu
        """
        #Menu for fitting
        self.menu1 = wx.Menu()
        
        #Set park engine
        id3 = wx.NewId()
        scipy_help= "Scipy Engine: Perform Simple fit. More in Help window...."
        self.menu1.AppendCheckItem(id3, "Simple Fit  [Scipy]",scipy_help) 
        wx.EVT_MENU(owner, id3,  self._onset_engine_scipy)
        
        id3 = wx.NewId()
        park_help = "Park Engine: Perform Complex fit. More in Help window...."
        self.menu1.AppendCheckItem(id3, "Complex Fit  [Park]",park_help) 
        wx.EVT_MENU(owner, id3,  self._onset_engine_park)
        
        self.menu1.FindItemByPosition(0).Check(True)
        self.menu1.FindItemByPosition(1).Check(False)
            
        self.menu1.AppendSeparator()
        id1 = wx.NewId()
        simul_help = "Allow to edit fit engine with multiple model and data"
        self.menu1.Append(id1, '&Simultaneous Page',simul_help)
        wx.EVT_MENU(owner, id1, self.on_add_sim_page)
       
        #menu for model
        menu2 = wx.Menu()
        self.menu_mng.populate_menu(menu2, owner)
        id2 = wx.NewId()
        owner.Bind(models.EVT_MODEL,self._on_model_menu)
      
        self.fit_panel.set_owner(owner)
        self.fit_panel.set_model_list(self.menu_mng.get_model_list())
        owner.Bind(fitpage.EVT_MODEL_BOX,self._on_model_panel)

        #create  menubar items
        return [(id, self.menu1, "Fitting")]
               
    def on_add_sim_page(self, event):
        """
            Create a page to access simultaneous fit option
        """
        Plugin.on_perspective(self,event=event)
        if self.sim_page !=None:
            msg= "Simultaneous Fit page already opened"
            wx.PostEvent(self.parent, StatusEvent(status= msg))
            return 
        
        self.sim_page= self.fit_panel.add_sim_page()
        
    def help(self, evt):
        """
            Show a general help dialog. 
            TODO: replace the text with a nice image
        """
        
        from help_panel import  HelpWindow
        frame = HelpWindow(None, -1, 'HelpWindow')    
        frame.Show(True)
        
        
    def get_context_menu(self, graph=None):
        """
            Get the context menu items available for P(r).them allow fitting option
            for Data2D and Data1D only.
            
            @param graph: the Graph object to which we attach the context menu
            @return: a list of menu items with call-back function
            @note: if Data1D was generated from Theory1D  
                    the fitting option is not allowed
        """
        self.graph = graph
        fit_option = "Select data for fitting"
        fit_hint =  "Dialog with fitting parameters "
       
        for item in graph.plottables:
            if item.__class__.__name__ is "Data2D":
                
                if hasattr(item,"is_data"):
                    if item.is_data:
                        return [[fit_option, fit_hint, self._onSelect]]
                    else:
                        return [] 
                return [[fit_option, fit_hint, self._onSelect]]
            else:
                if item.name == graph.selected_plottable :
                    if item.name in ["$I_{obs}(q)$","$I_{fit}(q)$","$P_{fit}(r)$"]:
                        return [] 
                    if hasattr(item, "group_id"):
                        # if is_data is true , this in an actual data loaded
                        #else it is a data created from a theory model
                        if hasattr(item,"is_data"):
                            if item.is_data:
                                return [[fit_option, fit_hint,
                                          self._onSelect]]
                            else:
                                return [] 
                        else:
                           return [[fit_option, fit_hint, self._onSelect]]
        return []   


    def get_panels(self, parent):
        """
            Create and return a list of panel objects
        """
        self.parent = parent
        # Creation of the fit panel
        self.fit_panel = FitPanel(self.parent, -1)
        #Set the manager for the main panel
        self.fit_panel.set_manager(self)
        # List of windows used for the perspective
        self.perspective = []
        self.perspective.append(self.fit_panel.window_name)
        # take care of saving  data, model and page associated with each other
        self.page_finder = {}
        #index number to create random model name
        self.index_model = 0
        self.index_theory= 0
        self.parent.Bind(EVT_SLICER_PANEL, self._on_slicer_event)
        self.parent.Bind(ERR_DATA, self._on_data_error)
        self.parent.Bind(EVT_REMOVE_DATA, self._closed_fitpage)
        self.parent.Bind(EVT_SLICER_PARS_UPDATE, self._onEVT_SLICER_PANEL)
        self.parent._mgr.Bind(wx.aui.EVT_AUI_PANE_CLOSE,self._onclearslicer)    
        #Create reader when fitting panel are created
        self.state_reader = Reader(self.set_state)   
        #append that reader to list of available reader 
        loader = Loader()
        loader.associate_file_reader(".fitv", self.state_reader)
        #Send the fitting panel to guiframe
        self.mypanels.append(self.fit_panel)
        return self.mypanels
    
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
        """
        self.parent.set_perspective(self.perspective)
   
    def set_default_perspective(self):
        """
           Call back method that True to notify the parent that the current plug-in
           can be set as default  perspective.
           when returning False, the plug-in is not candidate for an automatic 
           default perspective setting
        """
        return True
    
    def post_init(self):
        """
            Post initialization call back to close the loose ends
        """
        pass
    
    def set_state(self, state, datainfo=None):
        """
            Call-back method for the fit page state reader.
            This method is called when a .fitv file is loaded.
            @param state: PageState object
        """
        #working on reading state
        return 
        try: 
            # Load fitting state
            page = self.fit_panel.set_state(state)   
            # Make sure the user sees the fitting panel after loading
            self.parent.set_perspective(self.perspective)   
                   
        except:
            raise
        
    def save_fit_state(self, filepath, fitstate):  
        """
            save fit page state into file
        """
        self.state_reader.write(filename=filepath, fitstate=fitstate)
        
    def copy_data(self, item, dy=None):
        """
            receive a data 1D and the list of errors on dy
            and create a new data1D data
            @param return 
        """
        id = None
        if hasattr(item,"id"):
            id = item.id

        data= Data1D(x=item.x, y=item.y,dx=None, dy=None)
        data.copy_from_datainfo(item)
        item.clone_without_data(clone=data)    
        data.dy = deepcopy(dy)
        data.name = item.name
        ## allow to highlight data when plotted
        data.interactive = deepcopy(item.interactive)
        ## when 2 data have the same id override the 1 st plotted
        data.id = id
        data.group_id = item.group_id
        return data
    
    def set_fit_range(self, page, qmin, qmax):
        """
            Set the fitting range of a given page
        """
        if page in self.page_finder.iterkeys():
            fitproblem= self.page_finder[page]
            fitproblem.set_range(qmin= qmin, qmax= qmax)
                    
    def schedule_for_fit(self,value=0,page=None,fitproblem =None):  
        """
            Set the fit problem field to 0 or 1 to schedule that problem to fit.
            Schedule the specified fitproblem or get the fit problem related to 
            the current page and set value.
            @param value : integer 0 or 1 
            @param fitproblem: fitproblem to schedule or not to fit
        """   
        if fitproblem !=None:
            fitproblem.schedule_tofit(value)
        else:
            if page in self.page_finder.iterkeys():
                fitproblem= self.page_finder[page]
                fitproblem.schedule_tofit(value)
          
    def get_page_finder(self):
        """ @return self.page_finder used also by simfitpage.py"""  
        return self.page_finder 
    
    
    def set_page_finder(self,modelname,names,values):
        """
             Used by simfitpage.py to reset a parameter given the string constrainst.
             @param modelname: the name ot the model for with the parameter has to reset
             @param value: can be a string in this case.
             @param names: the paramter name
             @note: expecting park used for fit.
        """  
        sim_page= self.sim_page
        for page, value in self.page_finder.iteritems():
            if page != sim_page:
                list=value.get_model()
                model = list[0]
                if model.name== modelname:
                    value.set_model_param(names,values)
                    break
         
    def split_string(self,item): 
        """
            receive a word containing dot and split it. used to split parameterset
            name into model name and parameter name example:
            paramaterset (item) = M1.A
            @return model_name =M1 , parameter name =A
        """
        if string.find(item,".")!=-1:
            param_names= re.split("\.",item)
            model_name=param_names[0]           
            ##Assume max len is 3; eg., M0.radius.width
            if len(param_names) == 3:
                param_name=param_names[1]+"."+param_names[2]
            else:
                param_name=param_names[1]                    
            return model_name,param_name
        
    def stop_fit(self):
        """
            Stop the fit engine
        """
        if self.calc_fit!= None and self.calc_fit.isrunning():
            self.calc_fit.stop()
            wx.PostEvent(self.parent, StatusEvent(status="Fitting  \
                is cancelled" , type="stop"))
           
    def set_smearer_nodraw(self,smearer, qmin=None, qmax=None):
        """
            Get a smear object and store it to a fit problem
            @param smearer: smear object to allow smearing data
        """  
        self.current_pg=self.fit_panel.get_current_page()
        self.page_finder[self.current_pg].set_smearer(smearer)
        ## draw model 1D with smeared data
        data =  self.page_finder[self.current_pg].get_fit_data()
        model = self.page_finder[self.current_pg].get_model()
        ## if user has already selected a model to plot
        ## redraw the model with data smeared
        
        smear =self.page_finder[self.current_pg].get_smearer()   
            
    def set_smearer(self,smearer, qmin=None, qmax=None):
        """
            Get a smear object and store it to a fit problem
            @param smearer: smear object to allow smearing data
        """   
        self.current_pg=self.fit_panel.get_current_page()
        self.page_finder[self.current_pg].set_smearer(smearer)
        ## draw model 1D with smeared data
        data =  self.page_finder[self.current_pg].get_fit_data()
        model = self.page_finder[self.current_pg].get_model()
        ## if user has already selected a model to plot
        ## redraw the model with data smeared

        smear =self.page_finder[self.current_pg].get_smearer()
        if model!= None:
            self.draw_model( model=model, data= data, smearer= smear,
                qmin= qmin, qmax= qmax)

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

        if data.__class__.__name__ !="Data2D":    
            ## draw model 1D with no loaded data
            self._draw_model1D( model= model, data= data,
                                                    enable1D=enable1D, 
                                                    smearer= smearer,
                                                    qmin= qmin, qmax= qmax, qstep= qstep )
        else:     
            ## draw model 2D with no initial data
             self._draw_model2D(model=model,
                                      data = data,
                                      enable2D= enable2D,
                                      smearer= smearer,
                                      qmin=qmin,
                                      qmax=qmax,
                                      qstep=qstep)
            
    def onFit(self):
        """
            perform fit 
        """
        ##  count the number of fitproblem schedule to fit 
        fitproblem_count= 0
        for value in self.page_finder.itervalues():
            if value.get_scheduled()==1:
                fitproblem_count += 1
                
        ## if simultaneous fit change automatically the engine to park
        if fitproblem_count >1:
            self._on_change_engine(engine='park')
            
        self.fitproblem_count = fitproblem_count  
          
        from sans.fit.Fitting import Fit
        self.fitter= Fit(self._fit_engine)
        
        if self._fit_engine=="park":
            engineType="Simultaneous Fit"
        else:
            engineType="Single Fit"
            
        fproblemId = 0
        self.current_pg=None
        for page, value in self.page_finder.iteritems():
            try:
                if value.get_scheduled()==1:
                    #Get list of parameters name to fit
                    pars = []
                    templist = []
                    templist = page.get_param_list()
                    for element in templist:
                        name = str(element[1])
                        pars.append(name)
                    #Set Engine  (model , data) related to the page on 
                    self._fit_helper( value=value,pars=pars,
                                      id=fproblemId, title= engineType ) 
                    fproblemId += 1 
                    self.current_pg= page
            except:
                msg= "%s error: %s" % (engineType,sys.exc_value)
                wx.PostEvent(self.parent, StatusEvent(status=msg, info="error",
                                                      type="stop"))
                return 
        ## If a thread is already started, stop it
        #if self.calc_fit!= None and self.calc_fit.isrunning():
        #    self.calc_fit.stop()
         #Handler used for park engine displayed message
        handler = ConsoleUpdate(parent=self.parent,improvement_delta=0.1)
        ## perform single fit
        if fitproblem_count == 1:
            calc_fit=FitThread(parent =self.parent,
                                    handler = handler,
                                    fn= self.fitter,
                                   cpage=self.current_pg,
                                   pars= pars,
                                   updatefn=handler.update_fit,
                                   completefn= self._single_fit_completed)
        else:
            ## Perform more than 1 fit at the time
            calc_fit=FitThread(parent=self.parent,
                                handler=handler,
                                    fn= self.fitter,
                                   completefn= self._simul_fit_completed,
                                  updatefn=handler.update_fit)
        
        calc_fit.queue()
        self.ready_fit(calc_fit=calc_fit)
      
    def ready_fit(self, calc_fit):
        """
        Ready for another fit
        """
        if self.fitproblem_count != None and self.fitproblem_count > 1:
            calc_fit.ready(2.5)
            
        else:
            time.sleep(0.4)
            
    def remove_plot(self, page, theory=False):
        """
            remove model plot when a fit page is closed
        """
        fitproblem = self.page_finder[page]
        data = fitproblem.get_fit_data()
        model = fitproblem.get_model()
        if model is not None:
            name = model.name
            new_plot = Theory1D(x=[], y=[], dy=None)
            new_plot.name = name
            new_plot.xaxis(data._xaxis, data._xunit)
            new_plot.yaxis(data._yaxis, data._yunit)
            new_plot.group_id = data.group_id
            new_plot.id = data.id + name
            wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot, title=data.name))
        if theory:
            new_plot_data = Data1D(x=[], y=[], dx=None, dy=None)
            new_plot_data.name = data.name
            new_plot_data.xaxis(data._xaxis, data._xunit)
            new_plot_data.yaxis(data._yaxis, data._yunit)
            new_plot_data.group_id = data.group_id
            new_plot_data.id = data.id 
            wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot_data,
                                                    title=data.name))
    def create_fittable_data2D(self, data):
        """
            check if the current data is a data 2d and add dy to that data
            @return Data2D
        """
        if data.__class__.__name__ != "Data2D":
            raise ValueError, " create_fittable_data2D expects a Data2D"
        ## Data2D case
        new_data = deepcopy(data)
        if not hasattr(data, "is_data"):
            new_data.group_id += "data2D"
            new_data.id +="data2D"
            new_data.is_data = False
            title = new_data.name
            title += " Fit"
            wx.PostEvent(self.parent, NewPlotEvent(plot=new_data,
                                                    title=str(title)))
        else:
            new_data.is_data = True
        return new_data
        
    def create_fittable_data1D(self, data):
        """
            check if the current data is a theory 1d and add dy to that data
            @return Data1D
        """
        class_name = data.__class__.__name__
        if not class_name in ["Data1D", "Theory1D"]:
            raise ValueError, "create_fittable_data1D expects Data1D"
      
        #get the appropriate dy 
        dy = deepcopy(data.dy)
        if len(self.err_dy) > 0:
            if data.name in  self.err_dy.iterkeys():
                dy = self.err_dy[data.name]   
        if data.__class__.__name__ == "Theory1D":
            new_data = self.copy_data(data, dy)
            new_data.group_id = str(new_data.group_id)+"data1D"
            new_data.id = str(new_data.id)+"data1D"
            new_data.is_data = False
            title = new_data.name
            title = 'Data created from Theory'
            wx.PostEvent(self.parent, NewPlotEvent(plot=new_data,
                                                    title=str(title),
                                                   reset=True))
        else:
            new_data = self.copy_data(data, dy) 
            new_data.id = data.id 
            new_data.is_data = True
        return new_data
           
    def store_page(self, page, data):
        """
            Helper to save page reference into the plug-in
            @param page: page to store
        """
        page.set_data(data) 
        #create a fitproblem storing all link to data,model,page creation
        if not page in self.page_finder.keys():
            self.page_finder[page] = FitProblem()
        self.page_finder[page].add_fit_data(data)
        
    def add_fit_page(self, data):
        """
            given a data, ask to the fitting panel to create a new fitting page,
            get this page and store it into the page_finder of this plug-in
        """
        try:
            page = self.fit_panel.add_fit_page(data)
            # add data associated to the page created
            if page != None:  
                self.store_page(page=page, data=data)
                wx.PostEvent(self.parent, StatusEvent(status="Page Created",
                                               info="info"))
            else:
                msg = "Page was already Created"
                wx.PostEvent(self.parent, StatusEvent(status=msg, info="warning"))
        except:
            msg = "Creating Fit page: %s"%sys.exc_value
            wx.PostEvent(self.parent, StatusEvent(status=msg, info="error"))
       
    def _onEVT_SLICER_PANEL(self, event):
        """
            receive and event telling to update a panel with a name starting with 
            event.panel_name. this method update slicer panel for a given interactor.
            @param event: contains type of slicer , paramaters for updating the panel
            and panel_name to find the slicer 's panel concerned.
        """
        for item in self.parent.panels:
            if self.parent.panels[item].window_caption.startswith(event.panel_name):
                self.parent.panels[item].set_slicer(event.type, event.params)
                
        self.parent._mgr.Update()
   
              
    def _closed_fitpage(self, event):   
        """
            request fitpanel to close a given page when its unique data is removed 
            from the plot. close fitpage only when the a loaded data is removed
        """    
        if event is None or event.data is None:
            return
       
        if hasattr(event.data,"is_data"):
            if not event.data.is_data or event.data.__class__.__name__=="Data1D":
                self.fit_panel.close_page_with_data(event.data) 
        
    def _add_page_onmenu(self, name,fitproblem=None):
        """
            Add name of a closed page of fitpanel in a menu 
        """
        list = self.menu1.GetMenuItems()
        for item in list:
            if name == item.GetItemLabel():
                self.closed_page_dict[name][1] = fitproblem
                
        if not name in self.closed_page_dict.keys():    
            # Post paramters
            event_id = wx.NewId()
            self.menu1.Append(event_id, name, "Show %s fit panel" % name)
            self.closed_page_dict[name]= [event_id, fitproblem]
            wx.EVT_MENU(self.parent,event_id,  self._open_closed_page)
        
        
    def _open_closed_page(self, event):    
        """
            reopen a closed page
        """
        for name, value in self.closed_page_dict.iteritems():
            if event.GetId() in value:
                id,fitproblem = value
                if name !="Model":
                    data= fitproblem.get_fit_data()
                    page = self.fit_panel.add_fit_page(data= data,reset=True)
                    if fitproblem != None:
                        self.page_finder[page]=fitproblem
                        if self.sim_page != None:
                            self.sim_page.draw_page()
                            
                else:
                    model = fitproblem
                    self.fit_panel.add_model_page(model=model, topmenu=True,
                                                  reset= True)
                    break
        
        
    def _reset_schedule_problem(self, value=0):
        """
             unschedule or schedule all fitproblem to be fit
        """
        for page, fitproblem in self.page_finder.iteritems():
            fitproblem.schedule_tofit(value)
            
    def _fit_helper(self,pars,value, id, title="Single Fit " ):
        """
            helper for fitting
        """
        metadata = value.get_fit_data()
        model = value.get_model()
        smearer = value.get_smearer()
        qmin , qmax = value.get_range()
        self.fit_id =id
        #Create list of parameters for fitting used
        templist=[]
       
        try:
            #Extra list of parameters and their constraints
            listOfConstraint= []
            
            param = value.get_model_param()
            if len(param)>0:
                for item in param:
                    ## check if constraint
                    if item[0] !=None and item[1] != None:
                        listOfConstraint.append((item[0],item[1]))
                   
            #Do the single fit
            self.fitter.set_model(model, self.fit_id,
                                   pars,constraints = listOfConstraint)
            
            self.fitter.set_data(data=metadata,Uid=self.fit_id,
                                 smearer=smearer,qmin= qmin,qmax=qmax )
           
            self.fitter.select_problem_for_fit(Uid= self.fit_id,
                                               value= value.get_scheduled())
            value.clear_model_param()
        except:
            msg= title +" error: %s" % sys.exc_value
            wx.PostEvent(self.parent, StatusEvent(status= msg, type="stop"))
            return
       
    def _onSelect(self,event):
        """ 
            when Select data to fit a new page is created .Its reference is 
            added to self.page_finder
        """
        self.panel = event.GetEventObject()
        Plugin.on_perspective(self,event=event)
        for plottable in self.panel.graph.plottables:
            if plottable.__class__.__name__ in ["Data1D", "Theory1D"]:
                if plottable.name == self.panel.graph.selected_plottable:
                    data = self.create_fittable_data1D(data=plottable)
                    self.add_fit_page(data=data)
                    return
            else:
                data = self.create_fittable_data2D(data=plottable)
                self.add_fit_page(data=data)
            
    def _single_fit_completed(self,result,pars,cpage, elapsed=None):
        """
            Display fit result on one page of the notebook.
            @param result: result of fit 
            @param pars: list of names of parameters fitted
            @param current_pg: the page where information will be displayed
            @param qmin: the minimum value of x to replot the model 
            @param qmax: the maximum value of x to replot model
          
        """     
        try:
            if result ==None:
                msg= "Simple Fitting Stop !!!"
                wx.PostEvent(self.parent, StatusEvent(status=msg,info="warning",
                                                      type="stop"))
                return
            if not numpy.isfinite(result.fitness) or numpy.any(result.pvec ==None )or not numpy.all(numpy.isfinite(result.pvec) ):
                msg= "Single Fitting did not converge!!!"
                wx.PostEvent(self.parent, StatusEvent(status=msg,type="stop"))
                return
            for page, value in self.page_finder.iteritems():
                if page==cpage :
                    model= value.get_model()
                    break
            param_name = []
            i = 0
            for name in pars:
                param_name.append(name)

            cpage.onsetValues(result.fitness,param_name, result.pvec,result.stderr)
           
        except:
            msg= "Single Fit completed but Following error occurred:%s"% sys.exc_value
            wx.PostEvent(self.parent, StatusEvent(status=msg, info="error",
                                                  type="stop"))
            return
       
       
    def _simul_fit_completed(self,result,pars=None,cpage=None, elapsed=None):
        """
            Parameter estimation completed, 
            display the results to the user
            @param alpha: estimated best alpha
            @param elapsed: computation time
        """
        ## fit more than 1 model at the same time 
        try:
            msg = "" 
            if result ==None:
                msg= "Complex Fitting Stop !!!"
                wx.PostEvent(self.parent, StatusEvent(status=msg,type="stop"))
                return
            if not numpy.isfinite(result.fitness) or numpy.any(result.pvec ==None )or not numpy.all(numpy.isfinite(result.pvec) ):
                msg= "Single Fitting did not converge!!!"
                wx.PostEvent(self.parent, StatusEvent(status=msg,type="stop"))
                return
              
            for page, value in self.page_finder.iteritems():   
                if value.get_scheduled()==1:
                    model = value.get_model()
                    data =  value.get_fit_data()
                    small_param_name = []
                    small_out = []
                    small_cov = []
                    i = 0
                    #Separate result in to data corresponding to each page
                    for p in result.parameters:
                        model_name,param_name = self.split_string(p.name)  
                        if model.name == model_name:
                            p_name= model.name+"."+param_name
                            if p.name == p_name:      
                                if p.value != None and numpy.isfinite(p.value):
                                    small_out.append(p.value )
                                    small_param_name.append(param_name)
                                    small_cov.append(p.stderr)

                    # Display result on each page 
                    page.onsetValues(result.fitness, small_param_name,small_out,small_cov)
        except:
             msg= "Simultaneous Fit completed"
             msg +=" but Following error occurred:%s"%sys.exc_value
             wx.PostEvent(self.parent, StatusEvent(status=msg,type="stop"))
             return 
             
                           
        
    def _on_show_panel(self, event):
        print "_on_show_panel: fitting"
      
      
    def _onset_engine_park(self,event):
        """ 
            set engine to park
        """
        Plugin.on_perspective(self,event=event)
        self._on_change_engine('park')
       
       
    def _onset_engine_scipy(self,event):
        """ 
            set engine to scipy
        """
        self._on_change_engine('scipy')
       
    def _on_slicer_event(self, event):
        """
            Receive a panel as event and send it to guiframe 
            @param event: event containing a panel
        """
       
        if event.panel!=None:
            new_panel = event.panel
            self.slicer_panels.append(event.panel)
            # Set group ID if available
            event_id = self.parent.popup_panel(new_panel)
            #self.menu3.Append(event_id, new_panel.window_caption, 
            #                 "Show %s plot panel" % new_panel.window_caption)
            # Set UID to allow us to reference the panel later
         
            new_panel.uid = event_id
            self.mypanels.append(new_panel) 
        return  
    
    def _onclearslicer(self, event):
        """
            Clear the boxslicer when close the panel associate with this slicer
        """
        name =event.GetPane().caption
    
        for panel in self.slicer_panels:
            if panel.window_caption==name:
                
                for item in self.parent.panels:
                    if hasattr(self.parent.panels[item],"uid"):
                        if self.parent.panels[item].uid ==panel.base.uid:
                            self.parent.panels[item].onClearSlicer(event)
                            self.parent._mgr.Update()
                            break 
                break
       
       
        
        
    def _return_engine_type(self):
        """
            return the current type of engine
        """
        return self._fit_engine
     
     
    def _on_change_engine(self, engine='park'):
        """
            Allow to select the type of engine to perform fit 
            @param engine: the key work of the engine
        """
       
        ## saving fit engine name
        self._fit_engine = engine
        ## change menu item state
        if engine=="park":
            self.menu1.FindItemByPosition(0).Check(False)
            self.menu1.FindItemByPosition(1).Check(True)
        else:
            self.menu1.FindItemByPosition(0).Check(True)
            self.menu1.FindItemByPosition(1).Check(False)
            
        ## post a message to status bar
        wx.PostEvent(self.parent, StatusEvent(status="Engine set to: %s" % self._fit_engine))
   
        ## Bind every open fit page with a newevent to know the current fitting engine
        import fitpage
        event= fitpage.FitterTypeEvent()
        event.type = self._fit_engine
        for key in self.page_finder.keys():
            wx.PostEvent(key, event)
       
   
    def _on_model_panel(self, evt):
        """
            react to model selection on any combo box or model menu.plot the model  
            @param evt: wx.combobox event
        """
        model = evt.model
        if model == None:
            return
        smearer = None
        qmin = None
        qmax = None
        if hasattr(evt, "qmin"):
            qmin = evt.qmin
        if hasattr(evt, "qmax"):
            qmax = evt.qmax
        if hasattr(evt, "smearer"):
            smearer = evt.smearer
        model.origin_name = model.name
        self.current_pg = self.fit_panel.get_current_page() 
        ## make sure nothing is done on self.sim_page
        ## example trying to call set_panel on self.sim_page
        if self.current_pg != self.sim_page :
            if self.page_finder[self.current_pg].get_model()== None :
                
                model.name = "M"+str(self.index_model)
                self.index_model += 1  
            else:
                model.name= self.page_finder[self.current_pg].get_model().name
            
            data = self.page_finder[self.current_pg].get_fit_data()
            
            # save the name containing the data name with the appropriate model
            self.page_finder[self.current_pg].set_model(model)
            qmin, qmax= self.current_pg.get_range()
            self.page_finder[self.current_pg].set_range(qmin=qmin, qmax=qmax)
            smearer=  self.page_finder[self.current_pg].get_smearer()
            # save model name
            self.set_smearer(smearer=smearer, qmin=qmin, qmax=qmax)
            
            if self.sim_page!=None:
                self.sim_page.draw_page()
        
    def _on_model_menu(self, evt):
        """
            Plot a theory from a model selected from the menu
            @param evt: wx.menu event
        """
        model = evt.model
        Plugin.on_perspective(self,event=evt)
        # Create a model page. If a new page is created, the model
        # will be plotted automatically. If a page already exists,
        # the content will be updated and the plot refreshed
        self.fit_panel.add_model_page(model,topmenu=True)
    
   
    
    
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
        theory.err_data = numpy.ones(len(mask))
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
                
                
    def _complete1D(self, x,y, elapsed,index,model,data=None):
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
           
            title= new_plot.name
            # x, y are only in range of index 
            self.theory_data = new_plot
            #new_plot.perspective = self.get_perspective()
            # Pass the reset flag to let the plotting event handler
            # know that we are replacing the whole plot
            if title== None:
                title = "Analytical model 1D "
            if data ==None:
                wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot,
                             title=str(title), reset=True))
            else:
                wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot,title= str(title)))
            # Chisqr in fitpage
            current_pg=self.fit_panel.get_current_page()
            wx.PostEvent(current_pg,Chi2UpdateEvent(output=self._cal_chisqr(data=data,index=index)))
            msg = "Plot 1D  complete !"
            wx.PostEvent( self.parent, StatusEvent(status=msg , type="stop" ))
        except:
            msg= " Error occurred when drawing %s Model 1D: "%new_plot.name
            msg+= " %s"%sys.exc_value
            wx.PostEvent( self.parent, StatusEvent(status= msg, type="stop"))
            return  
                  
    def _update2D(self, output,time=None):
        """
            Update the output of plotting model
        """
        wx.PostEvent(self.parent, StatusEvent(status="Plot \
        #updating ... ",type="update"))
        self.ready_fit()
        #self.calc_thread.ready(0.01)
        
        
    def _complete2D(self, image,data, model,  elapsed,index,qmin, qmax,qstep=DEFAULT_NPTS):
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
            theory.err_data = err_image#numpy.zeros(len(data.err_data))#data.err_data
            theory.mask = data.mask
            ## plot boundaries
            theory.ymin= data.ymin
            theory.ymax= data.ymax
            theory.xmin= data.xmin
            theory.xmax= data.xmax
            
        self.theory_data = theory
        ## plot
        wx.PostEvent(self.parent, NewPlotEvent(plot=theory,
                         title="Analytical model 2D ", reset=True ))
        # Chisqr in fitpage
        current_pg=self.fit_panel.get_current_page()
        wx.PostEvent(current_pg,Chi2UpdateEvent(output=self._cal_chisqr(data=data,index=index)))
        msg = "Plot 2D complete !"
        wx.PostEvent( self.parent, StatusEvent( status= msg , type="stop" ))
     
    def _on_data_error(self, event):
        """
            receives and event from plotting plu-gins to store the data name and 
            their errors of y coordinates for 1Data hide and show error
        """
        self.err_dy = event.err_dy
         
    def _draw_model2D(self,model,data=None, smearer= None,description=None, enable2D=False,
                      qmin=DEFAULT_QMIN, qmax=DEFAULT_QMAX, qstep=DEFAULT_NPTS):
        """
            draw model in 2D
            @param model: instance of the model to draw
            @param description: the description of the model
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
            return None,None
        try:
            from model_thread import Calc2D
            ## If a thread is already started, stop it
            if self.calc_2D != None and self.calc_2D.isrunning():
                self.calc_2D.stop()

            self.calc_2D = Calc2D(  x= x,
                                    y= y,
                                    model= model, 
                                    data = data,
                                    smearer = smearer,
                                    qmin= qmin,
                                    qmax= qmax,
                                    qstep= qstep,
                                    completefn= self._complete2D,
                                    updatefn= self._update2D )
            self.calc_2D.queue()

        except:
            msg= " Error occurred when drawing %s Model 2D: "%model.name
            msg+= " %s"%sys.exc_value
            wx.PostEvent( self.parent, StatusEvent(status= msg ))

   
    def _draw_model1D(self, model, data=None, smearer= None,
                qmin=DEFAULT_QMIN, qmax=DEFAULT_QMAX, qstep= DEFAULT_NPTS,enable1D= True):
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
            msg= " Error occurred when drawing %s Model 1D: "%model.name
            msg+= " %s"%sys.exc_value
            wx.PostEvent( self.parent, StatusEvent(status= msg ))

    def _cal_chisqr(self, data=None, index=None): 
        """
            Get handy Chisqr using the output from draw1D and 2D, 
            instead of calling expansive CalcChisqr in guithread
        """
        # default chisqr
        chisqr = None
        
        # return None if data == None
        if data == None: return chisqr
        
        # Get data: data I, theory I, and data dI in order
        if data.__class__.__name__ =="Data2D":
            if index == None: index = numpy.ones(len(data.data),ntype=bool)
            index = index & (data.err_data !=0 )   # get rid of zero error points
            fn = data.data[index] 
            gn = self.theory_data.data[index]
            en = data.err_data[index]
        else:
            # 1 d theory from model_thread is only in the range of index
            if index == None: index = numpy.ones(len(data.y),ntype=bool)
            if data.dy== None or data.dy ==[]:
                dy = numpy.ones(len(data.y))
            else:
                ## Set consitently w/AbstractFitengine: But this should be corrected later.
                dy = data.dy
                dy[dy==0] = 1  
            fn = data.y[index] 
            gn = self.theory_data.y
            en = dy[index]

        # residual
        res = (fn - gn)/en
        # get chisqr only w/finite
        chisqr = numpy.average(res[numpy.isfinite(res)]*res[numpy.isfinite(res)])

        return chisqr
    
    
def profile(fn, *args, **kw):
    import cProfile, pstats, os
    global call_result
    def call():
        global call_result
        call_result = fn(*args, **kw)
    cProfile.runctx('call()', dict(call=call), {}, 'profile.out')
    stats = pstats.Stats('profile.out')
    #stats.sort_stats('time')
    stats.sort_stats('calls')
    stats.print_stats()
    os.unlink('profile.out')
    return call_result
if __name__ == "__main__":
    i = Plugin()
    
    
    
    