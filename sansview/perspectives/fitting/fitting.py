

################################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation. 
#
#See the license text in license.txt
#
#copyright 2009, University of Tennessee
################################################################################


import re
import sys
import wx
import logging
import numpy
import string
import time
from copy import deepcopy
import models
import fitpage


from DataLoader.loader import Loader
from sans.guiframe.dataFitting import Data2D
from sans.guiframe.dataFitting import Data1D
from sans.guiframe.events import NewPlotEvent 
from sans.guiframe.events import StatusEvent  
from sans.guiframe.events import EVT_SLICER_PANEL
from sans.guiframe.events import EVT_REMOVE_DATA
from sans.guiframe.events import EVT_SLICER_PARS_UPDATE
from sans.guiframe.gui_style import GUIFRAME_ID
from sans.guiframe.plugin_base import PluginBase 

from .console import ConsoleUpdate
from .fitproblem import FitProblem
from .fitpanel import FitPanel
from .fit_thread import FitThread
from .pagestate import Reader
from .fitpage import Chi2UpdateEvent

DEFAULT_BEAM = 0.005
DEFAULT_QMIN = 0.001
DEFAULT_QMAX = 0.13
DEFAULT_NPTS = 50
MAX_NBR_DATA = 4


(PageInfoEvent, EVT_PAGE_INFO)   = wx.lib.newevent.NewEvent()

   

