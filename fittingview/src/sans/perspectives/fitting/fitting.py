

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


from sans.dataloader.loader import Loader
from sans.guiframe.dataFitting import Data2D
from sans.guiframe.dataFitting import Data1D
from sans.guiframe.dataFitting import check_data_validity
from sans.guiframe.events import NewPlotEvent 
from sans.guiframe.events import StatusEvent  
from sans.guiframe.events import EVT_SLICER_PANEL
from sans.guiframe.events import EVT_SLICER_PARS_UPDATE
from sans.guiframe.gui_style import GUIFRAME_ID
from sans.guiframe.plugin_base import PluginBase 
from sans.fit.Fitting import Fit
from .console import ConsoleUpdate
from .fitproblem import FitProblemDictionary
from .fitpanel import FitPanel
from .fit_thread import FitThread
from .pagestate import Reader
from .fitpage import Chi2UpdateEvent

MAX_NBR_DATA = 4
SANS_F_TOL = 5e-05

(PageInfoEvent, EVT_PAGE_INFO)   = wx.lib.newevent.NewEvent()

if sys.platform.count("darwin")==0:
    ON_MAC = False
else:
    ON_MAC = True   

class Plugin(PluginBase):
    """
    Fitting plugin is used to perform fit 
    """
    def __init__(self, standalone=False):
        PluginBase.__init__(self, name="Fitting", standalone=standalone)
        
        #list of panel to send to guiframe
        self.mypanels = []
        # reference to the current running thread
        self.calc_2D = None
        self.calc_1D = None
        
        self.color_dict = {}
        
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
        self.ftol = SANS_F_TOL
        #List of selected data
        self.selected_data_list = []
        ## list of slicer panel created to display slicer parameters and results
        self.slicer_panels = []
        # model 2D view
        self.model2D_id = None
        #keep reference of the simultaneous fit page
        self.sim_page = None
        self.index_model = 0
        self.test_model_color = None
        #Create a reader for fit page's state
        self.state_reader = None 
        self._extensions = '.fitv'
        self.scipy_id = wx.NewId()
        self.park_id = wx.NewId()
        
        self.temp_state = []
        self.state_index = 0
        self.sfile_ext = None
        # take care of saving  data, model and page associated with each other
        self.page_finder = {}
        # Log startup
        logging.info("Fitting plug-in started") 
    
    def create_fit_problem(self, page_id):
        """
        Given an ID create a fitproblem container
        """
        self.page_finder[page_id] = FitProblemDictionary()
        
    def delete_fit_problem(self, page_id):
        """
        Given an ID create a fitproblem container
        """
        if page_id in self.page_finder.iterkeys():
            del self.page_finder[page_id]
        
    def add_color(self, color, id):
        """
        adds a color as a key with a plot id as its value to a dictionary
        """
        self.color_dict[id] = color
        
    def on_batch_selection(self, flag):
        """
        switch the the notebook of batch mode or not
        """
        self.batch_on = flag
        if self.fit_panel is not None:
            self.fit_panel.batch_on = self.batch_on
        
    def populate_menu(self, owner):
        """
        Create a menu for the Fitting plug-in
        
        :param id: id to create a menu
        :param owner: owner of menu
        
        :return: list of information to populate the main menu
        
        """
        #Menu for fitting
        self.menu1 = wx.Menu()
        id1 = wx.NewId()
        simul_help = "Add new fit panel"
        self.menu1.Append(id1, '&New Fit Page',simul_help)
        wx.EVT_MENU(owner, id1, self.on_add_new_page)
        self.menu1.AppendSeparator()
        id1 = wx.NewId()
        simul_help = "Simultaneous Fit"
        self.menu1.Append(id1, '&Simultaneous Fit',simul_help)
        wx.EVT_MENU(owner, id1, self.on_add_sim_page)
        self.menu1.AppendSeparator()
        #Set park engine
        
        scipy_help= "Scipy Engine: Perform Simple fit. More in Help window...."
        self.menu1.AppendCheckItem(self.scipy_id, "Simple FitEngine [LeastSq]",
                                   scipy_help) 
        wx.EVT_MENU(owner, self.scipy_id,  self._onset_engine_scipy)
        
        park_help = "Park Engine: Perform Complex fit. More in Help window...."
        self.menu1.AppendCheckItem(self.park_id, "Complex FitEngine [ParkMC]",
                                   park_help) 
        wx.EVT_MENU(owner, self.park_id,  self._onset_engine_park)
        
        self.menu1.FindItemById(self.scipy_id).Check(True)
        self.menu1.FindItemById(self.park_id).Check(False)
        self.menu1.AppendSeparator()
        self.id_tol = wx.NewId()
        ftol_help = "Change the current FTolerance (=%s) " % str(self.ftol)
        ftol_help += "of Simple FitEngine..." 
        self.menu1.Append(self.id_tol, "Change FTolerance [LeastSq Only]", 
                                   ftol_help) 
        wx.EVT_MENU(owner, self.id_tol,  self.show_ftol_dialog)
        
        
        #create  menubar items
        return [(self.menu1, self.sub_menu)]
               
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
        self.parent.Bind(EVT_SLICER_PARS_UPDATE, self._onEVT_SLICER_PANEL)
        self.parent._mgr.Bind(wx.aui.EVT_AUI_PANE_CLOSE,self._onclearslicer)    
        #Create reader when fitting panel are created
        self.state_reader = Reader(self.set_state)   
        #append that reader to list of available reader 
        loader = Loader()
        loader.associate_file_reader(".fitv", self.state_reader)
        #loader.associate_file_reader(".svs", self.state_reader)
        #from sans.perspectives.calculator.sld_panel import SldPanel
        #Send the fitting panel to guiframe
        self.mypanels.append(self.fit_panel) 
        #self.mypanels.append(SldPanel(parent=self.parent, base=self.parent))
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
        if self.batch_on:
            page = self.add_fit_page(data=data_list)
        else:
            if len(data_list) > MAX_NBR_DATA:
                from fitting_widgets import DataDialog
                dlg = DataDialog(data_list=data_list, nb_data=MAX_NBR_DATA)
                if dlg.ShowModal() == wx.ID_OK:
                    selected_data_list = dlg.get_data()
                dlg.Destroy()
                
            else:
                selected_data_list = data_list
            try:
                for data in selected_data_list:
                    page = self.add_fit_page(data=[data])
            except:
                msg = "Fitting Set_data: " + str(sys.exc_value)
                wx.PostEvent(self.parent, StatusEvent(status=msg, info="error"))
    
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
            state = state.clone()
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
        Set_state_helper. This actually sets state 
        after plotting data from state file.
        
        : event: FitStateUpdateEvent called 
            by dataloader.plot_data from guiframe
        """
        if len(self.temp_state) == 0:
            if self.state_index==0 and len(self.mypanels) <= 0 \
            and self.sfile_ext =='.svs':
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
                page = self.add_fit_page([data])
                caption = page.window_caption
                self.store_data(uid=page.uid, data_list=page.get_data_list(), 
                        caption=caption)
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
        
    def set_fit_range(self, uid, qmin, qmax, fid=None):
        """
        Set the fitting range of a given page for all
        its data by default. If fid is provide then set the range 
        only for the data with fid as id
        :param uid: id corresponding to a fit page
        :param fid: id corresponding to a fit problem (data, model)
        :param qmin: minimum  value of the fit range
        :param qmax: maximum  value of the fit range
        """
        if uid in self.page_finder.keys():
            self.page_finder[uid].set_range(qmin=qmin, qmax=qmax)
                    
    def schedule_for_fit(self, value=0, uid=None):  
        """
        Set the fit problem field to 0 or 1 to schedule that problem to fit.
        Schedule the specified fitproblem or get the fit problem related to 
        the current page and set value.
        :param value: integer 0 or 1 
        :param uid: the id related to a page contaning fitting information
        """
        if uid in self.page_finder.keys():  
            self.page_finder[uid].schedule_tofit(value)
          
    def get_page_finder(self):
        """
        return self.page_finder used also by simfitpage.py
        """  
        return self.page_finder 
    
    def set_page_finder(self,modelname,names,values):
        """
        Used by simfitpage.py to reset a parameter given the string constrainst.
         
        :param modelname: the name ot the model for with the parameter 
                            has to reset
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
            f_tol = SANS_F_TOL
            
        self.ftol = f_tol
        # update ftol menu help strings
        ftol_help = "Change the current FTolerance (=%s) " % str(self.ftol)
        ftol_help += "of Simple FitEngine..." 
        self.menu1.SetHelpString(self.id_tol, ftol_help)
        
    def show_ftol_dialog(self, event=None):
        """
        Dialog to select ftol for Scipy
        """
        #if event != None:
        #    event.Skip()
        from ftol_dialog import ChangeFtol
        panel = ChangeFtol(self.parent, self)
        panel.ShowModal()
                  
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
            del self.fit_thread_list[uid]
        #set the fit button label of page when fit stop is trigger from
        #simultaneous fit pane
        if  self.sim_page is not None and uid == self.sim_page.uid:
            for uid, value in self.page_finder.iteritems():
                if value.get_scheduled() == 1:
                    if uid in self.fit_panel.opened_pages.keys():
                        panel = self.fit_panel.opened_pages[uid]
                        panel. _on_fit_complete()
  
    def set_smearer(self, uid, smearer, fid, qmin=None, qmax=None, draw=True,
                    enable_smearer=False):
        """
        Get a smear object and store it to a fit problem of fid as id. If proper
        flag is enable , will plot the theory with smearing information.
        
        :param smearer: smear object to allow smearing data of id fid
        :param enable_smearer: Define whether or not all (data, model) contained
            in the structure of id uid will be smeared before fitting.
        :param qmin: the maximum value of the theory plotting range
        :param qmax: the maximum value of the theory plotting range
        :param draw: Determine if the theory needs to be plot
        """   
        if uid not in self.page_finder.keys():
            return
        self.page_finder[uid].enable_smearing(flag=enable_smearer)
        self.page_finder[uid].set_smearer(smearer, fid=fid)
        if draw:
            ## draw model 1D with smeared data
            data =  self.page_finder[uid].get_fit_data(fid=fid)
            if data is None:
                msg = "set_mearer requires at least data.\n"
                msg += "Got data = %s .\n" % str(data)
                raise ValueError, msg
            model = self.page_finder[uid].get_model(fid=fid)
            if model is None:
                return
            enable1D = issubclass(data.__class__, Data1D)
            enable2D = issubclass(data.__class__, Data2D)
            ## if user has already selected a model to plot
            ## redraw the model with data smeared
            smear = self.page_finder[uid].get_smearer(fid=fid)
            self.draw_model(model=model, data=data, page_id=uid, smearer=smear,
                enable1D=enable1D, enable2D=enable2D,
                qmin=qmin, qmax=qmax)
            self._mac_sleep(0.2)
            
    def _mac_sleep(self, sec=0.2):
        """
        Give sleep to MAC
        """
        if ON_MAC:
           time.sleep(sec)
        
    def draw_model(self, model, page_id, data=None, smearer=None,
                   enable1D=True, enable2D=False,
                   state=None,
                   toggle_mode_on=False,
                   qmin=None, qmax=None, 
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
        if issublclass(data.__class__, Data1D) or not enable2D:    
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
                                update_chisqr=update_chisqr)
            
    def onFit(self, uid=None):
        """
        Get series of data, model, associates parameters and range and send then
        to  series of fit engines. Fit data and model, display result to 
        corresponding panels. 
        :param uid: id related to the panel currently calling this fit function.
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
        if self._fit_engine == "park":
            engineType = "Simultaneous Fit"
        else:
            engineType = "Single Fit"
        fitter_list = []
        self.current_pg = None
        list_page_id = []
        for page_id, value in self.page_finder.iteritems():
            # For simulfit (uid give with None), do for-loop
            # if uid is specified (singlefit), do it only on the page.
            if engineType == "Single Fit":
                if page_id != uid:
                    continue
            try:
                if value.get_scheduled() == 1:
                    #Get list of parameters name to fit
                    pars = []
                    templist = []
                    page = self.fit_panel.get_page_by_id(page_id)
                    templist = page.get_param_list()
                    for element in templist:
                        name = str(element[1])
                        pars.append(name)
                    #Set Engine  (model , data) related to the page on 
                    self._fit_helper(value, pars, fitter_list)
                    list_page_id.append(page_id)
                    current_page_id = page_id
            except:
                msg= "%s error: %s" % (engineType, sys.exc_value)
                wx.PostEvent(self.parent, StatusEvent(status=msg, info="error",
                                                      type="stop"))
                return 
        ## If a thread is already started, stop it
        #if self.calc_fit!= None and self.calc_fit.isrunning():
        #    self.calc_fit.stop()
        msg = "Fitting is in progress..."
        wx.PostEvent( self.parent, StatusEvent(status=msg, type="progress" ))
        
        #Handler used for park engine displayed message
        handler = ConsoleUpdate(parent=self.parent,
                                manager=self,
                                improvement_delta=0.1)
        self._mac_sleep(0.2)
        ## perform single fit
        if fitproblem_count == 1:
            calc_fit = FitThread(handler = handler,
                                    fn=fitter_list,
                                    pars=pars,
                                    page_id=list_page_id,
                                    completefn=self._single_fit_completed,
                                    ftol=self.ftol)
        else:
            current_page_id = self.sim_page.uid
            ## Perform more than 1 fit at the time
            calc_fit = FitThread(handler=handler,
                                    fn=fitter_list,
                                    page_id=list_page_id,
                                    updatefn=handler.update_fit,
                                    completefn=self._simul_fit_completed,
                                    ftol=self.ftol)
        self.fit_thread_list[current_page_id] = calc_fit
        calc_fit.queue()
        msg = "Fitting is in progress..."
        wx.PostEvent( self.parent, StatusEvent(status=msg, type="progress" ))
        
        self.ready_fit(calc_fit=calc_fit)
        
    def ready_fit(self, calc_fit):
        """
        Ready for another fit
        """
        if self.fitproblem_count != None and self.fitproblem_count > 1:
            calc_fit.ready(2.5)
        else:
            time.sleep(0.4)
            
    def remove_plot(self, uid, fid=None, theory=False):
        """
        remove model plot when a fit page is closed
        :param uid: the id related to the fitpage to close
        :param fid: the id of the fitproblem(data, model, range,etc)
        """
        if uid not in self.page_finder.keys():
            return
        fitproblemList = self.page_finder[uid].get_fit_problem(fid)
        for fitproblem in fitproblemList:
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
           
    def store_data(self, uid, data_list=None, caption=None):
        """
        Recieve a list of data and store them ans well as a caption of
        the fit page where they come from.
        :param uid: if related to a fit page
        :param data_list: list of data to fit
        :param caption: caption of the window related to these data
        """
        if data_list is None:
            data_list = []
        self.page_finder[uid].set_fit_data(data=data_list)
        if caption is not None:
            self.page_finder[uid].set_fit_tab_caption(caption=caption)
        
    def on_add_new_page(self, event=None):
        """
        ask fit panel to create a new empty page
        """
        try:
            page = self.fit_panel.add_empty_page()
            page_caption = page.window_caption
            # add data associated to the page created
            if page != None:  
                wx.PostEvent(self.parent, StatusEvent(status="Page Created",
                                               info="info"))
            else:
                msg = "Page was already Created"
                wx.PostEvent(self.parent, StatusEvent(status=msg,
                                                       info="warning"))
            self.set_top_panel()
        except:
            msg = "Creating Fit page: %s"%sys.exc_value
            wx.PostEvent(self.parent, StatusEvent(status=msg, info="error"))
        
    def add_fit_page(self, data):
        """
        given a data, ask to the fitting panel to create a new fitting page,
        get this page and store it into the page_finder of this plug-in
        :param data: is a list of data
        """
        page = self.fit_panel.set_data(data)
        page_caption = page.window_caption
        #append Data1D to the panel containing its theory
        #if theory already plotted
        if page.uid in self.page_finder:
            data = page.get_data()
            theory_data = self.page_finder[page.uid].get_theory_data(data.id)
            if issubclass(data.__class__, Data2D):
                data.group_id = wx.NewId()
                if theory_data is not None:
                    group_id = str(page.uid) + " Model1D"
                    wx.PostEvent(self.parent, 
                             NewPlotEvent(group_id=group_id,
                                               action="delete"))
                    self.parent.update_data(prev_data=theory_data,
                                             new_data=data)      
            else:
                if theory_data is not None:
                    group_id = str(page.uid) + " Model2D"
                    data.group_id = theory_data.group_id
                    wx.PostEvent(self.parent, 
                             NewPlotEvent(group_id=group_id,
                                               action="delete"))
                    self.parent.update_data(prev_data=theory_data,
                                             new_data=data)   
              
        self.store_data(uid=page.uid, data_list=page.get_data_list(), 
                        caption=page.window_caption)
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
            name = event.panel_name
            if self.parent.panels[item].window_caption.startswith(name):
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
  
    def _reset_schedule_problem(self, value=0, uid=None):
        """
        unschedule or schedule all fitproblem to be fit
        """
        # case that uid is not specified
        if uid == None:
            for page_id in self.page_finder.keys():
                self.page_finder[page_id].schedule_tofit(value)
        # when uid is given
        else:
            if uid in self.page_finder.keys():
                self.page_finder[uid].schedule_tofit(value)
                
    def _fit_helper(self, value, pars, fitter_list):
        """
        Create and set fit engine with series of data and model
        :param pars: list of fittable parameters
        :param fitter_list: list of fit engine
        :param value:  structure storing data mapped to their model, range etc..
        """
        fit_id = 0
        for fitproblem in  value.get_fit_problem():
            fitter = Fit(self._fit_engine)
            data = fitproblem.get_fit_data()
            model = fitproblem.get_model()
            smearer = fitproblem.get_smearer()
            qmin, qmax = fitproblem.get_range()
            #Extra list of parameters and their constraints
            listOfConstraint = []
            param = fitproblem.get_model_param()
            if len(param) > 0:
                for item in param:
                    ## check if constraint
                    if item[0] != None and item[1] != None:
                        listOfConstraint.append((item[0],item[1]))
            fitter.set_model(model, fit_id, pars, constraints=listOfConstraint)
            fitter.set_data(data=data, id=fit_id, smearer=smearer, qmin=qmin, 
                            qmax=qmax)
            fitter.select_problem_for_fit(id=fit_id, value=1)
            fitter_list.append(fitter)
            fit_id += 1
        value.clear_model_param()
       
    def _onSelect(self,event):
        """ 
        when Select data to fit a new page is created .Its reference is 
        added to self.page_finder
        """
        self.panel = event.GetEventObject()
        Plugin.on_perspective(self, event=event)
        for plottable in self.panel.graph.plottables:
            if plottable.__class__.__name__ in ["Data1D", "Theory1D"]:
                data_id = self.panel.graph.selected_plottable
                if plottable == self.panel.plots[data_id]:
                    data = plottable
                    self.add_fit_page(data=[data])
                    return
            else:
                data = plottable
                self.add_fit_page(data=[data])
        self.set_top_panel()
            
    def update_fit(self, result=None, msg=""):
        """
        """
        print "update_fit result", result
        
    def _batch_single_fit_complete_helper(self, result, pars, page_id, 
                                          elapsed=None):
        """
        Display fit result in batch 
        :param result: list of objects received fromt fit engines
        :param pars: list of  fitted parameters names
        :param page_id: list of page ids which called fit function
        :param elapsed: time spent at the fitting level
        """
        self._update_fit_button(page_id)
        msg = "Single Fitting complete "
        wx.PostEvent(self.parent, StatusEvent(status=msg, info="info",
                                                      type="stop"))
        if self.batch_on:
            batch_result = {"Chi2":[]}
            for index  in range(len(pars)):
                    batch_result[pars[index]] = []
                    batch_result["error on %s" % pars[index]] = []
            for res in result:
                batch_result["Chi2"].append(res.fitness)
                for index  in range(len(pars)):
                    batch_result[pars[index]].append(res.pvec[index])
                    item = res.stderr[index]
                    batch_result["error on %s" % pars[index]].append(item)
            pid = page_id[0]
            self.page_finder[pid].set_result(result=batch_result)      
            self.parent.on_set_batch_result(data=batch_result, 
                                            name=self.sub_menu)
            for uid in page_id:
                cpage = self.fit_panel.get_page_by_id(uid)
                cpage._on_fit_complete()
            
    def _single_fit_completed(self, result, pars, page_id, elapsed=None):
        """
         Display fit result on one page of the notebook.
        :param result: list of object generated when fit ends
        :param pars: list of names of parameters fitted
        :param page_id: list of page ids which called fit function
        :param elapsed: time spent at the fitting level
        """  
        self._mac_sleep(0.2)
        if page_id[0] in self.fit_thread_list.keys():
            del self.fit_thread_list[page_id[0]] 
        if self.batch_on:
            wx.CallAfter(self._batch_single_fit_complete_helper,
                          result, pars, page_id, elapsed=None)
            return 
        else:  
            try:
                result = result[0]
                if result == None:
                    self._update_fit_button(page_id)
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
                    self._update_fit_button(page_id)
                    return
                
                for uid in page_id:
                    cpage = self.fit_panel.get_page_by_id(uid)
                    # Make sure we got all results 
                    #(CallAfter is important to MAC)
                    wx.CallAfter(cpage.onsetValues, result.fitness, pars, 
                                 result.pvec, result.stderr)
                    cpage._on_fit_complete()
                if result.stderr == None:
                    msg = "Fit Abort: "
                else:
                    msg = "Fitting: "
                msg += "Completed!!!"
                wx.PostEvent(self.parent, StatusEvent(status=msg))
            except ValueError:
                self._update_fit_button(page_id)
                msg = "Single Fitting did not converge!!!"
                wx.PostEvent(self.parent, StatusEvent(status=msg, info="error",
                                                      type="stop"))
            except:
                self._update_fit_button(page_id)
                msg = "Single Fit completed but Following"
                msg += " error occurred:%s" % sys.exc_value
                wx.PostEvent(self.parent, StatusEvent(status=msg, info="error",
                                                      type="stop"))
                raise
               
    def _simul_fit_completed(self, result, page_id, pars=None, elapsed=None):
        """
        Display result of the fit on related panel(s).
        :param result: list of object generated when fit ends
        :param pars: list of names of parameters fitted
        :param page_id: list of page ids which called fit function
        :param elapsed: time spent at the fitting level
        """
        result = result 
        self.fit_thread_list = {}
        if page_id is None:
            page_id = []
        ## fit more than 1 model at the same time 
        self._mac_sleep(0.2) 
        try:
            msg = "" 
            if result == None:
                self._update_fit_button(page_id)
                msg= "Complex Fitting did not converge!!!"
                wx.PostEvent(self.parent, StatusEvent(status=msg,
                                                      type="stop"))
                return
            if not numpy.isfinite(result.fitness) or \
                numpy.any(result.pvec == None) or not \
                numpy.all(numpy.isfinite(result.pvec)):
                self._update_fit_button(page_id)
                msg= "Simultaneous Fitting did not converge!!!"
                wx.PostEvent(self.parent, StatusEvent(status=msg,type="stop"))
                return
              
            for uid in page_id:   
                fpdict = self.page_finder[uid]
                for value in ftpdict.itervalues():
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
                wx.CallAfter(cpage.onsetValues, 
                                    result.fitness,
                                  small_param_name,
                                  small_out,small_cov)
                cpage._on_fit_complete()
                msg = "Fit completed!"
                wx.PostEvent(self.parent, StatusEvent(status=msg))
        except Exception:
            self._update_fit_button(page_id)
            msg = "Complex Fitting did not converge!!!"
            wx.PostEvent(self.parent, StatusEvent(status=msg, info="error",
                                                  type="stop"))
            return
        except:
            self._update_fit_button(page_id)
            msg = "Simultaneous Fit completed"
            msg += " but Following error occurred:%s" % sys.exc_value
            wx.PostEvent(self.parent, StatusEvent(status=msg, type="stop"))
    
    def _update_fit_button(self, page_id):
        """
        Update Fit button when fit stopped
        
        : parameter page_id: fitpage where the button is
        """
        if page_id.__class__.__name__ != 'list':
            page_id = [page_id]
        for uid in page_id:  
            page = self.fit_panel.get_page_by_id(uid)
            page._on_fit_complete()
        
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
                    if hasattr(self.parent.panels[item], "uid"):
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
        if engine == "park":
            self.menu1.FindItemById(self.park_id).Check(True)
            self.menu1.FindItemById(self.scipy_id).Check(False)
        else:
            self.menu1.FindItemById(self.park_id).Check(False)
            self.menu1.FindItemById(self.scipy_id).Check(True)
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
        caption = evt.caption
        enable_smearer = evt.enable_smearer
        if model == None:
            return
        if uid not in self.page_finder.keys():
            return
        # save the name containing the data name with the appropriate model
        self.page_finder[uid].set_model(model)
        self.page_finder[uid].enable_smearing(enable_smearer)
        self.page_finder[uid].set_range(qmin=qmin, qmax=qmax)
        self.page_finder[uid].set_fit_tab_caption(caption=caption)
        if self.sim_page is not None:
            self.sim_page.draw_page()
        
    def _update1D(self, x, output):
        """
        Update the output of plotting model 1D
        """
        msg = "Plot updating ... "
        wx.PostEvent(self.parent, StatusEvent(status=msg,type="update"))
        
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
            _yaxis, _yunit = data.get_yaxis() 
            _xaxis, _xunit = data.get_xaxis() 
            new_plot.title = data.name
            new_plot.group_id = data.group_id
            new_plot.id =  str(page_id) + "model"
            if new_plot.id in self.color_dict:
                new_plot.custom_color = self.color_dict[new_plot.id] 
            #find if this theory was already plotted and replace that plot given
            #the same id
            theory_data = self.page_finder[page_id].get_theory_data(fid=data.id)
            new_plot.name = model.name + " ["+ str(model.__class__.__name__)+"]"
            new_plot.xaxis(_xaxis, _xunit)
            new_plot.yaxis(_yaxis, _yunit)
            self.page_finder[page_id].set_theory_data(data=new_plot, fid=data.id)
            self.parent.update_theory(data_id=data.id, theory=new_plot,
                                       state=state)   
            current_pg = self.fit_panel.get_page_by_id(page_id)
            title = new_plot.title
            wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot,
                                            title=str(title)))
            caption = current_pg.window_caption
            self.page_finder[page_id].set_fit_tab_caption(caption=caption)
            self.page_finder[page_id].set_theory_data(data=new_plot, 
                                                      fid=data.id)
            if toggle_mode_on:
                wx.PostEvent(self.parent, 
                             NewPlotEvent(group_id=str(page_id) + " Model2D",
                                               action="Hide"))
            else:
                if update_chisqr:
                    wx.PostEvent(current_pg,
                                 Chi2UpdateEvent(output=self._cal_chisqr(data=data,
                                                            page_id=page_id,
                                                            index=index)))
                else:
                    self._plot_residuals(page_id, data, index)

            msg = "Computation  completed!"
            wx.PostEvent( self.parent, StatusEvent(status=msg, type="stop" ))
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
        #self.ready_fit()
  
    def _complete2D(self, image, data, model, page_id,  elapsed, index, qmin,
                     qmax, toggle_mode_on=False,state=None,qstep=DEFAULT_NPTS, 
                     update_chisqr=True):
        """
        Complete get the result of modelthread and create model 2D
        that can be plot.
        """
        new_plot= Data2D(image=image, err_image=data.err_data)
        new_plot.name = model.name
        new_plot.title = "Analytical model 2D "
        new_plot.id = str(page_id) + "model"
        new_plot.group_id = data.group_id
        new_plot.detector = data.detector
        new_plot.source = data.source
        new_plot.is_data = False 
        new_plot.qx_data = data.qx_data
        new_plot.qy_data = data.qy_data
        new_plot.q_data = data.q_data
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
        
        self.page_finder[page_id].set_theory_data(data=theory_data, fid=data.id)
        self.parent.update_theory(data_id=data.id, 
                                       theory=new_plot,
                                       state=state)  
        current_pg = self.fit_panel.get_page_by_id(page_id)
        title = new_plot.title
        wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot,
                                               title=title))
        self.page_finder[page_id].set_theory_data(data=new_plot, fid=data.id)
        if toggle_mode_on:
            wx.PostEvent(self.parent, 
                             NewPlotEvent(group_id=str(page_id) + " Model1D",
                                               action="Hide"))
        else:
            # Chisqr in fitpage
            if update_chisqr:
                wx.PostEvent(current_pg,
                             Chi2UpdateEvent(output=self._cal_chisqr(data=data,
                                                         page_id=page_id,
                                                         index=index)))
            else:
                self._plot_residuals(page_id, data, index)
        msg = "Computation  completed!"
        wx.PostEvent(self.parent, StatusEvent(status=msg, type="stop"))
    
    def _draw_model2D(self, model, page_id, qmin,
                      qmax,
                      data=None, smearer=None,
                      description=None, enable2D=False,
                      state=None,
                      toggle_mode_on=False,
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
        if not enable2D:
            return None
        try:
            from model_thread import Calc2D
            ## If a thread is already started, stop it
            if (self.calc_2D is not None) and self.calc_2D.isrunning():
                self.calc_2D.stop()
            self.calc_2D = Calc2D(model=model, 
                                    data=data,
                                    page_id=page_id,
                                    smearer=smearer,
                                    qmin=qmin,
                                    qmax=qmax,
                                    toggle_mode_on=toggle_mode_on,
                                    state=state,
                                    completefn=self._complete2D,
                                    update_chisqr=update_chisqr)
            self.calc_2D.queue()

        except:
            raise
            #msg = " Error occurred when drawing %s Model 2D: " % model.name
            #msg += " %s" % sys.exc_value
            #wx.PostEvent(self.parent, StatusEvent(status=msg))

    def _draw_model1D(self, model, page_id, data, 
                      qmin, qmax, smearer=None,
                state=None,
                toggle_mode_on=False, update_chisqr=True, 
                enable1D=True):
        """
        Draw model 1D from loaded data1D
        
        :param data: loaded data
        :param model: the model to plot
        
        """
        if not enable1D:
            return 
        try:
            from model_thread import Calc1D
            ## If a thread is already started, stop it
            if (self.calc_1D is not None) and self.calc_1D.isrunning():
                self.calc_1D.stop()
            self.calc_1D = Calc1D(data=data,
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
    
  
    
    def _cal_chisqr(self, page_id, data, index=None): 
        """
        Get handy Chisqr using the output from draw1D and 2D, 
        instead of calling expansive CalcChisqr in guithread
        """
        # default chisqr
        chisqr = None
        #to compute chisq make sure data has valid data
        # return None if data == None
        if not check_data_validity(data):
            return chisqr
        
        # Get data: data I, theory I, and data dI in order
        if data.__class__.__name__ == "Data2D":
            if index == None: 
                index = numpy.ones(len(data.data),ntype=bool)
            # get rid of zero error points
            index = index & (data.err_data != 0)  
            index = index & (numpy.isfinite(data.data)) 
            fn = data.data[index] 
            theory_data = self.page_finder[page_id].get_theory_data(fid=data.id)
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
            theory_data = self.page_finder[page_id].get_theory_data(fid=data.id)
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
        # Get data: data I, theory I, and data dI in order
        if data.__class__.__name__ == "Data2D":
            # build residuals
            residuals = Data2D()
            #residuals.copy_from_datainfo(data)
            # Not for trunk the line below, instead use the line above
            data.clone_without_data(len(data.data), residuals)
            residuals.data = None
            fn = data.data#[index] 
            theory_data = self.page_finder[page_id].get_theory_data(fid=data.id)
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
            theory_data = self.page_finder[page_id].get_theory_data(fid=data.id)
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
    
    
    
    