class Plugin(PluginBase):
    """
    Fitting plugin is used to perform fit 
    """
    def __init__(self, standalone=False):
        PluginBase.__init__(self, name="Model Fitting", standalone=standalone)
        
        #list of panel to send to guiframe
        self.mypanels = []
        # reference to the current running thread
        self.calc_2D = None
        self.calc_1D = None
        self.fit_thread_list = {}
        self.residuals = None
        self.fit_panel = None
        # Start with a good default
        self.elapsed = 0.022
        # the type of optimizer selected, park or scipy
        self.fitter  = None
        self.fit_panel = None
        #let fit ready
        self.fitproblem_count = None
        #Flag to let the plug-in know that it is running stand alone
        self.standalone = True
        ## dictionary of page closed and id 
        self.closed_page_dict = {}
        ## Fit engine
        self._fit_engine = 'scipy'
        ## Relative error desired in the sum of squares (float); scipy only
        self.ftol=1.49012e-08
        #List of selected data
        self.selected_data_list = []
        ## list of slicer panel created to display slicer parameters and results
        self.slicer_panels = []
        # model 2D view
        self.model2D_id = None
        #keep reference of the simultaneous fit page
        self.sim_page = None
        self.index_model = 0
        #Create a reader for fit page's state
        self.state_reader = None 
        self._extensions = '.fitv'
        self.temp_state = []
        self.state_index = 0
        self.sfile_ext = None
        # take care of saving  data, model and page associated with each other
        self.page_finder = {}
        # Log startup
        logging.info("Fitting plug-in started") 
        
    def populate_menu(self, owner):
        """
        Create a menu for the Fitting plug-in
        
        :param id: id to create a menu
        :param owner: owner of menu
        
        :return: list of information to populate the main menu
        
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
        simul_help = "Simultaneous Fit"
        self.menu1.Append(id1, '&Simultaneous Fit',simul_help)
        wx.EVT_MENU(owner, id1, self.on_add_sim_page)
        
        id1 = wx.NewId()
        simul_help = "Add new fit panel"
        self.menu1.Append(id1, '&New Fit Page',simul_help)
        wx.EVT_MENU(owner, id1, self.on_add_new_page)
    
        #create  menubar items
        return [(self.menu1, "FitEngine")]
               
    def on_add_sim_page(self, event):
        """
        Create a page to access simultaneous fit option
        """
        if self.sim_page != None:
            msg= "Simultaneous Fit page already opened"
            wx.PostEvent(self.parent, StatusEvent(status= msg))
            return 
        
        self.sim_page= self.fit_panel.add_sim_page()
        
    def help(self, evt):
        """
        Show a general help dialog. 
        """
        from help_panel import  HelpWindow
        frame = HelpWindow(None, -1, 'HelpWindow')    
        frame.Show(True)
        
    def get_context_menu(self, plotpanel=None):
        """
        Get the context menu items available for P(r).them allow fitting option
        for Data2D and Data1D only.
        
        :param graph: the Graph object to which we attach the context menu
        
        :return: a list of menu items with call-back function
        
        :note: if Data1D was generated from Theory1D  
                the fitting option is not allowed
                
        """
        graph = plotpanel.graph
        fit_option = "Select data for fitting"
        fit_hint =  "Dialog with fitting parameters "
        
        if graph.selected_plottable not in plotpanel.plots:
            return []
        item = plotpanel.plots[graph.selected_plottable]
        if item.__class__.__name__ is "Data2D": 
            if hasattr(item,"is_data"):
                if item.is_data:
                    return [[fit_option, fit_hint, self._onSelect]]
                else:
                    return [] 
            return [[fit_option, fit_hint, self._onSelect]]
        else:
            
            # if is_data is true , this in an actual data loaded
            #else it is a data created from a theory model
            if hasattr(item,"is_data"):
                if item.is_data:
                    return [[fit_option, fit_hint,
                              self._onSelect]]
                else:
                    return [] 
        return []   


    def get_panels(self, parent):
        """
        Create and return a list of panel objects
        """
        self.parent = parent
        #self.parent.Bind(EVT_FITSTATE_UPDATE, self.on_set_state_helper)
        # Creation of the fit panel
        self.fit_panel = FitPanel(parent=self.parent, manager=self)
        self.on_add_new_page(event=None)
        #Set the manager for the main panel
        self.fit_panel.set_manager(self)
        # List of windows used for the perspective
        self.perspective = []
        self.perspective.append(self.fit_panel.window_name)
       
        #index number to create random model name
        self.index_model = 0
        self.index_theory= 0
        self.parent.Bind(EVT_SLICER_PANEL, self._on_slicer_event)
       
        self.parent.Bind(EVT_REMOVE_DATA, self._closed_fitpage)
        self.parent.Bind(EVT_SLICER_PARS_UPDATE, self._onEVT_SLICER_PANEL)
        self.parent._mgr.Bind(wx.aui.EVT_AUI_PANE_CLOSE,self._onclearslicer)    
        #Create reader when fitting panel are created
        self.state_reader = Reader(self.set_state)   
        #append that reader to list of available reader 
        loader = Loader()
        loader.associate_file_reader(".fitv", self.state_reader)
        loader.associate_file_reader(".svs", self.state_reader)
        from sans.perspectives.calculator.sld_panel import SldPanel
        #Send the fitting panel to guiframe
        self.mypanels.append(self.fit_panel) 
        self.mypanels.append(SldPanel(parent=self.parent, base=self.parent))
        return self.mypanels
    
    def clear_panel(self):
        """
        """
        self.fit_panel.clear_panel()
        
    def set_default_perspective(self):
        """
        Call back method that True to notify the parent that the current plug-in
        can be set as default  perspective.
        when returning False, the plug-in is not candidate for an automatic 
        default perspective setting
        """
        return True
    
    def delete_data(self, data):
        """
        delete  the given data from panel
        """
        self.fit_panel.delete_data(data)
        
    def set_data(self, data_list=None):
        """
        receive a list of data to fit
        """
        if data_list is None:
            data_list = []
        selected_data_list = []
        if len(data_list) > MAX_NBR_DATA :
            from fitting_widgets import DataDialog
            dlg = DataDialog(data_list=data_list, nb_data=MAX_NBR_DATA)
            if dlg.ShowModal() == wx.ID_OK:
                selected_data_list = dlg.get_data()
        else:
            selected_data_list = data_list
        try:
            for data in selected_data_list:
                self.add_fit_page(data=data)
                wx.PostEvent(self.parent, NewPlotEvent(plot=data, 
                                                       title=str(data.title)))
                
        except:
            raise
            #msg = "Fitting Set_data: " + str(sys.exc_value)
            #wx.PostEvent(self.parent, StatusEvent(status=msg, info="error"))
    
    def set_top_panel(self):
        """
        Close default (welcome) panel
        """
        if 'default' in self.parent.panels:
            self.parent.on_close_welcome_panel()

             
    def set_theory(self,  theory_list=None):
        """
        """
        #set the model state for a given theory_state:
        for item in theory_list:
            try:
                _, theory_state = item
                self.fit_panel.set_model_state(theory_state)
            except:
                msg = "Fitting: cannot deal with the theory received"
                logging.error("set_theory " + msg + "\n" + str(sys.exc_value))
                wx.PostEvent(self.parent, StatusEvent(status=msg, info="error"))
            
    def set_state(self, state=None, datainfo=None, format=None):
        """
        Call-back method for the fit page state reader.
        This method is called when a .fitv/.svs file is loaded.
        
        : param state: PageState object
        : param datainfo: data
        """
        #state = self.state_reader.get_state()
        if state != None:
            # store fitting state in temp_state
            self.temp_state.append(state) 
        else:
            self.temp_state = []
        # index to start with for a new set_state
        self.state_index = 0
        # state file format
        self.sfile_ext = format
        
        self.on_set_state_helper(event=None)

    def  on_set_state_helper(self,event=None):
        """
        Set_state_helper. This actually sets state after plotting data from state file.
        
        : event: FitStateUpdateEvent called by dataloader.plot_data from guiframe
        """
        if len(self.temp_state) == 0:
            if self.state_index==0 and len(self.mypanels) <= 0 and self.sfile_ext =='.svs':
                self.fit_panel.add_default_pages()
                self.temp_state = []
                self.state_index = 0
            return
        
        try:
            # Load fitting state
            state = self.temp_state[self.state_index]
            #panel state should have model selection to set_state
            if state.formfactorcombobox != None:
                #set state
                data = self.parent.create_gui_data(state.data)
                
                data.group_id = state.data.group_id
                self.parent.add_data(data_list={data.id:data})
                wx.PostEvent(self.parent, NewPlotEvent(plot=data,
                                        title=data.title))
                #need to be fix later make sure we are sendind guiframe.data
                #to panel
                state.data = data
                page = self.fit_panel.set_state(state)   
            else:
                #just set data because set_state won't work
                data = self.parent.create_gui_data(state.data)
                data.group_id = state.data.group_id
                self.parent.add_data(data_list={data.id:data})
                wx.PostEvent(self.parent, NewPlotEvent(plot=data,
                                        title=data.title))
                page = self.add_fit_page(data)
                caption = page.window_name
                self.store_data(page=page.id, data=data, caption=caption)
                self.mypanels.append(page) 
                
            # get ready for the next set_state
            self.state_index += 1

            #reset state variables to default when all set_state is finished. 
            if len(self.temp_state) == self.state_index:
                
                self.temp_state = []
                #self.state_index = 0
                # Make sure the user sees the fitting panel after loading
                #self.parent.set_perspective(self.perspective) 
                self.on_perspective(event=None)
        except:
            self.state_index==0
            self.temp_state = []
            raise
                 
    def save_fit_state(self, filepath, fitstate):  
        """
        save fit page state into file
        """
        self.state_reader.write(filename=filepath, fitstate=fitstate)
        
    def set_fit_range(self, uid, qmin, qmax):
        """
        Set the fitting range of a given page
        """
        self.page_finder[uid].set_range(qmin=qmin, qmax=qmax)
                    
    def schedule_for_fit(self,value=0, uid=None,fitproblem =None):  
        """
        Set the fit problem field to 0 or 1 to schedule that problem to fit.
        Schedule the specified fitproblem or get the fit problem related to 
        the current page and set value.
        
        :param value: integer 0 or 1 
        :param fitproblem: fitproblem to schedule or not to fit
        
        """   
        if fitproblem !=None:
            fitproblem.schedule_tofit(value)
        else:
            self.page_finder[uid].schedule_tofit(value)
          
    def get_page_finder(self):
        """
        return self.page_finder used also by simfitpage.py
        """  
        return self.page_finder 
    
    def set_page_finder(self,modelname,names,values):
        """
        Used by simfitpage.py to reset a parameter given the string constrainst.
         
        :param modelname: the name ot the model for with the parameter has to reset
        :param value: can be a string in this case.
        :param names: the paramter name
         
        :note: expecting park used for fit.
         
        """  
        sim_page_id = self.sim_page.uid
        for uid, value in self.page_finder.iteritems():
            if uid != sim_page_id:
                list = value.get_model()
                model = list[0]
                if model.name == modelname:
                    value.set_model_param(names, values)
                    break
         
    def split_string(self,item): 
        """
        receive a word containing dot and split it. used to split parameterset
        name into model name and parameter name example: ::
        
            paramaterset (item) = M1.A
            Will return model_name = M1 , parameter name = A
            
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
   
    def set_ftol(self, ftol=None):
        """
        Set ftol: Relative error desired in the sum of chi squares.  
        """
        # check if it is flaot
        try:
            f_tol = float(ftol)
        except:
            # default
            f_tol = 1.49012e-08
            
        self.ftol = f_tol
              
    def stop_fit(self, uid):
        """
        Stop the fit engine
        """
        if uid in self.fit_thread_list.keys():
            calc_fit = self.fit_thread_list[uid]
            if calc_fit is not  None and calc_fit.isrunning():
                calc_fit.stop()
                msg = "Fit stop!"
                wx.PostEvent(self.parent, StatusEvent(status=msg, type="stop"))
        #set the fit button label of page when fit stop is trigger from
        #simultaneous fit pane
        if  self.sim_page is not None and uid == self.sim_page.uid:
            for uid, value in self.page_finder.iteritems():
                if value.get_scheduled() == 1:
                    if uid in self.fit_panel.opened_pages.keys():
                        panel = self.fit_panel.opened_pages[uid]
                        panel. _on_fit_complete()
  
    def set_smearer(self, uid, smearer, qmin=None, qmax=None, draw=True, 
                    enable2D=False):
        """
        Get a smear object and store it to a fit problem
        
        :param smearer: smear object to allow smearing data
        
        """   
        if uid not in self.page_finder.keys():
            msg = "Cannot find ID: %s in page_finder" % str(uid)
            raise ValueError, msg
        self.page_finder[uid].set_smearer(smearer)
        self.page_finder[uid].set_enable2D(enable2D)
        if draw:
            ## draw model 1D with smeared data
            data =  self.page_finder[uid].get_fit_data()
            model = self.page_finder[uid].get_model()
            if model is None:
                return
            enable1D = True
            enable2D = self.page_finder[uid].get_enable2D()
            if enable2D:
                enable1D = False

            ## if user has already selected a model to plot
            ## redraw the model with data smeared
            smear = self.page_finder[uid].get_smearer()
            self.draw_model(model=model, data=data, page_id=uid, smearer=smear,
                enable1D=enable1D, enable2D=enable2D,
                qmin=qmin, qmax=qmax)

    def draw_model(self, model, page_id, data=None, smearer=None,
                   enable1D=True, enable2D=False,
                   state=None,
                   toggle_mode_on=False,
                   qmin=DEFAULT_QMIN, qmax=DEFAULT_QMAX, 
                   qstep=DEFAULT_NPTS,
                   update_chisqr=True):
        """
        Draw model.
        
        :param model: the model to draw
        :param name: the name of the model to draw
        :param data: the data on which the model is based to be drawn
        :param description: model's description
        :param enable1D: if true enable drawing model 1D
        :param enable2D: if true enable drawing model 2D
        :param qmin:  Range's minimum value to draw model
        :param qmax:  Range's maximum value to draw model
        :param qstep: number of step to divide the x and y-axis
        :param update_chisqr: update chisqr [bool]
             
        """
        if data.__class__.__name__ == "Data1D" or not enable2D:    
            ## draw model 1D with no loaded data
            self._draw_model1D(model=model, 
                               data=data,
                               page_id=page_id,
                               enable1D=enable1D, 
                               smearer=smearer,
                               qmin=qmin,
                               qmax=qmax, 
                               toggle_mode_on=toggle_mode_on,
                               state=state,
                               qstep=qstep,
                               update_chisqr=update_chisqr)
        else:     
            ## draw model 2D with no initial data
            self._draw_model2D(model=model,
                                page_id=page_id,
                                data=data,
                                enable2D=enable2D,
                                smearer=smearer,
                                qmin=qmin,
                                qmax=qmax,
                                state=state,
                                toggle_mode_on=toggle_mode_on,
                                qstep=qstep,
                                update_chisqr=update_chisqr)
            
    def onFit(self):
        """
        perform fit 
        """
        ##  count the number of fitproblem schedule to fit 
        fitproblem_count = 0
        for value in self.page_finder.values():
            if value.get_scheduled() == 1:
                fitproblem_count += 1
                
        ## if simultaneous fit change automatically the engine to park
        if fitproblem_count > 1:
            self._on_change_engine(engine='park')
            
        self.fitproblem_count = fitproblem_count  
          
        from sans.fit.Fitting import Fit
        fitter = Fit(self._fit_engine)
        
        if self._fit_engine == "park":
            engineType = "Simultaneous Fit"
        else:
            engineType = "Single Fit"
            
        fproblemId = 0
        self.current_pg = None
        list_page_id = []
        for page_id, value in self.page_finder.iteritems():
            try:
                if value.get_scheduled() == 1:
                    #Get list of parameters name to fit
                    pars = []
                    templist = []
                    
                    page = self.fit_panel.get_page_by_id(page_id)
                    templist = page.get_param_list()
                    # missing fit parameters
                    #if not templist:
                    #    return
                    # have the list
                    for element in templist:
                        name = str(element[1])
                        pars.append(name)
                    #Set Engine  (model , data) related to the page on 
                    self._fit_helper(value=value, pars=pars,
                                     fitter=fitter,
                                      fitproblem_id=fproblemId,
                                      title=engineType) 
                    list_page_id.append(page_id)
                    fproblemId += 1 
                    current_page_id = page_id
            except:
                #raise
                msg= "%s error: %s" % (engineType, sys.exc_value)
                wx.PostEvent(self.parent, StatusEvent(status=msg, info="error",
                                                      type="stop"))
                return 
        ## If a thread is already started, stop it
        #if self.calc_fit!= None and self.calc_fit.isrunning():
        #    self.calc_fit.stop()
         #Handler used for park engine displayed message
        handler = ConsoleUpdate(parent=self.parent,
                                manager=self,
                                improvement_delta=0.1)
        
        ## perform single fit
        if fitproblem_count == 1:
            calc_fit = FitThread(handler = handler,
                                    fn=fitter,
                                    pars=pars,
                                    page_id=list_page_id,
                                    completefn=self._single_fit_completed,
                                    ftol=self.ftol)
        else:
            current_page_id = self.sim_page.uid
            ## Perform more than 1 fit at the time
            calc_fit = FitThread(handler=handler,
                                    fn=fitter,
                                    page_id=list_page_id,
                                    updatefn=handler.update_fit,
                                    ftol=self.ftol)
        self.fit_thread_list[current_page_id] = calc_fit
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
            
    def remove_plot(self, uid, theory=False):
        """
        remove model plot when a fit page is closed
        """
        fitproblem = self.page_finder[uid]
        data = fitproblem.get_fit_data()
        model = fitproblem.get_model()
        plot_id = None
        if model is not None:
            plot_id = data.id + name
        if theory:
            plot_id = data.id 
        group_id = data.group_id
        wx.PostEvent(self.parent, NewPlotEvent(id=plot_id,
                                                   group_id=group_id,
                                                   action='remove'))
           
    def store_data(self, uid, data=None, caption=None):
        """
        Helper to save page reference into the plug-in
        
        :param page: page to store
        
        """
        #create a fitproblem storing all link to data,model,page creation
        if not uid in self.page_finder.keys():
            self.page_finder[uid] = FitProblem()
        self.page_finder[uid].set_fit_data(data)
        self.page_finder[uid].set_fit_tab_caption(caption)
        
    def on_add_new_page(self, event=None):
        """
        ask fit panel to create a new empty page
        """
        try:
            page = self.fit_panel.add_empty_page()
            page_caption = page.window_name
            # add data associated to the page created
            if page != None:  
                self.store_data(uid=page.uid, caption=page_caption,
                                data=page.get_data())
                wx.PostEvent(self.parent, StatusEvent(status="Page Created",
                                               info="info"))
            else:
                msg = "Page was already Created"
                wx.PostEvent(self.parent, StatusEvent(status=msg,
                                                       info="warning"))
            self.set_top_panel()
        except:
            raise
            #msg = "Creating Fit page: %s"%sys.exc_value
            #wx.PostEvent(self.parent, StatusEvent(status=msg, info="error"))
        
        
    def add_fit_page(self, data):
        """
        given a data, ask to the fitting panel to create a new fitting page,
        get this page and store it into the page_finder of this plug-in
        """
        page = self.fit_panel.set_data(data)
        page_caption = page.window_name
        #append Data1D to the panel containing its theory
        #if theory already plotted
        if page.uid in self.page_finder:
            theory_data = self.page_finder[page.uid].get_theory_data()
            if issubclass(data.__class__, Data2D):
                data.group_id = wx.NewId()
                if theory_data is not None:
                    group_id = str(page.uid) + " Model1D"
                    wx.PostEvent(self.parent, 
                             NewPlotEvent(group_id=group_id,
                                               action="delete"))
                    self.parent.update_data(prev_data=theory_data, new_data=data)      
            else:
                if theory_data is not None:
                    group_id = str(page.uid) + " Model2D"
                    data.group_id = theory_data.group_id
                    wx.PostEvent(self.parent, 
                             NewPlotEvent(group_id=group_id,
                                               action="delete"))
                    self.parent.update_data(prev_data=theory_data, new_data=data)   
              
        self.store_data(uid=page.uid, data=data, caption=page.window_name)
        if self.sim_page is not None:
            self.sim_page.draw_page()
        return page
            
    def _onEVT_SLICER_PANEL(self, event):
        """
        receive and event telling to update a panel with a name starting with 
        event.panel_name. this method update slicer panel for a given interactor.
        
        :param event: contains type of slicer , paramaters for updating the panel
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
            if not event.data.is_data or \
                event.data.__class__.__name__ == "Data1D":
                self.fit_panel.close_page_with_data(event.data) 
        
    def _add_page_onmenu(self, name, fitproblem=None):
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
            wx.EVT_MENU(self.parent, event_id, self._open_closed_page)
        
    def _open_closed_page(self, event):    
        """
        reopen a closed page
        """
        for name, value in self.closed_page_dict.iteritems():
            if event.GetId() in value:
                uid,fitproblem = value
                if name !="Model":
                    data= fitproblem.get_fit_data()
                    page = self.fit_panel.add_fit_page(data=data, reset=True)
                    if fitproblem != None:
                        self.page_finder[uid] = fitproblem
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
        for page_id in self.page_finder.keys():
            self.page_finder[page_id].schedule_tofit(value)
            
    def _fit_helper(self, pars, value, fitproblem_id,fitter, title="Single Fit " ):
        """
        helper for fitting
        """
        metadata = value.get_fit_data()
        model = value.get_model()
        smearer = value.get_smearer()
        qmin, qmax = value.get_range()
        self.fit_id = fitproblem_id
        #Create list of parameters for fitting used
        templist = []
       
        try:
            #Extra list of parameters and their constraints
            listOfConstraint = []
            
            param = value.get_model_param()
            if len(param) > 0:
                for item in param:
                    ## check if constraint
                    if item[0] != None and item[1] != None:
                        listOfConstraint.append((item[0],item[1]))
                   
            #Do the single fit
            fitter.set_model(model, self.fit_id,
                                   pars, constraints=listOfConstraint)
            
            fitter.set_data(data=metadata, id=self.fit_id,
                                 smearer=smearer, qmin=qmin, qmax=qmax)
           
            fitter.select_problem_for_fit(id=self.fit_id,
                                               value=value.get_scheduled())
            value.clear_model_param()
        except:
            raise
            #msg = title + " error: %s" % sys.exc_value
            #wx.PostEvent(self.parent, StatusEvent(status=msg, type="stop"))
          
    def _onSelect(self,event):
        """ 
        when Select data to fit a new page is created .Its reference is 
        added to self.page_finder
        """
        self.panel = event.GetEventObject()
        Plugin.on_perspective(self, event=event)
        for plottable in self.panel.graph.plottables:
            if plottable.__class__.__name__ in ["Data1D", "Theory1D"]:
                if plottable.name == self.panel.graph.selected_plottable:
                    data = plottable
                    self.add_fit_page(data=data)
                    return
            else:
                data = plottable
                self.add_fit_page(data=data)
        self.set_top_panel()
            
    def update_fit(self, result=None, msg=""):
        """
        """
        print "update_fit result", result
        
    def _single_fit_completed(self, result, pars, page_id, elapsed=None):
        """
        Display fit result on one page of the notebook.
        
        :param result: result of fit 
        :param pars: list of names of parameters fitted
        :param current_pg: the page where information will be displayed
        :param qmin: the minimum value of x to replot the model 
        :param qmax: the maximum value of x to replot model
          
        """     
        try:
            if result == None:
                msg= "Single Fitting did not converge!!!"
                wx.PostEvent(self.parent, 
                             StatusEvent(status=msg, 
                                         info="warning",
                                         type="stop"))
                return
            if not numpy.isfinite(result.fitness) or \
                    numpy.any(result.pvec == None) or \
                    not numpy.all(numpy.isfinite(result.pvec)):
                msg = "Single Fitting did not converge!!!"
                wx.PostEvent(self.parent, 
                             StatusEvent(status=msg, 
                                         info="warning",
                                         type="stop"))
                return
            for uid in page_id:
                value = self.page_finder[uid]   
                model = value.get_model()
                page_id = uid
                    
                param_name = []
                for name in pars:
                    param_name.append(name)
                    
                cpage = self.fit_panel.get_page_by_id(uid)
                cpage.onsetValues(result.fitness, 
                                  param_name, result.pvec,result.stderr)
                cpage._on_fit_complete()

        except ValueError:
            msg = "Single Fitting did not converge!!!"
            wx.PostEvent(self.parent, StatusEvent(status=msg, info="error",
                                                  type="stop"))
            return   
        except:
            raise
            #msg = "Single Fit completed but Following"
            #msg += " error occurred:%s" % sys.exc_value
            #wx.PostEvent(self.parent, StatusEvent(status=msg, info="error",
            #                                      type="stop"))
            return
       
    def _simul_fit_completed(self, result, page_id,pars=None, elapsed=None):
        """
        Parameter estimation completed, 
        display the results to the user
        
        :param alpha: estimated best alpha
        :param elapsed: computation time
        
        """
        if page_id is None:
            page_id = []
        ## fit more than 1 model at the same time 
        try:
            msg = "" 
            if result == None:
                msg= "Complex Fitting did not converge!!!"
                wx.PostEvent(self.parent, StatusEvent(status=msg,
                                                      type="stop"))
                return
            if not numpy.isfinite(result.fitness) or \
                numpy.any(result.pvec == None) or not \
                numpy.all(numpy.isfinite(result.pvec)):
                msg= "Simultaneous Fitting did not converge!!!"
                wx.PostEvent(self.parent, StatusEvent(status=msg,type="stop"))
                return
              
            for uid in page_id:   
                value = self.page_finder[uid]
                model = value.get_model()
                data =  value.get_fit_data()
                small_param_name = []
                small_out = []
                small_cov = []
                #Separate result in to data corresponding to each page
                for p in result.parameters:
                    model_name, param_name = self.split_string(p.name)  
                    if model.name == model_name:
                        p_name= model.name+"."+param_name
                        if p.name == p_name:      
                            if p.value != None and numpy.isfinite(p.value):
                                small_out.append(p.value)
                                small_param_name.append(param_name)
                                small_cov.append(p.stderr)
                # Display result on each page 
                cpage = self.fit_panel.get_page_by_id(uid)
                cpage.onsetValues(result.fitness,
                                  small_param_name,
                                  small_out,small_cov)
                cpage._on_fit_complete()
                
        except Exception:
            msg = "Complex Fitting did not converge!!!"
            wx.PostEvent(self.parent, StatusEvent(status=msg, info="error",
                                                  type="stop"))
            return

        except:
            msg = "Simultaneous Fit completed"
            msg += " but Following error occurred:%s" % sys.exc_value
            wx.PostEvent(self.parent, StatusEvent(status=msg, type="stop"))
   
    def _on_show_panel(self, event):
        """
        """
        pass
        
    def _onset_engine_park(self,event):
        """ 
        set engine to park
        """
        self._on_change_engine('park')
       
    def _onset_engine_scipy(self,event):
        """ 
        set engine to scipy
        """
        self._on_change_engine('scipy')
       
    def _on_slicer_event(self, event):
        """
        Receive a panel as event and send it to guiframe 
        
        :param event: event containing a panel
        
        """
        if event.panel is not None:
            new_panel = event.panel
            self.slicer_panels.append(event.panel)
            # Set group ID if available
            event_id = self.parent.popup_panel(new_panel)
            #self.menu3.Append(event_id, new_panel.window_caption, 
            #                 "Show %s plot panel" % new_panel.window_caption)
            # Set id to allow us to reference the panel later
         
            new_panel.uid = event_id
            self.mypanels.append(new_panel) 
       
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
        
        :param engine: the key work of the engine
        
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
        msg = "Engine set to: %s" % self._fit_engine
        wx.PostEvent(self.parent, 
                     StatusEvent(status=msg))
        ## send the current engine type to fitpanel
        self.fit_panel._on_engine_change(name=self._fit_engine)
       
    def _on_model_panel(self, evt):
        """
        react to model selection on any combo box or model menu.plot the model  
        
        :param evt: wx.combobox event
        
        """
        model = evt.model
        uid = evt.uid 
        qmin = evt.qmin
        qmax = evt.qmax
        smearer = evt.smearer
        
        if model == None:
            return

        if self.page_finder[uid].get_model() is None:
            model.name = "M" + str(self.index_model)
            self.index_model += 1  
        else:
            model.name = self.page_finder[uid].get_model().name
        # save the name containing the data name with the appropriate model
        self.page_finder[uid].set_model(model)
        self.page_finder[uid].set_range(qmin=qmin, qmax=qmax)
        if self.sim_page is not None:
            self.sim_page.draw_page()
        
    def _update1D(self,x, output):
        """
        Update the output of plotting model 1D
        """
        msg = "Plot updating ... "
        wx.PostEvent(self.parent, StatusEvent(status=msg,type="update"))
        self.ready_fit()
        
    
    def _fill_default_model2D(self, theory, page_id, qmax,qstep, qmin=None):
        """
        fill Data2D with default value 
        
        :param theory: Data2D to fill
        
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

        # theory default: assume the beam 
        #center is located at the center of sqr detector
        xmax = qmax
        xmin = -qmax
        ymax = qmax
        ymin = -qmax
        
        x=  numpy.linspace(start= -1*qmax,
                               stop=qmax,
                               num=qstep,
                               endpoint=True)  
        y = numpy.linspace(start=-1*qmax,
                               stop= qmax,
                               num= qstep,
                               endpoint=True)
         
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
        
        # calculate the range of qx and qy: this way,
        # it is a little more independent
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
        theory.xmin = xmin 
        theory.xmax = xmax
        theory.ymin = ymin 
        theory.ymax = ymax 
        theory.group_id = str(page_id) + " Model2D"
        theory.id = str(page_id) + " Model2D"
  
    def _complete1D(self, x,y, page_id, elapsed,index,model,
                    toggle_mode_on=False,state=None, 
                    data=None, update_chisqr=True):
        """
        Complete plotting 1D data
        """ 
        try:
            new_plot = Data1D(x=x, y=y)
            new_plot.is_data = False
            new_plot.symbol = GUIFRAME_ID.CURVE_SYMBOL_NUM
            if data != None:
                _xaxis, _xunit = data.get_xaxis() 
                _yaxis, _yunit = data.get_yaxis() 
                new_plot.title = data.name
                #if the theory is already plotted use the same group id 
                #to replot
                if page_id in self.page_finder:
                    theory_data = self.page_finder[page_id].get_theory_data()
                    if theory_data is not None:
                       data.group_id = theory_data.group_id
                #data is plotted before the theory, then take its group_id
                #assign to the new theory
                new_plot.group_id = data.group_id
               
            else:
                _xaxis, _xunit = "\\rm{Q}", 'A^{-1}'
                _yaxis, _yunit = "\\rm{Intensity} ", "cm^{-1}"
                new_plot.title = "Analytical model 1D "
                #find a group id to plot theory without data
                new_plot.group_id =  str(page_id) + " Model1D"  
            new_plot.id =  str(page_id) + " Model1D"  
            
            #find if this theory was already plotted and replace that plot given
            #the same id
            
            theory_data = self.page_finder[page_id].get_theory_data()
            if theory_data is not None:
                new_plot.id = theory_data.id
             
            new_plot.name = model.name + " ["+ str(model.__class__.__name__)+ "]"
            new_plot.xaxis(_xaxis, _xunit)
            new_plot.yaxis(_yaxis, _yunit)
            if toggle_mode_on:
                new_plot.id =  str(page_id) + " Model" 
                wx.PostEvent(self.parent, 
                             NewPlotEvent(group_id=str(page_id) + " Model2D",
                                               action="Hide"))
           
            self.page_finder[page_id].set_theory_data(new_plot)
            if data is None:
                data_id = None
            else:
                data_id = data.id
            self.parent.update_theory(data_id=data_id, 
                                       theory=new_plot,
                                       state=state)     
            current_pg = self.fit_panel.get_page_by_id(page_id)
            title = new_plot.title
            wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot,
                                            title= str(title)))
            if update_chisqr:
                wx.PostEvent(current_pg,
                             Chi2UpdateEvent(output=self._cal_chisqr(data=data,
                                                        page_id=page_id,
                                                        index=index)))
            else:
                self._plot_residuals(page_id, data, index)

            msg = "Plot 1D  complete !"
            wx.PostEvent( self.parent, StatusEvent(status=msg, type="stop" ))
            #self.current_pg.state.theory_data = deepcopy(self.theory_data)
        except:
            raise
            #msg = " Error occurred when drawing %s Model 1D: " % new_plot.name
            #msg += " %s"  % sys.exc_value
            #wx.PostEvent(self.parent, StatusEvent(status=msg, type="stop"))
   
    def _update2D(self, output,time=None):
        """
        Update the output of plotting model
        """
        wx.PostEvent(self.parent, StatusEvent(status="Plot \
        #updating ... ", type="update"))
        self.ready_fit()
  
    def _complete2D(self, image, data, model, page_id,  elapsed, index, qmin,
                     qmax, toggle_mode_on=False,state=None,qstep=DEFAULT_NPTS, 
                     update_chisqr=True):
        """
        Complete get the result of modelthread and create model 2D
        that can be plot.
        """
        err_image = numpy.zeros(numpy.shape(image))
       
        new_plot= Data2D(image=image, err_image=err_image)
        new_plot.name = model.name
        new_plot.title = "Analytical model 2D "
        if data is None:
            self._fill_default_model2D(theory=new_plot, 
                                       qmax=qmax, 
                                       page_id=page_id,
                                       qstep=qstep,
                                        qmin= qmin)
           
        else:
            new_plot.id = str(page_id) + " Model2D"
            new_plot.group_id = str(page_id) + " Model2D"
            new_plot.x_bins = data.x_bins
            new_plot.y_bins = data.y_bins
            new_plot.detector = data.detector
            new_plot.source = data.source
            new_plot.is_data = False 
            new_plot.qx_data = data.qx_data
            new_plot.qy_data = data.qy_data
            new_plot.q_data = data.q_data
            #numpy.zeros(len(data.err_data))#data.err_data
            new_plot.err_data = err_image
            new_plot.mask = data.mask
            ## plot boundaries
            new_plot.ymin = data.ymin
            new_plot.ymax = data.ymax
            new_plot.xmin = data.xmin
            new_plot.xmax = data.xmax
            title = data.title
            if len(title) > 1:
                new_plot.title = "Model2D for " + data.name
        new_plot.is_data = False
        new_plot.name = model.name + " ["+ str(model.__class__.__name__)+ "]"

        theory_data = deepcopy(new_plot)
        theory_data.name = "Unknown"
        if toggle_mode_on:
            new_plot.id = str(page_id) + " Model"      
            wx.PostEvent(self.parent, 
                             NewPlotEvent(group_id=str(page_id) + " Model1D",
                                               action="Hide"))
        
        self.page_finder[page_id].set_theory_data(new_plot)
        if data is None:
            data_id = None
        else:
            data_id = data.id
        self.parent.update_theory(data_id=data_id, 
                                       theory=new_plot,
                                       state=state)  
        current_pg = self.fit_panel.get_page_by_id(page_id)
        title = new_plot.title

        wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot,
                                               title=title))
        # Chisqr in fitpage
        if update_chisqr:
            wx.PostEvent(current_pg,
                         Chi2UpdateEvent(output=\
                                    self._cal_chisqr(data=data,
                                                     page_id=page_id,
                                                     index=index)))
        else:
            self._plot_residuals(page_id, data, index)
        msg = "Plot 2D complete !"
        wx.PostEvent(self.parent, StatusEvent(status=msg, type="stop"))
    
    def _draw_model2D(self, model, page_id, data=None, smearer=None,
                      description=None, enable2D=False,
                      state=None,
                      toggle_mode_on=False,
                      qmin=DEFAULT_QMIN, qmax=DEFAULT_QMAX,
                      qstep=DEFAULT_NPTS,
                      update_chisqr=True):
        """
        draw model in 2D
        
        :param model: instance of the model to draw
        :param description: the description of the model
        :param enable2D: when True allows to draw model 2D
        :param qmin: the minimum value to  draw model 2D
        :param qmax: the maximum value to draw model 2D
        :param qstep: the number of division of Qx and Qy of the model to draw
            
        """
        x=  numpy.linspace(start=-1*qmax,
                               stop=qmax,
                               num=qstep,
                               endpoint=True)  
        y = numpy.linspace(start= -1*qmax,
                               stop=qmax,
                               num=qstep,
                               endpoint=True)
        if model is None:
            msg = "Panel with ID: %s does not contained model" % str(page_id)
            raise ValueError, msg
        ## use data info instead
        if data is not None:
            ## check if data2D to plot
            if hasattr(data, "x_bins"):
                enable2D = True
                x = data.x_bins
                y = data.y_bins
               
        if not enable2D:
            return None, None
        try:
            from model_thread import Calc2D
            ## If a thread is already started, stop it
            if (self.calc_2D is not None) and self.calc_2D.isrunning():
                self.calc_2D.stop()
            self.calc_2D = Calc2D(x=x,
                                    y=y,
                                    model=model, 
                                    data=data,
                                    page_id=page_id,
                                    smearer=smearer,
                                    qmin=qmin,
                                    qmax=qmax,
                                    qstep=qstep,
                                    toggle_mode_on=toggle_mode_on,
                                    state=state,
                                    completefn=self._complete2D,
                                    #updatefn= self._update2D,
                                    update_chisqr=update_chisqr)

            self.calc_2D.queue()

        except:
            raise
            #msg = " Error occurred when drawing %s Model 2D: " % model.name
            #msg += " %s" % sys.exc_value
            #wx.PostEvent(self.parent, StatusEvent(status=msg))

    def _draw_model1D(self, model, page_id, data=None, smearer=None,
                qmin=DEFAULT_QMIN, qmax=DEFAULT_QMAX, 
                state=None,
                toggle_mode_on=False,
                qstep=DEFAULT_NPTS, update_chisqr=True, 
                enable1D=True):
        """
        Draw model 1D from loaded data1D
        
        :param data: loaded data
        :param model: the model to plot
        
        """
        x=  numpy.linspace(start=qmin,
                           stop=qmax,
                           num=qstep,
                           endpoint=True
                           )
        if data is not None:
            ## check for data2D
            if hasattr(data,"x_bins"):
                return
            x = data.x
            if qmin == None :
                qmin == DEFAULT_QMIN

            if qmax == None:
                qmax == DEFAULT_QMAX 
        if not enable1D:
            return 
        try:
            from model_thread import Calc1D
            ## If a thread is already started, stop it
            if (self.calc_1D is not None) and self.calc_1D.isrunning():
                self.calc_1D.stop()
            self.calc_1D = Calc1D(x=x,
                                  data=data,
                                  model=model,
                                  page_id=page_id, 
                                  qmin=qmin,
                                  qmax=qmax,
                                  smearer=smearer,
                                  state=state,
                                  toggle_mode_on=toggle_mode_on,
                                  completefn=self._complete1D,
                                  #updatefn = self._update1D,
                                  update_chisqr=update_chisqr)

            self.calc_1D.queue()

        except:
            msg = " Error occurred when drawing %s Model 1D: " % model.name
            msg += " %s" % sys.exc_value
            wx.PostEvent(self.parent, StatusEvent(status=msg))

    def _cal_chisqr(self, page_id, data=None, index=None): 
        """
        Get handy Chisqr using the output from draw1D and 2D, 
        instead of calling expansive CalcChisqr in guithread
        """
        # default chisqr
        chisqr = None
        
        # return None if data == None
        if data == None: return chisqr
        
        # Get data: data I, theory I, and data dI in order
        if data.__class__.__name__ == "Data2D":
            if index == None: 
                index = numpy.ones(len(data.data),ntype=bool)
            # get rid of zero error points
            index = index & (data.err_data != 0 )  
            index = index & (numpy.isfinite(data.data)) 
            fn = data.data[index] 
            theory_data = self.page_finder[page_id].get_theory_data()
            gn = theory_data.data[index]
            en = data.err_data[index]
        else:
            # 1 d theory from model_thread is only in the range of index
            if index == None: 
                index = numpy.ones(len(data.y), ntype=bool)
            if data.dy == None or data.dy == []:
                dy = numpy.ones(len(data.y))
            else:
                ## Set consitently w/AbstractFitengine:
                # But this should be corrected later.
                dy = deepcopy(data.dy)
                dy[dy==0] = 1  
            fn = data.y[index] 
            theory_data = self.page_finder[page_id].get_theory_data()
            gn = theory_data.y
            en = dy[index]
        # residual
        res = (fn - gn) / en
        residuals = res[numpy.isfinite(res)]
        # get chisqr only w/finite
        chisqr = numpy.average(residuals * residuals)
        
        self._plot_residuals(page_id, data, index)
        return chisqr
    

        
    def _plot_residuals(self, page_id, data=None, index=None): 
        """
        Plot the residuals
        
        :param data: data
        :param index: index array (bool) 
        : Note: this is different from the residuals in cal_chisqr()
        """
        if data == None: 
            return 
        
        # Get data: data I, theory I, and data dI in order
        if data.__class__.__name__ == "Data2D":
            # build residuals
            #print data
            residuals = Data2D()
            #residuals.copy_from_datainfo(data)
            # Not for trunk the line below, instead use the line above
            data.clone_without_data(len(data.data), residuals)
            residuals.data = None
            fn = data.data#[index] 
            theory_data = self.page_finder[page_id].get_theory_data()
            gn = theory_data.data#[index]
            en = data.err_data#[index]
            residuals.data = (fn - gn) / en 
            residuals.qx_data = data.qx_data#[index]
            residuals.qy_data = data.qy_data #[index]
            residuals.q_data = data.q_data#[index]
            residuals.err_data = numpy.ones(len(residuals.data))#[index]
            residuals.xmin = min(residuals.qx_data)
            residuals.xmax = max(residuals.qx_data)
            residuals.ymin = min(residuals.qy_data)
            residuals.ymax = max(residuals.qy_data)
            residuals.q_data = data.q_data#[index]
            residuals.mask = data.mask
            residuals.scale = 'linear'
            #print "print data",residuals
            # check the lengths
            if len(residuals.data) != len(residuals.q_data):
                return

        else:
            # 1 d theory from model_thread is only in the range of index
            if data.dy == None or data.dy == []:
                dy = numpy.ones(len(data.y))
            else:
                ## Set consitently w/AbstractFitengine: 
                ## But this should be corrected later.
                dy = deepcopy(data.dy)
                dy[dy==0] = 1  
            fn = data.y[index] 
            theory_data = self.page_finder[page_id].get_theory_data()
            gn = theory_data.y
            en = dy[index]
            # build residuals
            residuals = Data1D()
            residuals.y = (fn - gn) / en
            residuals.x = data.x[index]
            residuals.dy = numpy.ones(len(residuals.y))
            residuals.dx = None
            residuals.dxl = None
            residuals.dxw = None
            residuals.ytransform = 'y'
            # For latter scale changes 
            residuals.xaxis('\\rm{Q} ', 'A^{-1}')
            residuals.yaxis('\\rm{Residuals} ', 'normalized')
            
        new_plot = residuals
        if data.id == None:
            data.id = data.name
        name  = data.id
        new_plot.name = "Residuals for " + str(data.name)
        ## allow to highlight data when plotted
        new_plot.interactive = True
        ## when 2 data have the same id override the 1 st plotted
        new_plot.id = new_plot.name#name + " residuals"
        ##group_id specify on which panel to plot this data
        new_plot.group_id = new_plot.id
        #new_plot.is_data = True
        ##post data to plot
        title = new_plot.name 
        
        # plot data
        wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot, title=title))   
        
#def profile(fn, *args, **kw):
#    import cProfile, pstats, os
#    global call_result
#    def call():
#        global call_result
#        call_result = fn(*args, **kw)
#    cProfile.runctx('call()', dict(call=call), {}, 'profile.out')
#    stats = pstats.Stats('profile.out')
#    #stats.sort_stats('time')
#    stats.sort_stats('calls')
#    stats.print_stats()
#    os.unlink('profile.out')
#    return call_result
if __name__ == "__main__":
    i = Plugin()
    
    
    
    